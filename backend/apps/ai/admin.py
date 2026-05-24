from django.contrib import admin

from .models import AIJob, AILeadInsight, AIUsageLog


@admin.register(AIJob)
class AIJobAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "job_type",
        "status",
        "total_items",
        "completed_items",
        "failed_items",
        "skipped_items",
        "credits_used",
        "created_at",
    ]

    list_filter = [
        "job_type",
        "status",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "error_message",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
    ]


@admin.register(AILeadInsight)
class AILeadInsightAdmin(admin.ModelAdmin):
    list_display = [
        "lead",
        "user",
        "ai_priority",
        "ai_suggested_offer",
        "ai_best_channel",
        "provider",
        "model_name",
        "generated_at",
    ]

    list_filter = [
        "ai_priority",
        "provider",
        "model_name",
        "generated_at",
    ]

    search_fields = [
        "lead__name",
        "user__email",
        "ai_summary",
        "ai_suggested_offer",
        "ai_email_subject",
    ]

    readonly_fields = [
        "raw_response",
        "generated_at",
        "created_at",
        "updated_at",
    ]


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "lead",
        "job",
        "request_type",
        "credits_used",
        "provider",
        "model_name",
        "created_at",
    ]

    list_filter = [
        "provider",
        "model_name",
        "request_type",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "lead__name",
    ]