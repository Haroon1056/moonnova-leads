from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import SystemEvent
from .services import get_system_health, log_system_event


@shared_task
def monitoring_health_check_task():
    """
    Scheduled system health check.

    This checks:
    - Database
    - Redis
    - Celery worker response

    If system status is warning/error, it creates a SystemEvent.
    """

    health = get_system_health()

    if health.get("status") in ["warning", "error"]:
        log_system_event(
            level=SystemEvent.LEVEL_WARNING
            if health.get("status") == "warning"
            else SystemEvent.LEVEL_ERROR,
            source=SystemEvent.SOURCE_SYSTEM,
            title="System health issue detected",
            message=f"System health status: {health.get('status')}",
            metadata=health,
        )

    return health


@shared_task
def cleanup_old_system_events_task(days=30):
    """
    Delete old resolved/info monitoring events.

    Keeps unresolved errors/warnings for admin review.
    """

    cutoff = timezone.now() - timedelta(days=days)

    qs = SystemEvent.objects.filter(
        created_at__lt=cutoff,
        resolved=True,
    )

    deleted_count = qs.count()
    qs.delete()

    return {
        "deleted": deleted_count,
        "cutoff": cutoff.isoformat(),
    }


@shared_task
def auto_resolve_old_info_events_task(days=7):
    """
    Auto-resolve old info events so admin dashboard stays clean.
    """

    cutoff = timezone.now() - timedelta(days=days)

    qs = SystemEvent.objects.filter(
        level=SystemEvent.LEVEL_INFO,
        resolved=False,
        created_at__lt=cutoff,
    )

    count = qs.count()

    qs.update(
        resolved=True,
        resolved_at=timezone.now(),
    )

    return {
        "resolved": count,
        "cutoff": cutoff.isoformat(),
    }