from django.conf import settings
from django.db import models
from django.utils import timezone


class UserUsage(models.Model):
    """
    Stores beta usage limits and current usage for each user.

    This is not billing yet.
    This is only for free beta control.
    """

    ACCOUNT_STATUS_BETA = "beta"
    ACCOUNT_STATUS_ACTIVE = "active"
    ACCOUNT_STATUS_LIMITED = "limited"
    ACCOUNT_STATUS_SUSPENDED = "suspended"
    ACCOUNT_STATUS_BLOCKED = "blocked"

    ACCOUNT_STATUS_CHOICES = [
        (ACCOUNT_STATUS_BETA, "Beta"),
        (ACCOUNT_STATUS_ACTIVE, "Active"),
        (ACCOUNT_STATUS_LIMITED, "Limited"),
        (ACCOUNT_STATUS_SUSPENDED, "Suspended"),
        (ACCOUNT_STATUS_BLOCKED, "Blocked"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage",
    )

    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default=ACCOUNT_STATUS_BETA,
    )

    beta_access = models.BooleanField(default=True)

    # Daily usage
    searches_today = models.PositiveIntegerField(default=0)
    exports_today = models.PositiveIntegerField(default=0)
    leads_today = models.PositiveIntegerField(default=0)

    # Monthly usage
    searches_this_month = models.PositiveIntegerField(default=0)
    exports_this_month = models.PositiveIntegerField(default=0)
    leads_this_month = models.PositiveIntegerField(default=0)

    # Beta limits
    max_searches_per_day = models.PositiveIntegerField(default=5)
    max_searches_per_month = models.PositiveIntegerField(default=100)

    max_exports_per_day = models.PositiveIntegerField(default=3)
    max_exports_per_month = models.PositiveIntegerField(default=50)

    max_leads_per_search = models.PositiveIntegerField(default=300)
    max_leads_per_day = models.PositiveIntegerField(default=1000)
    max_leads_per_month = models.PositiveIntegerField(default=5000)

    # Admin override
    unlimited_searches = models.BooleanField(default=False)
    unlimited_exports = models.BooleanField(default=False)
    unlimited_leads = models.BooleanField(default=False)

    # Reset dates
    daily_reset_at = models.DateField(default=timezone.localdate)
    monthly_reset_at = models.DateField(default=timezone.localdate)
    
    # Data retention settings
    lead_retention_days = models.PositiveIntegerField(default=15)
    search_history_retention_days = models.PositiveIntegerField(default=30)
    raw_data_retention_days = models.PositiveIntegerField(default=7)
    export_retention_days = models.PositiveIntegerField(default=7)

    # Storage control
    auto_delete_old_leads = models.BooleanField(default=True)
    auto_clear_raw_data = models.BooleanField(default=True)
    auto_delete_old_exports = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Usage"
        verbose_name_plural = "User Usage"

    def __str__(self):
        return f"{self.user} - {self.account_status}"

    @property
    def is_allowed(self):
        return self.account_status not in [
            self.ACCOUNT_STATUS_SUSPENDED,
            self.ACCOUNT_STATUS_BLOCKED,
        ]

    @property
    def remaining_searches_today(self):
        if self.unlimited_searches:
            return None

        return max(self.max_searches_per_day - self.searches_today, 0)

    @property
    def remaining_leads_this_month(self):
        if self.unlimited_leads:
            return None

        return max(self.max_leads_per_month - self.leads_this_month, 0)

    @property
    def remaining_exports_today(self):
        if self.unlimited_exports:
            return None

        return max(self.max_exports_per_day - self.exports_today, 0)


class UsageEvent(models.Model):
    """
    Logs user actions for analytics and debugging.
    """

    EVENT_SEARCH_CREATED = "search_created"
    EVENT_SEARCH_BLOCKED = "search_blocked"
    EVENT_LEAD_SAVED = "lead_saved"
    EVENT_LEAD_BLOCKED = "lead_blocked"
    EVENT_EXPORT_CREATED = "export_created"
    EVENT_EXPORT_BLOCKED = "export_blocked"
    EVENT_LIMIT_RESET = "limit_reset"

    EVENT_CHOICES = [
        (EVENT_SEARCH_CREATED, "Search Created"),
        (EVENT_SEARCH_BLOCKED, "Search Blocked"),
        (EVENT_LEAD_SAVED, "Lead Saved"),
        (EVENT_LEAD_BLOCKED, "Lead Blocked"),
        (EVENT_EXPORT_CREATED, "Export Created"),
        (EVENT_EXPORT_BLOCKED, "Export Blocked"),
        (EVENT_LIMIT_RESET, "Limit Reset"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_events",
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_CHOICES,
    )

    amount = models.PositiveIntegerField(default=1)

    meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "event_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.event_type} - {self.amount}"