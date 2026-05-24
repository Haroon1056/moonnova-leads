from django.contrib import admin

from .models import UserUsage, UsageEvent


@admin.register(UserUsage)
class UserUsageAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "account_status",
        "beta_access",
        "searches_today",
        "searches_this_month",
        "leads_today",
        "leads_this_month",
        "exports_today",
        "exports_this_month",
        "max_searches_per_day",
        "max_leads_per_month",
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

    list_filter = [
        "account_status",
        "beta_access",
        "auto_delete_old_leads",
        "auto_clear_raw_data",
        "auto_delete_old_exports",
        "unlimited_searches",
        "unlimited_leads",
        "unlimited_exports",
    ]

    search_fields = [
        "user__email",
        "user__username",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "daily_reset_at",
        "monthly_reset_at",
    ]


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "event_type",
        "amount",
        "created_at",
    ]

    list_filter = [
        "event_type",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "user__username",
    ]

    readonly_fields = [
        "user",
        "event_type",
        "amount",
        "meta",
        "created_at",
    ]