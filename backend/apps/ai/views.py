from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.leads.models import Lead
from apps.realtime.events import send_ai_job_started

from .models import AIJob
from .serializers import AIJobSerializer, AILeadInsightSerializer
from .services import (
    generate_ai_lead_insight,
    get_credit_cost,
    check_ai_credits,
    get_user_ai_usage_summary,
    extract_ai_options_from_dict,
)
from .tasks import bulk_generate_ai_task


class AIUsageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_user_ai_usage_summary(request.user))


class LeadAIInsightAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lead_id):
        lead = Lead.objects.filter(
            id=lead_id,
            search__user=request.user,
        ).first()

        if not lead:
            return Response(
                {"detail": "Lead not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            insight = lead.ai_insight
        except Exception:
            insight = None

        if not insight:
            return Response(
                {"detail": "AI insight not found for this lead."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(AILeadInsightSerializer(insight).data)

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
        options = extract_ai_options_from_dict(request.data)

        credit_cost = get_credit_cost(AIJob.JOB_TYPE_FULL_PERSONALIZATION)
        credit_check = check_ai_credits(request.user, credit_cost)

        if not credit_check["allowed"]:
            return Response(
                {
                    "detail": credit_check["message"],
                    "limit": credit_check["limit"],
                    "remaining": credit_check["remaining"],
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            result = generate_ai_lead_insight(
                lead=lead,
                user=request.user,
                force=force,
                options=options,
            )

            return Response(
                {
                    "message": "AI insight generated.",
                    "skipped": result.get("skipped"),
                    "credits_used": result.get("credits_used"),
                    "target_offer": options.get("target_offer"),
                    "campaign_goal": options.get("campaign_goal"),
                    "insight": AILeadInsightSerializer(result["insight"]).data,
                }
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BulkGenerateAIAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lead_ids = request.data.get("lead_ids", [])
        job_type = request.data.get(
            "job_type",
            AIJob.JOB_TYPE_FULL_PERSONALIZATION,
        )
        force = bool(request.data.get("force", False))
        options = extract_ai_options_from_dict(request.data)

        if job_type not in [
            AIJob.JOB_TYPE_LEAD_INSIGHT,
            AIJob.JOB_TYPE_FULL_PERSONALIZATION,
        ]:
            return Response(
                {"detail": "Invalid job_type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(lead_ids, list) or not lead_ids:
            return Response(
                {"detail": "lead_ids list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_bulk = int(getattr(settings, "AI_BULK_MAX_LEADS", 50))

        if len(lead_ids) > max_bulk:
            return Response(
                {"detail": f"Maximum {max_bulk} leads allowed per AI bulk job."},
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

        credit_cost_per_item = get_credit_cost(job_type)
        total_credit_cost = credit_cost_per_item * len(valid_lead_ids)

        credit_check = check_ai_credits(request.user, total_credit_cost)

        if not credit_check["allowed"]:
            return Response(
                {
                    "detail": credit_check["message"],
                    "required": total_credit_cost,
                    "limit": credit_check["limit"],
                    "remaining": credit_check["remaining"],
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        job = AIJob.objects.create(
            user=request.user,
            job_type=job_type,
            status=AIJob.STATUS_PENDING,
            lead_ids=valid_lead_ids,
            total_items=len(valid_lead_ids),
            credit_cost=total_credit_cost,

            target_offer=options.get("target_offer"),
            campaign_goal=options.get("campaign_goal"),
            tone=options.get("tone"),
            target_audience=options.get("target_audience"),
            outreach_channel=options.get("outreach_channel"),
            custom_instructions=options.get("custom_instructions"),
        )

        bulk_generate_ai_task.delay(
            job_id=job.id,
            force=force,
        )

        send_ai_job_started(request.user.id, job)

        return Response(
            {
                "message": "AI bulk generation started.",
                "job": AIJobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AIJobListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = AIJob.objects.filter(user=request.user).order_by("-created_at")[:50]

        return Response(AIJobSerializer(jobs, many=True).data)


class AIJobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = AIJob.objects.filter(id=job_id, user=request.user).first()

        if not job:
            return Response(
                {"detail": "AI job not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(AIJobSerializer(job).data)