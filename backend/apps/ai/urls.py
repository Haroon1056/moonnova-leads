from django.urls import path

from .views import (
    AIUsageAPIView,
    LeadAIInsightAPIView,
    BulkGenerateAIAPIView,
    AIJobListAPIView,
    AIJobDetailAPIView,
)


urlpatterns = [
    path("usage/", AIUsageAPIView.as_view(), name="ai_usage"),

    path(
        "leads/<int:lead_id>/insight/",
        LeadAIInsightAPIView.as_view(),
        name="ai_lead_insight",
    ),

    path(
        "bulk-generate/",
        BulkGenerateAIAPIView.as_view(),
        name="ai_bulk_generate",
    ),

    path("jobs/", AIJobListAPIView.as_view(), name="ai_jobs"),
    path("jobs/<int:job_id>/", AIJobDetailAPIView.as_view(), name="ai_job_detail"),
]