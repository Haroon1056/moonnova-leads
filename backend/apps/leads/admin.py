from django.contrib import admin

from .models import (
    Lead,
    LeadList,
    LeadListItem,
    ExportHistory,
    LeadEnrichmentJob,
)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "phone",
        "website_status",
        "enrichment_status",
        "enrichment_attempts",
        "email_confidence",
        "status",
        "lead_score",
        "opportunity_score",
        "rating",
        "review_count",
        "created_at",
    ]

    list_filter = [
        "status",
        "website_status",
        "enrichment_status",
        "has_website",
        "is_social_only",
        "is_free_builder",
        "is_broken_website",
        "is_favorite",
        "created_at",
    ]

    search_fields = [
        "name",
        "phone",
        "email_1",
        "email_2",
        "email_3",
        "website",
        "domain",
        "category",
        "city",
        "state",
        "country",
    ]

    readonly_fields = [
        "lead_score",
        "opportunity_score",
        "opportunity_reason",
        "enrichment_last_run_at",
        "enrichment_error",
        "email_source_pages",
        "email_confidence",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Business Info",
            {
                "fields": (
                    "search",
                    "name",
                    "keyword",
                    "location",
                    "category",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "pincode",
                    "country",
                    "latitude",
                    "longitude",
                    "map_link",
                    "place_id",
                )
            },
        ),
        (
            "Emails",
            {
                "fields": (
                    "email_1",
                    "email_2",
                    "email_3",
                    "email_confidence",
                    "email_source_pages",
                )
            },
        ),
        (
            "Website",
            {
                "fields": (
                    "website",
                    "domain",
                    "has_website",
                    "website_status",
                    "website_http_status",
                    "website_error",
                    "website_platform",
                    "is_social_only",
                    "is_free_builder",
                    "is_broken_website",
                )
            },
        ),
        (
            "Social Links",
            {
                "fields": (
                    "facebook_url",
                    "instagram_url",
                    "linkedin_url",
                    "youtube_url",
                    "tiktok_url",
                )
            },
        ),
        (
            "Rating & Scores",
            {
                "fields": (
                    "rating",
                    "rating_count",
                    "review_count",
                    "status",
                    "lead_score",
                    "opportunity_score",
                    "opportunity_reason",
                )
            },
        ),
        (
            "User Lead Management",
            {
                "fields": (
                    "tags",
                    "notes",
                    "is_favorite",
                )
            },
        ),
        (
            "Enrichment Status",
            {
                "fields": (
                    "enrichment_status",
                    "enrichment_attempts",
                    "enrichment_error",
                    "enrichment_last_run_at",
                )
            },
        ),
        (
            "Source",
            {
                "fields": (
                    "source_query",
                    "source_keyword",
                    "source_location",
                    "raw_data",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


class LeadListItemInline(admin.TabularInline):
    model = LeadListItem
    extra = 0
    autocomplete_fields = ["lead"]


@admin.register(LeadList)
class LeadListAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "created_at",
    ]

    search_fields = [
        "name",
        "user__email",
    ]

    inlines = [LeadListItemInline]


@admin.register(LeadListItem)
class LeadListItemAdmin(admin.ModelAdmin):
    list_display = [
        "lead_list",
        "lead",
        "added_at",
    ]

    search_fields = [
        "lead_list__name",
        "lead__name",
    ]

    autocomplete_fields = [
        "lead_list",
        "lead",
    ]


@admin.register(ExportHistory)
class ExportHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "export_type",
        "status",
        "total_rows",
        "file_name",
        "expires_at",
        "created_at",
    ]

    list_filter = [
        "export_type",
        "status",
        "created_at",
        "expires_at",
    ]

    search_fields = [
        "user__email",
        "file_name",
    ]

    readonly_fields = [
        "user",
        "search",
        "export_type",
        "status",
        "filters",
        "total_rows",
        "file_name",
        "file_path",
        "error_message",
        "expires_at",
        "created_at",
        "updated_at",
    ]


@admin.register(LeadEnrichmentJob)
class LeadEnrichmentJobAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "job_type",
        "status",
        "total_items",
        "completed_items",
        "failed_items",
        "skipped_items",
        "progress_display",
        "created_at",
    ]

    list_filter = [
        "job_type",
        "status",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "lead__name",
    ]

    readonly_fields = [
        "user",
        "job_type",
        "status",
        "search",
        "lead",
        "lead_ids",
        "total_items",
        "completed_items",
        "failed_items",
        "skipped_items",
        "error_message",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]

    def progress_display(self, obj):
        return f"{obj.progress()}%"

    progress_display.short_description = "Progress"