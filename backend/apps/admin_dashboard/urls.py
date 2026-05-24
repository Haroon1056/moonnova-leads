from django.urls import path

from .views import (
    AdminDashboardOverviewAPIView,
    AdminDashboardTopUsersAPIView,
    AdminDashboardActivityAPIView,
    AdminDashboardHealthAPIView,
    AdminDashboardFailuresAPIView,

    AdminUserListAPIView,
    AdminUserDetailAPIView,
    AdminUserUsageUpdateAPIView,
    AdminUserSuspendAPIView,
    AdminUserActivateAPIView,

    AdminSearchListAPIView,
    AdminLeadListAPIView,
    AdminExportListAPIView,
    AdminEnrichmentJobListAPIView,

    AdminMonitoringEventListAPIView,
    AdminAISummaryAPIView,
    AdminAIJobListAPIView,
)


urlpatterns = [
    path("overview/", AdminDashboardOverviewAPIView.as_view(), name="admin_dashboard_overview"),
    path("top-users/", AdminDashboardTopUsersAPIView.as_view(), name="admin_dashboard_top_users"),
    path("activity/", AdminDashboardActivityAPIView.as_view(), name="admin_dashboard_activity"),
    path("system-health/", AdminDashboardHealthAPIView.as_view(), name="admin_dashboard_health"),
    path("failures/", AdminDashboardFailuresAPIView.as_view(), name="admin_dashboard_failures"),

    path("users/", AdminUserListAPIView.as_view(), name="admin_dashboard_users"),
    path("users/<int:user_id>/", AdminUserDetailAPIView.as_view(), name="admin_dashboard_user_detail"),
    path("users/<int:user_id>/usage/", AdminUserUsageUpdateAPIView.as_view(), name="admin_dashboard_user_usage_update"),
    path("users/<int:user_id>/suspend/", AdminUserSuspendAPIView.as_view(), name="admin_dashboard_user_suspend"),
    path("users/<int:user_id>/activate/", AdminUserActivateAPIView.as_view(), name="admin_dashboard_user_activate"),

    path("searches/", AdminSearchListAPIView.as_view(), name="admin_dashboard_searches"),
    path("leads/", AdminLeadListAPIView.as_view(), name="admin_dashboard_leads"),
    path("exports/", AdminExportListAPIView.as_view(), name="admin_dashboard_exports"),
    path("enrichment-jobs/", AdminEnrichmentJobListAPIView.as_view(), name="admin_dashboard_enrichment_jobs"),

    # F6 professional admin endpoints
    path("monitoring/events/", AdminMonitoringEventListAPIView.as_view(), name="admin_monitoring_events"),
    path("ai/summary/", AdminAISummaryAPIView.as_view(), name="admin_ai_summary"),
    path("ai/jobs/", AdminAIJobListAPIView.as_view(), name="admin_ai_jobs"),
]