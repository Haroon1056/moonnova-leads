from django.conf import settings
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.http import Http404
from django.db import transaction

import os
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from apps.core.ratelimits import api_ratelimit
from apps.searches.models import Search
from apps.realtime.events import send_enrichment_started, send_export_started, send_notification

from .models import Lead, LeadList, LeadListItem, ExportHistory, LeadEnrichmentJob
from .serializers import (
    LeadSerializer,
    LeadListSerializer,
    LeadListDetailSerializer,
    ExportHistorySerializer,
    LeadEnrichmentJobSerializer,
)
from .exporter import (
    export_leads_csv,
    build_export_queryset,
    create_export_history,
    generate_export_file,
    get_export_download_response,
)
from .cleanup import get_user_storage_summary
from .tasks import (
    enrich_lead_website_task,
    bulk_enrich_leads_task,
    enrich_search_leads_task,
    cleanup_user_data_task,
    generate_export_file_task,
)

from apps.usage.services import (
    check_can_export,
    record_export_created,
)


def normalize_boolean(value):
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.strip().lower()

        if value in ["true", "1", "yes", "on"]:
            return True

        if value in ["false", "0", "no", "off"]:
            return False

    return None


def apply_lead_filters(leads, request):
    search_id = request.GET.get("search_id")
    keyword = request.GET.get("keyword")
    location = request.GET.get("location")
    status_value = request.GET.get("status")
    rating = request.GET.get("rating")
    website_status = request.GET.get("website_status")
    enrichment_status = request.GET.get("enrichment_status")
    min_score = request.GET.get("min_score")
    has_email = normalize_boolean(request.GET.get("has_email"))
    has_website = normalize_boolean(request.GET.get("has_website"))
    is_favorite = normalize_boolean(request.GET.get("is_favorite"))
    is_broken_website = normalize_boolean(request.GET.get("is_broken_website"))
    is_social_only = normalize_boolean(request.GET.get("is_social_only"))
    is_free_builder = normalize_boolean(request.GET.get("is_free_builder"))
    website_platform = request.GET.get("website_platform")
    q = request.GET.get("q")

    if search_id:
        leads = leads.filter(search_id=search_id)

    if keyword:
        leads = leads.filter(keyword__icontains=keyword)

    if location:
        leads = leads.filter(location__icontains=location)

    if status_value:
        leads = leads.filter(status=status_value)

    if website_status:
        leads = leads.filter(website_status=website_status)

    if enrichment_status:
        leads = leads.filter(enrichment_status=enrichment_status)

    if rating:
        try:
            rating_value = float(rating)
            leads = leads.filter(rating__gte=rating_value)
        except Exception:
            pass

    if min_score:
        try:
            min_score_value = int(min_score)
            leads = leads.filter(opportunity_score__gte=min_score_value)
        except Exception:
            pass

    if has_email is True:
        leads = leads.exclude(email_1__isnull=True).exclude(email_1="")

    if has_email is False:
        leads = leads.filter(Q(email_1__isnull=True) | Q(email_1=""))

    if has_website is True:
        leads = leads.filter(has_website=True)

    if has_website is False:
        leads = leads.filter(has_website=False)

    if is_favorite is not None:
        leads = leads.filter(is_favorite=is_favorite)

    if is_broken_website is not None:
        leads = leads.filter(is_broken_website=is_broken_website)

    if is_social_only is not None:
        leads = leads.filter(is_social_only=is_social_only)

    if is_free_builder is not None:
        leads = leads.filter(is_free_builder=is_free_builder)

    if website_platform:
        leads = leads.filter(website_platform__icontains=website_platform)

    if q:
        leads = leads.filter(
            Q(name__icontains=q)
            | Q(phone__icontains=q)
            | Q(email_1__icontains=q)
            | Q(website__icontains=q)
            | Q(category__icontains=q)
            | Q(city__icontains=q)
            | Q(state__icontains=q)
            | Q(country__icontains=q)
        )

    return leads


def apply_sorting(leads, request):
    sort = request.GET.get("sort", "-created_at")

    allowed_sort_fields = [
        "created_at",
        "-created_at",
        "rating",
        "-rating",
        "review_count",
        "-review_count",
        "lead_score",
        "-lead_score",
        "opportunity_score",
        "-opportunity_score",
        "email_confidence",
        "-email_confidence",
        "name",
        "-name",
    ]

    if sort not in allowed_sort_fields:
        sort = "-created_at"

    return leads.order_by(sort)


class LeadListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leads = Lead.objects.filter(
            search__user=request.user
        ).select_related("search")

        leads = apply_lead_filters(leads, request)
        leads = apply_sorting(leads, request)

        paginator = PageNumberPagination()
        paginator.page_size = int(
            request.GET.get(
                "page_size",
                getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 25),
            )
        )

        page = paginator.paginate_queryset(leads, request)
        serializer = LeadSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class LeadUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, lead_id):
        lead = Lead.objects.filter(
            id=lead_id,
            search__user=request.user,
        ).first()

        if not lead:
            return Response(
                {"detail": "Lead not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        allowed_fields = [
            "status",
            "notes",
            "is_favorite",
            "tags",
        ]

        update_fields = []

        for field in allowed_fields:
            if field in request.data:
                setattr(lead, field, request.data.get(field))
                update_fields.append(field)

        if update_fields:
            lead.save(update_fields=update_fields + ["updated_at"])

        return Response(LeadSerializer(lead).data)


class BulkLeadActionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lead_ids = request.data.get("lead_ids", [])
        action = request.data.get("action")

        if not isinstance(lead_ids, list) or not lead_ids:
            return Response(
                {"detail": "lead_ids list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leads = Lead.objects.filter(
            id__in=lead_ids,
            search__user=request.user,
        )

        if action == "delete":
            count = leads.count()
            leads.delete()
            return Response({"message": f"{count} leads deleted."})

        if action == "favorite":
            count = leads.update(is_favorite=True)
            return Response({"message": f"{count} leads marked favorite."})

        if action == "unfavorite":
            count = leads.update(is_favorite=False)
            return Response({"message": f"{count} leads removed from favorite."})

        if action == "status":
            new_status = request.data.get("status")

            if new_status not in [
                Lead.STATUS_HOT,
                Lead.STATUS_WARM,
                Lead.STATUS_COLD,
            ]:
                return Response(
                    {"detail": "Invalid lead status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            count = leads.update(status=new_status)
            return Response({"message": f"{count} leads updated."})

        return Response(
            {"detail": "Invalid action."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@method_decorator(
    api_ratelimit("lead_export", key="user_or_ip", method="GET"),
    name="dispatch",
)
class ExportLeadsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit_check = check_can_export(request.user)

        if not limit_check.allowed:
            return Response(
                {
                    "detail": limit_check.message,
                    "limit": limit_check.limit,
                    "remaining": limit_check.remaining,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        response = export_leads_csv(
            user=request.user,
            search_id=request.GET.get("search_id"),
            keyword=request.GET.get("keyword"),
            location=request.GET.get("location"),
            status=request.GET.get("status"),
            rating=request.GET.get("rating"),
            has_email=request.GET.get("has_email"),
            has_website=request.GET.get("has_website"),
            include_ai=request.GET.get("include_ai"),
        )

        record_export_created(request.user)

        return response


@method_decorator(
    api_ratelimit("enrichment", key="user_or_ip", method="POST"),
    name="dispatch",
)
class EnrichLeadWebsiteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lead_id):
        lead = Lead.objects.filter(
            id=lead_id,
            search__user=request.user,
        ).first()

        if not lead:
            return Response(
                {"detail": "Lead not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        force = bool(request.data.get("force", False))

        job = LeadEnrichmentJob.objects.create(
            user=request.user,
            job_type=LeadEnrichmentJob.JOB_TYPE_SINGLE,
            status=LeadEnrichmentJob.STATUS_PENDING,
            lead=lead,
            lead_ids=[lead.id],
            total_items=1,
        )
        
        send_enrichment_started(request.user.id, job)

        enrich_lead_website_task.delay(
            lead_id=lead.id,
            job_id=job.id,
            force=force,
        )

        return Response(
            {
                "message": "Website enrichment started.",
                "lead_id": lead.id,
                "job": LeadEnrichmentJobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(
    api_ratelimit("enrichment", key="user_or_ip", method="POST"),
    name="dispatch",
)
class BulkEnrichLeadWebsiteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lead_ids = request.data.get("lead_ids", [])
        force = bool(request.data.get("force", False))

        if not isinstance(lead_ids, list) or not lead_ids:
            return Response(
                {"detail": "lead_ids list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_lead_ids = list(
            Lead.objects.filter(
                id__in=lead_ids,
                search__user=request.user,
            ).values_list("id", flat=True)
        )

        if not valid_lead_ids:
            return Response(
                {"detail": "No valid leads found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        job = LeadEnrichmentJob.objects.create(
            user=request.user,
            job_type=LeadEnrichmentJob.JOB_TYPE_BULK,
            status=LeadEnrichmentJob.STATUS_PENDING,
            lead_ids=valid_lead_ids,
            total_items=len(valid_lead_ids),
        )

        send_enrichment_started(request.user.id, job)

        bulk_enrich_leads_task.delay(
            lead_ids=valid_lead_ids,
            job_id=job.id,
            force=force,
        )

        return Response(
            {
                "message": "Bulk website enrichment started.",
                "total": len(valid_lead_ids),
                "lead_ids": valid_lead_ids,
                "job": LeadEnrichmentJobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(
    api_ratelimit("enrichment", key="user_or_ip", method="POST"),
    name="dispatch",
)
class EnrichSearchLeadsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, search_id):
        force = bool(request.data.get("force", False))

        search = Search.objects.filter(
            id=search_id,
            user=request.user,
        ).first()

        if not search:
            return Response(
                {"detail": "Search not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        valid_lead_ids = list(
            Lead.objects.filter(
                search=search,
            ).values_list("id", flat=True)
        )

        if not valid_lead_ids:
            return Response(
                {"detail": "No leads found for this search."},
                status=status.HTTP_404_NOT_FOUND,
            )

        job = LeadEnrichmentJob.objects.create(
            user=request.user,
            job_type=LeadEnrichmentJob.JOB_TYPE_SEARCH,
            status=LeadEnrichmentJob.STATUS_PENDING,
            search=search,
            lead_ids=valid_lead_ids,
            total_items=len(valid_lead_ids),
        )

        send_enrichment_started(request.user.id, job)

        enrich_search_leads_task.delay(
            search_id=search_id,
            job_id=job.id,
            force=force,
        )

        return Response(
            {
                "message": "Website enrichment started for this search.",
                "search_id": search_id,
                "total": len(valid_lead_ids),
                "job": LeadEnrichmentJobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class EnrichmentJobListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = LeadEnrichmentJob.objects.filter(
            user=request.user
        ).order_by("-created_at")[:50]

        return Response(
            LeadEnrichmentJobSerializer(jobs, many=True).data
        )


class EnrichmentJobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = LeadEnrichmentJob.objects.filter(
            id=job_id,
            user=request.user,
        ).first()

        if not job:
            return Response(
                {"detail": "Enrichment job not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(LeadEnrichmentJobSerializer(job).data)


class LeadListCollectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lists = LeadList.objects.filter(user=request.user).order_by("-created_at")
        return Response(LeadListSerializer(lists, many=True).data)

    def post(self, request):
        name = request.data.get("name")
        description = request.data.get("description")

        if not name:
            return Response(
                {"detail": "List name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead_list, created = LeadList.objects.get_or_create(
            user=request.user,
            name=name,
            defaults={"description": description},
        )

        if not created and description is not None:
            lead_list.description = description
            lead_list.save(update_fields=["description", "updated_at"])

        return Response(
            LeadListSerializer(lead_list).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class LeadListDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, list_id):
        lead_list = LeadList.objects.filter(
            id=list_id,
            user=request.user,
        ).prefetch_related("items__lead").first()

        if not lead_list:
            return Response(
                {"detail": "Lead list not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(LeadListDetailSerializer(lead_list).data)

    def delete(self, request, list_id):
        lead_list = LeadList.objects.filter(
            id=list_id,
            user=request.user,
        ).first()

        if not lead_list:
            return Response(
                {"detail": "Lead list not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        lead_list.delete()

        return Response({"message": "Lead list deleted."})


class AddLeadsToListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, list_id):
        lead_list = LeadList.objects.filter(
            id=list_id,
            user=request.user,
        ).first()

        if not lead_list:
            return Response(
                {"detail": "Lead list not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        lead_ids = request.data.get("lead_ids", [])

        if not isinstance(lead_ids, list) or not lead_ids:
            return Response(
                {"detail": "lead_ids list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        leads = Lead.objects.filter(
            id__in=lead_ids,
            search__user=request.user,
        )

        added = 0

        for lead in leads:
            _, created = LeadListItem.objects.get_or_create(
                lead_list=lead_list,
                lead=lead,
            )

            if created:
                added += 1

        return Response(
            {
                "message": f"{added} leads added to list.",
                "added": added,
            }
        )


class RemoveLeadFromListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, list_id, lead_id):
        lead_list = LeadList.objects.filter(
            id=list_id,
            user=request.user,
        ).first()

        if not lead_list:
            return Response(
                {"detail": "Lead list not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted, _ = LeadListItem.objects.filter(
            lead_list=lead_list,
            lead_id=lead_id,
        ).delete()

        return Response(
            {
                "message": "Lead removed from list.",
                "deleted": deleted,
            }
        )


class StorageSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary = get_user_storage_summary(request.user)
        return Response(summary)


class RunMyCleanupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cleanup_user_data_task.delay(request.user.id)

        return Response(
            {
                "message": "Cleanup started.",
                "user_id": request.user.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DeleteSearchDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, search_id):
        search = Search.objects.filter(
            id=search_id,
            user=request.user,
        ).first()

        if not search:
            return Response(
                {"detail": "Search not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        search.delete()

        return Response(
            {
                "message": "Search and related leads deleted.",
                "search_id": search_id,
            }
        )


class ClearSearchLeadsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, search_id):
        search = Search.objects.filter(
            id=search_id,
            user=request.user,
        ).first()

        if not search:
            return Response(
                {"detail": "Search not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_count, _ = Lead.objects.filter(search=search).delete()

        return Response(
            {
                "message": "Search leads deleted. Search history kept.",
                "search_id": search_id,
                "deleted_count": deleted_count,
            }
        )
        
def normalize_export_type(value):
    value = value or ExportHistory.EXPORT_TYPE_CSV
    value = str(value).lower().strip()

    if value in ["excel", "xls"]:
        value = ExportHistory.EXPORT_TYPE_XLSX

    if value not in [
        ExportHistory.EXPORT_TYPE_CSV,
        ExportHistory.EXPORT_TYPE_XLSX,
    ]:
        return None

    return value


def normalize_export_scope(value):
    value = value or ExportHistory.SCOPE_ALL
    value = str(value).lower().strip()

    scope_map = {
        "all": ExportHistory.SCOPE_ALL,
        "all_leads": ExportHistory.SCOPE_ALL,
        "filtered": ExportHistory.SCOPE_ALL,
        "search": ExportHistory.SCOPE_SEARCH,
        "lead_list": ExportHistory.SCOPE_LEAD_LIST,
        "list": ExportHistory.SCOPE_LEAD_LIST,
        "selected": ExportHistory.SCOPE_SELECTED,
        "selected_leads": ExportHistory.SCOPE_SELECTED,
    }

    return scope_map.get(value, ExportHistory.SCOPE_ALL)


def normalize_int_list_for_view(value):
    if not value:
        return []

    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = value.split(",")
    else:
        items = [value]

    final_ids = []

    for item in items:
        try:
            final_ids.append(int(item))
        except Exception:
            continue

    return list(set(final_ids))


class ExportCreateAPIView(APIView):
    """
    Professional export endpoint.

    GET  /api/leads/exports/  -> list export history
    POST /api/leads/exports/  -> create background export
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        exports = (
            ExportHistory.objects.filter(user=request.user)
            .select_related("search", "lead_list")
            .order_by("-created_at")
        )

        serializer = ExportHistorySerializer(
            exports,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        limit_check = check_can_export(request.user)

        if not limit_check.allowed:
            return Response(
                {
                    "detail": limit_check.message,
                    "limit": limit_check.limit,
                    "remaining": limit_check.remaining,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        export_type = normalize_export_type(
            request.data.get("export_type")
            or request.data.get("file_format")
        )

        if not export_type:
            return Response(
                {"detail": "Invalid export type. Use csv or xlsx."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        export_scope = normalize_export_scope(
            request.data.get("export_scope")
        )

        # Accept both frontend and backend names
        search_id = (
            request.data.get("search_id")
            or request.data.get("search")
            or None
        )

        lead_list_id = (
            request.data.get("lead_list_id")
            or request.data.get("lead_list")
            or None
        )

        selected_lead_ids = normalize_int_list_for_view(
            request.data.get("selected_lead_ids")
            or request.data.get("lead_ids")
            or []
        )

        if export_scope == ExportHistory.SCOPE_SEARCH and not search_id:
            return Response(
                {"detail": "search_id is required for search export."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if export_scope == ExportHistory.SCOPE_LEAD_LIST and not lead_list_id:
            return Response(
                {"detail": "lead_list_id is required for lead list export."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if export_scope == ExportHistory.SCOPE_SELECTED and not selected_lead_ids:
            return Response(
                {"detail": "lead_ids list is required for selected leads export."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        include_ai = (
            normalize_boolean(request.data.get("include_ai")) is True
            or normalize_boolean(request.data.get("include_ai_fields")) is True
        )

        filters = {
            "search_id": search_id,
            "lead_list_id": lead_list_id,
            "keyword": request.data.get("keyword"),
            "location": request.data.get("location"),
            "status": request.data.get("status"),
            "rating": request.data.get("rating"),
            "has_email": request.data.get("has_email"),
            "has_website": request.data.get("has_website"),
            "website_status": request.data.get("website_status"),
            "enrichment_status": request.data.get("enrichment_status"),
            "min_score": request.data.get("min_score"),
            "include_ai": include_ai,
            "include_basic_fields": request.data.get("include_basic_fields", True),
            "include_contact_fields": request.data.get("include_contact_fields", True),
            "include_website_fields": request.data.get("include_website_fields", True),
            "include_enrichment_fields": request.data.get(
                "include_enrichment_fields",
                True,
            ),
            "include_ai_fields": include_ai,
            "include_raw_data": request.data.get("include_raw_data", False),
        }

        leads = build_export_queryset(
            user=request.user,
            search_id=search_id,
            lead_list_id=lead_list_id,
            selected_lead_ids=selected_lead_ids,
            keyword=filters.get("keyword"),
            location=filters.get("location"),
            status=filters.get("status"),
            rating=filters.get("rating"),
            has_email=filters.get("has_email"),
            has_website=filters.get("has_website"),
            website_status=filters.get("website_status"),
            enrichment_status=filters.get("enrichment_status"),
            min_score=filters.get("min_score"),
        )

        total_rows = leads.count()

        if total_rows <= 0:
            return Response(
                {"detail": "No leads found for this export."},
                status=status.HTTP_404_NOT_FOUND,
            )

        export_history = create_export_history(
            user=request.user,
            export_type=export_type,
            search_id=search_id,
            lead_list_id=lead_list_id,
            selected_lead_ids=selected_lead_ids,
            filters=filters,
            total_rows=total_rows,
            status=ExportHistory.STATUS_PENDING,
        )

        generate_export_file_task.apply_async(
            args=[export_history.id],
            queue="default",
        )

        send_export_started(request.user.id, export_history)
        record_export_created(request.user)

        serializer = ExportHistorySerializer(
            export_history,
            context={"request": request},
        )

        return Response(
            {
                "message": "Export job started.",
                "export": serializer.data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ExportDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        export_history = ExportHistory.objects.filter(
            id=export_id,
            user=request.user,
        ).first()

        if not export_history:
            return Response(
                {"detail": "Export not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ExportHistorySerializer(
            export_history,
            context={"request": request},
        )

        return Response(serializer.data)

    def delete(self, request, export_id):
        export_history = ExportHistory.objects.filter(
            id=export_id,
            user=request.user,
        ).first()

        if not export_history:
            return Response(
                {"detail": "Export not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if export_history.file_path and os.path.exists(export_history.file_path):
            try:
                os.remove(export_history.file_path)
            except Exception:
                pass

        export_history.delete()

        return Response({"message": "Export deleted."})


class ExportDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        export_history = ExportHistory.objects.filter(
            id=export_id,
            user=request.user,
        ).first()

        if not export_history:
            return Response(
                {"detail": "Export not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if export_history.status != ExportHistory.STATUS_COMPLETED:
            return Response(
                {"detail": "Export is not ready yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if export_history.expires_at and export_history.expires_at < timezone.now():
            export_history.status = ExportHistory.STATUS_EXPIRED
            export_history.save(update_fields=["status", "updated_at"])

            return Response(
                {"detail": "Export has expired."},
                status=status.HTTP_410_GONE,
            )

        response = get_export_download_response(export_history)

        if not response:
            return Response(
                {"detail": "Export file not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return response


# Backward-compatible history route.
# Frontend should use /exports/, but this keeps old route working.
class ExportHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        exports = (
            ExportHistory.objects.filter(user=request.user)
            .select_related("search", "lead_list")
            .order_by("-created_at")
        )

        serializer = ExportHistorySerializer(
            exports,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)


class DeleteExportHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, export_id):
        export_history = ExportHistory.objects.filter(
            id=export_id,
            user=request.user,
        ).first()

        if not export_history:
            return Response(
                {"detail": "Export history not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if export_history.file_path and os.path.exists(export_history.file_path):
            try:
                os.remove(export_history.file_path)
            except Exception:
                pass

        export_history.delete()

        return Response({"message": "Export history deleted."})


# Backward-compatible old delete endpoint.
# You can remove this later after frontend fully uses DELETE /exports/<id>/.
class DeleteExportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, export_id):
        export_history = ExportHistory.objects.filter(
            id=export_id,
            user=request.user,
        ).first()

        if not export_history:
            return Response(
                {"detail": "Export not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if export_history.file_path and os.path.exists(export_history.file_path):
            try:
                os.remove(export_history.file_path)
            except Exception:
                pass

        export_history.delete()

        return Response({"message": "Export deleted."})
    
class TestRealtimeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        send_notification(
            user_id=request.user.id,
            title="Realtime test",
            message="Your WebSocket connection is working.",
            level="success",
        )

        return Response(
            {
                "message": "Realtime test event sent.",
            }
        )
        
        
def clean_extension_value(value, max_length=None):
    value = "" if value is None else str(value)
    value = " ".join(value.split()).strip()

    if max_length and len(value) > max_length:
        return value[:max_length]

    return value


def safe_create_model_instance(model_class, **data):
    """
    Creates model instance using only fields that really exist on the model.
    This avoids deployment errors if model fields change slightly.
    """
    valid_fields = {
        field.name
        for field in model_class._meta.get_fields()
        if hasattr(field, "attname") and not field.auto_created
    }

    clean_data = {
        key: value
        for key, value in data.items()
        if key in valid_fields
    }

    return model_class.objects.create(**clean_data)


class ExtensionImportLeadsAPIView(APIView):
    """
    Import visible Google Maps leads from MoonNova Chrome Extension.

    Expected payload:
    {
        "context": {
            "keyword": "plumber",
            "location": "Perth",
            "source_url": "https://www.google.com/maps/..."
        },
        "leads": [
            {
                "business_name": "ABC Plumbing",
                "phone": "+61 ...",
                "website": "https://...",
                "map_link": "https://www.google.com/maps/place/...",
                "rating": "4.8",
                "review_count": "120",
                "raw_text": "..."
            }
        ]
    }
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        context = request.data.get("context") or {}
        leads_data = request.data.get("leads") or []

        if not isinstance(leads_data, list) or not leads_data:
            return Response(
                {"detail": "leads list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        keyword = clean_extension_value(
            context.get("keyword") or request.data.get("keyword") or "Google Maps"
        )
        location = clean_extension_value(
            context.get("location") or request.data.get("location") or "Extension Import"
        )
        source_url = clean_extension_value(context.get("source_url"))

        completed_status = getattr(Search, "STATUS_COMPLETED", "completed")

        search = safe_create_model_instance(
            Search,
            user=request.user,
            keyword=keyword,
            location=location,
            status=completed_status,
            max_leads=len(leads_data),
            total_tasks=1,
            completed_tasks=1,
            progress=100,
            source_url=source_url,
        )

        created = 0
        skipped = 0
        imported_lead_ids = []

        for item in leads_data:
            if not isinstance(item, dict):
                skipped += 1
                continue

            name = clean_extension_value(
                item.get("name") or item.get("business_name"),
                max_length=255,
            )

            if not name:
                skipped += 1
                continue

            phone = clean_extension_value(item.get("phone"), max_length=100)
            website = clean_extension_value(item.get("website"), max_length=500)
            map_link = clean_extension_value(item.get("map_link"), max_length=1000)
            category = clean_extension_value(item.get("category"), max_length=255)
            address = clean_extension_value(item.get("address"), max_length=500)
            raw_text = clean_extension_value(item.get("raw_text"))

            rating = item.get("rating")
            review_count = item.get("review_count")

            try:
                rating = float(rating) if rating not in [None, ""] else None
            except Exception:
                rating = None

            try:
                review_count = int(str(review_count).replace(",", "")) if review_count not in [None, ""] else None
            except Exception:
                review_count = None

            duplicate_query = Lead.objects.filter(
                search__user=request.user,
                name__iexact=name,
            )

            if map_link:
                duplicate_query = duplicate_query.filter(map_link=map_link)

            if duplicate_query.exists():
                skipped += 1
                continue

            has_website = bool(website)

            lead = safe_create_model_instance(
                Lead,
                search=search,
                name=name,
                category=category,
                phone=phone,
                website=website,
                address=address,
                rating=rating,
                review_count=review_count,
                map_link=map_link,
                keyword=keyword,
                location=location,
                has_website=has_website,
                source="chrome_extension",
                raw_data={
                    "source": "chrome_extension",
                    "source_url": source_url,
                    "raw_text": raw_text,
                    "payload": item,
                },
            )

            imported_lead_ids.append(lead.id)
            created += 1

        # Update search totals if those fields exist
        update_fields = []

        if hasattr(search, "total_leads"):
            search.total_leads = created
            update_fields.append("total_leads")

        if hasattr(search, "total_results"):
            search.total_results = created
            update_fields.append("total_results")

        if hasattr(search, "completed_tasks"):
            search.completed_tasks = 1
            update_fields.append("completed_tasks")

        if hasattr(search, "progress"):
            search.progress = 100
            update_fields.append("progress")

        if update_fields:
            search.save(update_fields=update_fields)

        return Response(
            {
                "message": "Extension leads imported successfully.",
                "created": created,
                "skipped": skipped,
                "search_id": search.id,
                "lead_ids": imported_lead_ids,
            },
            status=status.HTTP_201_CREATED,
        )