import traceback

import redis

from celery import current_app
from django.conf import settings
from django.db import connection
from django.utils import timezone

from .models import SystemEvent


def log_system_event(
    level="info",
    source="system",
    title="System event",
    message=None,
    user=None,
    task_name=None,
    task_id=None,
    object_type=None,
    object_id=None,
    metadata=None,
):
    try:
        return SystemEvent.objects.create(
            level=level,
            source=source,
            title=title,
            message=message,
            user=user,
            task_name=task_name,
            task_id=task_id,
            object_type=object_type,
            object_id=str(object_id) if object_id is not None else None,
            metadata=metadata or {},
        )
    except Exception:
        return None


def log_exception_event(
    exc,
    source="system",
    title="Unhandled exception",
    user=None,
    task_name=None,
    task_id=None,
    object_type=None,
    object_id=None,
    metadata=None,
):
    message = str(exc)

    meta = metadata or {}
    meta["traceback"] = traceback.format_exc()

    return log_system_event(
        level=SystemEvent.LEVEL_ERROR,
        source=source,
        title=title,
        message=message,
        user=user,
        task_name=task_name,
        task_id=task_id,
        object_type=object_type,
        object_id=object_id,
        metadata=meta,
    )


def check_database_health():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return {
            "status": "ok",
            "message": "Database connection is working.",
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def check_redis_health():
    try:
        redis_url = getattr(settings, "HEALTH_CHECK_REDIS_URL", None)

        if not redis_url:
            return {
                "status": "warning",
                "message": "Redis URL is not configured.",
            }

        client = redis.Redis.from_url(redis_url)
        pong = client.ping()

        if pong:
            return {
                "status": "ok",
                "message": "Redis connection is working.",
            }

        return {
            "status": "error",
            "message": "Redis ping failed.",
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def check_celery_health():
    try:
        timeout = getattr(settings, "HEALTH_CHECK_CELERY_TIMEOUT", 5)

        inspector = current_app.control.inspect(timeout=timeout)
        stats = inspector.stats() or {}
        active = inspector.active() or {}

        if not stats:
            return {
                "status": "warning",
                "message": "No Celery workers responded.",
                "workers": [],
            }

        workers = []

        for worker_name, worker_stats in stats.items():
            workers.append(
                {
                    "name": worker_name,
                    "pool": worker_stats.get("pool", {}),
                    "broker": worker_stats.get("broker", {}),
                    "active_tasks": len(active.get(worker_name, [])),
                }
            )

        return {
            "status": "ok",
            "message": "Celery workers are responding.",
            "workers": workers,
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "workers": [],
        }


def get_system_health():
    database = check_database_health()
    redis_status = check_redis_health()
    celery = check_celery_health()

    statuses = [
        database["status"],
        redis_status["status"],
        celery["status"],
    ]

    overall = "ok"

    if "error" in statuses:
        overall = "error"
    elif "warning" in statuses:
        overall = "warning"

    return {
        "status": overall,
        "checked_at": timezone.now(),
        "database": database,
        "redis": redis_status,
        "celery": celery,
    }


def get_monitoring_summary():
    last_24h = timezone.now() - timezone.timedelta(hours=24)

    return {
        "events_total": SystemEvent.objects.count(),
        "errors_24h": SystemEvent.objects.filter(
            level__in=[
                SystemEvent.LEVEL_ERROR,
                SystemEvent.LEVEL_CRITICAL,
            ],
            created_at__gte=last_24h,
        ).count(),
        "unresolved_errors": SystemEvent.objects.filter(
            level__in=[
                SystemEvent.LEVEL_ERROR,
                SystemEvent.LEVEL_CRITICAL,
            ],
            resolved=False,
        ).count(),
        "warnings_24h": SystemEvent.objects.filter(
            level=SystemEvent.LEVEL_WARNING,
            created_at__gte=last_24h,
        ).count(),
        "by_source": list(
            SystemEvent.objects.values("source")
            .order_by("source")
            .annotate(total=models_count("id"))
        ),
    }


def models_count(field):
    from django.db.models import Count

    return Count(field)