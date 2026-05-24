from datetime import timedelta
import os

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.searches.models import Search
from apps.usage.services import get_or_create_usage

from .models import Lead, ExportHistory


User = get_user_model()


def get_user_storage_summary(user):
    """
    Storage summary for user dashboard.
    """

    searches = Search.objects.filter(user=user)
    leads = Lead.objects.filter(search__user=user)
    exports = ExportHistory.objects.filter(user=user)

    total_leads = leads.count()
    total_searches = searches.count()
    total_exports = exports.count()

    raw_data_count = leads.exclude(raw_data={}).count()

    status_counts = (
        leads.values("website_status")
        .annotate(total=Count("id"))
        .order_by("website_status")
    )

    lead_quality_counts = (
        leads.values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    return {
        "total_searches": total_searches,
        "total_leads": total_leads,
        "total_exports": total_exports,
        "raw_data_count": raw_data_count,
        "website_status_counts": list(status_counts),
        "lead_quality_counts": list(lead_quality_counts),
    }


def cleanup_user_raw_data(user):
    """
    Clear raw_data for old leads.
    Keeps clean fields but removes heavy/debug raw payload.
    """

    usage = get_or_create_usage(user)

    if not usage.auto_clear_raw_data:
        return {
            "cleared": 0,
            "enabled": False,
        }

    cutoff = timezone.now() - timedelta(days=usage.raw_data_retention_days)

    qs = Lead.objects.filter(
        search__user=user,
        created_at__lt=cutoff,
    ).exclude(raw_data={})

    count = qs.count()

    qs.update(raw_data={})

    return {
        "cleared": count,
        "enabled": True,
        "cutoff": cutoff.isoformat(),
    }


def cleanup_user_old_leads(user):
    """
    Delete old leads but keep search history.

    This is good for free beta users:
    - User can see search summary
    - But old heavy lead rows are removed
    """

    usage = get_or_create_usage(user)

    if not usage.auto_delete_old_leads:
        return {
            "deleted": 0,
            "enabled": False,
        }

    cutoff = timezone.now() - timedelta(days=usage.lead_retention_days)

    qs = Lead.objects.filter(
        search__user=user,
        created_at__lt=cutoff,
    )

    count = qs.count()

    qs.delete()

    return {
        "deleted": count,
        "enabled": True,
        "cutoff": cutoff.isoformat(),
    }


def cleanup_user_old_searches(user):
    """
    Delete old searches that have no leads left.
    Keeps recent search history.
    """

    usage = get_or_create_usage(user)

    cutoff = timezone.now() - timedelta(days=usage.search_history_retention_days)

    qs = (
        Search.objects.filter(
            user=user,
            created_at__lt=cutoff,
        )
        .annotate(leads_count=Count("leads"))
        .filter(leads_count=0)
    )

    count = qs.count()

    qs.delete()

    return {
        "deleted": count,
        "cutoff": cutoff.isoformat(),
    }


def cleanup_user_old_exports(user):
    usage = get_or_create_usage(user)

    if not usage.auto_delete_old_exports:
        return {
            "expired": 0,
            "deleted_files": 0,
            "enabled": False,
        }

    cutoff = timezone.now() - timedelta(days=usage.export_retention_days)

    qs = ExportHistory.objects.filter(
        user=user,
        created_at__lt=cutoff,
    ).exclude(status=ExportHistory.STATUS_EXPIRED)

    expired_count = 0
    deleted_files = 0

    for export in qs:
        if export.file_path and os.path.exists(export.file_path):
            try:
                os.remove(export.file_path)
                deleted_files += 1
            except Exception:
                pass

        export.status = ExportHistory.STATUS_EXPIRED
        export.expires_at = timezone.now()
        export.file_path = None
        export.save(
            update_fields=[
                "status",
                "expires_at",
                "file_path",
                "updated_at",
            ]
        )

        expired_count += 1

    return {
        "expired": expired_count,
        "deleted_files": deleted_files,
        "enabled": True,
        "cutoff": cutoff.isoformat(),
    }


def cleanup_user_data(user):
    """
    Run full cleanup for one user.
    """

    raw_result = cleanup_user_raw_data(user)
    lead_result = cleanup_user_old_leads(user)
    search_result = cleanup_user_old_searches(user)
    export_result = cleanup_user_old_exports(user)

    return {
        "user_id": user.id,
        "raw_data": raw_result,
        "leads": lead_result,
        "searches": search_result,
        "exports": export_result,
    }


def cleanup_all_users_data():
    """
    Run cleanup for all users.
    This should be called by Celery beat daily.
    """

    results = []

    for user in User.objects.all().iterator():
        results.append(cleanup_user_data(user))

    return {
        "total_users": len(results),
        "results": results,
    }