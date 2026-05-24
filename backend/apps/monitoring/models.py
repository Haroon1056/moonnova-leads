from django.conf import settings
from django.db import models


class SystemEvent(models.Model):
    LEVEL_INFO = "info"
    LEVEL_WARNING = "warning"
    LEVEL_ERROR = "error"
    LEVEL_CRITICAL = "critical"

    LEVEL_CHOICES = [
        (LEVEL_INFO, "Info"),
        (LEVEL_WARNING, "Warning"),
        (LEVEL_ERROR, "Error"),
        (LEVEL_CRITICAL, "Critical"),
    ]

    SOURCE_API = "api"
    SOURCE_CELERY = "celery"
    SOURCE_SCRAPER = "scraper"
    SOURCE_ENRICHMENT = "enrichment"
    SOURCE_EXPORT = "export"
    SOURCE_SYSTEM = "system"

    SOURCE_CHOICES = [
        (SOURCE_API, "API"),
        (SOURCE_CELERY, "Celery"),
        (SOURCE_SCRAPER, "Scraper"),
        (SOURCE_ENRICHMENT, "Enrichment"),
        (SOURCE_EXPORT, "Export"),
        (SOURCE_SYSTEM, "System"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="system_events",
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default=LEVEL_INFO,
        db_index=True,
    )

    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default=SOURCE_SYSTEM,
        db_index=True,
    )

    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)

    task_name = models.CharField(max_length=255, blank=True, null=True)
    task_id = models.CharField(max_length=255, blank=True, null=True)

    object_type = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)

    metadata = models.JSONField(default=dict, blank=True)

    resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["level", "created_at"]),
            models.Index(fields=["source", "created_at"]),
            models.Index(fields=["resolved"]),
            models.Index(fields=["task_id"]),
        ]

    def __str__(self):
        return f"{self.level} - {self.source} - {self.title}"