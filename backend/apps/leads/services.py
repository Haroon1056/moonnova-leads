from urllib.parse import urlparse

from django.db import IntegrityError, transaction

from apps.usage.services import (
    check_can_save_lead,
    record_lead_saved,
)

from .models import Lead


SOCIAL_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
]

FREE_BUILDER_DOMAINS = [
    "wixsite.com",
    "weebly.com",
    "wordpress.com",
    "blogspot.com",
    "godaddysites.com",
    "sites.google.com",
]


def clean_value(value):
    if value == "":
        return None

    if isinstance(value, str):
        value = value.strip()
        return value if value else None

    return value


def normalize_source_data(data):
    if not data:
        return {}

    normalized = dict(data)

    review_value = (
        normalized.get("review_count")
        or normalized.get("reviews_count")
        or normalized.get("reviews")
        or normalized.get("total_reviews")
        or normalized.get("reviews_total")
        or normalized.get("rating_count")
    )

    if review_value not in [None, ""]:
        normalized["review_count"] = review_value
        normalized["rating_count"] = review_value

    normalized.pop("reviews", None)
    normalized.pop("reviews_count", None)
    normalized.pop("total_reviews", None)
    normalized.pop("reviews_total", None)

    return normalized


def get_allowed_lead_fields():
    return {
        field.name
        for field in Lead._meta.get_fields()
        if hasattr(field, "attname") and not field.many_to_many
    }


def filter_lead_model_fields(data):
    allowed_fields = get_allowed_lead_fields()

    return {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }


def get_domain(website):
    if not website:
        return None

    try:
        parsed = urlparse(website)

        domain = parsed.netloc or parsed.path
        domain = domain.lower().replace("www.", "").strip("/")

        if ":" in domain:
            domain = domain.split(":")[0]

        return domain or None

    except Exception:
        return None


def is_social_website(website):
    domain = get_domain(website)

    if not domain:
        return False

    return any(social in domain for social in SOCIAL_DOMAINS)


def is_free_builder_website(website):
    domain = get_domain(website)

    if not domain:
        return False

    return any(builder in domain for builder in FREE_BUILDER_DOMAINS)


def detect_website_status(data):
    website = clean_value(data.get("website"))

    if not website:
        return {
            "has_website": False,
            "website_status": Lead.WEBSITE_STATUS_NO_WEBSITE,
            "domain": None,
            "is_social_only": False,
            "is_free_builder": False,
            "is_broken_website": False,
        }

    domain = get_domain(website)
    social_only = is_social_website(website)
    free_builder = is_free_builder_website(website)

    if social_only:
        website_status = Lead.WEBSITE_STATUS_SOCIAL_ONLY
    elif free_builder:
        website_status = Lead.WEBSITE_STATUS_FREE_BUILDER
    else:
        website_status = Lead.WEBSITE_STATUS_UNKNOWN

    return {
        "has_website": True,
        "website_status": website_status,
        "domain": domain,
        "is_social_only": social_only,
        "is_free_builder": free_builder,
        "is_broken_website": False,
    }


def build_opportunity_reason(data, score):
    reasons = []

    if not data.get("has_website"):
        reasons.append("Business has no website")

    if data.get("website_status") == Lead.WEBSITE_STATUS_404:
        reasons.append("Website returns 404 error")

    if data.get("website_status") == Lead.WEBSITE_STATUS_EXPIRED:
        reasons.append("Domain appears expired or unavailable")

    if data.get("website_status") == Lead.WEBSITE_STATUS_TIMEOUT:
        reasons.append("Website is timing out")

    if data.get("website_status") == Lead.WEBSITE_STATUS_SSL_ERROR:
        reasons.append("Website has SSL issue")

    if data.get("website_status") == Lead.WEBSITE_STATUS_CONNECTION_ERROR:
        reasons.append("Website connection failed")

    if data.get("website_status") == Lead.WEBSITE_STATUS_UNDER_CONSTRUCTION:
        reasons.append("Website appears under construction")

    if data.get("is_social_only"):
        reasons.append("Business uses social profile instead of a proper website")

    if data.get("is_free_builder"):
        reasons.append("Business uses a free website builder")

    if data.get("is_broken_website"):
        reasons.append("Website appears broken")

    rating = data.get("rating")
    review_count = data.get("review_count") or data.get("rating_count")

    try:
        rating = float(rating) if rating not in [None, ""] else None
    except Exception:
        rating = None

    try:
        review_count = int(review_count) if review_count not in [None, ""] else None
    except Exception:
        review_count = None

    if rating and rating >= 4.3:
        reasons.append("Good rating")

    if review_count and review_count >= 20:
        reasons.append("Good review count")

    if data.get("phone"):
        reasons.append("Phone number available")

    if data.get("email_1"):
        reasons.append("Email available")

    if data.get("website_platform"):
        reasons.append(f"Website platform detected: {data.get('website_platform')}")

    if data.get("email_confidence"):
        reasons.append(f"Email confidence: {data.get('email_confidence')}%")

    if not reasons:
        reasons.append("Basic lead collected from Google Maps")

    return f"Opportunity Score {score}/100: " + ", ".join(reasons)


def calculate_lead_score(data):
    score = 0

    website_status = data.get("website_status")

    if not data.get("has_website"):
        score += 35

    if website_status in [
        Lead.WEBSITE_STATUS_404,
        Lead.WEBSITE_STATUS_EXPIRED,
        Lead.WEBSITE_STATUS_TIMEOUT,
        Lead.WEBSITE_STATUS_SSL_ERROR,
        Lead.WEBSITE_STATUS_CONNECTION_ERROR,
        Lead.WEBSITE_STATUS_REDIRECT_ERROR,
        Lead.WEBSITE_STATUS_BROKEN,
    ]:
        score += 35

    if website_status == Lead.WEBSITE_STATUS_UNDER_CONSTRUCTION:
        score += 25

    if data.get("is_broken_website"):
        score += 30

    if data.get("is_social_only"):
        score += 25

    if data.get("is_free_builder"):
        score += 20

    try:
        rating = float(data.get("rating")) if data.get("rating") not in [None, ""] else None
    except Exception:
        rating = None

    try:
        review_count = int(data.get("review_count") or data.get("rating_count") or 0)
    except Exception:
        review_count = 0

    if rating and rating >= 4.5:
        score += 15
    elif rating and rating >= 4.0:
        score += 10

    if review_count >= 50:
        score += 15
    elif review_count >= 20:
        score += 10
    elif review_count >= 5:
        score += 5

    if data.get("phone"):
        score += 10

    if data.get("email_1"):
        score += 10

    if int(data.get("email_confidence") or 0) >= 80:
        score += 5

    return min(score, 100)


def classify_lead(data):
    score = data.get("lead_score") or calculate_lead_score(data)

    if score >= 70:
        return Lead.STATUS_HOT

    if score >= 40:
        return Lead.STATUS_WARM

    return Lead.STATUS_COLD


def build_tags(data):
    tags = []

    website_status = data.get("website_status")

    if not data.get("has_website"):
        tags.append("No Website")

    if data.get("is_broken_website"):
        tags.append("Broken Website")

    if website_status == Lead.WEBSITE_STATUS_404:
        tags.append("404 Website")

    if website_status == Lead.WEBSITE_STATUS_EXPIRED:
        tags.append("Expired Domain")

    if website_status == Lead.WEBSITE_STATUS_TIMEOUT:
        tags.append("Timeout Website")

    if website_status == Lead.WEBSITE_STATUS_SSL_ERROR:
        tags.append("SSL Issue")

    if website_status == Lead.WEBSITE_STATUS_UNDER_CONSTRUCTION:
        tags.append("Under Construction")

    if data.get("is_social_only"):
        tags.append("Social Only")

    if data.get("is_free_builder"):
        tags.append("Free Builder")

    if data.get("email_1"):
        tags.append("Email Found")

    if int(data.get("email_confidence") or 0) >= 80:
        tags.append("High Confidence Email")

    if data.get("website_platform"):
        tags.append(data.get("website_platform"))

    try:
        rating = float(data.get("rating")) if data.get("rating") not in [None, ""] else None
    except Exception:
        rating = None

    if rating and rating >= 4.5:
        tags.append("High Rating")

    final_tags = []

    for tag in tags:
        if tag and tag not in final_tags:
            final_tags.append(tag)

    return final_tags


def prepare_lead_data(data, status):
    prepared = normalize_source_data(data)
    prepared["status"] = status

    website_info = detect_website_status(prepared)
    prepared.update(website_info)

    lead_score = calculate_lead_score(prepared)

    prepared["lead_score"] = lead_score
    prepared["opportunity_score"] = lead_score
    prepared["opportunity_reason"] = build_opportunity_reason(prepared, lead_score)

    if not prepared.get("tags"):
        prepared["tags"] = build_tags(prepared)

    for key, value in list(prepared.items()):
        prepared[key] = clean_value(value)

    prepared = filter_lead_model_fields(prepared)

    return prepared


def recalculate_lead_quality(lead):
    data = {
        "has_website": lead.has_website,
        "website_status": lead.website_status,
        "is_social_only": lead.is_social_only,
        "is_free_builder": lead.is_free_builder,
        "is_broken_website": lead.is_broken_website,
        "website_platform": lead.website_platform,
        "rating": lead.rating,
        "review_count": lead.review_count,
        "rating_count": lead.rating_count,
        "phone": lead.phone,
        "email_1": lead.email_1,
        "email_confidence": lead.email_confidence,
    }

    score = calculate_lead_score(data)

    lead.lead_score = score
    lead.opportunity_score = score
    lead.status = classify_lead({"lead_score": score})
    lead.opportunity_reason = build_opportunity_reason(data, score)
    lead.tags = build_tags(data)

    lead.save(
        update_fields=[
            "lead_score",
            "opportunity_score",
            "status",
            "opportunity_reason",
            "tags",
            "updated_at",
        ]
    )

    return lead


def apply_website_enrichment_to_lead(lead, result):
    if not result:
        return lead

    update_fields = []

    field_map = [
        "domain",
        "has_website",
        "website_status",
        "website_http_status",
        "website_error",
        "website_platform",
        "is_social_only",
        "is_free_builder",
        "is_broken_website",
        "facebook_url",
        "instagram_url",
        "linkedin_url",
        "youtube_url",
        "tiktok_url",
    ]

    if result.get("final_url"):
        lead.website = result.get("final_url")
        update_fields.append("website")

    for field in field_map:
        if field in result:
            setattr(lead, field, result.get(field))
            update_fields.append(field)

    emails = result.get("emails") or []

    if emails:
        if not lead.email_1 and len(emails) > 0:
            lead.email_1 = emails[0]
            update_fields.append("email_1")

        if not lead.email_2 and len(emails) > 1:
            lead.email_2 = emails[1]
            update_fields.append("email_2")

        if not lead.email_3 and len(emails) > 2:
            lead.email_3 = emails[2]
            update_fields.append("email_3")

    lead.email_source_pages = (
        result.get("email_source_pages")
        or result.get("source_pages")
        or []
    )
    lead.email_confidence = int(
        result.get("email_confidence")
        or result.get("confidence")
        or 0
    )

    lead.enrichment_status = Lead.ENRICHMENT_STATUS_COMPLETED
    lead.enrichment_error = None

    update_fields.extend(
        [
            "email_source_pages",
            "email_confidence",
            "enrichment_status",
            "enrichment_error",
        ]
    )

    if update_fields:
        lead.save(update_fields=list(set(update_fields + ["updated_at"])))

    return recalculate_lead_quality(lead)


def build_lookup(search, data):
    name = clean_value(data.get("name"))
    phone = clean_value(data.get("phone"))
    website = clean_value(data.get("website"))
    address = clean_value(data.get("address"))
    place_id = clean_value(data.get("place_id"))

    if place_id:
        return {
            "search": search,
            "place_id": place_id,
        }

    if not name:
        return None

    if phone and website:
        return {
            "search": search,
            "name": name,
            "phone": phone,
            "website": website,
        }

    if website:
        return {
            "search": search,
            "name": name,
            "website": website,
        }

    if phone:
        return {
            "search": search,
            "name": name,
            "phone": phone,
        }

    if address:
        return {
            "search": search,
            "name": name,
            "address": address,
        }

    return {
        "search": search,
        "name": name,
    }


def find_existing_lead(search, data):
    name = clean_value(data.get("name"))
    phone = clean_value(data.get("phone"))
    website = clean_value(data.get("website"))
    address = clean_value(data.get("address"))
    place_id = clean_value(data.get("place_id"))

    if place_id:
        lead = Lead.objects.filter(search=search, place_id=place_id).first()
        if lead:
            return lead

    if not name:
        return None

    base_query = Lead.objects.filter(search=search, name=name)

    if phone and website:
        lead = base_query.filter(phone=phone, website=website).first()
        if lead:
            return lead

    if website:
        lead = base_query.filter(website=website).first()
        if lead:
            return lead

    if phone:
        lead = base_query.filter(phone=phone).first()
        if lead:
            return lead

    if address:
        lead = base_query.filter(address=address).first()
        if lead:
            return lead

    return None


def update_missing_fields(lead, data):
    data = normalize_source_data(data)
    data = filter_lead_model_fields(data)

    update_fields = []

    allowed_fields = [
        "keyword",
        "location",
        "category",
        "website",
        "domain",
        "has_website",
        "website_status",
        "website_http_status",
        "website_error",
        "website_platform",
        "is_social_only",
        "is_free_builder",
        "is_broken_website",
        "phone",
        "email_1",
        "email_2",
        "email_3",
        "email_source_pages",
        "email_confidence",
        "facebook_url",
        "instagram_url",
        "linkedin_url",
        "youtube_url",
        "tiktok_url",
        "address",
        "city",
        "state",
        "pincode",
        "country",
        "latitude",
        "longitude",
        "rating",
        "rating_count",
        "review_count",
        "map_link",
        "place_id",
        "status",
        "lead_score",
        "opportunity_score",
        "opportunity_reason",
        "tags",
        "source_query",
        "source_keyword",
        "source_location",
        "enrichment_status",
        "enrichment_attempts",
        "enrichment_error",
        "enrichment_last_run_at",
        "raw_data",
    ]

    for field in allowed_fields:
        if field not in data:
            continue

        new_value = clean_value(data.get(field))

        if new_value in [None, ""]:
            continue

        current_value = getattr(lead, field, None)

        if current_value in [None, "", [], {}]:
            setattr(lead, field, new_value)
            update_fields.append(field)

        elif field in [
            "lead_score",
            "opportunity_score",
            "opportunity_reason",
            "status",
            "tags",
            "website_status",
            "has_website",
            "is_social_only",
            "is_free_builder",
            "is_broken_website",
            "email_source_pages",
            "email_confidence",
            "enrichment_status",
        ]:
            setattr(lead, field, new_value)
            update_fields.append(field)

    if update_fields:
        lead.save(update_fields=list(set(update_fields)))

    return lead


def save_lead(search, data):
    if not data:
        return None

    data = dict(data)

    data.pop("reviews", None)
    data.pop("reviews_count", None)
    data.pop("total_reviews", None)
    data.pop("reviews_total", None)

    data = normalize_source_data(data)

    name = clean_value(data.get("name"))

    if not name:
        return None

    data["source_keyword"] = data.get("keyword")
    data["source_location"] = data.get("location")

    if data.get("keyword") and data.get("location"):
        data["source_query"] = f"{data.get('keyword')} in {data.get('location')}"

    prepared_data = prepare_lead_data(data, status=Lead.STATUS_COLD)
    prepared_data["status"] = classify_lead(prepared_data)

    existing_lead = find_existing_lead(search, prepared_data)

    if existing_lead:
        return update_missing_fields(existing_lead, prepared_data)

    limit_check = check_can_save_lead(search.user)

    if not limit_check.allowed:
        return None

    lookup = build_lookup(search, prepared_data)

    if not lookup:
        return None

    defaults = {
        **prepared_data,
    }

    for key in lookup.keys():
        defaults.pop(key, None)

    defaults = filter_lead_model_fields(defaults)

    try:
        with transaction.atomic():
            lead, created = Lead.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )

            if created:
                record_lead_saved(search.user)
                return lead

            lead = update_missing_fields(lead, prepared_data)
            return lead

    except IntegrityError:
        existing_lead = find_existing_lead(search, prepared_data)

        if existing_lead:
            return update_missing_fields(existing_lead, prepared_data)

        return None