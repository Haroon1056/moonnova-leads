from django.conf import settings
from django.db import models
from django.utils import timezone


class Search(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    SCRAPE_MODE_SAFE = "safe"
    SCRAPE_MODE_BALANCED = "balanced"
    SCRAPE_MODE_DEEP = "deep"

    SCRAPE_MODE_CHOICES = [
        (SCRAPE_MODE_SAFE, "Safe"),
        (SCRAPE_MODE_BALANCED, "Balanced"),
        (SCRAPE_MODE_DEEP, "Deep"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="searches",
    )

    keywords = models.JSONField(default=list)
    locations = models.JSONField(default=list)

    max_leads = models.PositiveIntegerField(default=100)

    scrape_mode = models.CharField(
        max_length=20,
        choices=SCRAPE_MODE_CHOICES,
        default=SCRAPE_MODE_SAFE,
    )

    email_enrichment = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    failed_tasks = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True, null=True)

    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Search #{self.id} - {self.user}"

    def progress(self):
        if not self.total_tasks:
            return 0

        done = self.completed_tasks + self.failed_tasks

        progress_value = int((done / self.total_tasks) * 100)

        return min(progress_value, 100)

    @property
    def is_active(self):
        return self.status in [
            self.STATUS_PENDING,
            self.STATUS_RUNNING,
        ]


class SearchQueryTask(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_PAUSED = "paused"
    STATUS_CANCELLED = "cancelled"
    STATUS_SKIPPED = "skipped"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    search = models.ForeignKey(
        Search,
        on_delete=models.CASCADE,
        related_name="query_tasks",
    )

    keyword = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    query_text = models.CharField(max_length=500)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    max_leads = models.PositiveIntegerField(default=100)

    leads_found = models.PositiveIntegerField(default=0)
    processed_index = models.PositiveIntegerField(default=0)

    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=1)

    error_message = models.TextField(blank=True, null=True)

    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        unique_together = ("search", "keyword", "location")
        indexes = [
            models.Index(fields=["search", "status"]),
            models.Index(fields=["keyword", "location"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.query_text

    def mark_running(self):
        self.status = self.STATUS_RUNNING
        self.started_at = self.started_at or timezone.now()
        self.error_message = None
        self.save(
            update_fields=[
                "status",
                "started_at",
                "error_message",
                "updated_at",
            ]
        )

    def mark_completed(self):
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.error_message = None
        self.save(
            update_fields=[
                "status",
                "completed_at",
                "error_message",
                "updated_at",
            ]
        )

    def mark_failed(self, message=None):
        self.status = self.STATUS_FAILED
        self.completed_at = timezone.now()
        self.error_message = message
        self.save(
            update_fields=[
                "status",
                "completed_at",
                "error_message",
                "updated_at",
            ]
        )

    def can_retry(self):
        return self.retry_count < self.max_retries