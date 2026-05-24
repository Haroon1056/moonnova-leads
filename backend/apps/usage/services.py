from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import UserUsage, UsageEvent


@dataclass
class UsageResult:
    allowed: bool
    message: str
    remaining: int | None = None
    limit: int | None = None


def get_or_create_usage(user):
    usage, _ = UserUsage.objects.get_or_create(user=user)
    reset_usage_if_needed(usage)
    return usage


def reset_usage_if_needed(usage):
    """
    Reset daily and monthly counters when date/month changes.
    """

    today = timezone.localdate()

    changed = False

    if usage.daily_reset_at != today:
        usage.searches_today = 0
        usage.exports_today = 0
        usage.leads_today = 0
        usage.daily_reset_at = today
        changed = True

    if (
        usage.monthly_reset_at.year != today.year
        or usage.monthly_reset_at.month != today.month
    ):
        usage.searches_this_month = 0
        usage.exports_this_month = 0
        usage.leads_this_month = 0
        usage.monthly_reset_at = today
        changed = True

    if changed:
        usage.save(
            update_fields=[
                "searches_today",
                "exports_today",
                "leads_today",
                "searches_this_month",
                "exports_this_month",
                "leads_this_month",
                "daily_reset_at",
                "monthly_reset_at",
                "updated_at",
            ]
        )

        UsageEvent.objects.create(
            user=usage.user,
            event_type=UsageEvent.EVENT_LIMIT_RESET,
            meta={"reset_date": str(today)},
        )


def check_account_allowed(user):
    usage = get_or_create_usage(user)

    if not usage.is_allowed:
        return UsageResult(
            allowed=False,
            message="Your account is suspended or blocked. Please contact support.",
        )

    if not usage.beta_access and usage.account_status == UserUsage.ACCOUNT_STATUS_BETA:
        return UsageResult(
            allowed=False,
            message="Beta access is not enabled for this account.",
        )

    return UsageResult(
        allowed=True,
        message="Account is allowed.",
    )


def check_can_create_search(user, requested_max_leads=None):
    usage = get_or_create_usage(user)

    account_check = check_account_allowed(user)

    if not account_check.allowed:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_SEARCH_BLOCKED,
            meta={"reason": account_check.message},
        )
        return account_check

    if not usage.unlimited_searches:
        if usage.searches_today >= usage.max_searches_per_day:
            UsageEvent.objects.create(
                user=user,
                event_type=UsageEvent.EVENT_SEARCH_BLOCKED,
                meta={"reason": "daily_search_limit_reached"},
            )

            return UsageResult(
                allowed=False,
                message="Daily search limit reached.",
                remaining=0,
                limit=usage.max_searches_per_day,
            )

        if usage.searches_this_month >= usage.max_searches_per_month:
            UsageEvent.objects.create(
                user=user,
                event_type=UsageEvent.EVENT_SEARCH_BLOCKED,
                meta={"reason": "monthly_search_limit_reached"},
            )

            return UsageResult(
                allowed=False,
                message="Monthly search limit reached.",
                remaining=0,
                limit=usage.max_searches_per_month,
            )

    if requested_max_leads and not usage.unlimited_leads:
        if requested_max_leads > usage.max_leads_per_search:
            return UsageResult(
                allowed=False,
                message=f"Maximum leads per search allowed is {usage.max_leads_per_search}.",
                remaining=usage.max_leads_per_search,
                limit=usage.max_leads_per_search,
            )

    return UsageResult(
        allowed=True,
        message="Search allowed.",
        remaining=usage.remaining_searches_today,
        limit=usage.max_searches_per_day,
    )


@transaction.atomic
def record_search_created(user):
    usage = UserUsage.objects.select_for_update().get(user=user)
    reset_usage_if_needed(usage)

    usage.searches_today += 1
    usage.searches_this_month += 1
    usage.save(
        update_fields=[
            "searches_today",
            "searches_this_month",
            "updated_at",
        ]
    )

    UsageEvent.objects.create(
        user=user,
        event_type=UsageEvent.EVENT_SEARCH_CREATED,
    )

    return usage


def check_can_save_lead(user, amount=1):
    usage = get_or_create_usage(user)

    account_check = check_account_allowed(user)

    if not account_check.allowed:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_LEAD_BLOCKED,
            meta={"reason": account_check.message},
        )
        return account_check

    if usage.unlimited_leads:
        return UsageResult(
            allowed=True,
            message="Lead saving allowed.",
        )

    if usage.leads_today + amount > usage.max_leads_per_day:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_LEAD_BLOCKED,
            meta={"reason": "daily_lead_limit_reached"},
        )

        return UsageResult(
            allowed=False,
            message="Daily lead limit reached.",
            remaining=max(usage.max_leads_per_day - usage.leads_today, 0),
            limit=usage.max_leads_per_day,
        )

    if usage.leads_this_month + amount > usage.max_leads_per_month:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_LEAD_BLOCKED,
            meta={"reason": "monthly_lead_limit_reached"},
        )

        return UsageResult(
            allowed=False,
            message="Monthly lead limit reached.",
            remaining=max(usage.max_leads_per_month - usage.leads_this_month, 0),
            limit=usage.max_leads_per_month,
        )

    return UsageResult(
        allowed=True,
        message="Lead saving allowed.",
        remaining=usage.remaining_leads_this_month,
        limit=usage.max_leads_per_month,
    )


@transaction.atomic
def record_lead_saved(user, amount=1):
    usage = UserUsage.objects.select_for_update().get(user=user)
    reset_usage_if_needed(usage)

    usage.leads_today += amount
    usage.leads_this_month += amount
    usage.save(
        update_fields=[
            "leads_today",
            "leads_this_month",
            "updated_at",
        ]
    )

    UsageEvent.objects.create(
        user=user,
        event_type=UsageEvent.EVENT_LEAD_SAVED,
        amount=amount,
    )

    return usage


def check_can_export(user):
    usage = get_or_create_usage(user)

    account_check = check_account_allowed(user)

    if not account_check.allowed:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_EXPORT_BLOCKED,
            meta={"reason": account_check.message},
        )
        return account_check

    if usage.unlimited_exports:
        return UsageResult(
            allowed=True,
            message="Export allowed.",
        )

    if usage.exports_today >= usage.max_exports_per_day:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_EXPORT_BLOCKED,
            meta={"reason": "daily_export_limit_reached"},
        )

        return UsageResult(
            allowed=False,
            message="Daily export limit reached.",
            remaining=0,
            limit=usage.max_exports_per_day,
        )

    if usage.exports_this_month >= usage.max_exports_per_month:
        UsageEvent.objects.create(
            user=user,
            event_type=UsageEvent.EVENT_EXPORT_BLOCKED,
            meta={"reason": "monthly_export_limit_reached"},
        )

        return UsageResult(
            allowed=False,
            message="Monthly export limit reached.",
            remaining=0,
            limit=usage.max_exports_per_month,
        )

    return UsageResult(
        allowed=True,
        message="Export allowed.",
        remaining=usage.remaining_exports_today,
        limit=usage.max_exports_per_day,
    )


@transaction.atomic
def record_export_created(user):
    usage = UserUsage.objects.select_for_update().get(user=user)
    reset_usage_if_needed(usage)

    usage.exports_today += 1
    usage.exports_this_month += 1
    usage.save(
        update_fields=[
            "exports_today",
            "exports_this_month",
            "updated_at",
        ]
    )

    UsageEvent.objects.create(
        user=user,
        event_type=UsageEvent.EVENT_EXPORT_CREATED,
    )

    return usage


def get_usage_summary(user):
    usage = get_or_create_usage(user)

    return {
        "account_status": usage.account_status,
        "beta_access": usage.beta_access,

        "searches_today": usage.searches_today,
        "searches_this_month": usage.searches_this_month,
        "max_searches_per_day": usage.max_searches_per_day,
        "max_searches_per_month": usage.max_searches_per_month,
        "remaining_searches_today": usage.remaining_searches_today,

        "leads_today": usage.leads_today,
        "leads_this_month": usage.leads_this_month,
        "max_leads_per_day": usage.max_leads_per_day,
        "max_leads_per_month": usage.max_leads_per_month,
        "max_leads_per_search": usage.max_leads_per_search,
        "remaining_leads_this_month": usage.remaining_leads_this_month,

        "exports_today": usage.exports_today,
        "exports_this_month": usage.exports_this_month,
        "max_exports_per_day": usage.max_exports_per_day,
        "max_exports_per_month": usage.max_exports_per_month,
        "remaining_exports_today": usage.remaining_exports_today,

        "lead_retention_days": usage.lead_retention_days,
        "search_history_retention_days": usage.search_history_retention_days,
        "raw_data_retention_days": usage.raw_data_retention_days,
        "export_retention_days": usage.export_retention_days,

        "auto_delete_old_leads": usage.auto_delete_old_leads,
        "auto_clear_raw_data": usage.auto_clear_raw_data,
        "auto_delete_old_exports": usage.auto_delete_old_exports,

        "unlimited_searches": usage.unlimited_searches,
        "unlimited_leads": usage.unlimited_leads,
        "unlimited_exports": usage.unlimited_exports,
    }