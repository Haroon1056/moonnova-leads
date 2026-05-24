import re
import socket
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from .email_extractor import extract_emails_from_website

try:
    from .playwright_email_extractor import extract_emails_with_playwright
except Exception:
    extract_emails_with_playwright = None


SOCIAL_DOMAINS = {
    "facebook.com": "facebook_url",
    "instagram.com": "instagram_url",
    "linkedin.com": "linkedin_url",
    "youtube.com": "youtube_url",
    "tiktok.com": "tiktok_url",
    "twitter.com": "twitter_url",
    "x.com": "twitter_url",
}

FREE_BUILDER_DOMAINS = [
    "wixsite.com",
    "weebly.com",
    "wordpress.com",
    "blogspot.com",
    "godaddysites.com",
    "sites.google.com",
]

UNDER_CONSTRUCTION_PATTERNS = [
    "under construction",
    "coming soon",
    "site coming soon",
    "website coming soon",
    "this site is under construction",
    "temporarily unavailable",
    "maintenance mode",
    "launching soon",
]

PLATFORM_PATTERNS = {
    "WordPress": [
        "wp-content",
        "wp-includes",
        "wordpress",
        "/wp-json/",
    ],
    "Wix": [
        "wix.com",
        "wixstatic",
        "wixsite",
    ],
    "Shopify": [
        "cdn.shopify.com",
        "myshopify.com",
        "shopify",
    ],
    "Squarespace": [
        "squarespace",
        "static1.squarespace.com",
    ],
    "Webflow": [
        "webflow",
        "webflow.io",
    ],
    "Weebly": [
        "weebly",
        "weeblycloud",
    ],
    "GoDaddy Builder": [
        "godaddysites",
        "godaddy website builder",
    ],
    "Blogger": [
        "blogger",
        "blogspot",
    ],
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class WebsiteCheckResult:
    website: str | None = None
    final_url: str | None = None
    domain: str | None = None

    has_website: bool = False
    website_status: str = "unknown"
    website_http_status: int | None = None
    website_error: str | None = None
    website_platform: str | None = None

    is_social_only: bool = False
    is_free_builder: bool = False
    is_broken_website: bool = False

    facebook_url: str | None = None
    instagram_url: str | None = None
    linkedin_url: str | None = None
    youtube_url: str | None = None
    tiktok_url: str | None = None

    title: str | None = None
    meta_description: str | None = None

    contact_page_url: str | None = None

    emails: list | None = None
    email_source_pages: list | None = None
    email_confidence: int = 0


def normalize_url(website):
    if not website:
        return None

    website = str(website).strip()

    if not website:
        return None

    if website.startswith("mailto:"):
        return None

    if website.startswith("tel:"):
        return None

    if website.startswith("//"):
        website = "https:" + website

    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    return website


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


def is_social_domain(domain):
    if not domain:
        return False

    return any(social in domain for social in SOCIAL_DOMAINS.keys())


def is_free_builder_domain(domain):
    if not domain:
        return False

    return any(builder in domain for builder in FREE_BUILDER_DOMAINS)


def check_dns(domain):
    if not domain:
        return False

    try:
        socket.gethostbyname(domain)
        return True

    except Exception:
        return False


def detect_platform(html, final_url=None):
    text = f"{html or ''} {final_url or ''}".lower()

    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in text:
                return platform

    return None


def detect_under_construction(html):
    if not html:
        return False

    text = html.lower()

    return any(pattern in text for pattern in UNDER_CONSTRUCTION_PATTERNS)


def extract_title_and_description(html):
    title = None
    description = None

    if not html:
        return title, description

    try:
        soup = BeautifulSoup(html, "html.parser")

        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        meta = soup.find("meta", attrs={"name": "description"})

        if meta and meta.get("content"):
            description = meta.get("content").strip()

    except Exception:
        pass

    return title, description


def extract_social_links(html, base_url):
    results = {
        "facebook_url": None,
        "instagram_url": None,
        "linkedin_url": None,
        "youtube_url": None,
        "tiktok_url": None,
    }

    if not html:
        return results

    try:
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link.get("href")

            if not href:
                continue

            href = urljoin(base_url, href)
            href_lower = href.lower()

            for domain, field_name in SOCIAL_DOMAINS.items():
                if domain in href_lower and field_name in results:
                    if not results[field_name]:
                        results[field_name] = href

    except Exception:
        pass

    return results


def extract_emails_from_html(html):
    if not html:
        return []

    emails = set()

    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    for email in re.findall(email_pattern, html):
        email = email.strip().lower()

        if email.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")):
            continue

        if "example.com" in email:
            continue

        emails.add(email)

    return list(emails)[:3]


def find_contact_page(html, base_url):
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")

        preferred_words = [
            "contact",
            "contact us",
            "get in touch",
            "reach us",
        ]

        for link in soup.find_all("a", href=True):
            text = link.get_text(" ", strip=True).lower()
            href = link.get("href", "").lower()

            if any(word in text for word in preferred_words) or "contact" in href:
                return urljoin(base_url, link.get("href"))

    except Exception:
        pass

    return None


def classify_status_from_response(response, html, social_only, free_builder):
    status_code = response.status_code

    if social_only:
        return "social_only", False

    if free_builder:
        return "free_builder", False

    if status_code == 404:
        return "404", True

    if status_code in [401, 403]:
        return "protected", False

    if 200 <= status_code < 400:
        if detect_under_construction(html):
            return "under_construction", True

        return "working", False

    if 400 <= status_code < 500:
        return "broken", True

    if status_code >= 500:
        return "broken", True

    return "unknown", False


def run_email_extraction(final_url, status_value):
    emails = []
    email_source_pages = []
    email_confidence = 0

    try:
        email_result = extract_emails_from_website(final_url)

        emails = email_result.get("emails") or []
        email_source_pages = email_result.get("source_pages") or []
        email_confidence = int(email_result.get("confidence") or 0)

    except Exception:
        pass

    if not emails and status_value in ["protected", "working"]:
        if extract_emails_with_playwright:
            try:
                fallback_result = extract_emails_with_playwright(final_url)

                emails = fallback_result.get("emails") or []
                email_source_pages = fallback_result.get("source_pages") or []
                email_confidence = int(fallback_result.get("confidence") or 0)

            except Exception:
                pass

    return emails, email_source_pages, email_confidence


def check_website_status(website, timeout=12):
    normalized_url = normalize_url(website)

    if not normalized_url:
        return asdict(
            WebsiteCheckResult(
                website=website,
                has_website=False,
                website_status="no_website",
                is_broken_website=False,
                website_error="No website URL provided.",
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    domain = get_domain(normalized_url)

    if not domain or "." not in domain:
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="invalid_url",
                is_broken_website=True,
                website_error="Invalid website URL.",
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    social_only = is_social_domain(domain)
    free_builder = is_free_builder_domain(domain)

    if not check_dns(domain):
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="expired_domain",
                is_social_only=social_only,
                is_free_builder=free_builder,
                is_broken_website=True,
                website_error="DNS lookup failed. Domain may be expired or unavailable.",
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    try:
        response = requests.get(
            normalized_url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
            verify=True,
        )

    except requests.exceptions.SSLError as exc:
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="ssl_error",
                is_social_only=social_only,
                is_free_builder=free_builder,
                is_broken_website=True,
                website_error=str(exc)[:500],
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    except requests.exceptions.TooManyRedirects as exc:
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="redirect_error",
                is_social_only=social_only,
                is_free_builder=free_builder,
                is_broken_website=True,
                website_error=str(exc)[:500],
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    except requests.exceptions.Timeout as exc:
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="timeout",
                is_social_only=social_only,
                is_free_builder=free_builder,
                is_broken_website=True,
                website_error=str(exc)[:500],
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    except requests.exceptions.ConnectionError as exc:
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="connection_error",
                is_social_only=social_only,
                is_free_builder=free_builder,
                is_broken_website=True,
                website_error=str(exc)[:500],
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    except requests.exceptions.RequestException as exc:
        return asdict(
            WebsiteCheckResult(
                website=normalized_url,
                domain=domain,
                has_website=True,
                website_status="broken",
                is_social_only=social_only,
                is_free_builder=free_builder,
                is_broken_website=True,
                website_error=str(exc)[:500],
                emails=[],
                email_source_pages=[],
                email_confidence=0,
            )
        )

    final_url = response.url
    final_domain = get_domain(final_url) or domain
    html = response.text or ""

    status_value, is_broken = classify_status_from_response(
        response=response,
        html=html,
        social_only=social_only,
        free_builder=free_builder,
    )

    platform = detect_platform(html, final_url=final_url)
    title, description = extract_title_and_description(html)
    social_links = extract_social_links(html, final_url)
    contact_page_url = find_contact_page(html, final_url)

    basic_emails = extract_emails_from_html(html)

    emails, email_source_pages, email_confidence = run_email_extraction(
        final_url=final_url,
        status_value=status_value,
    )

    if not emails:
        emails = basic_emails

    result = WebsiteCheckResult(
        website=normalized_url,
        final_url=final_url,
        domain=final_domain,
        has_website=True,
        website_status=status_value,
        website_http_status=response.status_code,
        website_error=None,
        website_platform=platform,
        is_social_only=social_only,
        is_free_builder=free_builder,
        is_broken_website=is_broken,
        title=title,
        meta_description=description,
        contact_page_url=contact_page_url,
        emails=emails,
        email_source_pages=email_source_pages,
        email_confidence=email_confidence,
        **social_links,
    )

    return asdict(result)