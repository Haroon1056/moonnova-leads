from rest_framework import serializers

from apps.usage.models import UserUsage


class UserUsageAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserUsage
        fields = [
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

        extra_kwargs = {
            field: {"required": False}
            for field in fields
        }