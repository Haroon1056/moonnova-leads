from rest_framework import serializers

from .models import (
    Lead,
    LeadList,
    LeadListItem,
    ExportHistory,
    LeadEnrichmentJob,
)


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = "__all__"
        read_only_fields = [
            "id",
            "search",
            "lead_score",
            "opportunity_score",
            "opportunity_reason",
            "created_at",
            "updated_at",
        ]


class LeadListItemSerializer(serializers.ModelSerializer):
    lead = LeadSerializer(read_only=True)

    class Meta:
        model = LeadListItem
        fields = [
            "id",
            "lead",
            "added_at",
        ]


class LeadListSerializer(serializers.ModelSerializer):
    leads_count = serializers.SerializerMethodField()

    class Meta:
        model = LeadList
        fields = [
            "id",
            "name",
            "description",
            "leads_count",
            "created_at",
            "updated_at",
        ]

    def get_leads_count(self, obj):
        return obj.items.count()


class LeadListDetailSerializer(serializers.ModelSerializer):
    items = LeadListItemSerializer(many=True, read_only=True)
    leads_count = serializers.SerializerMethodField()

    class Meta:
        model = LeadList
        fields = [
            "id",
            "name",
            "description",
            "leads_count",
            "items",
            "created_at",
            "updated_at",
        ]

    def get_leads_count(self, obj):
        return obj.items.count()


class ExportHistorySerializer(serializers.ModelSerializer):
    is_ready = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ExportHistory
        fields = [
            "id",
            "search",
            "lead_list",
            "export_type",
            "export_scope",
            "status",
            "filters",
            "selected_lead_ids",
            "total_rows",
            "file_name",
            "file_path",
            "file_size_bytes",
            "error_message",
            "expires_at",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
            "is_ready",
            "download_url",
        ]
        read_only_fields = fields

    def get_is_ready(self, obj):
        return obj.is_ready

    def get_download_url(self, obj):
        if not obj.is_ready:
            return None

        return f"/api/leads/exports/{obj.id}/download/"


class LeadEnrichmentJobSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = LeadEnrichmentJob
        fields = [
            "id",
            "job_type",
            "status",
            "search",
            "lead",
            "lead_ids",
            "total_items",
            "completed_items",
            "failed_items",
            "skipped_items",
            "progress",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_progress(self, obj):
        if not obj.total_items:
            return 0

        done = obj.completed_items + obj.failed_items + obj.skipped_items

        return min(int((done / obj.total_items) * 100), 100)