import time
import random
import re


class ScraperCancelled(Exception):
    """
    Raised when user cancels/stops a running search permanently.
    Do not retry this exception.
    """
    pass


class ScraperPaused(Exception):
    """
    Raised when user pauses a running search.
    Do not retry this exception.
    Resume API will continue remaining work later.
    """
    pass


def clean_text(value):
    """
    Clean common Google Maps icon/private unicode text.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    bad_values = [
        "îƒˆ",
        "îƒ‰",
        "îƒŠ",
        "îƒ‹",
        "îƒŒ",
        "îƒŽ",
        "îƒ‘",
        "îƒ’",
        "îƒ“",
        "îƒ•",
        "îƒ–",
        "îƒ˜",
        "îƒ™",
        "îƒš",
        "îƒœ",
        "îƒž",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "\ue0c8",
        "\uf3c5",
        "\uf041",
    ]

    for bad in bad_values:
        value = value.replace(bad, " ")

    # Remove private-use unicode icons and control characters
    value = re.sub(r"[\ue000-\uf8ff]", " ", value)
    value = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", value)

    value = value.replace("\r", " ").replace("\n", " ")
    value = re.sub(r"\s+", " ", value)

    value = value.strip()

    return value if value else None


def clean_phone(phone):
    """
    Basic phone cleaner.

    Keeps readable phone format:
    +61 8 8166 5000
    +1 (512) 555-1234
    """

    phone = clean_text(phone)

    if not phone:
        return None

    phone = (
        phone.replace("Phone:", "")
        .replace("Phone number:", "")
        .replace("Call", "")
        .replace("Copy phone number", "")
        .strip()
    )

    # Keep digits, +, spaces, brackets, dots and dashes
    phone = re.sub(r"[^\d+\-\s().]", "", phone)
    phone = re.sub(r"\s+", " ", phone).strip()

    digits = re.sub(r"\D", "", phone)

    if len(digits) < 7:
        return None

    return phone


def clean_url(url):
    """
    Clean website/map URL.
    """

    url = clean_text(url)

    if not url:
        return None

    unwanted = [
        "website",
        "directions",
        "call",
        "save",
        "share",
        "copy address",
        "copy phone number",
    ]

    if url.lower() in unwanted:
        return None

    if url.startswith("http://") or url.startswith("https://"):
        return url

    if "." in url and " " not in url:
        return "https://" + url

    return None


def is_valid_lead(data):
    """
    Basic lead validation.
    """

    if not data:
        return False

    name = data.get("name")

    if not name:
        return False

    bad_names = [
        "results",
        "google maps",
        "maps",
        "directions",
        "website",
        "call",
        "save",
        "share",
        "menu",
    ]

    if str(name).lower().strip() in bad_names:
        return False

    return bool(
        data.get("phone")
        or data.get("website")
        or data.get("address")
        or data.get("map_link")
    )


def retry(operation, retries=3, delay=2, retry_exceptions=(Exception,)):
    """
    Generic retry wrapper for unstable scraping operations.

    Important:
    - Does not retry ScraperCancelled
    - Does not retry ScraperPaused
    - Returns None after all retries fail
    """

    for attempt in range(retries):
        try:
            return operation()

        except (ScraperCancelled, ScraperPaused):
            raise

        except retry_exceptions as e:
            print(f"[RETRY] Attempt {attempt + 1} failed: {e}")

            if attempt < retries - 1:
                time.sleep(delay + random.uniform(0, 2))

    return None