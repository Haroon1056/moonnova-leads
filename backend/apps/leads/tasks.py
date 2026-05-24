from celery import shared_task
from django.db.models import F
from django.utils import timezone

from .models import Lead, LeadEnrichmentJob, ExportHistory
from .exporter import generate_export_file, mark_export_failed
from .services import apply_website_enrichment_to_lead
from .cleanup import cleanup_all_users_data, cleanup_user_data

from apps.monitoring.services import log_exception_event
from apps.monitoring.models import SystemEvent

from apps.realtime.events import (
    send_enrichment_progress,
    send_lead_enriched,
    send_export_completed,
    send_export_failed,
)

from apps.services.enrichment.website_checker import check_website_status


def mark_lead_enrichment_running(lead):
    Lead.objects.filter(id=lead.id).update(
        enrichment_status=Lead.ENRICHMENT_STATUS_RUNNING,
        enrichment_attempts=F("enrichment_attempts") + 1,
        enrichment_error=None,
        enrichment_last_run_at=timezone.now(),
    )


def mark_lead_enrichment_failed(lead, error_message):
    Lead.objects.filter(id=lead.id).update(
        enrichment_status=Lead.ENRICHMENT_STATUS_FAILED,
        enrichment_error=str(error_message)[:1000],
        enrichment_last_run_at=timezone.now(),
    )


def should_skip_enrichment(lead, force=False):
    if force:
        return False

    if lead.enrichment_status == Lead.ENRICHMENT_STATUS_RUNNING:
        return True

    if lead.enrichment_status == Lead.ENRICHMENT_STATUS_COMPLETED and lead.email_1:
        return True

    return False


def send_job_progress_if_available(job_id, user_id):
    if not job_id:
        return

    job = LeadEnrichmentJob.objects.filter(id=job_id).first()

    if job:
        send_enrichment_progress(user_id, job)


def mark_job_completed_if_done(job_id, user_id):
    if not job_id:
        return

    job = LeadEnrichmentJob.objects.filter(id=job_id).first()

    if not job:
        return

    processed = job.completed_items + job.failed_items + job.skipped_items

    if job.total_items and processed >= job.total_items:
        job.status = LeadEnrichmentJob.STATUS_COMPLETED
        job.completed_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        send_enrichment_progress(user_id, job)


@shared_task(bind=True, max_retries=2)
def enrich_lead_website_task(self, lead_id, job_id=None, force=False):
    """
    Enrich one lead website.

    Professional behavior:
    - Runs only when explicitly queued.
    - Does not start from scraper automatically.
    - Tracks lead enrichment status.
    - Updates enrichment job progress.
    - Sends realtime lead_enriched and enrichment_progress events.
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

    if should_skip_enrichment(lead, force=force):
        if job_id:
            LeadEnrichmentJob.objects.filter(id=job_id).update(
                skipped_items=F("skipped_items") + 1
            )

            send_job_progress_if_available(
                job_id=job_id,
                user_id=lead.search.user_id,
            )

            mark_job_completed_if_done(
                job_id=job_id,
                user_id=lead.search.user_id,
            )

        return {
            "status": "skipped",
            "lead_id": lead.id,
            "reason": "Already running or already enriched.",
        }

    mark_lead_enrichment_running(lead)

    try:
        result = check_website_status(lead.website)

        lead.refresh_from_db()

        apply_website_enrichment_to_lead(lead, result)

        lead.refresh_from_db()

        send_lead_enriched(lead.search.user_id, lead)

        if job_id:
            LeadEnrichmentJob.objects.filter(id=job_id).update(
                completed_items=F("completed_items") + 1
            )

            send_job_progress_if_available(
                job_id=job_id,
                user_id=lead.search.user_id,
            )

            mark_job_completed_if_done(
                job_id=job_id,
                user_id=lead.search.user_id,
            )

        return {
            "status": "completed",
            "lead_id": lead.id,
            "website_status": result.get("website_status"),
            "http_status": result.get("website_http_status"),
            "emails": result.get("emails") or [],
            "email_confidence": result.get("email_confidence") or 0,
        }

    except Exception as exc:
        lead.refresh_from_db()

        if lead.enrichment_attempts < 3:
            try:
                raise self.retry(exc=exc, countdown=30)
            except self.MaxRetriesExceededError:
                pass

        mark_lead_enrichment_failed(lead, exc)

        if job_id:
            LeadEnrichmentJob.objects.filter(id=job_id).update(
                failed_items=F("failed_items") + 1
            )

            send_job_progress_if_available(
                job_id=job_id,
                user_id=lead.search.user_id,
            )

            mark_job_completed_if_done(
                job_id=job_id,
                user_id=lead.search.user_id,
            )

        log_exception_event(
            exc,
            source=SystemEvent.SOURCE_ENRICHMENT,
            title="Lead enrichment failed",
            user=lead.search.user,
            task_name="enrich_lead_website_task",
            task_id=getattr(self.request, "id", None),
            object_type="lead",
            object_id=lead.id,
            metadata={
                "lead_id": lead.id,
                "job_id": job_id,
                "website": lead.website,
                "force": force,
            },
        )

        return {
            "status": "failed",
            "lead_id": lead.id,
            "error": str(exc),
        }


@shared_task
def bulk_enrich_leads_task(lead_ids, job_id=None, force=False):
    """
    Queue enrichment for multiple leads.

    Important:
    - Child enrichment tasks go to enrichment queue.
    - This prevents scraping queue from being blocked.
    """

    valid_lead_ids = list(
        Lead.objects.filter(id__in=lead_ids)
        .values_list("id", flat=True)
    )

    if job_id:
        LeadEnrichmentJob.objects.filter(id=job_id).update(
            status=LeadEnrichmentJob.STATUS_RUNNING,
            total_items=len(valid_lead_ids),
            started_at=timezone.now(),
        )

        job = LeadEnrichmentJob.objects.filter(id=job_id).first()

        if job:
            send_enrichment_progress(job.user_id, job)

    if not valid_lead_ids:
        if job_id:
            job = LeadEnrichmentJob.objects.filter(id=job_id).first()

            if job:
                job.status = LeadEnrichmentJob.STATUS_COMPLETED
                job.completed_at = timezone.now()
                job.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "updated_at",
                    ]
                )
                send_enrichment_progress(job.user_id, job)

        return {
            "status": "completed",
            "total": 0,
            "job_id": job_id,
        }

    for lead_id in valid_lead_ids:
        enrich_lead_website_task.apply_async(
            kwargs={
                "lead_id": lead_id,
                "job_id": job_id,
                "force": force,
            },
            queue="enrichment",
        )

    return {
        "status": "queued",
        "total": len(valid_lead_ids),
        "job_id": job_id,
    }


@shared_task
def enrich_search_leads_task(search_id, job_id=None, force=False):
    """
    Queue enrichment for all leads inside one search.

    Important:
    - This is called only after scraping completes.
    - It should not run if search.email_enrichment is False.
    """

    lead_ids = list(
        Lead.objects.filter(search_id=search_id)
        .values_list("id", flat=True)
    )

    if job_id:
        LeadEnrichmentJob.objects.filter(id=job_id).update(
            status=LeadEnrichmentJob.STATUS_RUNNING,
            total_items=len(lead_ids),
            started_at=timezone.now(),
        )

        job = LeadEnrichmentJob.objects.filter(id=job_id).first()

        if job:
            send_enrichment_progress(job.user_id, job)

    if not lead_ids:
        if job_id:
            job = LeadEnrichmentJob.objects.filter(id=job_id).first()

            if job:
                job.status = LeadEnrichmentJob.STATUS_COMPLETED
                job.completed_at = timezone.now()
                job.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "updated_at",
                    ]
                )
                send_enrichment_progress(job.user_id, job)

        return {
            "status": "completed",
            "search_id": search_id,
            "total": 0,
            "job_id": job_id,
        }

    for lead_id in lead_ids:
        enrich_lead_website_task.apply_async(
            kwargs={
                "lead_id": lead_id,
                "job_id": job_id,
                "force": force,
            },
            queue="enrichment",
        )

    return {
        "status": "queued",
        "search_id": search_id,
        "total": len(lead_ids),
        "job_id": job_id,
    }


@shared_task
def finalize_enrichment_jobs_task():
    """
    Mark running enrichment jobs completed when all items are processed.
    """

    running_jobs = LeadEnrichmentJob.objects.filter(
        status=LeadEnrichmentJob.STATUS_RUNNING
    )

    updated = 0

    for job in running_jobs:
        processed = job.completed_items + job.failed_items + job.skipped_items

        if job.total_items and processed >= job.total_items:
            job.status = LeadEnrichmentJob.STATUS_COMPLETED
            job.completed_at = timezone.now()
            job.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )

            send_enrichment_progress(job.user_id, job)

            updated += 1

    return {
        "completed_jobs": updated,
    }


@shared_task(bind=True, max_retries=1)
def generate_export_file_task(self, export_id):
    """
    Generate CSV/XLSX export file in background.
    """

    export_history = (
        ExportHistory.objects.filter(id=export_id)
        .select_related(
            "user",
            "search",
            "lead_list",
        )
        .first()
    )

    if not export_history:
        return {
            "status": "not_found",
            "export_id": export_id,
        }

    if export_history.status == ExportHistory.STATUS_COMPLETED:
        return {
            "status": "already_completed",
            "export_id": export_id,
        }

    try:
        generate_export_file(export_history)

        export_history.refresh_from_db()

        send_export_completed(export_history.user_id, export_history)

        return {
            "status": "completed",
            "export_id": export_history.id,
            "file_name": export_history.file_name,
            "total_rows": export_history.total_rows,
        }

    except Exception as exc:
        try:
            raise self.retry(exc=exc, countdown=20)
        except self.MaxRetriesExceededError:
            mark_export_failed(export_history, exc)

            export_history.refresh_from_db()

            send_export_failed(export_history.user_id, export_history)

            log_exception_event(
                exc,
                source=SystemEvent.SOURCE_EXPORT,
                title="Export generation failed",
                user=export_history.user,
                task_name="generate_export_file_task",
                task_id=getattr(self.request, "id", None),
                object_type="export",
                object_id=export_history.id,
                metadata={
                    "export_id": export_history.id,
                    "export_type": export_history.export_type,
                    "export_scope": export_history.export_scope,
                    "filters": export_history.filters,
                },
            )

            return {
                "status": "failed",
                "export_id": export_history.id,
                "error": str(exc),
            }


@shared_task
def cleanup_all_users_data_task():
    """
    Scheduled cleanup task for all users.
    """

    return cleanup_all_users_data()


@shared_task
def cleanup_user_data_task(user_id):
    """
    Manual cleanup task for one user.
    """

    from django.contrib.auth import get_user_model

    User = get_user_model()

    user = User.objects.filter(id=user_id).first()

    if not user:
        return {
            "status": "failed",
            "message": "User not found",
        }

    result = cleanup_user_data(user)

    return {
        "status": "completed",
        "result": result,
    }