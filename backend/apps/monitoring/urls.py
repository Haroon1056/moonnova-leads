from django.urls import path

from .views import (
    MonitoringHealthAPIView,
    MonitoringEventListAPIView,
    MonitoringEventDetailAPIView,
    MonitoringEventResolveAPIView,
    MonitoringEventUnresolveAPIView,
    MonitoringTestEventAPIView,
)


urlpatterns = [
    path("health/", MonitoringHealthAPIView.as_view(), name="monitoring_health"),
    path("events/", MonitoringEventListAPIView.as_view(), name="monitoring_events"),
    path("events/<int:event_id>/", MonitoringEventDetailAPIView.as_view(), name="monitoring_event_detail"),
    path("events/<int:event_id>/resolve/", MonitoringEventResolveAPIView.as_view(), name="monitoring_event_resolve"),
    path("events/<int:event_id>/unresolve/", MonitoringEventUnresolveAPIView.as_view(), name="monitoring_event_unresolve"),
    path("test-event/", MonitoringTestEventAPIView.as_view(), name="monitoring_test_event"),
]