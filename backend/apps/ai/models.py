from django.conf import settings
from django.db import models


class AIJob(models.Model):
    JOB_TYPE_LEAD_INSIGHT = "lead_insight"
    JOB_TYPE_FULL_PERSONALIZATION = "full_personalization"

    JOB_TYPE_CHOICES = [
        (JOB_TYPE_LEAD_INSIGHT, "Lead Insight"),
        (JOB_TYPE_FULL_PERSONALIZATION, "Full Personalization"),
    ]

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_jobs",
    )

    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES,
        default=JOB_TYPE_FULL_PERSONALIZATION,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    lead_ids = models.JSONField(default=list, blank=True)

    total_items = models.PositiveIntegerField(default=0)
    completed_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)
    skipped_items = models.PositiveIntegerField(default=0)

    credit_cost = models.PositiveIntegerField(default=0)
    credits_used = models.PositiveIntegerField(default=0)

    # Campaign / AI generation settings
    target_offer = models.CharField(max_length=255, blank=True, null=True)
    campaign_goal = models.TextField(blank=True, null=True)
    tone = models.CharField(max_length=150, blank=True, null=True)
    target_audience = models.CharField(max_length=255, blank=True, null=True)
    outreach_channel = models.CharField(max_length=100, blank=True, null=True)
    custom_instructions = models.TextField(blank=True, null=True)

    error_message = models.TextField(blank=True, null=True)

    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["job_type", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.job_type} - {self.status}"

    def progress(self):
        if not self.total_items:
            return 0

        done = self.completed_items + self.failed_items + self.skipped_items

        return min(int((done / self.total_items) * 100), 100)

    @property
    def processed_items(self):
        return self.completed_items + self.failed_items + self.skipped_items

    @property
    def is_finished(self):
        return bool(self.total_items and self.processed_items >= self.total_items)


class AILeadInsight(models.Model):
    PRIORITY_VERY_HIGH = "very_high"
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"
    PRIORITY_SKIP = "skip"

    PRIORITY_CHOICES = [
        (PRIORITY_VERY_HIGH, "Very High"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_LOW, "Low"),
        (PRIORITY_SKIP, "Skip"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_lead_insights",
    )

    lead = models.OneToOneField(
        "leads.Lead",
        on_delete=models.CASCADE,
        related_name="ai_insight",
    )

    # Campaign settings used to generate this insight
    target_offer = models.CharField(max_length=255, blank=True, null=True)
    campaign_goal = models.TextField(blank=True, null=True)
    tone = models.CharField(max_length=150, blank=True, null=True)
    target_audience = models.CharField(max_length=255, blank=True, null=True)
    outreach_channel = models.CharField(max_length=100, blank=True, null=True)
    custom_instructions = models.TextField(blank=True, null=True)

    ai_priority = models.CharField(
        max_length=30,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True,
    )

    ai_summary = models.TextField(blank=True, null=True)

    ai_suggested_offer = models.CharField(max_length=255, blank=True, null=True)
    ai_offer_reason = models.TextField(blank=True, null=True)

    ai_best_channel = models.CharField(max_length=100, blank=True, null=True)
    ai_channel_reason = models.TextField(blank=True, null=True)

    ai_first_line = models.TextField(blank=True, null=True)

    ai_email_subject = models.CharField(max_length=255, blank=True, null=True)
    ai_email_body = models.TextField(blank=True, null=True)

    ai_followup_1 = models.TextField(blank=True, null=True)
    ai_followup_2 = models.TextField(blank=True, null=True)
    ai_followup_3 = models.TextField(blank=True, null=True)

    ai_facebook_message = models.TextField(blank=True, null=True)
    ai_linkedin_message = models.TextField(blank=True, null=True)
    ai_whatsapp_message = models.TextField(blank=True, null=True)

    ai_website_weakness = models.TextField(blank=True, null=True)
    ai_local_seo_opportunity = models.TextField(blank=True, null=True)
    ai_score_explanation = models.TextField(blank=True, null=True)

    provider = models.CharField(max_length=50, default="gemini")
    model_name = models.CharField(max_length=100, blank=True, null=True)

    raw_response = models.JSONField(default=dict, blank=True)

    generated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "ai_priority"]),
            models.Index(fields=["generated_at"]),
            models.Index(fields=["target_offer"]),
            models.Index(fields=["outreach_channel"]),
        ]

    def __str__(self):
        lead_name = getattr(self.lead, "name", None) or "Lead"
        return f"{lead_name} - {self.ai_priority}"

    # Frontend-friendly aliases.
    # These help if serializers expose properties or if you use SerializerMethodField.
    @property
    def priority(self):
        return self.ai_priority

    @property
    def suggested_offer(self):
        return self.ai_suggested_offer

    @property
    def best_outreach_channel(self):
        return self.ai_best_channel

    @property
    def first_line(self):
        return self.ai_first_line

    @property
    def email_subject(self):
        return self.ai_email_subject

    @property
    def email_body(self):
        return self.ai_email_body

    @property
    def follow_up_1(self):
        return self.ai_followup_1

    @property
    def follow_up_2(self):
        return self.ai_followup_2

    @property
    def follow_up_3(self):
        return self.ai_followup_3

    @property
    def facebook_message(self):
        return self.ai_facebook_message

    @property
    def linkedin_message(self):
        return self.ai_linkedin_message

    @property
    def whatsapp_message(self):
        return self.ai_whatsapp_message

    @property
    def website_weakness(self):
        return self.ai_website_weakness

    @property
    def local_seo_opportunity(self):
        return self.ai_local_seo_opportunity

    @property
    def opportunity_reason(self):
        return self.ai_score_explanation


class AIUsageLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_usage_logs",
    )

    job = models.ForeignKey(
        AIJob,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="usage_logs",
    )

    lead = models.ForeignKey(
        "leads.Lead",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ai_usage_logs",
    )

    credits_used = models.PositiveIntegerField(default=0)

    provider = models.CharField(max_length=50, default="gemini")
    model_name = models.CharField(max_length=100, blank=True, null=True)

    request_type = models.CharField(max_length=100, default="lead_insight")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["request_type"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.credits_used} credits"