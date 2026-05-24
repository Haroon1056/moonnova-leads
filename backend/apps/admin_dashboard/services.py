from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Sum, Q
from django.utils import timezone

from apps.searches.models import Search, SearchQueryTask
from apps.leads.models import Lead, ExportHistory, LeadEnrichmentJob
from apps.usage.models import UserUsage
from apps.monitoring.models import SystemEvent

try:
    from apps.ai.models import AIJob, AIUsageLog
except Exception:
    AIJob = None
    AIUsageLog = None


User = get_user_model()


def get_date_range(days=30):
    now = timezone.now()
    start = now - timedelta(days=days)
    return start, now


def safe_count(queryset):
    try:
        return queryset.count()
    except Exception:
        return 0


def get_admin_overview(days=30):
    start, now = get_date_range(days)

    total_users = safe_count(User.objects.all())
    active_users = safe_count(User.objects.filter(is_active=True))
    staff_users = safe_count(User.objects.filter(is_staff=True))

    total_searches = safe_count(Search.objects.all())
    running_searches = safe_count(Search.objects.filter(status=Search.STATUS_RUNNING))
    completed_searches = safe_count(Search.objects.filter(status=Search.STATUS_COMPLETED))
    failed_searches = safe_count(Search.objects.filter(status=Search.STATUS_FAILED))
    cancelled_searches = safe_count(Search.objects.filter(status=Search.STATUS_CANCELLED))
    searches_last_period = safe_count(Search.objects.filter(created_at__gte=start))

    total_leads = safe_count(Lead.objects.all())
    leads_last_period = safe_count(Lead.objects.filter(created_at__gte=start))

    total_exports = safe_count(ExportHistory.objects.all())
    completed_exports = safe_count(
        ExportHistory.objects.filter(status=ExportHistory.STATUS_COMPLETED)
    )
    failed_exports = safe_count(
        ExportHistory.objects.filter(status=ExportHistory.STATUS_FAILED)
    )
    exports_last_period = safe_count(ExportHistory.objects.filter(created_at__gte=start))

    total_enrichment_jobs = safe_count(LeadEnrichmentJob.objects.all())
    running_enrichment_jobs = safe_count(
        LeadEnrichmentJob.objects.filter(status=LeadEnrichmentJob.STATUS_RUNNING)
    )
    failed_enrichment_jobs = safe_count(
        LeadEnrichmentJob.objects.filter(status=LeadEnrichmentJob.STATUS_FAILED)
    )

    total_ai_jobs = safe_count(AIJob.objects.all()) if AIJob else 0
    running_ai_jobs = (
        safe_count(AIJob.objects.filter(status=AIJob.STATUS_RUNNING))
        if AIJob
        else 0
    )
    failed_ai_jobs = (
        safe_count(AIJob.objects.filter(status=AIJob.STATUS_FAILED))
        if AIJob
        else 0
    )

    ai_credits_used = 0
    if AIUsageLog:
        ai_credits_used = (
            AIUsageLog.objects.aggregate(total=Sum("credits_used")).get("total") or 0
        )

    return {
        "period_days": days,

        # Frontend-friendly flat fields
        "users_total": total_users,
        "active_users": active_users,
        "staff_users": staff_users,
        "searches_total": total_searches,
        "running_searches": running_searches,
        "completed_searches": completed_searches,
        "failed_searches": failed_searches,
        "cancelled_searches": cancelled_searches,
        "leads_total": total_leads,
        "exports_total": total_exports,
        "ai_jobs_total": total_ai_jobs,
        "ai_jobs_running": running_ai_jobs,
        "ai_jobs_failed": failed_ai_jobs,
        "ai_credits_used_total": ai_credits_used,
        "system_status": "ok",

        # Backward-compatible grouped fields
        "users": {
            "total": total_users,
            "active": active_users,
            "staff": staff_users,
        },
        "searches": {
            "total": total_searches,
            "running": running_searches,
            "completed": completed_searches,
            "failed": failed_searches,
            "cancelled": cancelled_searches,
            "last_period": searches_last_period,
        },
        "leads": {
            "total": total_leads,
            "last_period": leads_last_period,
        },
        "exports": {
            "total": total_exports,
            "completed": completed_exports,
            "failed": failed_exports,
            "last_period": exports_last_period,
        },
        "enrichment": {
            "total_jobs": total_enrichment_jobs,
            "running_jobs": running_enrichment_jobs,
            "failed_jobs": failed_enrichment_jobs,
        },
    }


def get_admin_user_queryset():
    return (
        User.objects.annotate(
            total_searches=Count("searches", distinct=True),
            total_leads=Count("searches__leads", distinct=True),
            total_exports=Count("export_history", distinct=True),
        )
        .order_by("-date_joined")
    )


def serialize_admin_user(user):
    usage = UserUsage.objects.filter(user=user).first()

    return {
        "id": user.id,
        "email": getattr(user, "email", None),
        "username": getattr(user, "email", None),
        "full_name": getattr(user, "full_name", None),
        "first_name": "",
        "last_name": "",
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "is_verified": getattr(user, "is_verified", False),
        "auth_provider": getattr(user, "auth_provider", "email"),
        "date_joined": user.date_joined,
        "last_login": user.last_login,

        "account_status": usage.account_status if usage else None,
        "beta_access": usage.beta_access if usage else None,
        "ai_enabled": True if usage and usage.is_allowed else False,
        "plan_name": usage.account_status if usage else "beta",

        "searches_count": getattr(user, "total_searches", 0),
        "leads_count": getattr(user, "total_leads", 0),
        "exports_count": getattr(user, "total_exports", 0),
        "ai_jobs_count": (
            safe_count(AIJob.objects.filter(user=user)) if AIJob else 0
        ),

        # Backward-compatible names
        "total_searches": getattr(user, "total_searches", 0),
        "total_leads": getattr(user, "total_leads", 0),
        "total_exports": getattr(user, "total_exports", 0),
    }


def get_top_users_by_usage(limit=10):
    users = get_admin_user_queryset().order_by("-total_leads")[:limit]
    return [serialize_admin_user(user) for user in users]


def get_user_detail(user_id):
    user = User.objects.filter(id=user_id).first()

    if not user:
        return None

    usage = UserUsage.objects.filter(user=user).first()

    searches = Search.objects.filter(user=user)
    leads = Lead.objects.filter(search__user=user)
    exports = ExportHistory.objects.filter(user=user)
    enrichments = LeadEnrichmentJob.objects.filter(user=user)
    ai_jobs = AIJob.objects.filter(user=user) if AIJob else []

    return {
        **serialize_admin_user(user),
        "usage": {
            "account_status": usage.account_status if usage else None,
            "beta_access": usage.beta_access if usage else None,
            "searches_today": usage.searches_today if usage else 0,
            "searches_this_month": usage.searches_this_month if usage else 0,
            "leads_today": usage.leads_today if usage else 0,
            "leads_this_month": usage.leads_this_month if usage else 0,
            "exports_today": usage.exports_today if usage else 0,
            "exports_this_month": usage.exports_this_month if usage else 0,
            "max_searches_per_day": usage.max_searches_per_day if usage else 0,
            "max_searches_per_month": usage.max_searches_per_month if usage else 0,
            "max_leads_per_day": usage.max_leads_per_day if usage else 0,
            "max_leads_per_month": usage.max_leads_per_month if usage else 0,
            "max_exports_per_day": usage.max_exports_per_day if usage else 0,
            "max_exports_per_month": usage.max_exports_per_month if usage else 0,
            "lead_retention_days": usage.lead_retention_days if usage else 0,
            "search_history_retention_days": usage.search_history_retention_days if usage else 0,
            "raw_data_retention_days": usage.raw_data_retention_days if usage else 0,
            "export_retention_days": usage.export_retention_days if usage else 0,
            "unlimited_searches": usage.unlimited_searches if usage else False,
            "unlimited_leads": usage.unlimited_leads if usage else False,
            "unlimited_exports": usage.unlimited_exports if usage else False,
        },
        "stats": {
            "total_searches": searches.count(),
            "total_leads": leads.count(),
            "total_exports": exports.count(),
            "total_enrichment_jobs": enrichments.count(),
            "total_ai_jobs": ai_jobs.count() if AIJob else 0,
            "running_searches": searches.filter(status=Search.STATUS_RUNNING).count(),
            "failed_searches": searches.filter(status=Search.STATUS_FAILED).count(),
            "completed_searches": searches.filter(status=Search.STATUS_COMPLETED).count(),
        },
    }


def update_user_usage_limits(user, data):
    usage, _ = UserUsage.objects.get_or_create(user=user)

    allowed_fields = [
        "account_status",
        "beta_access",
        "max_searches_per_day",
        "max_searches_per_month",
        "max_leads_per_day",
        "max_leads_per_month",
        "max_leads_per_search",
        "max_exports_per_day",
        "max_exports_per_month",
        "lead_retention_days",
        "search_history_retention_days",
        "raw_data_retention_days",
        "export_retention_days",
        "auto_delete_old_leads",
        "auto_clear_raw_data",
        "auto_delete_old_exports",
        "unlimited_searches",
        "unlimited_leads",
        "unlimited_exports",
    ]

    update_fields = []

    for field in allowed_fields:
        if field in data:
            setattr(usage, field, data.get(field))
            update_fields.append(field)

    if update_fields:
        usage.save(update_fields=update_fields + ["updated_at"])

    return usage


def get_recent_activity(limit=30):
    recent_searches = Search.objects.select_related("user").order_by("-created_at")[:limit]
    recent_exports = ExportHistory.objects.select_related("user").order_by("-created_at")[:limit]
    recent_enrichments = LeadEnrichmentJob.objects.select_related("user").order_by("-created_at")[:limit]

    activities = []

    for search in recent_searches:
        activities.append(
            {
                "type": "search",
                "id": search.id,
                "user_id": search.user_id,
                "user_email": getattr(search.user, "email", None),
                "status": search.status,
                "title": f"Search created: {search.keywords} / {search.locations}",
                "created_at": search.created_at,
            }
        )

    for export in recent_exports:
        activities.append(
            {
                "type": "export",
                "id": export.id,
                "user_id": export.user_id,
                "user_email": getattr(export.user, "email", None),
                "status": export.status,
                "title": f"Export {export.export_type}: {export.total_rows} rows",
                "created_at": export.created_at,
            }
        )

    for job in recent_enrichments:
        activities.append(
            {
                "type": "enrichment",
                "id": job.id,
                "user_id": job.user_id,
                "user_email": getattr(job.user, "email", None),
                "status": job.status,
                "title": f"Enrichment job: {job.job_type} / {job.total_items} items",
                "created_at": job.created_at,
            }
        )

    if AIJob:
        for job in AIJob.objects.select_related("user").order_by("-created_at")[:limit]:
            activities.append(
                {
                    "type": "ai",
                    "id": job.id,
                    "user_id": job.user_id,
                    "user_email": getattr(job.user, "email", None),
                    "status": job.status,
                    "title": f"AI job: {job.job_type} / {job.total_items} items",
                    "created_at": job.created_at,
                }
            )

    activities.sort(key=lambda item: item["created_at"], reverse=True)

    return activities[:limit]


def check_database_status():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return "healthy"
    except Exception:
        return "unhealthy"


def check_cache_status():
    try:
        cache.set("admin_dashboard_health_check", "ok", timeout=10)
        cache_value = cache.get("admin_dashboard_health_check")
        return "healthy" if cache_value == "ok" else "degraded"
    except Exception:
        return "unhealthy"


def get_worker_health_names():
    """
    Uses Celery inspect if available. Returns worker names only.
    If Redis/Celery is not running, returns empty list.
    """
    try:
        from celery import current_app

        inspect = current_app.control.inspect(timeout=1)
        ping = inspect.ping() or {}
        return list(ping.keys())
    except Exception:
        return []


def get_system_health_summary():
    database_status = check_database_status()
    cache_status = check_cache_status()
    worker_names = get_worker_health_names()

    worker_text = "healthy" if worker_names else "unknown"

    stuck_searches = Search.objects.filter(
        status=Search.STATUS_RUNNING,
        updated_at__lt=timezone.now() - timedelta(hours=2),
    ).count()

    stuck_enrichment_jobs = LeadEnrichmentJob.objects.filter(
        status=LeadEnrichmentJob.STATUS_RUNNING,
        updated_at__lt=timezone.now() - timedelta(hours=2),
    ).count()

    failed_searches_24h = Search.objects.filter(
        status=Search.STATUS_FAILED,
        updated_at__gte=timezone.now() - timedelta(hours=24),
    ).count()

    failed_exports_24h = ExportHistory.objects.filter(
        status=ExportHistory.STATUS_FAILED,
        updated_at__gte=timezone.now() - timedelta(hours=24),
    ).count()

    failed_ai_jobs_24h = 0
    if AIJob:
        failed_ai_jobs_24h = AIJob.objects.filter(
            status=AIJob.STATUS_FAILED,
            updated_at__gte=timezone.now() - timedelta(hours=24),
        ).count()

    overall = "healthy"

    if database_status == "unhealthy":
        overall = "unhealthy"
    elif (
        cache_status in ["unhealthy", "degraded"]
        or stuck_searches
        or stuck_enrichment_jobs
        or failed_searches_24h
        or failed_exports_24h
        or failed_ai_jobs_24h
    ):
        overall = "degraded"

    worker_blob = " ".join(worker_names).lower()

    scraper_worker = "healthy" if "scraping" in worker_blob else worker_text
    enrichment_worker = "healthy" if "enrichment" in worker_blob else worker_text
    default_worker = "healthy" if "default" in worker_blob else worker_text

    return {
        "status": overall,
        "database": database_status,
        "redis": cache_status,
        "cache": cache_status,
        "celery": worker_text,
        "scraper_worker": scraper_worker,
        "enrichment_worker": enrichment_worker,
        "default_worker": default_worker,
        "storage": "healthy",
        "ai_provider": "healthy" if AIJob else "not_configured",
        "worker_names": worker_names,
        "stuck_searches": stuck_searches,
        "stuck_enrichment_jobs": stuck_enrichment_jobs,
        "failed_searches_24h": failed_searches_24h,
        "failed_exports_24h": failed_exports_24h,
        "failed_ai_jobs_24h": failed_ai_jobs_24h,
        "checked_at": timezone.now(),
    }


def get_failure_summary(days=7):
    start, now = get_date_range(days)

    failed_searches = Search.objects.filter(
        status=Search.STATUS_FAILED,
        updated_at__gte=start,
    ).count()

    failed_query_tasks = SearchQueryTask.objects.filter(
        status=SearchQueryTask.STATUS_FAILED,
        updated_at__gte=start,
    ).count()

    failed_exports = ExportHistory.objects.filter(
        status=ExportHistory.STATUS_FAILED,
        updated_at__gte=start,
    ).count()

    failed_enrichments = LeadEnrichmentJob.objects.filter(
        status=LeadEnrichmentJob.STATUS_FAILED,
        updated_at__gte=start,
    ).count()

    failed_ai_jobs = 0
    if AIJob:
        failed_ai_jobs = AIJob.objects.filter(
            status=AIJob.STATUS_FAILED,
            updated_at__gte=start,
        ).count()

    recent_failed_searches = list(
        Search.objects.filter(status=Search.STATUS_FAILED)
        .select_related("user")
        .order_by("-updated_at")[:10]
        .values(
            "id",
            "user_id",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        )
    )

    recent_failed_exports = list(
        ExportHistory.objects.filter(status=ExportHistory.STATUS_FAILED)
        .select_related("user")
        .order_by("-updated_at")[:10]
        .values(
            "id",
            "user_id",
            "export_type",
            "error_message",
            "created_at",
            "updated_at",
        )
    )

    return {
        "period_days": days,
        "failed_searches": failed_searches,
        "failed_query_tasks": failed_query_tasks,
        "failed_exports": failed_exports,
        "failed_enrichments": failed_enrichments,
        "failed_ai_jobs": failed_ai_jobs,
        "recent_failed_searches": recent_failed_searches,
        "recent_failed_exports": recent_failed_exports,
    }


def get_admin_ai_summary(days=30):
    start, now = get_date_range(days)

    if not AIJob:
        return {
            "ai_enabled": False,
            "provider": None,
            "model": None,
            "jobs_total": 0,
            "jobs_running": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "credits_used_total": 0,
            "credits_used_this_month": 0,
            "quota_errors": 0,
            "last_error": None,
        }

    jobs_total = AIJob.objects.count()
    jobs_running = AIJob.objects.filter(status=AIJob.STATUS_RUNNING).count()
    jobs_completed = AIJob.objects.filter(status=AIJob.STATUS_COMPLETED).count()
    jobs_failed = AIJob.objects.filter(status=AIJob.STATUS_FAILED).count()

    credits_used_total = (
        AIJob.objects.aggregate(total=Sum("credits_used")).get("total") or 0
    )

    credits_used_this_month = (
        AIJob.objects.filter(created_at__gte=start)
        .aggregate(total=Sum("credits_used"))
        .get("total")
        or 0
    )

    quota_errors = AIJob.objects.filter(
        error_message__icontains="RESOURCE_EXHAUSTED"
    ).count() + AIJob.objects.filter(
        error_message__icontains="429"
    ).count()

    last_failed = (
        AIJob.objects.filter(status=AIJob.STATUS_FAILED)
        .exclude(error_message__isnull=True)
        .exclude(error_message="")
        .order_by("-updated_at")
        .first()
    )

    return {
        "ai_enabled": True,
        "provider": "gemini",
        "model": "gemini",
        "jobs_total": jobs_total,
        "jobs_running": jobs_running,
        "jobs_completed": jobs_completed,
        "jobs_failed": jobs_failed,
        "credits_used_total": credits_used_total,
        "credits_used_this_month": credits_used_this_month,
        "quota_errors": quota_errors,
        "last_error": last_failed.error_message if last_failed else None,
    }


def serialize_admin_ai_job(job):
    return {
        "id": job.id,
        "user": job.user_id,
        "user_email": getattr(job.user, "email", None),
        "job_type": job.job_type,
        "status": job.status,
        "total_items": job.total_items,
        "completed_items": job.completed_items,
        "failed_items": job.failed_items,
        "skipped_items": job.skipped_items,
        "credits_used": job.credits_used,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at,
    }


def get_monitoring_events_queryset():
    return SystemEvent.objects.select_related("user").order_by("-created_at")