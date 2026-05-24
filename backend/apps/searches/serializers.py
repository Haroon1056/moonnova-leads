from rest_framework import serializers

from .models import Search, SearchQueryTask
from apps.leads.models import Lead
from apps.usage.services import get_or_create_usage


class SearchQueryTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchQueryTask
        fields = [
            "id",
            "keyword",
            "location",
            "query_text",
            "status",
            "max_leads",
            "leads_found",
            "processed_index",
            "retry_count",
            "max_retries",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class SearchSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    leads_count = serializers.SerializerMethodField()
    remaining_leads_this_month = serializers.SerializerMethodField()
    query_tasks = SearchQueryTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Search
        fields = "__all__"
        read_only_fields = [
            "id",
            "user",
            "status",
            "completed_tasks",
            "failed_tasks",
            "total_tasks",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate_max_leads(self, value):
        request = self.context.get("request")

        if not request or not request.user or not request.user.is_authenticated:
            return value

        usage = get_or_create_usage(request.user)

        if usage.unlimited_leads:
            return value

        if value > usage.max_leads_per_search:
            raise serializers.ValidationError(
                f"Maximum leads per search allowed is {usage.max_leads_per_search}."
            )

        return value

    def get_progress(self, obj):
        try:
            return obj.progress()
        except Exception:
            return 0

    def get_leads_count(self, obj):
        try:
            if hasattr(obj, "leads_count_db"):
                return obj.leads_count_db

            return Lead.objects.filter(search=obj).count()

        except Exception:
            return 0

    def get_remaining_leads_this_month(self, obj):
        try:
            usage = get_or_create_usage(obj.user)
            return usage.remaining_leads_this_month
        except Exception:
            return None