import json


def build_lead_context(lead):
    return {
        "business_name": lead.name,
        "category": lead.category,
        "keyword": lead.keyword,
        "location": lead.location,
        "phone_available": bool(lead.phone),
        "email_available": bool(lead.email_1 or lead.email_2 or lead.email_3),
        "website": lead.website,
        "domain": lead.domain,
        "website_status": lead.website_status,
        "website_http_status": lead.website_http_status,
        "website_platform": lead.website_platform,
        "website_error": lead.website_error,
        "is_broken_website": lead.is_broken_website,
        "is_social_only": lead.is_social_only,
        "is_free_builder": lead.is_free_builder,
        "rating": lead.rating,
        "review_count": lead.review_count,
        "lead_score": lead.lead_score,
        "opportunity_score": lead.opportunity_score,
        "opportunity_reason": lead.opportunity_reason,
        "address": lead.address,
        "city": lead.city,
        "state": lead.state,
        "country": lead.country,
    }


def normalize_ai_goal_options(options=None):
    options = options or {}

    return {
        "target_offer": (options.get("target_offer") or "").strip(),
        "campaign_goal": (options.get("campaign_goal") or "").strip(),
        "tone": (
            options.get("tone")
            or "friendly, simple, natural, practical, not too salesy"
        ).strip(),
        "target_audience": (
            options.get("target_audience")
            or "local business owner"
        ).strip(),
        "outreach_channel": (
            options.get("outreach_channel")
            or "email"
        ).strip(),
        "custom_instructions": (
            options.get("custom_instructions")
            or ""
        ).strip(),
    }


def build_ai_goal_instruction(options=None):
    options = normalize_ai_goal_options(options)

    if options["target_offer"]:
        offer_mode = f"""
CUSTOM OFFER MODE:
The user wants to pitch this specific offer:
"{options["target_offer"]}"

Use this as the main offer. Do not choose a different main offer unless the lead is clearly not relevant.
All outreach fields must align with this target offer.
"""
    else:
        offer_mode = """
AUTO OFFER MODE:
The user did not provide a target offer.
Choose the most practical offer based on the lead data.

Examples:
- If website is missing, broken, slow, protected, or weak: pitch website improvement, website rebuild, or lead-generation website.
- If website exists but local SEO opportunity is visible: pitch local SEO/GMB improvement.
- If email/website data is weak: pitch data cleanup or online presence improvement.
"""

    campaign_goal = (
        options["campaign_goal"]
        or "Create useful outreach-ready insights and messages for this business lead."
    )

    return f"""
{offer_mode}

User campaign settings:
- Campaign goal: {campaign_goal}
- Tone: {options["tone"]}
- Target audience: {options["target_audience"]}
- Preferred outreach channel: {options["outreach_channel"]}
- Extra instructions: {options["custom_instructions"] or "None"}

Important campaign rules:
- If the user selected a target_offer, keep ai_suggested_offer aligned with that offer.
- If the user selected an outreach_channel, write the strongest message for that channel and still provide the other message fields.
- If custom_instructions conflict with generic sales copy, follow custom_instructions.
"""


def build_ai_lead_insight_prompt(lead, options=None):
    context = build_lead_context(lead)
    goal_instruction = build_ai_goal_instruction(options)

    return f"""
You are an expert B2B lead generation, local SEO, website audit, and outreach assistant.

Your task:
Analyze the business lead and create a complete outreach-ready AI profile.

Business lead data:
{json.dumps(context, indent=2, default=str)}

{goal_instruction}

Strict output rules:
- Return JSON only.
- No markdown.
- No explanation outside JSON.
- Do not wrap JSON in code fences.
- Do not use line breaks inside JSON string values.
- Do not use \\n inside values.
- Every key must be present.
- Do not leave important message fields empty.
- Use simple, natural, human wording.
- Do not sound like AI.
- Do not overpromise.
- Do not make guaranteed claims.
- Do not invent facts not present in the lead data.
- If data is limited, write a reasonable practical message based on category, location, website status, and offer.
- Email body should be 70 to 120 words.
- Follow-ups should be short and polite.
- Facebook, LinkedIn, and WhatsApp messages should be 1 to 3 short sentences.

Return this exact JSON structure with these exact keys:

{{
  "ai_priority": "very_high | high | medium | low | skip",
  "ai_summary": "Short useful summary of this lead.",
  "ai_suggested_offer": "The main offer to pitch. If target_offer is provided, align with it.",
  "ai_offer_reason": "Why this offer fits this lead.",
  "ai_best_channel": "Email | Phone | Facebook | WhatsApp | LinkedIn | Website Contact Form | Skip",
  "ai_channel_reason": "Why this channel is best.",
  "ai_first_line": "One personalized first line for cold outreach.",
  "ai_email_subject": "Short subject line.",
  "ai_email_body": "Short friendly cold email between 70 and 120 words.",
  "ai_followup_1": "Short follow-up message.",
  "ai_followup_2": "Second short follow-up message.",
  "ai_followup_3": "Final polite follow-up message.",
  "ai_facebook_message": "Short Facebook DM style message.",
  "ai_linkedin_message": "Short LinkedIn DM style message.",
  "ai_whatsapp_message": "Short WhatsApp style message.",
  "ai_website_weakness": "Simple website weakness or online presence issue.",
  "ai_local_seo_opportunity": "Simple local SEO or online visibility opportunity.",
  "ai_score_explanation": "Explain why this lead is high, medium, low, or skip priority for the selected offer."
}}
"""