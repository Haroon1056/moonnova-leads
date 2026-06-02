import logging
import threading

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.db import close_old_connections
from django.utils import timezone
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .permissions import IsSearchOwner
from .models import Search, SearchQueryTask
from .serializers import SearchSerializer
from .tasks import (
    run_search_sync,
    create_query_tasks_for_search,
)

from apps.core.ratelimits import api_ratelimit
from apps.realtime.events import send_search_started

from apps.usage.services import (
    check_account_allowed,
    check_can_create_search,
    record_search_created,
    get_or_create_usage,
)

logger = logging.getLogger(__name__)

ACTIVE_SEARCH_STATUSES = ["pending", "running"]


def normalize_to_list(value):
    if not value:
        return []

    if isinstance(value, list):
        final_items = []

        for item in value:
            if isinstance(item, str):
                parts = item.replace("\r", "").replace("\n", ",").split(",")

                for part in parts:
                    part = part.strip()
                    if part:
                        final_items.append(part)

            elif item:
                item = str(item).strip()
                if item:
                    final_items.append(item)

        return final_items

    if isinstance(value, str):
        value = value.replace("\r", "").replace("\n", ",")
        return [part.strip() for part in value.split(",") if part.strip()]

    item = str(value).strip()

    return [item] if item else []


def normalize_boolean(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in ["true", "1", "yes", "on"]

    return bool(value)


def normalize_max_leads(value):
    try:
        value = int(value)
    except Exception:
        value = 100

    if value <= 0:
        value = 100

    return value


def normalize_scrape_mode(value):
    if value not in ["safe", "balanced", "deep"]:
        return "safe"

    return value


def get_max_active_searches_per_user():
    return int(
        getattr(
            settings,
            "SCRAPER_MAX_ACTIVE_SEARCHES_PER_USER",
            1,
        )
    )


def run_search_in_background_thread(search_id):
    """
    Free Render MVP runner.

    This replaces Celery Background Workers temporarily.
    The API returns immediately while scraper continues in-process.
    """

    def target():
        close_old_connections()

        try:
            logger.info("Starting background search thread for search_id=%s", search_id)
            run_search_sync(search_id)
            logger.info("Finished background search thread for search_id=%s", search_id)

        except Exception:
            logger.exception(
                "Background search thread crashed for search_id=%s",
                search_id,
            )

            try:
                search = Search.objects.get(id=search_id)
                search.status = Search.STATUS_FAILED
                search.error_message = "Search worker crashed. Please try again."
                search.save(update_fields=["status", "error_message", "updated_at"])
            except Exception:
                logger.exception("Could not mark search as failed after thread crash")

        finally:
            close_old_connections()

    thread = threading.Thread(
        target=target,
        name=f"search-runner-{search_id}",
        daemon=True,
    )
    thread.start()

    return thread


@method_decorator(
    api_ratelimit("search_create", key="user_or_ip", method="POST"),
    name="dispatch",
)
class CreateSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account_check = check_account_allowed(request.user)

        if not account_check.allowed:
            return Response(
                {
                    "detail": account_check.message,
                    "limit": account_check.limit,
                    "remaining": account_check.remaining,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        active_count = Search.objects.filter(
            user=request.user,
            status__in=ACTIVE_SEARCH_STATUSES,
        ).count()

        max_active = get_max_active_searches_per_user()

        if active_count >= max_active:
            return Response(
                {
                    "detail": (
                        f"You already have {active_count} active search. "
                        f"Maximum active searches allowed is {max_active}."
                    ),
                    "limit": max_active,
                    "remaining": 0,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        keywords = request.data.get("keywords") or request.data.get("keyword")
        locations = request.data.get("locations") or request.data.get("location")

        keywords = normalize_to_list(keywords)
        locations = normalize_to_list(locations)

        if not keywords or not locations:
            return Response(
                {"error": "Keywords and locations are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_max_leads = normalize_max_leads(
            request.data.get("max_leads", 100)
        )

        limit_check = check_can_create_search(
            request.user,
            requested_max_leads=requested_max_leads,
        )

        if not limit_check.allowed:
            return Response(
                {
                    "detail": limit_check.message,
                    "limit": limit_check.limit,
                    "remaining": limit_check.remaining,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        usage = get_or_create_usage(request.user)

        max_leads = requested_max_leads

        if not usage.unlimited_leads:
            max_leads = min(
                requested_max_leads,
                usage.max_leads_per_search,
            )

        scrape_mode = normalize_scrape_mode(
            request.data.get("scrape_mode", "safe")
        )

        # Important for free MVP:
        # Keep default False because enrichment still requires Celery.
        email_enrichment = normalize_boolean(
            request.data.get("email_enrichment"),
            default=False,
        )

        total_tasks = len(keywords) * len(locations)

        search = Search.objects.create(
            user=request.user,
            keywords=keywords,
            locations=locations,
            max_leads=max_leads,
            scrape_mode=scrape_mode,
            email_enrichment=email_enrichment,
            total_tasks=total_tasks,
            completed_tasks=0,
            failed_tasks=0,
            status=Search.STATUS_PENDING,
        )

        create_query_tasks_for_search(search)

        record_search_created(request.user)

        send_search_started(request.user.id, search)

        run_search_in_background_thread(search.id)

        return Response(
            {
                "message": "Search started successfully",
                "search_id": search.id,
                "status": search.status,
                "email_enrichment": search.email_enrichment,
                "usage": {
                    "remaining_searches_today": usage.remaining_searches_today,
                    "remaining_leads_this_month": usage.remaining_leads_this_month,
                },
                "search": SearchSerializer(search).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SearchDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSearchOwner]

    def get_object(self, search_id, user):
        return get_object_or_404(Search, id=search_id, user=user)

    def get(self, request, search_id):
        search = self.get_object(search_id, request.user)
        return Response(SearchSerializer(search).data)


class SearchListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        searches = (
            Search.objects.filter(user=request.user)
            .annotate(leads_count_db=Count("leads"))
            .prefetch_related("query_tasks")
            .order_by("-created_at")
        )

        paginator = PageNumberPagination()
        paginator.page_size = int(
            request.GET.get(
                "page_size",
                getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 25),
            )
        )

        page = paginator.paginate_queryset(searches, request)
        serializer = SearchSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class PauseSearchAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSearchOwner]

    def post(self, request, search_id):
        search = get_object_or_404(Search, id=search_id, user=request.user)

        if search.status == Search.STATUS_PAUSED:
            return Response(
                {
                    "message": "Search is already paused",
                    "search_id": search.id,
                    "status": search.status,
                    "search": SearchSerializer(search).data,
                },
                status=status.HTTP_200_OK,
            )

        if search.status in [
            Search.STATUS_COMPLETED,
            Search.STATUS_FAILED,
            Search.STATUS_CANCELLED,
        ]:
            return Response(
                {
                    "error": f"Search is already {search.status} and cannot be paused.",
                    "search_id": search.id,
                    "status": search.status,
                    "search": SearchSerializer(search).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        search.status = Search.STATUS_PAUSED
        search.save(update_fields=["status", "updated_at"])

        SearchQueryTask.objects.filter(
            search=search,
            status__in=[
                SearchQueryTask.STATUS_PENDING,
                SearchQueryTask.STATUS_RUNNING,
            ],
        ).update(status=SearchQueryTask.STATUS_PAUSED)

        return Response(
            {
                "message": "Search paused successfully",
                "search_id": search.id,
                "status": search.status,
                "search": SearchSerializer(search).data,
            },
            status=status.HTTP_200_OK,
        )


class ResumeSearchAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSearchOwner]

    def post(self, request, search_id):
        account_check = check_account_allowed(request.user)

        if not account_check.allowed:
            return Response(
                {
                    "detail": account_check.message,
                    "limit": account_check.limit,
                    "remaining": account_check.remaining,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        search = get_object_or_404(Search, id=search_id, user=request.user)

        if search.status != Search.STATUS_PAUSED:
            return Response(
                {
                    "error": "Only paused searches can be resumed.",
                    "search_id": search.id,
                    "status": search.status,
                    "search": SearchSerializer(search).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_count = Search.objects.filter(
            user=request.user,
            status__in=ACTIVE_SEARCH_STATUSES,
        ).exclude(id=search.id).count()

        max_active = get_max_active_searches_per_user()

        if active_count >= max_active:
            return Response(
                {
                    "detail": (
                        f"You already have {active_count} active search. "
                        f"Maximum active searches allowed is {max_active}."
                    ),
                    "limit": max_active,
                    "remaining": 0,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        search.status = Search.STATUS_RUNNING
        search.save(update_fields=["status", "updated_at"])

        SearchQueryTask.objects.filter(
            search=search,
            status=SearchQueryTask.STATUS_PAUSED,
        ).update(status=SearchQueryTask.STATUS_PENDING)

        send_search_started(request.user.id, search)

        run_search_in_background_thread(search.id)

        return Response(
            {
                "message": "Search resumed successfully",
                "search_id": search.id,
                "status": search.status,
                "search": SearchSerializer(search).data,
            },
            status=status.HTTP_200_OK,
        )


class CancelSearchAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSearchOwner]

    def post(self, request, search_id):
        search = get_object_or_404(Search, id=search_id, user=request.user)

        if search.status == Search.STATUS_CANCELLED:
            return Response(
                {
                    "message": "Search is already cancelled",
                    "search_id": search.id,
                    "status": search.status,
                    "search": SearchSerializer(search).data,
                },
                status=status.HTTP_200_OK,
            )

        if search.status in [
            Search.STATUS_COMPLETED,
            Search.STATUS_FAILED,
        ]:
            return Response(
                {
                    "error": f"Search is already {search.status} and cannot be cancelled.",
                    "search_id": search.id,
                    "status": search.status,
                    "search": SearchSerializer(search).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        search.status = Search.STATUS_CANCELLED
        search.completed_at = timezone.now()
        search.save(update_fields=["status", "completed_at", "updated_at"])

        SearchQueryTask.objects.filter(
            search=search,
            status__in=[
                SearchQueryTask.STATUS_PENDING,
                SearchQueryTask.STATUS_RUNNING,
                SearchQueryTask.STATUS_PAUSED,
                SearchQueryTask.STATUS_FAILED,
            ],
        ).update(status=SearchQueryTask.STATUS_CANCELLED)

        return Response(
            {
                "message": "Search cancelled successfully",
                "search_id": search.id,
                "status": search.status,
                "search": SearchSerializer(search).data,
            },
            status=status.HTTP_200_OK,
        )



















# from django.conf import settings
# from django.shortcuts import get_object_or_404
# from django.db.models import Count
# from django.utils import timezone
# from django.utils.decorators import method_decorator

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from rest_framework.pagination import PageNumberPagination

# from .permissions import IsSearchOwner
# from .models import Search, SearchQueryTask
# from .serializers import SearchSerializer
# from .tasks import (
#     start_search_task,
#     resume_search_task,
#     create_query_tasks_for_search,
# )

# from apps.core.ratelimits import api_ratelimit
# from apps.realtime.events import send_search_started

# from apps.usage.services import (
#     check_account_allowed,
#     check_can_create_search,
#     record_search_created,
#     get_or_create_usage,
# )


# ACTIVE_SEARCH_STATUSES = ["pending", "running"]


# def normalize_to_list(value):
#     if not value:
#         return []

#     if isinstance(value, list):
#         final_items = []

#         for item in value:
#             if isinstance(item, str):
#                 parts = item.replace("\r", "").replace("\n", ",").split(",")

#                 for part in parts:
#                     part = part.strip()
#                     if part:
#                         final_items.append(part)

#             elif item:
#                 item = str(item).strip()
#                 if item:
#                     final_items.append(item)

#         return final_items

#     if isinstance(value, str):
#         value = value.replace("\r", "").replace("\n", ",")
#         return [part.strip() for part in value.split(",") if part.strip()]

#     item = str(value).strip()

#     return [item] if item else []


# def normalize_boolean(value, default=False):
#     """
#     Safe boolean normalizer.

#     Important:
#     - False must stay False.
#     - Missing value uses default.
#     - This fixes frontend toggle issue.
#     """

#     if value is None:
#         return default

#     if isinstance(value, bool):
#         return value

#     if isinstance(value, str):
#         return value.strip().lower() in ["true", "1", "yes", "on"]

#     return bool(value)


# def normalize_max_leads(value):
#     try:
#         value = int(value)
#     except Exception:
#         value = 100

#     if value <= 0:
#         value = 100

#     return value


# def normalize_scrape_mode(value):
#     if value not in ["safe", "balanced", "deep"]:
#         return "safe"

#     return value


# def get_max_active_searches_per_user():
#     return int(
#         getattr(
#             settings,
#             "SCRAPER_MAX_ACTIVE_SEARCHES_PER_USER",
#             1,
#         )
#     )


# @method_decorator(
#     api_ratelimit("search_create", key="user_or_ip", method="POST"),
#     name="dispatch",
# )
# class CreateSearchAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         account_check = check_account_allowed(request.user)

#         if not account_check.allowed:
#             return Response(
#                 {
#                     "detail": account_check.message,
#                     "limit": account_check.limit,
#                     "remaining": account_check.remaining,
#                 },
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         active_count = Search.objects.filter(
#             user=request.user,
#             status__in=ACTIVE_SEARCH_STATUSES,
#         ).count()

#         max_active = get_max_active_searches_per_user()

#         if active_count >= max_active:
#             return Response(
#                 {
#                     "detail": (
#                         f"You already have {active_count} active search. "
#                         f"Maximum active searches allowed is {max_active}."
#                     ),
#                     "limit": max_active,
#                     "remaining": 0,
#                 },
#                 status=status.HTTP_429_TOO_MANY_REQUESTS,
#             )

#         keywords = request.data.get("keywords") or request.data.get("keyword")
#         locations = request.data.get("locations") or request.data.get("location")

#         keywords = normalize_to_list(keywords)
#         locations = normalize_to_list(locations)

#         if not keywords or not locations:
#             return Response(
#                 {"error": "Keywords and locations are required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         requested_max_leads = normalize_max_leads(
#             request.data.get("max_leads", 100)
#         )

#         limit_check = check_can_create_search(
#             request.user,
#             requested_max_leads=requested_max_leads,
#         )

#         if not limit_check.allowed:
#             return Response(
#                 {
#                     "detail": limit_check.message,
#                     "limit": limit_check.limit,
#                     "remaining": limit_check.remaining,
#                 },
#                 status=status.HTTP_429_TOO_MANY_REQUESTS,
#             )

#         usage = get_or_create_usage(request.user)

#         max_leads = requested_max_leads

#         if not usage.unlimited_leads:
#             max_leads = min(
#                 requested_max_leads,
#                 usage.max_leads_per_search,
#             )

#         scrape_mode = normalize_scrape_mode(
#             request.data.get("scrape_mode", "safe")
#         )

#         # Important:
#         # Default is False so backend does not unexpectedly enrich if frontend misses field.
#         # If frontend sends true, enrichment will run after scraping.
#         email_enrichment = normalize_boolean(
#             request.data.get("email_enrichment"),
#             default=False,
#         )

#         total_tasks = len(keywords) * len(locations)

#         search = Search.objects.create(
#             user=request.user,
#             keywords=keywords,
#             locations=locations,
#             max_leads=max_leads,
#             scrape_mode=scrape_mode,
#             email_enrichment=email_enrichment,
#             total_tasks=total_tasks,
#             completed_tasks=0,
#             failed_tasks=0,
#             status=Search.STATUS_PENDING,
#         )

#         create_query_tasks_for_search(search)

#         record_search_created(request.user)

#         # Send scraping job to scraping queue.
#         start_search_task.apply_async(
#             args=[search.id],
#             queue="scraping",
#         )

#         send_search_started(request.user.id, search)

#         return Response(
#             {
#                 "message": "Search started successfully",
#                 "search_id": search.id,
#                 "status": search.status,
#                 "email_enrichment": search.email_enrichment,
#                 "usage": {
#                     "remaining_searches_today": usage.remaining_searches_today,
#                     "remaining_leads_this_month": usage.remaining_leads_this_month,
#                 },
#                 "search": SearchSerializer(search).data,
#             },
#             status=status.HTTP_201_CREATED,
#         )


# class SearchDetailAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsSearchOwner]

#     def get_object(self, search_id, user):
#         return get_object_or_404(Search, id=search_id, user=user)

#     def get(self, request, search_id):
#         search = self.get_object(search_id, request.user)
#         return Response(SearchSerializer(search).data)


# class SearchListAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         searches = (
#             Search.objects.filter(user=request.user)
#             .annotate(leads_count_db=Count("leads"))
#             .prefetch_related("query_tasks")
#             .order_by("-created_at")
#         )

#         paginator = PageNumberPagination()
#         paginator.page_size = int(
#             request.GET.get(
#                 "page_size",
#                 getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 25),
#             )
#         )

#         page = paginator.paginate_queryset(searches, request)
#         serializer = SearchSerializer(page, many=True)

#         return paginator.get_paginated_response(serializer.data)


# class PauseSearchAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsSearchOwner]

#     def post(self, request, search_id):
#         search = get_object_or_404(Search, id=search_id, user=request.user)

#         if search.status == Search.STATUS_PAUSED:
#             return Response(
#                 {
#                     "message": "Search is already paused",
#                     "search_id": search.id,
#                     "status": search.status,
#                     "search": SearchSerializer(search).data,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         if search.status in [
#             Search.STATUS_COMPLETED,
#             Search.STATUS_FAILED,
#             Search.STATUS_CANCELLED,
#         ]:
#             return Response(
#                 {
#                     "error": f"Search is already {search.status} and cannot be paused.",
#                     "search_id": search.id,
#                     "status": search.status,
#                     "search": SearchSerializer(search).data,
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         search.status = Search.STATUS_PAUSED
#         search.save(update_fields=["status", "updated_at"])

#         SearchQueryTask.objects.filter(
#             search=search,
#             status__in=[
#                 SearchQueryTask.STATUS_PENDING,
#                 SearchQueryTask.STATUS_RUNNING,
#             ],
#         ).update(status=SearchQueryTask.STATUS_PAUSED)

#         return Response(
#             {
#                 "message": "Search paused successfully",
#                 "search_id": search.id,
#                 "status": search.status,
#                 "search": SearchSerializer(search).data,
#             },
#             status=status.HTTP_200_OK,
#         )


# class ResumeSearchAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsSearchOwner]

#     def post(self, request, search_id):
#         account_check = check_account_allowed(request.user)

#         if not account_check.allowed:
#             return Response(
#                 {
#                     "detail": account_check.message,
#                     "limit": account_check.limit,
#                     "remaining": account_check.remaining,
#                 },
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         search = get_object_or_404(Search, id=search_id, user=request.user)

#         if search.status != Search.STATUS_PAUSED:
#             return Response(
#                 {
#                     "error": "Only paused searches can be resumed.",
#                     "search_id": search.id,
#                     "status": search.status,
#                     "search": SearchSerializer(search).data,
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         active_count = Search.objects.filter(
#             user=request.user,
#             status__in=ACTIVE_SEARCH_STATUSES,
#         ).exclude(id=search.id).count()

#         max_active = get_max_active_searches_per_user()

#         if active_count >= max_active:
#             return Response(
#                 {
#                     "detail": (
#                         f"You already have {active_count} active search. "
#                         f"Maximum active searches allowed is {max_active}."
#                     ),
#                     "limit": max_active,
#                     "remaining": 0,
#                 },
#                 status=status.HTTP_429_TOO_MANY_REQUESTS,
#             )

#         search.status = Search.STATUS_RUNNING
#         search.save(update_fields=["status", "updated_at"])

#         SearchQueryTask.objects.filter(
#             search=search,
#             status=SearchQueryTask.STATUS_PAUSED,
#         ).update(status=SearchQueryTask.STATUS_PENDING)

#         resume_search_task.apply_async(
#             args=[search.id],
#             queue="scraping",
#         )

#         return Response(
#             {
#                 "message": "Search resumed successfully",
#                 "search_id": search.id,
#                 "status": search.status,
#                 "search": SearchSerializer(search).data,
#             },
#             status=status.HTTP_200_OK,
#         )


# class CancelSearchAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsSearchOwner]

#     def post(self, request, search_id):
#         search = get_object_or_404(Search, id=search_id, user=request.user)

#         if search.status == Search.STATUS_CANCELLED:
#             return Response(
#                 {
#                     "message": "Search is already cancelled",
#                     "search_id": search.id,
#                     "status": search.status,
#                     "search": SearchSerializer(search).data,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         if search.status in [
#             Search.STATUS_COMPLETED,
#             Search.STATUS_FAILED,
#         ]:
#             return Response(
#                 {
#                     "error": f"Search is already {search.status} and cannot be cancelled.",
#                     "search_id": search.id,
#                     "status": search.status,
#                     "search": SearchSerializer(search).data,
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         search.status = Search.STATUS_CANCELLED
#         search.completed_at = timezone.now()
#         search.save(update_fields=["status", "completed_at", "updated_at"])

#         SearchQueryTask.objects.filter(
#             search=search,
#             status__in=[
#                 SearchQueryTask.STATUS_PENDING,
#                 SearchQueryTask.STATUS_RUNNING,
#                 SearchQueryTask.STATUS_PAUSED,
#                 SearchQueryTask.STATUS_FAILED,
#             ],
#         ).update(status=SearchQueryTask.STATUS_CANCELLED)

#         return Response(
#             {
#                 "message": "Search cancelled successfully",
#                 "search_id": search.id,
#                 "status": search.status,
#                 "search": SearchSerializer(search).data,
#             },
#             status=status.HTTP_200_OK,
#         )