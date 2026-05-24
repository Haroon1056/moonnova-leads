from rest_framework import serializers

from .models import AIJob, AILeadInsight


class AILeadInsightSerializer(serializers.ModelSerializer):
    lead_name = serializers.SerializerMethodField()

    # Frontend-friendly aliases
    priority = serializers.CharField(source="ai_priority", read_only=True)
    suggested_offer = serializers.CharField(source="ai_suggested_offer", read_only=True)
    offer_reason = serializers.CharField(source="ai_offer_reason", read_only=True)
    best_outreach_channel = serializers.CharField(source="ai_best_channel", read_only=True)
    channel_reason = serializers.CharField(source="ai_channel_reason", read_only=True)
    first_line = serializers.CharField(source="ai_first_line", read_only=True)

    email_subject = serializers.CharField(source="ai_email_subject", read_only=True)
    email_body = serializers.CharField(source="ai_email_body", read_only=True)

    follow_up_1 = serializers.CharField(source="ai_followup_1", read_only=True)
    follow_up_2 = serializers.CharField(source="ai_followup_2", read_only=True)
    follow_up_3 = serializers.CharField(source="ai_followup_3", read_only=True)

    facebook_message = serializers.CharField(source="ai_facebook_message", read_only=True)
    linkedin_message = serializers.CharField(source="ai_linkedin_message", read_only=True)
    whatsapp_message = serializers.CharField(source="ai_whatsapp_message", read_only=True)

    website_weakness = serializers.CharField(source="ai_website_weakness", read_only=True)
    local_seo_opportunity = serializers.CharField(
        source="ai_local_seo_opportunity",
        read_only=True,
    )
    opportunity_reason = serializers.CharField(
        source="ai_score_explanation",
        read_only=True,
    )

    class Meta:
        model = AILeadInsight
        fields = [
            "id",
            "lead",
            "lead_name",

            # Campaign settings
            "target_offer",
            "campaign_goal",
            "tone",
            "target_audience",
            "outreach_channel",
            "custom_instructions",

            # Original backend field names
            "ai_priority",
            "ai_summary",
            "ai_suggested_offer",
            "ai_offer_reason",
            "ai_best_channel",
            "ai_channel_reason",
            "ai_first_line",
            "ai_email_subject",
            "ai_email_body",
            "ai_followup_1",
            "ai_followup_2",
            "ai_followup_3",
            "ai_facebook_message",
            "ai_linkedin_message",
            "ai_whatsapp_message",
            "ai_website_weakness",
            "ai_local_seo_opportunity",
            "ai_score_explanation",

            # Frontend-friendly aliases
            "priority",
            "suggested_offer",
            "offer_reason",
            "best_outreach_channel",
            "channel_reason",
            "first_line",
            "email_subject",
            "email_body",
            "follow_up_1",
            "follow_up_2",
            "follow_up_3",
            "facebook_message",
            "linkedin_message",
            "whatsapp_message",
            "website_weakness",
            "local_seo_opportunity",
            "opportunity_reason",

            # Provider
            "provider",
            "model_name",
            "raw_response",

            # Dates
            "generated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_lead_name(self, obj):
        return obj.lead.name if obj.lead else None


class AIJobSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    processed_items = serializers.SerializerMethodField()
    is_finished = serializers.SerializerMethodField()

    class Meta:
        model = AIJob
        fields = [
            "id",
            "job_type",
            "status",
            "lead_ids",

            "total_items",
            "completed_items",
            "failed_items",
            "skipped_items",
            "processed_items",

            "credit_cost",
            "credits_used",

            "target_offer",
            "campaign_goal",
            "tone",
            "target_audience",
            "outreach_channel",
            "custom_instructions",

            "progress",
            "is_finished",
            "error_message",

            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_progress(self, obj):
        return obj.progress()

    def get_processed_items(self, obj):
        return obj.completed_items + obj.failed_items + obj.skipped_items

    def get_is_finished(self, obj):
        if not obj.total_items:
            return False

        processed = obj.completed_items + obj.failed_items + obj.skipped_items
        return processed >= obj.total_items


class AIUsageSummarySerializer(serializers.Serializer):
    used_this_month = serializers.IntegerField()
    monthly_limit = serializers.IntegerField()
    remaining_this_month = serializers.IntegerField()
    ai_enabled = serializers.BooleanField()
    model = serializers.CharField()

    # Optional frontend-friendly aliases
    credits_used = serializers.IntegerField(required=False)
    credits_remaining = serializers.IntegerField(required=False)
    credits_total = serializers.IntegerField(required=False)
    plan_name = serializers.CharField(required=False)