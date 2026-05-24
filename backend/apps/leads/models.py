from django.conf import settings
from django.db import models


class Lead(models.Model):
    STATUS_HOT = "hot"
    STATUS_WARM = "warm"
    STATUS_COLD = "cold"

    STATUS_CHOICES = [
        (STATUS_HOT, "Hot"),
        (STATUS_WARM, "Warm"),
        (STATUS_COLD, "Cold"),
    ]

    WEBSITE_STATUS_UNKNOWN = "unknown"
    WEBSITE_STATUS_NO_WEBSITE = "no_website"
    WEBSITE_STATUS_WORKING = "working"
    WEBSITE_STATUS_BROKEN = "broken"
    WEBSITE_STATUS_404 = "404"
    WEBSITE_STATUS_EXPIRED = "expired_domain"
    WEBSITE_STATUS_REDIRECT_ERROR = "redirect_error"
    WEBSITE_STATUS_SOCIAL_ONLY = "social_only"
    WEBSITE_STATUS_FREE_BUILDER = "free_builder"
    WEBSITE_STATUS_UNDER_CONSTRUCTION = "under_construction"
    WEBSITE_STATUS_TIMEOUT = "timeout"
    WEBSITE_STATUS_SSL_ERROR = "ssl_error"
    WEBSITE_STATUS_INVALID_URL = "invalid_url"
    WEBSITE_STATUS_CONNECTION_ERROR = "connection_error"
    WEBSITE_STATUS_PROTECTED = "protected"

    WEBSITE_STATUS_CHOICES = [
        (WEBSITE_STATUS_UNKNOWN, "Unknown"),
        (WEBSITE_STATUS_NO_WEBSITE, "No Website"),
        (WEBSITE_STATUS_WORKING, "Working"),
        (WEBSITE_STATUS_BROKEN, "Broken"),
        (WEBSITE_STATUS_404, "404"),
        (WEBSITE_STATUS_EXPIRED, "Expired Domain"),
        (WEBSITE_STATUS_REDIRECT_ERROR, "Redirect Error"),
        (WEBSITE_STATUS_SOCIAL_ONLY, "Social Only"),
        (WEBSITE_STATUS_FREE_BUILDER, "Free Builder"),
        (WEBSITE_STATUS_UNDER_CONSTRUCTION, "Under Construction"),
        (WEBSITE_STATUS_TIMEOUT, "Timeout"),
        (WEBSITE_STATUS_SSL_ERROR, "SSL Error"),
        (WEBSITE_STATUS_INVALID_URL, "Invalid URL"),
        (WEBSITE_STATUS_CONNECTION_ERROR, "Connection Error"),
        (WEBSITE_STATUS_PROTECTED, "Protected"),
    ]

    ENRICHMENT_STATUS_PENDING = "pending"
    ENRICHMENT_STATUS_RUNNING = "running"
    ENRICHMENT_STATUS_COMPLETED = "completed"
    ENRICHMENT_STATUS_FAILED = "failed"
    ENRICHMENT_STATUS_SKIPPED = "skipped"

    ENRICHMENT_STATUS_CHOICES = [
        (ENRICHMENT_STATUS_PENDING, "Pending"),
        (ENRICHMENT_STATUS_RUNNING, "Running"),
        (ENRICHMENT_STATUS_COMPLETED, "Completed"),
        (ENRICHMENT_STATUS_FAILED, "Failed"),
        (ENRICHMENT_STATUS_SKIPPED, "Skipped"),
    ]

    search = models.ForeignKey(
        "searches.Search",
        on_delete=models.CASCADE,
        related_name="leads",
    )

    name = models.CharField(max_length=500)

    keyword = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)

    phone = models.CharField(max_length=100, blank=True, null=True)

    email_1 = models.EmailField(blank=True, null=True)
    email_2 = models.EmailField(blank=True, null=True)
    email_3 = models.EmailField(blank=True, null=True)

    email_source_pages = models.JSONField(default=list, blank=True)
    email_confidence = models.PositiveIntegerField(default=0)

    website = models.URLField(max_length=1000, blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)

    has_website = models.BooleanField(default=False)

    website_status = models.CharField(
        max_length=50,
        choices=WEBSITE_STATUS_CHOICES,
        default=WEBSITE_STATUS_UNKNOWN,
        db_index=True,
    )

    website_http_status = models.PositiveIntegerField(blank=True, null=True)
    website_error = models.TextField(blank=True, null=True)
    website_platform = models.CharField(max_length=100, blank=True, null=True)

    is_social_only = models.BooleanField(default=False)
    is_free_builder = models.BooleanField(default=False)
    is_broken_website = models.BooleanField(default=False)

    facebook_url = models.URLField(max_length=1000, blank=True, null=True)
    instagram_url = models.URLField(max_length=1000, blank=True, null=True)
    linkedin_url = models.URLField(max_length=1000, blank=True, null=True)
    youtube_url = models.URLField(max_length=1000, blank=True, null=True)
    tiktok_url = models.URLField(max_length=1000, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
    )

    rating = models.FloatField(blank=True, null=True)
    rating_count = models.PositiveIntegerField(blank=True, null=True)
    review_count = models.PositiveIntegerField(blank=True, null=True)

    map_link = models.URLField(max_length=2000, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_COLD,
        db_index=True,
    )

    lead_score = models.PositiveIntegerField(default=0, db_index=True)
    opportunity_score = models.PositiveIntegerField(default=0, db_index=True)
    opportunity_reason = models.TextField(blank=True, null=True)

    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, null=True)
    is_favorite = models.BooleanField(default=False)

    source_query = models.CharField(max_length=500, blank=True, null=True)
    source_keyword = models.CharField(max_length=255, blank=True, null=True)
    source_location = models.CharField(max_length=255, blank=True, null=True)

    enrichment_status = models.CharField(
        max_length=20,
        choices=ENRICHMENT_STATUS_CHOICES,
        default=ENRICHMENT_STATUS_PENDING,
        db_index=True,
    )

    enrichment_attempts = models.PositiveIntegerField(default=0)
    enrichment_error = models.TextField(blank=True, null=True)
    enrichment_last_run_at = models.DateTimeField(blank=True, null=True)

    raw_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["search", "created_at"]),
            models.Index(fields=["keyword", "location"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["review_count"]),
            models.Index(fields=["website_status"]),
            models.Index(fields=["enrichment_status"]),
            models.Index(fields=["lead_score"]),
            models.Index(fields=["opportunity_score"]),
            models.Index(fields=["place_id"]),
            models.Index(fields=["domain"]),
        ]

    def __str__(self):
        return self.name


class LeadList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lead_lists",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    leads = models.ManyToManyField(
        Lead,
        through="LeadListItem",
        related_name="lead_lists",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "name")

    def __str__(self):
        return self.name


class LeadListItem(models.Model):
    lead_list = models.ForeignKey(
        LeadList,
        on_delete=models.CASCADE,
        related_name="items",
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="list_items",
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("lead_list", "lead")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.lead_list} - {self.lead}"


class ExportHistory(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    EXPORT_TYPE_CSV = "csv"
    EXPORT_TYPE_XLSX = "xlsx"

    EXPORT_TYPE_CHOICES = [
        (EXPORT_TYPE_CSV, "CSV"),
        (EXPORT_TYPE_XLSX, "Excel"),
    ]

    SCOPE_ALL = "all"
    SCOPE_SEARCH = "search"
    SCOPE_SELECTED = "selected"
    SCOPE_LEAD_LIST = "lead_list"

    SCOPE_CHOICES = [
        (SCOPE_ALL, "All Filtered Leads"),
        (SCOPE_SEARCH, "Search Leads"),
        (SCOPE_SELECTED, "Selected Leads"),
        (SCOPE_LEAD_LIST, "Lead List"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="export_history",
    )

    search = models.ForeignKey(
        "searches.Search",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="exports",
    )

    lead_list = models.ForeignKey(
        "leads.LeadList",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="exports",
    )

    export_type = models.CharField(
        max_length=20,
        choices=EXPORT_TYPE_CHOICES,
        default=EXPORT_TYPE_CSV,
    )

    export_scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_ALL,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    filters = models.JSONField(default=dict, blank=True)
    selected_lead_ids = models.JSONField(default=list, blank=True)

    total_rows = models.PositiveIntegerField(default=0)

    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_path = models.CharField(max_length=1000, blank=True, null=True)
    file_size_bytes = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True, null=True)

    expires_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["export_type"]),
            models.Index(fields=["export_scope"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.export_type} - {self.status}"

    @property
    def is_ready(self):
        return self.status == self.STATUS_COMPLETED and bool(self.file_path)

    @property
    def is_failed(self):
        return self.status == self.STATUS_FAILED


class LeadEnrichmentJob(models.Model):
    JOB_TYPE_SINGLE = "single"
    JOB_TYPE_BULK = "bulk"
    JOB_TYPE_SEARCH = "search"

    JOB_TYPE_CHOICES = [
        (JOB_TYPE_SINGLE, "Single Lead"),
        (JOB_TYPE_BULK, "Bulk Leads"),
        (JOB_TYPE_SEARCH, "Search Leads"),
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
        related_name="enrichment_jobs",
    )

    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default=JOB_TYPE_SINGLE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    search = models.ForeignKey(
        "searches.Search",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="enrichment_jobs",
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="enrichment_jobs",
    )

    lead_ids = models.JSONField(default=list, blank=True)

    total_items = models.PositiveIntegerField(default=0)
    completed_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)
    skipped_items = models.PositiveIntegerField(default=0)

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