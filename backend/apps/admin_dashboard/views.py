from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from apps.searches.models import Search
from apps.leads.models import Lead, ExportHistory, LeadEnrichmentJob
from apps.usage.models import UserUsage

try:
    from apps.ai.models import AIJob
except Exception:
    AIJob = None

from .permissions import IsAdminUserOnly
from .serializers import UserUsageAdminUpdateSerializer
from .services import (
    get_admin_overview,
    get_top_users_by_usage,
    get_recent_activity,
    get_system_health_summary,
    get_failure_summary,
    get_admin_user_queryset,
    get_user_detail,
    serialize_admin_user,
    update_user_usage_limits,
    get_admin_ai_summary,
    serialize_admin_ai_job,
    get_monitoring_events_queryset,
)


User = get_user_model()


def get_page_size(request, default=25, maximum=100):
    try:
        size = int(request.GET.get("page_size", default))
    except Exception:
        size = default

    return min(max(size, 1), maximum)


class AdminDashboardOverviewAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        try:
            days = int(request.GET.get("days", 30))
        except Exception:
            days = 30

        return Response(get_admin_overview(days=days))


class AdminDashboardTopUsersAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        try:
            limit = int(request.GET.get("limit", 10))
        except Exception:
            limit = 10

        return Response(get_top_users_by_usage(limit=limit))


class AdminDashboardActivityAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        try:
            limit = int(request.GET.get("limit", 30))
        except Exception:
            limit = 30

        return Response(get_recent_activity(limit=limit))


class AdminDashboardHealthAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        return Response(get_system_health_summary())


class AdminDashboardFailuresAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        try:
            days = int(request.GET.get("days", 7))
        except Exception:
            days = 7

        return Response(get_failure_summary(days=days))


class AdminUserListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        users = get_admin_user_queryset()

        q = request.GET.get("q")
        account_status = request.GET.get("account_status")
        is_active = request.GET.get("is_active")
        is_staff = request.GET.get("is_staff")

        if q:
            users = users.filter(
                Q(email__icontains=q)
                | Q(full_name__icontains=q)
            )

        if is_active in ["true", "false"]:
            users = users.filter(is_active=is_active == "true")

        if is_staff in ["true", "false"]:
            users = users.filter(is_staff=is_staff == "true")

        if account_status:
            users = users.filter(usage__account_status=account_status)

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request)

        page = paginator.paginate_queryset(users, request)
        data = [serialize_admin_user(user) for user in page]

        return paginator.get_paginated_response(data)


class AdminUserDetailAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request, user_id):
        data = get_user_detail(user_id)

        if not data:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data)


class AdminUserUsageUpdateAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def patch(self, request, user_id):
        user = User.objects.filter(id=user_id).first()

        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserUsageAdminUpdateSerializer(data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usage = update_user_usage_limits(user, serializer.validated_data)

        return Response(
            {
                "message": "User usage settings updated.",
                "user_id": user.id,
                "usage": {
                    "account_status": usage.account_status,
                    "beta_access": usage.beta_access,
                    "max_searches_per_day": usage.max_searches_per_day,
                    "max_searches_per_month": usage.max_searches_per_month,
                    "max_leads_per_day": usage.max_leads_per_day,
                    "max_leads_per_month": usage.max_leads_per_month,
                    "max_exports_per_day": usage.max_exports_per_day,
                    "max_exports_per_month": usage.max_exports_per_month,
                    "unlimited_searches": usage.unlimited_searches,
                    "unlimited_leads": usage.unlimited_leads,
                    "unlimited_exports": usage.unlimited_exports,
                },
            }
        )


class AdminUserSuspendAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request, user_id):
        user = User.objects.filter(id=user_id).first()

        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_superuser:
            return Response(
                {"detail": "Superuser cannot be suspended from this endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = False
        user.save(update_fields=["is_active"])

        usage, _ = UserUsage.objects.get_or_create(user=user)
        usage.account_status = UserUsage.ACCOUNT_STATUS_SUSPENDED
        usage.save(update_fields=["account_status", "updated_at"])

        return Response(
            {
                "message": "User suspended.",
                "user_id": user.id,
            }
        )


class AdminUserActivateAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request, user_id):
        user = User.objects.filter(id=user_id).first()

        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        usage, _ = UserUsage.objects.get_or_create(user=user)
        usage.account_status = UserUsage.ACCOUNT_STATUS_ACTIVE
        usage.save(update_fields=["account_status", "updated_at"])

        return Response(
            {
                "message": "User activated.",
                "user_id": user.id,
            }
        )


class AdminSearchListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        searches = Search.objects.select_related("user").order_by("-created_at")

        q = request.GET.get("q")
        status_value = request.GET.get("status")
        user_id = request.GET.get("user_id")

        if q:
            searches = searches.filter(
                Q(user__email__icontains=q)
                | Q(keywords__icontains=q)
                | Q(locations__icontains=q)
            )

        if status_value:
            searches = searches.filter(status=status_value)

        if user_id:
            searches = searches.filter(user_id=user_id)

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request)

        page = paginator.paginate_queryset(searches, request)

        data = []

        for search in page:
            data.append(
                {
                    "id": search.id,
                    "user_id": search.user_id,
                    "user_email": getattr(search.user, "email", None),
                    "keywords": search.keywords,
                    "locations": search.locations,
                    "status": search.status,
                    "max_leads": search.max_leads,
                    "scrape_mode": search.scrape_mode,
                    "email_enrichment": search.email_enrichment,
                    "total_tasks": search.total_tasks,
                    "completed_tasks": search.completed_tasks,
                    "failed_tasks": search.failed_tasks,
                    "progress": search.progress(),
                    "leads_count": search.leads.count(),
                    "error_message": search.error_message,
                    "created_at": search.created_at,
                    "updated_at": search.updated_at,
                }
            )

        return paginator.get_paginated_response(data)


class AdminLeadListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        leads = Lead.objects.select_related("search", "search__user").order_by("-created_at")

        q = request.GET.get("q")
        user_id = request.GET.get("user_id")
        website_status = request.GET.get("website_status")
        enrichment_status = request.GET.get("enrichment_status")
        lead_status = request.GET.get("status")

        if q:
            leads = leads.filter(
                Q(name__icontains=q)
                | Q(phone__icontains=q)
                | Q(email_1__icontains=q)
                | Q(website__icontains=q)
                | Q(search__user__email__icontains=q)
            )

        if user_id:
            leads = leads.filter(search__user_id=user_id)

        if website_status:
            leads = leads.filter(website_status=website_status)

        if enrichment_status:
            leads = leads.filter(enrichment_status=enrichment_status)

        if lead_status:
            leads = leads.filter(status=lead_status)

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request)

        page = paginator.paginate_queryset(leads, request)

        data = []

        for lead in page:
            data.append(
                {
                    "id": lead.id,
                    "user_id": lead.search.user_id,
                    "user_email": getattr(lead.search.user, "email", None),
                    "search_id": lead.search_id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "email_1": lead.email_1,
                    "website": lead.website,
                    "website_status": lead.website_status,
                    "enrichment_status": lead.enrichment_status,
                    "email_confidence": lead.email_confidence,
                    "status": lead.status,
                    "lead_score": lead.lead_score,
                    "opportunity_score": lead.opportunity_score,
                    "created_at": lead.created_at,
                }
            )

        return paginator.get_paginated_response(data)


class AdminExportListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        exports = ExportHistory.objects.select_related("user", "search", "lead_list").order_by("-created_at")

        q = request.GET.get("q")
        user_id = request.GET.get("user_id")
        status_value = request.GET.get("status")
        export_type = request.GET.get("export_type")

        if q:
            exports = exports.filter(
                Q(user__email__icontains=q)
                | Q(file_name__icontains=q)
            )

        if user_id:
            exports = exports.filter(user_id=user_id)

        if status_value:
            exports = exports.filter(status=status_value)

        if export_type:
            exports = exports.filter(export_type=export_type)

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request)

        page = paginator.paginate_queryset(exports, request)

        data = []

        for export in page:
            data.append(
                {
                    "id": export.id,
                    "user_id": export.user_id,
                    "user_email": getattr(export.user, "email", None),
                    "search_id": export.search_id,
                    "lead_list_id": export.lead_list_id,
                    "export_type": export.export_type,
                    "file_format": export.export_type,
                    "export_scope": export.export_scope,
                    "status": export.status,
                    "total_rows": export.total_rows,
                    "file_name": export.file_name,
                    "file_size_bytes": export.file_size_bytes,
                    "error_message": export.error_message,
                    "created_at": export.created_at,
                    "completed_at": export.completed_at,
                }
            )

        return paginator.get_paginated_response(data)


class AdminEnrichmentJobListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        jobs = LeadEnrichmentJob.objects.select_related("user", "search", "lead").order_by("-created_at")

        q = request.GET.get("q")
        user_id = request.GET.get("user_id")
        status_value = request.GET.get("status")
        job_type = request.GET.get("job_type")

        if q:
            jobs = jobs.filter(
                Q(user__email__icontains=q)
                | Q(error_message__icontains=q)
            )

        if user_id:
            jobs = jobs.filter(user_id=user_id)

        if status_value:
            jobs = jobs.filter(status=status_value)

        if job_type:
            jobs = jobs.filter(job_type=job_type)

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request)

        page = paginator.paginate_queryset(jobs, request)

        data = []

        for job in page:
            data.append(
                {
                    "id": job.id,
                    "user_id": job.user_id,
                    "user_email": getattr(job.user, "email", None),
                    "job_type": job.job_type,
                    "status": job.status,
                    "search_id": job.search_id,
                    "lead_id": job.lead_id,
                    "total_items": job.total_items,
                    "completed_items": job.completed_items,
                    "failed_items": job.failed_items,
                    "skipped_items": job.skipped_items,
                    "progress": job.progress(),
                    "error_message": job.error_message,
                    "created_at": job.created_at,
                    "completed_at": job.completed_at,
                }
            )

        return paginator.get_paginated_response(data)


class AdminMonitoringEventListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        events = get_monitoring_events_queryset()

        q = request.GET.get("q")
        level = request.GET.get("level")
        source = request.GET.get("source")
        resolved = request.GET.get("resolved")

        if q:
            events = events.filter(
                Q(title__icontains=q)
                | Q(message__icontains=q)
                | Q(task_name__icontains=q)
                | Q(object_type__icontains=q)
                | Q(object_id__icontains=q)
            )

        if level:
            events = events.filter(level=level)

        if source:
            events = events.filter(source=source)

        if resolved in ["true", "false"]:
            events = events.filter(resolved=resolved == "true")

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request, default=25, maximum=100)

        page = paginator.paginate_queryset(events, request)

        data = []

        for event in page:
            data.append(
                {
                    "id": event.id,
                    "user": event.user_id,
                    "user_email": getattr(event.user, "email", None),
                    "level": event.level,
                    "source": event.source,
                    "title": event.title,
                    "message": event.message,
                    "task_name": event.task_name,
                    "task_id": event.task_id,
                    "object_type": event.object_type,
                    "object_id": event.object_id,
                    "metadata": event.metadata,
                    "resolved": event.resolved,
                    "resolved_at": event.resolved_at,
                    "created_at": event.created_at,
                }
            )

        return paginator.get_paginated_response(data)


class AdminAISummaryAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        try:
            days = int(request.GET.get("days", 30))
        except Exception:
            days = 30

        return Response(get_admin_ai_summary(days=days))


class AdminAIJobListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        if not AIJob:
            return Response([])

        jobs = AIJob.objects.select_related("user").order_by("-created_at")

        q = request.GET.get("q")
        user_id = request.GET.get("user_id")
        status_value = request.GET.get("status")
        job_type = request.GET.get("job_type")

        if q:
            jobs = jobs.filter(
                Q(user__email__icontains=q)
                | Q(error_message__icontains=q)
            )

        if user_id:
            jobs = jobs.filter(user_id=user_id)

        if status_value:
            jobs = jobs.filter(status=status_value)

        if job_type:
            jobs = jobs.filter(job_type=job_type)

        paginator = PageNumberPagination()
        paginator.page_size = get_page_size(request)

        page = paginator.paginate_queryset(jobs, request)

        data = [serialize_admin_ai_job(job) for job in page]

        return paginator.get_paginated_response(data)