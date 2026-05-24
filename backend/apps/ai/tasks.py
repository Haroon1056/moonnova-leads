from celery import shared_task
from django.db.models import F
from django.utils import timezone

from apps.leads.models import Lead
from apps.monitoring.models import SystemEvent
from apps.monitoring.services import log_exception_event

from apps.realtime.events import (
    send_ai_job_progress,
    send_ai_lead_completed,
    send_ai_job_completed,
    send_ai_job_failed,
)

from .models import AIJob
from .services import generate_ai_lead_insight, get_ai_options_from_job


def get_ai_monitoring_source():
    return getattr(SystemEvent, "SOURCE_AI", SystemEvent.SOURCE_SYSTEM)


def safe_send_ai_job_progress(job):
    try:
        send_ai_job_progress(job.user_id, job)
    except Exception:
        pass


def safe_send_ai_job_completed(job):
    try:
        send_ai_job_completed(job.user_id, job)
    except Exception:
        pass


def safe_send_ai_job_failed(job):
    try:
        send_ai_job_failed(job.user_id, job)
    except Exception:
        pass


def safe_send_ai_lead_completed(user_id, job, lead, insight):
    try:
        send_ai_lead_completed(
            user_id=user_id,
            job=job,
            lead=lead,
            insight=insight,
        )
    except Exception:
        pass


def finalize_ai_job_if_done(job_id):
    """
    Finalize parent AI job immediately when all child lead tasks are processed.

    This fixes the issue where frontend shows:
    AI Job running
    1/1 done

    because completed_items was updated but job.status stayed running.
    """

    if not job_id:
        return None

    job = AIJob.objects.filter(id=job_id).first()

    if not job:
        return None

    processed = (
        int(job.completed_items or 0)
        + int(job.failed_items or 0)
        + int(job.skipped_items or 0)
    )

    if not job.total_items:
        return job

    if processed < job.total_items:
        return job

    if job.status in [
        AIJob.STATUS_COMPLETED,
        AIJob.STATUS_FAILED,
        AIJob.STATUS_CANCELLED,
    ]:
        return job

    if job.completed_items == 0 and job.failed_items > 0:
        job.status = AIJob.STATUS_FAILED
        job.error_message = job.error_message or "All AI items failed."
    else:
        job.status = AIJob.STATUS_COMPLETED

    job.completed_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "error_message",
            "completed_at",
            "updated_at",
        ]
    )

    if job.status == AIJob.STATUS_FAILED:
        safe_send_ai_job_failed(job)
    else:
        safe_send_ai_job_completed(job)

    return job


def mark_ai_job_running(job):
    if not job:
        return None

    if job.status in [
        AIJob.STATUS_COMPLETED,
        AIJob.STATUS_FAILED,
        AIJob.STATUS_CANCELLED,
    ]:
        return job

    if not job.started_at:
        job.started_at = timezone.now()

    job.status = AIJob.STATUS_RUNNING
    job.save(
        update_fields=[
            "status",
            "started_at",
            "updated_at",
        ]
    )

    safe_send_ai_job_progress(job)

    return job


def mark_ai_job_item_completed(job, credits_used=0, skipped=False):
    if not job:
        return None

    if skipped:
        AIJob.objects.filter(id=job.id).update(
            skipped_items=F("skipped_items") + 1
        )
    else:
        AIJob.objects.filter(id=job.id).update(
            completed_items=F("completed_items") + 1,
            credits_used=F("credits_used") + int(credits_used or 0),
        )

    job.refresh_from_db()
    safe_send_ai_job_progress(job)

    return finalize_ai_job_if_done(job.id)


def mark_ai_job_item_failed(job, error_message):
    if not job:
        return None

    AIJob.objects.filter(id=job.id).update(
        failed_items=F("failed_items") + 1,
        error_message=str(error_message)[:1000],
    )

    job.refresh_from_db()
    safe_send_ai_job_progress(job)

    return finalize_ai_job_if_done(job.id)


@shared_task(bind=True, max_retries=1)
def generate_ai_for_lead_task(self, lead_id, job_id=None, force=False):
    """
    Generate AI insight for one lead.

    Professional behavior:
    - Loads lead and parent job.
    - Uses job options.
    - Generates full AI insight.
    - Updates completed/failed/skipped counters.
    - Finalizes parent job immediately when all items are done.
    """

    lead = (
        Lead.objects.filter(id=lead_id)
        .select_related("search", "search__user")
        .first()
    )

    if not lead:
        return {
            "status": "not_found",
            "lead_id": lead_id,
        }

    job = AIJob.objects.filter(id=job_id).first() if job_id else None
    options = get_ai_options_from_job(job) if job else {}

    if job:
        mark_ai_job_running(job)

    try:
        result = generate_ai_lead_insight(
            lead=lead,
            user=lead.search.user,
            job=job,
            force=force,
            options=options,
        )

        insight = result["insight"]
        credits_used = int(result.get("credits_used") or 0)
        skipped = bool(result.get("skipped"))

        if job:
            job = mark_ai_job_item_completed(
                job=job,
                credits_used=credits_used,
                skipped=skipped,
            )

        safe_send_ai_lead_completed(
            user_id=lead.search.user_id,
            job=job,
            lead=lead,
            insight=insight,
        )

        return {
            "status": "skipped" if skipped else "completed",
            "lead_id": lead.id,
            "insight_id": insight.id,
            "credits_used": credits_used,
            "job_id": job.id if job else None,
            "job_status": job.status if job else None,
            "target_offer": insight.target_offer,
            "ai_suggested_offer": insight.ai_suggested_offer,
        }

    except Exception as exc:
        if job:
            job = mark_ai_job_item_failed(job, exc)

        log_exception_event(
            exc,
            source=get_ai_monitoring_source(),
            title="AI lead task failed",
            user=lead.search.user,
            task_name="generate_ai_for_lead_task",
            task_id=getattr(self.request, "id", None),
            object_type="lead",
            object_id=lead.id,
            metadata={
                "lead_id": lead.id,
                "job_id": job_id,
                "target_offer": options.get("target_offer"),
                "campaign_goal": options.get("campaign_goal"),
            },
        )

        return {
            "status": "failed",
            "lead_id": lead.id,
            "job_id": job.id if job else job_id,
            "job_status": job.status if job else None,
            "error": str(exc),
        }


@shared_task
def bulk_generate_ai_task(job_id, force=False):
    """
    Queue AI generation for all leads in one AIJob.

    Important:
    - Parent job goes running immediately.
    - Child tasks run in default queue.
    - If there are no lead IDs, job completes immediately.
    """

    job = AIJob.objects.filter(id=job_id).first()

    if not job:
        return {
            "status": "not_found",
            "job_id": job_id,
        }

    lead_ids = list(job.lead_ids or [])

    if not lead_ids:
        job.status = AIJob.STATUS_COMPLETED
        job.total_items = 0
        job.completed_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "total_items",
                "completed_at",
                "updated_at",
            ]
        )

        safe_send_ai_job_completed(job)

        return {
            "status": "completed",
            "job_id": job.id,
            "total_items": 0,
        }

    job.status = AIJob.STATUS_RUNNING
    job.started_at = job.started_at or timezone.now()
    job.total_items = len(lead_ids)
    job.completed_items = 0
    job.failed_items = 0
    job.skipped_items = 0
    job.error_message = None
    job.save(
        update_fields=[
            "status",
            "started_at",
            "total_items",
            "completed_items",
            "failed_items",
            "skipped_items",
            "error_message",
            "updated_at",
        ]
    )

    safe_send_ai_job_progress(job)

    for lead_id in lead_ids:
        generate_ai_for_lead_task.apply_async(
            kwargs={
                "lead_id": lead_id,
                "job_id": job.id,
                "force": force,
            },
            queue="default",
        )

    return {
        "status": "queued",
        "job_id": job.id,
        "total_items": job.total_items,
        "target_offer": job.target_offer,
    }


@shared_task
def finalize_ai_jobs_task():
    """
    Safety cleanup task.

    It marks any running AI jobs completed/failed if all child items are already processed.
    This is a backup. Normal finalization happens immediately in generate_ai_for_lead_task.
    """

    running_jobs = AIJob.objects.filter(status=AIJob.STATUS_RUNNING)

    completed_count = 0

    for job in running_jobs:
        before_status = job.status
        finalized_job = finalize_ai_job_if_done(job.id)

        if finalized_job and finalized_job.status != before_status:
            completed_count += 1

    return {
        "completed_jobs": completed_count,
    }