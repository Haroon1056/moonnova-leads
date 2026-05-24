import re
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from apps.monitoring.models import SystemEvent
from apps.monitoring.services import log_exception_event

from .gemini_client import GeminiClient
from .models import AILeadInsight, AIUsageLog, AIJob
from .prompts import build_ai_lead_insight_prompt, normalize_ai_goal_options


REQUIRED_AI_FIELDS = [
    "ai_priority",
    "ai_summary",
    "ai_suggested_offer",
    "ai_offer_reason",
    "ai_best_channel",
    "ai_channel_reason",
    "ai_first_line",
    "ai_email_subject",
    "ai_email_body",
    "ai_followup_1",
    "ai_followup_2",
    "ai_facebook_message",
    "ai_whatsapp_message",
    "ai_website_weakness",
    "ai_local_seo_opportunity",
    "ai_score_explanation",
]


def get_credit_cost(job_type):
    costs = getattr(settings, "AI_CREDIT_COSTS", {})

    return int(costs.get(job_type, 5))


def get_monthly_ai_credits_used(user):
    start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = AIUsageLog.objects.filter(
        user=user,
        created_at__gte=start,
    ).aggregate(total=Sum("credits_used"))

    return int(result.get("total") or 0)


def get_max_ai_credits(user):
    return int(getattr(settings, "AI_DEFAULT_MONTHLY_CREDITS", 500))


def check_ai_credits(user, required_credits):
    used = get_monthly_ai_credits_used(user)
    max_credits = get_max_ai_credits(user)
    remaining = max(max_credits - used, 0)

    if required_credits > remaining:
        return {
            "allowed": False,
            "used": used,
            "limit": max_credits,
            "remaining": remaining,
            "message": "AI credit limit reached.",
        }

    return {
        "allowed": True,
        "used": used,
        "limit": max_credits,
        "remaining": remaining,
        "message": "Allowed.",
    }


def normalize_ai_priority(value):
    value = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    allowed = [
        AILeadInsight.PRIORITY_VERY_HIGH,
        AILeadInsight.PRIORITY_HIGH,
        AILeadInsight.PRIORITY_MEDIUM,
        AILeadInsight.PRIORITY_LOW,
        AILeadInsight.PRIORITY_SKIP,
    ]

    if value in allowed:
        return value

    if value in ["veryhigh", "very_high_priority"]:
        return AILeadInsight.PRIORITY_VERY_HIGH

    return AILeadInsight.PRIORITY_MEDIUM


def clean_ai_text(value):
    """
    Clean AI text for frontend/export.

    Removes:
    - \n and \n\n line breaks
    - extra spaces
    - markdown bullets if simple
    - surrounding quotes
    """

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\\n", " ")
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")
    value = value.replace("\t", " ")

    value = re.sub(r"\s+", " ", value)

    value = value.strip()

    value = value.strip('"').strip("'").strip()

    return value


def clean_ai_data(data):
    cleaned = {}

    for field in REQUIRED_AI_FIELDS:
        cleaned[field] = clean_ai_text(data.get(field) or "")

    cleaned["ai_priority"] = normalize_ai_priority(cleaned.get("ai_priority"))

    return cleaned


def create_usage_log(user, lead, job=None, request_type="lead_insight", credits_used=0):
    return AIUsageLog.objects.create(
        user=user,
        lead=lead,
        job=job,
        request_type=request_type,
        credits_used=credits_used,
        provider="gemini",
        model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
    )


def get_existing_ai_insight(lead):
    try:
        return lead.ai_insight
    except Exception:
        return None


def should_skip_existing_insight(existing, force=False, options=None):
    """
    Skip only when force=False and the existing insight was generated
    with the same important campaign settings.

    If user changes target_offer/campaign_goal/tone/channel, generate again.
    """

    if not existing or not existing.generated_at:
        return False

    if force:
        return False

    options = normalize_ai_goal_options(options)

    same_settings = (
        (existing.target_offer or "") == options["target_offer"]
        and (existing.campaign_goal or "") == options["campaign_goal"]
        and (existing.tone or "") == options["tone"]
        and (existing.target_audience or "") == options["target_audience"]
        and (existing.outreach_channel or "") == options["outreach_channel"]
        and (existing.custom_instructions or "") == options["custom_instructions"]
    )

    return same_settings


def generate_ai_lead_insight(lead, user=None, job=None, force=False, options=None):
    """
    Generate AI insight for one lead using Gemini.

    Supports:
    - Auto offer mode
    - Custom target_offer mode
    - Custom campaign_goal
    - Custom tone
    - Custom outreach_channel
    """

    user = user or lead.search.user
    options = normalize_ai_goal_options(options)

    if not getattr(settings, "AI_ENABLED", True):
        raise ValueError("AI is currently disabled.")

    existing = get_existing_ai_insight(lead)

    if should_skip_existing_insight(existing, force=force, options=options):
        return {
            "created": False,
            "skipped": True,
            "insight": existing,
            "credits_used": 0,
        }

    credit_cost = get_credit_cost(AIJob.JOB_TYPE_FULL_PERSONALIZATION)
    credit_check = check_ai_credits(user, credit_cost)

    if not credit_check["allowed"]:
        raise ValueError(credit_check["message"])

    prompt = build_ai_lead_insight_prompt(lead, options=options)

    try:
        client = GeminiClient()
        result = client.generate_json(prompt)

        cleaned = clean_ai_data(result)

        insight, created = AILeadInsight.objects.update_or_create(
            lead=lead,
            defaults={
                "user": user,
                "target_offer": options["target_offer"],
                "campaign_goal": options["campaign_goal"],
                "tone": options["tone"],
                "target_audience": options["target_audience"],
                "outreach_channel": options["outreach_channel"],
                "custom_instructions": options["custom_instructions"],
                **cleaned,
                "provider": "gemini",
                "model_name": getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                "raw_response": result,
                "generated_at": timezone.now(),
            },
        )

        create_usage_log(
            user=user,
            lead=lead,
            job=job,
            request_type=AIJob.JOB_TYPE_FULL_PERSONALIZATION,
            credits_used=credit_cost,
        )

        return {
            "created": created,
            "skipped": False,
            "insight": insight,
            "credits_used": credit_cost,
        }

    except Exception as exc:
        log_exception_event(
            exc,
            source=SystemEvent.SOURCE_SYSTEM,
            title="AI lead insight generation failed",
            user=user,
            object_type="lead",
            object_id=lead.id,
            metadata={
                "lead_id": lead.id,
                "job_id": job.id if job else None,
                "provider": "gemini",
                "target_offer": options["target_offer"],
                "campaign_goal": options["campaign_goal"],
                "outreach_channel": options["outreach_channel"],
            },
        )

        raise


def get_user_ai_usage_summary(user):
    used = get_monthly_ai_credits_used(user)
    limit = get_max_ai_credits(user)

    return {
        "used_this_month": used,
        "monthly_limit": limit,
        "remaining_this_month": max(limit - used, 0),
        "ai_enabled": getattr(settings, "AI_ENABLED", True),
        "model": getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
    }


def extract_ai_options_from_dict(data):
    data = data or {}

    return normalize_ai_goal_options(
        {
            "target_offer": data.get("target_offer"),
            "campaign_goal": data.get("campaign_goal"),
            "tone": data.get("tone"),
            "target_audience": data.get("target_audience"),
            "outreach_channel": data.get("outreach_channel"),
            "custom_instructions": data.get("custom_instructions"),
        }
    )


def get_ai_options_from_job(job):
    return normalize_ai_goal_options(
        {
            "target_offer": job.target_offer,
            "campaign_goal": job.campaign_goal,
            "tone": job.tone,
            "target_audience": job.target_audience,
            "outreach_channel": job.outreach_channel,
            "custom_instructions": job.custom_instructions,
        }
    )