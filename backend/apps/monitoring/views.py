from django.db.models import Q
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from apps.admin_dashboard.permissions import IsAdminUserOnly

from .models import SystemEvent
from .serializers import SystemEventSerializer
from .services import get_system_health, log_system_event


class MonitoringHealthAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        return Response(get_system_health())


class MonitoringEventListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        events = SystemEvent.objects.select_related("user").order_by("-created_at")

        level = request.GET.get("level")
        source = request.GET.get("source")
        resolved = request.GET.get("resolved")
        q = request.GET.get("q")

        if level:
            events = events.filter(level=level)

        if source:
            events = events.filter(source=source)

        if resolved in ["true", "false"]:
            events = events.filter(resolved=resolved == "true")

        if q:
            events = events.filter(
                Q(title__icontains=q)
                | Q(message__icontains=q)
                | Q(task_name__icontains=q)
                | Q(task_id__icontains=q)
                | Q(user__email__icontains=q)
            )

        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get("page_size", 25))

        page = paginator.paginate_queryset(events, request)

        serializer = SystemEventSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class MonitoringEventDetailAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request, event_id):
        event = SystemEvent.objects.filter(id=event_id).select_related("user").first()

        if not event:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(SystemEventSerializer(event).data)


class MonitoringEventResolveAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request, event_id):
        event = SystemEvent.objects.filter(id=event_id).first()

        if not event:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        event.resolved = True
        event.resolved_at = timezone.now()
        event.save(update_fields=["resolved", "resolved_at"])

        return Response({"message": "Event marked as resolved."})


class MonitoringEventUnresolveAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request, event_id):
        event = SystemEvent.objects.filter(id=event_id).first()

        if not event:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        event.resolved = False
        event.resolved_at = None
        event.save(update_fields=["resolved", "resolved_at"])

        return Response({"message": "Event marked as unresolved."})


class MonitoringTestEventAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request):
        event = log_system_event(
            level=SystemEvent.LEVEL_INFO,
            source=SystemEvent.SOURCE_SYSTEM,
            title="Test monitoring event",
            message="Monitoring event created successfully.",
            user=request.user,
            metadata={
                "test": True,
            },
        )

        return Response(
            {
                "message": "Test monitoring event created.",
                "event_id": event.id if event else None,
            }
        )