import logging

from celery import shared_task
from django.db import transaction, close_old_connections
from django.db.models import Count
from django.utils import timezone

from .models import Search, SearchQueryTask
from apps.services.scraper.engine import run_scraper
from apps.usage.services import check_account_allowed

from apps.monitoring.services import log_exception_event
from apps.monitoring.models import SystemEvent

from apps.realtime.events import (
    send_search_progress,
    send_search_completed,
    send_search_failed,
)

logger = logging.getLogger(__name__)


def build_query_text(keyword, location):
    return f"{keyword} in {location}"


def create_query_tasks_for_search(search):
    created_count = 0

    for keyword in search.keywords:
        for location in search.locations:
            query_text = build_query_text(keyword, location)

            _, created = SearchQueryTask.objects.get_or_create(
                search=search,
                keyword=keyword,
                location=location,
                defaults={
                    "query_text": query_text,
                    "max_leads": search.max_leads,
                    "status": SearchQueryTask.STATUS_PENDING,
                },
            )

            if created:
                created_count += 1

    total_tasks = SearchQueryTask.objects.filter(search=search).count()

    search.total_tasks = total_tasks
    search.save(update_fields=["total_tasks", "updated_at"])

    return created_count


def refresh_search_counters(search_id):
    search = Search.objects.get(id=search_id)

    counts = (
        SearchQueryTask.objects.filter(search=search)
        .values("status")
        .annotate(total=Count("id"))
    )

    count_map = {item["status"]: item["total"] for item in counts}

    completed = count_map.get(SearchQueryTask.STATUS_COMPLETED, 0)
    failed = count_map.get(SearchQueryTask.STATUS_FAILED, 0)
    cancelled = count_map.get(SearchQueryTask.STATUS_CANCELLED, 0)
    skipped = count_map.get(SearchQueryTask.STATUS_SKIPPED, 0)
    paused = count_map.get(SearchQueryTask.STATUS_PAUSED, 0)

    search.completed_tasks = completed
    search.failed_tasks = failed + cancelled + skipped

    total_done = search.completed_tasks + search.failed_tasks

    if search.status in [
        Search.STATUS_PAUSED,
        Search.STATUS_CANCELLED,
        Search.STATUS_FAILED,
    ]:
        search.save(
            update_fields=[
                "completed_tasks",
                "failed_tasks",
                "updated_at",
            ]
        )
        return search

    if paused > 0:
        search.status = Search.STATUS_PAUSED

    elif search.total_tasks and total_done >= search.total_tasks:
        if completed == 0 and search.failed_tasks > 0:
            search.status = Search.STATUS_FAILED
            search.error_message = "All search query tasks failed."
        else:
            search.status = Search.STATUS_COMPLETED
            search.completed_at = timezone.now()

    else:
        search.status = Search.STATUS_RUNNING

    search.save(
        update_fields=[
            "completed_tasks",
            "failed_tasks",
            "status",
            "completed_at",
            "error_message",
            "updated_at",
        ]
    )

    return search


def get_next_pending_task(search):
    return (
        SearchQueryTask.objects.filter(
            search=search,
            status__in=[
                SearchQueryTask.STATUS_PENDING,
                SearchQueryTask.STATUS_FAILED,
            ],
        )
        .order_by("id")
        .first()
    )


def log_search_failure(exc, search=None, query_task=None, task_id=None):
    try:
        log_exception_event(
            exc,
            source=SystemEvent.SOURCE_SCRAPER,
            title="Search scraper task failed",
            user=search.user if search else None,
            task_name="run_search_sync",
            task_id=task_id,
            object_type="search",
            object_id=search.id if search else None,
            metadata={
                "search_id": search.id if search else None,
                "query_task_id": query_task.id if query_task else None,
                "query_text": query_task.query_text if query_task else None,
            },
        )
    except Exception:
        logger.exception("Could not log search failure")


def log_enrichment_dispatch_failure(exc, search=None):
    try:
        log_exception_event(
            exc,
            source=SystemEvent.SOURCE_ENRICHMENT,
            title="Search enrichment dispatch failed",
            user=search.user if search else None,
            task_name="maybe_start_search_enrichment",
            object_type="search",
            object_id=search.id if search else None,
            metadata={
                "search_id": search.id if search else None,
            },
        )
    except Exception:
        logger.exception("Could not log enrichment dispatch failure")


def send_enrichment_started_safely(user_id, job):
    try:
        from apps.realtime.events import send_enrichment_started

        send_enrichment_started(user_id, job)

    except Exception:
        try:
            from apps.realtime.events import send_enrichment_progress

            send_enrichment_progress(user_id, job)
        except Exception:
            pass


def get_enrichment_job_type_search(LeadEnrichmentJob):
    return getattr(
        LeadEnrichmentJob,
        "JOB_TYPE_SEARCH",
        "search",
    )


def maybe_start_search_enrichment(search):
    """
    MVP note:
    This still queues enrichment to Celery if email_enrichment=True.
    If you are not running Celery workers, keep email_enrichment=False.
    """

    search.refresh_from_db()

    if search.status != Search.STATUS_COMPLETED:
        return None

    if not getattr(search, "email_enrichment", False):
        return None

    try:
        from apps.leads.models import Lead, LeadEnrichmentJob
        from apps.leads.tasks import enrich_search_leads_task

        lead_ids = list(
            Lead.objects.filter(search_id=search.id)
            .values_list("id", flat=True)
        )

        if not lead_ids:
            return None

        existing_job = LeadEnrichmentJob.objects.filter(
            search=search,
            status__in=[
                LeadEnrichmentJob.STATUS_PENDING,
                LeadEnrichmentJob.STATUS_RUNNING,
            ],
        ).first()

        if existing_job:
            return existing_job

        job = LeadEnrichmentJob.objects.create(
            user=search.user,
            search=search,
            job_type=get_enrichment_job_type_search(LeadEnrichmentJob),
            status=LeadEnrichmentJob.STATUS_PENDING,
            lead_ids=lead_ids,
            total_items=len(lead_ids),
            completed_items=0,
            failed_items=0,
            skipped_items=0,
        )

        send_enrichment_started_safely(search.user_id, job)

        enrich_search_leads_task.apply_async(
            kwargs={
                "search_id": search.id,
                "job_id": job.id,
                "force": False,
            },
            queue="enrichment",
        )

        return job

    except Exception as exc:
        search.error_message = (
            f"Search completed, but enrichment could not be started: {exc}"
        )
        search.save(update_fields=["error_message", "updated_at"])

        log_enrichment_dispatch_failure(exc, search=search)

        return None


def run_search_sync(search_id, celery_task_id=None):
    """
    Main reusable search runner.

    Works in:
    - Celery worker
    - Render free MVP background thread

    This allows you to launch without paid Render Background Workers.
    """

    close_old_connections()

    try:
        try:
            search = Search.objects.select_related("user").get(id=search_id)

        except Search.DoesNotExist:
            return {
                "error": "Search not found",
                "search_id": search_id,
            }

        account_check = check_account_allowed(search.user)

        if not account_check.allowed:
            search.status = Search.STATUS_FAILED
            search.error_message = account_check.message
            search.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            send_search_failed(search.user_id, search, account_check.message)

            return {
                "error": account_check.message,
                "search_id": search.id,
            }

        if search.status == Search.STATUS_CANCELLED:
            return {
                "status": "cancelled",
                "search_id": search.id,
            }

        if search.status == Search.STATUS_PAUSED:
            return {
                "status": "paused",
                "search_id": search.id,
            }

        create_query_tasks_for_search(search)

        if not search.started_at:
            search.started_at = timezone.now()

        search.status = Search.STATUS_RUNNING
        search.error_message = None
        search.save(
            update_fields=[
                "status",
                "started_at",
                "error_message",
                "updated_at",
            ]
        )

        send_search_progress(search.user_id, search)

        while True:
            close_old_connections()

            search.refresh_from_db()

            if search.status == Search.STATUS_PAUSED:
                return {
                    "status": "paused",
                    "search_id": search.id,
                }

            if search.status == Search.STATUS_CANCELLED:
                SearchQueryTask.objects.filter(
                    search=search,
                    status__in=[
                        SearchQueryTask.STATUS_PENDING,
                        SearchQueryTask.STATUS_RUNNING,
                        SearchQueryTask.STATUS_FAILED,
                    ],
                ).update(status=SearchQueryTask.STATUS_CANCELLED)

                refreshed_search = refresh_search_counters(search.id)
                send_search_progress(refreshed_search.user_id, refreshed_search)

                return {
                    "status": "cancelled",
                    "search_id": search.id,
                }

            account_check = check_account_allowed(search.user)

            if not account_check.allowed:
                search.status = Search.STATUS_FAILED
                search.error_message = account_check.message
                search.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "updated_at",
                    ]
                )

                send_search_failed(search.user_id, search, account_check.message)

                return {
                    "error": account_check.message,
                    "search_id": search.id,
                }

            query_task = get_next_pending_task(search)

            if not query_task:
                refreshed_search = refresh_search_counters(search.id)

                if refreshed_search.status == Search.STATUS_FAILED:
                    send_search_failed(
                        refreshed_search.user_id,
                        refreshed_search,
                        refreshed_search.error_message,
                    )

                    return {
                        "status": refreshed_search.status,
                        "search_id": refreshed_search.id,
                        "email_enrichment": refreshed_search.email_enrichment,
                        "enrichment_started": False,
                        "enrichment_job_id": None,
                    }

                send_search_completed(refreshed_search.user_id, refreshed_search)

                enrichment_job = maybe_start_search_enrichment(refreshed_search)

                return {
                    "status": refreshed_search.status,
                    "search_id": refreshed_search.id,
                    "email_enrichment": refreshed_search.email_enrichment,
                    "enrichment_started": bool(enrichment_job),
                    "enrichment_job_id": enrichment_job.id if enrichment_job else None,
                }

            if (
                query_task.status == SearchQueryTask.STATUS_FAILED
                and not query_task.can_retry()
            ):
                query_task.status = SearchQueryTask.STATUS_SKIPPED
                query_task.save(update_fields=["status", "updated_at"])

                refreshed_search = refresh_search_counters(search.id)
                send_search_progress(
                    refreshed_search.user_id,
                    refreshed_search,
                    query_task,
                )

                continue

            try:
                with transaction.atomic():
                    query_task = SearchQueryTask.objects.select_for_update().get(
                        id=query_task.id
                    )

                    if query_task.status == SearchQueryTask.STATUS_FAILED:
                        query_task.retry_count += 1

                    query_task.status = SearchQueryTask.STATUS_RUNNING
                    query_task.started_at = query_task.started_at or timezone.now()
                    query_task.error_message = None
                    query_task.save(
                        update_fields=[
                            "status",
                            "retry_count",
                            "started_at",
                            "error_message",
                            "updated_at",
                        ]
                    )

                send_search_progress(search.user_id, search, query_task)

                run_scraper(
                    search_id=search.id,
                    query=query_task.query_text,
                    query_task_id=query_task.id,
                )

                query_task.refresh_from_db()

                if query_task.status == SearchQueryTask.STATUS_RUNNING:
                    query_task.mark_completed()

                refreshed_search = refresh_search_counters(search.id)

                send_search_progress(
                    refreshed_search.user_id,
                    refreshed_search,
                    query_task,
                )

            except Exception as exc:
                message = str(exc)

                query_task.refresh_from_db()
                search.refresh_from_db()

                if search.status == Search.STATUS_PAUSED:
                    query_task.status = SearchQueryTask.STATUS_PAUSED
                    query_task.error_message = message
                    query_task.save(
                        update_fields=[
                            "status",
                            "error_message",
                            "updated_at",
                        ]
                    )

                    refreshed_search = refresh_search_counters(search.id)

                    send_search_progress(
                        refreshed_search.user_id,
                        refreshed_search,
                        query_task,
                    )

                    return {
                        "status": "paused",
                        "search_id": search.id,
                    }

                if search.status == Search.STATUS_CANCELLED:
                    query_task.status = SearchQueryTask.STATUS_CANCELLED
                    query_task.error_message = message
                    query_task.save(
                        update_fields=[
                            "status",
                            "error_message",
                            "updated_at",
                        ]
                    )

                    refreshed_search = refresh_search_counters(search.id)

                    send_search_progress(
                        refreshed_search.user_id,
                        refreshed_search,
                        query_task,
                    )

                    return {
                        "status": "cancelled",
                        "search_id": search.id,
                    }

                query_task.mark_failed(message)

                log_search_failure(
                    exc,
                    search=search,
                    query_task=query_task,
                    task_id=celery_task_id,
                )

                refreshed_search = refresh_search_counters(search.id)

                send_search_failed(
                    refreshed_search.user_id,
                    refreshed_search,
                    message,
                )

                continue

    finally:
        close_old_connections()


@shared_task(bind=True)
def start_search_task(self, search_id):
    """
    Celery-compatible wrapper for future paid worker deployment.
    """
    return run_search_sync(
        search_id=search_id,
        celery_task_id=getattr(self.request, "id", None),
    )


@shared_task(bind=True)
def resume_search_task(self, search_id):
    """
    Celery-compatible resume wrapper.
    """
    try:
        search = Search.objects.get(id=search_id)

    except Search.DoesNotExist:
        return {
            "error": "Search not found",
            "search_id": search_id,
        }

    SearchQueryTask.objects.filter(
        search=search,
        status=SearchQueryTask.STATUS_PAUSED,
    ).update(status=SearchQueryTask.STATUS_PENDING)

    search.status = Search.STATUS_RUNNING
    search.save(update_fields=["status", "updated_at"])

    send_search_progress(search.user_id, search)

    return run_search_sync(
        search_id=search_id,
        celery_task_id=getattr(self.request, "id", None),
    )



















# from celery import shared_task
# from django.db import transaction
# from django.db.models import Count
# from django.utils import timezone

# from .models import Search, SearchQueryTask
# from apps.services.scraper.engine import run_scraper
# from apps.usage.services import check_account_allowed

# from apps.monitoring.services import log_exception_event
# from apps.monitoring.models import SystemEvent

# from apps.realtime.events import (
#     send_search_progress,
#     send_search_completed,
#     send_search_failed,
# )


# # =====================================================
# # QUERY HELPERS
# # =====================================================
# def build_query_text(keyword, location):
#     return f"{keyword} in {location}"


# def create_query_tasks_for_search(search):
#     """
#     Create one SearchQueryTask for every keyword + location.

#     Example:
#     keywords = ["plumber", "electrician"]
#     locations = ["Perth WA", "Sydney NSW"]

#     This creates:
#     - plumber in Perth WA
#     - plumber in Sydney NSW
#     - electrician in Perth WA
#     - electrician in Sydney NSW
#     """

#     created_count = 0

#     for keyword in search.keywords:
#         for location in search.locations:
#             query_text = build_query_text(keyword, location)

#             _, created = SearchQueryTask.objects.get_or_create(
#                 search=search,
#                 keyword=keyword,
#                 location=location,
#                 defaults={
#                     "query_text": query_text,
#                     "max_leads": search.max_leads,
#                     "status": SearchQueryTask.STATUS_PENDING,
#                 },
#             )

#             if created:
#                 created_count += 1

#     total_tasks = SearchQueryTask.objects.filter(search=search).count()

#     search.total_tasks = total_tasks
#     search.save(update_fields=["total_tasks", "updated_at"])

#     return created_count


# # =====================================================
# # SEARCH COUNTERS / STATUS
# # =====================================================
# def refresh_search_counters(search_id):
#     """
#     Update completed/failed counters from SearchQueryTask table.
#     """

#     search = Search.objects.get(id=search_id)

#     counts = (
#         SearchQueryTask.objects.filter(search=search)
#         .values("status")
#         .annotate(total=Count("id"))
#     )

#     count_map = {item["status"]: item["total"] for item in counts}

#     completed = count_map.get(SearchQueryTask.STATUS_COMPLETED, 0)
#     failed = count_map.get(SearchQueryTask.STATUS_FAILED, 0)
#     cancelled = count_map.get(SearchQueryTask.STATUS_CANCELLED, 0)
#     skipped = count_map.get(SearchQueryTask.STATUS_SKIPPED, 0)
#     paused = count_map.get(SearchQueryTask.STATUS_PAUSED, 0)

#     search.completed_tasks = completed
#     search.failed_tasks = failed + cancelled + skipped

#     total_done = search.completed_tasks + search.failed_tasks

#     if search.status in [
#         Search.STATUS_PAUSED,
#         Search.STATUS_CANCELLED,
#         Search.STATUS_FAILED,
#     ]:
#         search.save(
#             update_fields=[
#                 "completed_tasks",
#                 "failed_tasks",
#                 "updated_at",
#             ]
#         )
#         return search

#     if paused > 0:
#         search.status = Search.STATUS_PAUSED

#     elif search.total_tasks and total_done >= search.total_tasks:
#         if completed == 0 and search.failed_tasks > 0:
#             search.status = Search.STATUS_FAILED
#             search.error_message = "All search query tasks failed."
#         else:
#             search.status = Search.STATUS_COMPLETED
#             search.completed_at = timezone.now()

#     else:
#         search.status = Search.STATUS_RUNNING

#     search.save(
#         update_fields=[
#             "completed_tasks",
#             "failed_tasks",
#             "status",
#             "completed_at",
#             "error_message",
#             "updated_at",
#         ]
#     )

#     return search


# def get_next_pending_task(search):
#     """
#     Get next task which is pending or failed and retryable.
#     """

#     return (
#         SearchQueryTask.objects.filter(
#             search=search,
#             status__in=[
#                 SearchQueryTask.STATUS_PENDING,
#                 SearchQueryTask.STATUS_FAILED,
#             ],
#         )
#         .order_by("id")
#         .first()
#     )


# # =====================================================
# # MONITORING
# # =====================================================
# def log_search_failure(exc, search=None, query_task=None, task_id=None):
#     """
#     Log scraper failure into monitoring system.
#     """

#     log_exception_event(
#         exc,
#         source=SystemEvent.SOURCE_SCRAPER,
#         title="Search scraper task failed",
#         user=search.user if search else None,
#         task_name="start_search_task",
#         task_id=task_id,
#         object_type="search",
#         object_id=search.id if search else None,
#         metadata={
#             "search_id": search.id if search else None,
#             "query_task_id": query_task.id if query_task else None,
#             "query_text": query_task.query_text if query_task else None,
#         },
#     )


# def log_enrichment_dispatch_failure(exc, search=None):
#     """
#     Log enrichment dispatch failure.
#     """

#     log_exception_event(
#         exc,
#         source=SystemEvent.SOURCE_ENRICHMENT,
#         title="Search enrichment dispatch failed",
#         user=search.user if search else None,
#         task_name="maybe_start_search_enrichment",
#         object_type="search",
#         object_id=search.id if search else None,
#         metadata={
#             "search_id": search.id if search else None,
#         },
#     )


# # =====================================================
# # REALTIME ENRICHMENT EVENT HELPER
# # =====================================================
# def send_enrichment_started_safely(user_id, job):
#     """
#     Send enrichment started event if available.

#     If your realtime events file does not have send_enrichment_started,
#     fallback to send_enrichment_progress.
#     """

#     try:
#         from apps.realtime.events import send_enrichment_started

#         send_enrichment_started(user_id, job)

#     except Exception:
#         try:
#             from apps.realtime.events import send_enrichment_progress

#             send_enrichment_progress(user_id, job)
#         except Exception:
#             pass


# # =====================================================
# # ENRICHMENT AFTER SCRAPING
# # =====================================================
# def get_enrichment_job_type_search(LeadEnrichmentJob):
#     """
#     Safely get job type constant from LeadEnrichmentJob.
#     """

#     return getattr(
#         LeadEnrichmentJob,
#         "JOB_TYPE_SEARCH",
#         "search",
#     )


# def maybe_start_search_enrichment(search):
#     """
#     Start enrichment only after scraping is fully completed
#     and only if search.email_enrichment=True.

#     This fixes:
#     - enrichment running even when user disabled it
#     - scraper being blocked by enrichment
#     - frontend not knowing enrichment phase
#     """

#     search.refresh_from_db()

#     if search.status != Search.STATUS_COMPLETED:
#         return None

#     if not getattr(search, "email_enrichment", False):
#         return None

#     try:
#         from apps.leads.models import Lead, LeadEnrichmentJob
#         from apps.leads.tasks import enrich_search_leads_task

#         lead_ids = list(
#             Lead.objects.filter(search_id=search.id)
#             .values_list("id", flat=True)
#         )

#         if not lead_ids:
#             return None

#         existing_job = LeadEnrichmentJob.objects.filter(
#             search=search,
#             status__in=[
#                 LeadEnrichmentJob.STATUS_PENDING,
#                 LeadEnrichmentJob.STATUS_RUNNING,
#             ],
#         ).first()

#         if existing_job:
#             return existing_job

#         job = LeadEnrichmentJob.objects.create(
#             user=search.user,
#             search=search,
#             job_type=get_enrichment_job_type_search(LeadEnrichmentJob),
#             status=LeadEnrichmentJob.STATUS_PENDING,
#             lead_ids=lead_ids,
#             total_items=len(lead_ids),
#             completed_items=0,
#             failed_items=0,
#             skipped_items=0,
#         )

#         send_enrichment_started_safely(search.user_id, job)

#         enrich_search_leads_task.apply_async(
#             kwargs={
#                 "search_id": search.id,
#                 "job_id": job.id,
#                 "force": False,
#             },
#             queue="enrichment",
#         )

#         return job

#     except Exception as exc:
#         search.error_message = (
#             f"Search completed, but enrichment could not be started: {exc}"
#         )
#         search.save(update_fields=["error_message", "updated_at"])

#         log_enrichment_dispatch_failure(exc, search=search)

#         return None


# # =====================================================
# # MAIN SEARCH TASK
# # =====================================================
# @shared_task(bind=True)
# def start_search_task(self, search_id):
#     """
#     Main search runner.

#     Professional flow:
#     1. Create query tasks.
#     2. Scrape Google Maps only.
#     3. Save leads live.
#     4. Mark search completed after all scraping tasks are done.
#     5. If email_enrichment=True, start enrichment as a separate Celery job.
#     6. If email_enrichment=False, stop after scraping.
#     """

#     try:
#         search = Search.objects.select_related("user").get(id=search_id)

#     except Search.DoesNotExist:
#         return {
#             "error": "Search not found",
#             "search_id": search_id,
#         }

#     account_check = check_account_allowed(search.user)

#     if not account_check.allowed:
#         search.status = Search.STATUS_FAILED
#         search.error_message = account_check.message
#         search.save(
#             update_fields=[
#                 "status",
#                 "error_message",
#                 "updated_at",
#             ]
#         )

#         send_search_failed(search.user_id, search, account_check.message)

#         return {
#             "error": account_check.message,
#             "search_id": search.id,
#         }

#     if search.status == Search.STATUS_CANCELLED:
#         return {
#             "status": "cancelled",
#             "search_id": search.id,
#         }

#     if search.status == Search.STATUS_PAUSED:
#         return {
#             "status": "paused",
#             "search_id": search.id,
#         }

#     create_query_tasks_for_search(search)

#     if not search.started_at:
#         search.started_at = timezone.now()

#     search.status = Search.STATUS_RUNNING
#     search.error_message = None
#     search.save(
#         update_fields=[
#             "status",
#             "started_at",
#             "error_message",
#             "updated_at",
#         ]
#     )

#     send_search_progress(search.user_id, search)

#     while True:
#         search.refresh_from_db()

#         if search.status == Search.STATUS_PAUSED:
#             return {
#                 "status": "paused",
#                 "search_id": search.id,
#             }

#         if search.status == Search.STATUS_CANCELLED:
#             SearchQueryTask.objects.filter(
#                 search=search,
#                 status__in=[
#                     SearchQueryTask.STATUS_PENDING,
#                     SearchQueryTask.STATUS_RUNNING,
#                     SearchQueryTask.STATUS_FAILED,
#                 ],
#             ).update(status=SearchQueryTask.STATUS_CANCELLED)

#             refreshed_search = refresh_search_counters(search.id)
#             send_search_progress(refreshed_search.user_id, refreshed_search)

#             return {
#                 "status": "cancelled",
#                 "search_id": search.id,
#             }

#         account_check = check_account_allowed(search.user)

#         if not account_check.allowed:
#             search.status = Search.STATUS_FAILED
#             search.error_message = account_check.message
#             search.save(
#                 update_fields=[
#                     "status",
#                     "error_message",
#                     "updated_at",
#                 ]
#             )

#             send_search_failed(search.user_id, search, account_check.message)

#             return {
#                 "error": account_check.message,
#                 "search_id": search.id,
#             }

#         query_task = get_next_pending_task(search)

#         # =====================================================
#         # ALL QUERY TASKS FINISHED
#         # =====================================================
#         if not query_task:
#             refreshed_search = refresh_search_counters(search.id)

#             if refreshed_search.status == Search.STATUS_FAILED:
#                 send_search_failed(
#                     refreshed_search.user_id,
#                     refreshed_search,
#                     refreshed_search.error_message,
#                 )

#                 return {
#                     "status": refreshed_search.status,
#                     "search_id": refreshed_search.id,
#                     "email_enrichment": refreshed_search.email_enrichment,
#                     "enrichment_started": False,
#                     "enrichment_job_id": None,
#                 }

#             send_search_completed(refreshed_search.user_id, refreshed_search)

#             enrichment_job = maybe_start_search_enrichment(refreshed_search)

#             return {
#                 "status": refreshed_search.status,
#                 "search_id": refreshed_search.id,
#                 "email_enrichment": refreshed_search.email_enrichment,
#                 "enrichment_started": bool(enrichment_job),
#                 "enrichment_job_id": enrichment_job.id if enrichment_job else None,
#             }

#         # =====================================================
#         # FAILED TASK RETRY/SKIP LOGIC
#         # =====================================================
#         if (
#             query_task.status == SearchQueryTask.STATUS_FAILED
#             and not query_task.can_retry()
#         ):
#             query_task.status = SearchQueryTask.STATUS_SKIPPED
#             query_task.save(update_fields=["status", "updated_at"])

#             refreshed_search = refresh_search_counters(search.id)
#             send_search_progress(refreshed_search.user_id, refreshed_search, query_task)

#             continue

#         try:
#             with transaction.atomic():
#                 query_task = SearchQueryTask.objects.select_for_update().get(
#                     id=query_task.id
#                 )

#                 if query_task.status == SearchQueryTask.STATUS_FAILED:
#                     query_task.retry_count += 1

#                 query_task.status = SearchQueryTask.STATUS_RUNNING
#                 query_task.started_at = query_task.started_at or timezone.now()
#                 query_task.error_message = None
#                 query_task.save(
#                     update_fields=[
#                         "status",
#                         "retry_count",
#                         "started_at",
#                         "error_message",
#                         "updated_at",
#                     ]
#                 )

#             send_search_progress(search.user_id, search, query_task)

#             run_scraper(
#                 search_id=search.id,
#                 query=query_task.query_text,
#                 query_task_id=query_task.id,
#             )

#             query_task.refresh_from_db()

#             if query_task.status == SearchQueryTask.STATUS_RUNNING:
#                 query_task.mark_completed()

#             refreshed_search = refresh_search_counters(search.id)

#             send_search_progress(
#                 refreshed_search.user_id,
#                 refreshed_search,
#                 query_task,
#             )

#         except Exception as exc:
#             message = str(exc)

#             query_task.refresh_from_db()
#             search.refresh_from_db()

#             if search.status == Search.STATUS_PAUSED:
#                 query_task.status = SearchQueryTask.STATUS_PAUSED
#                 query_task.error_message = message
#                 query_task.save(
#                     update_fields=[
#                         "status",
#                         "error_message",
#                         "updated_at",
#                     ]
#                 )

#                 refreshed_search = refresh_search_counters(search.id)

#                 send_search_progress(
#                     refreshed_search.user_id,
#                     refreshed_search,
#                     query_task,
#                 )

#                 return {
#                     "status": "paused",
#                     "search_id": search.id,
#                 }

#             if search.status == Search.STATUS_CANCELLED:
#                 query_task.status = SearchQueryTask.STATUS_CANCELLED
#                 query_task.error_message = message
#                 query_task.save(
#                     update_fields=[
#                         "status",
#                         "error_message",
#                         "updated_at",
#                     ]
#                 )

#                 refreshed_search = refresh_search_counters(search.id)

#                 send_search_progress(
#                     refreshed_search.user_id,
#                     refreshed_search,
#                     query_task,
#                 )

#                 return {
#                     "status": "cancelled",
#                     "search_id": search.id,
#                 }

#             query_task.mark_failed(message)

#             log_search_failure(
#                 exc,
#                 search=search,
#                 query_task=query_task,
#                 task_id=getattr(self.request, "id", None),
#             )

#             refreshed_search = refresh_search_counters(search.id)

#             send_search_failed(
#                 refreshed_search.user_id,
#                 refreshed_search,
#                 message,
#             )

#             continue


# # =====================================================
# # RESUME SEARCH TASK
# # =====================================================
# @shared_task(bind=True)
# def resume_search_task(self, search_id):
#     """
#     Resume paused search.

#     It puts paused query tasks back to pending and sends the actual
#     scraper job to the scraping queue.
#     """

#     try:
#         search = Search.objects.get(id=search_id)

#     except Search.DoesNotExist:
#         return {
#             "error": "Search not found",
#             "search_id": search_id,
#         }

#     SearchQueryTask.objects.filter(
#         search=search,
#         status=SearchQueryTask.STATUS_PAUSED,
#     ).update(status=SearchQueryTask.STATUS_PENDING)

#     search.status = Search.STATUS_RUNNING
#     search.save(update_fields=["status", "updated_at"])

#     send_search_progress(search.user_id, search)

#     result = start_search_task.apply_async(
#         args=[search_id],
#         queue="scraping",
#     )

#     return result.id