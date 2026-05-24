from django.urls import path

from .views import (
    LeadListAPIView,
    LeadUpdateAPIView,
    BulkLeadActionAPIView,

    # Old immediate CSV export
    ExportLeadsAPIView,

    # New Phase 8B export system
    ExportCreateAPIView,
    ExportDetailAPIView,
    ExportDownloadAPIView,
    DeleteExportAPIView,
    ExportHistoryAPIView,
    DeleteExportHistoryAPIView,

    LeadListCollectionAPIView,
    LeadListDetailAPIView,
    AddLeadsToListAPIView,
    RemoveLeadFromListAPIView,

    EnrichLeadWebsiteAPIView,
    BulkEnrichLeadWebsiteAPIView,
    EnrichSearchLeadsAPIView,
    EnrichmentJobListAPIView,
    EnrichmentJobDetailAPIView,

    StorageSummaryAPIView,
    RunMyCleanupAPIView,

    DeleteSearchDataAPIView,
    ClearSearchLeadsAPIView,
    
    TestRealtimeAPIView,
)


urlpatterns = [
    # =====================================================
    # Leads
    # =====================================================
    path("", LeadListAPIView.as_view(), name="lead_list"),
    path("<int:lead_id>/", LeadUpdateAPIView.as_view(), name="lead_update"),
    path("bulk-action/", BulkLeadActionAPIView.as_view(), name="lead_bulk_action"),

    # =====================================================
    # Export System
    # =====================================================

    # Old/simple direct CSV export - keep for backward compatibility
    path("export/", ExportLeadsAPIView.as_view(), name="lead_export"),

    # Professional background export system
    # GET  /exports/ = export history
    # POST /exports/ = create export
    path("exports/", ExportCreateAPIView.as_view(), name="exports"),

    # GET    /exports/<id>/ = export detail
    # DELETE /exports/<id>/ = delete export
    path("exports/<int:export_id>/", ExportDetailAPIView.as_view(), name="export_detail"),

    path(
        "exports/<int:export_id>/download/",
        ExportDownloadAPIView.as_view(),
        name="export_download",
    ),

    # Backward-compatible old history route
    path("export-history/", ExportHistoryAPIView.as_view(), name="export_history"),
    path(
        "export-history/<int:export_id>/",
        DeleteExportHistoryAPIView.as_view(),
        name="delete_export_history",
    ),

    # =====================================================
    # Storage / Cleanup
    # =====================================================
    path("storage/summary/", StorageSummaryAPIView.as_view(), name="storage_summary"),
    path("cleanup/run/", RunMyCleanupAPIView.as_view(), name="run_my_cleanup"),

    # =====================================================
    # Search Data Controls
    # =====================================================
    path(
        "search/<int:search_id>/delete/",
        DeleteSearchDataAPIView.as_view(),
        name="delete_search_data",
    ),
    path(
        "search/<int:search_id>/clear-leads/",
        ClearSearchLeadsAPIView.as_view(),
        name="clear_search_leads",
    ),

    # =====================================================
    # Enrichment Jobs
    # =====================================================
    path(
        "enrichment-jobs/",
        EnrichmentJobListAPIView.as_view(),
        name="enrichment_jobs",
    ),
    path(
        "enrichment-jobs/<int:job_id>/",
        EnrichmentJobDetailAPIView.as_view(),
        name="enrichment_job_detail",
    ),

    # =====================================================
    # Website Enrichment
    # =====================================================
    path(
        "<int:lead_id>/enrich-website/",
        EnrichLeadWebsiteAPIView.as_view(),
        name="lead_enrich_website",
    ),
    path(
        "bulk-enrich-website/",
        BulkEnrichLeadWebsiteAPIView.as_view(),
        name="lead_bulk_enrich_website",
    ),
    path(
        "search/<int:search_id>/enrich-website/",
        EnrichSearchLeadsAPIView.as_view(),
        name="search_leads_enrich_website",
    ),
    
    path("realtime/test/", TestRealtimeAPIView.as_view(), name="realtime_test"),

    # =====================================================
    # Lead Lists
    # =====================================================
    path("lists/", LeadListCollectionAPIView.as_view(), name="lead_lists"),
    path("lists/<int:list_id>/", LeadListDetailAPIView.as_view(), name="lead_list_detail"),
    path("lists/<int:list_id>/add/", AddLeadsToListAPIView.as_view(), name="lead_list_add"),
    path(
        "lists/<int:list_id>/remove/<int:lead_id>/",
        RemoveLeadFromListAPIView.as_view(),
        name="lead_list_remove",
    ),
]