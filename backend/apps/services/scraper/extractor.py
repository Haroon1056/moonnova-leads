import re

from .anti_block import human_delay


def safe_inner_text(page, selectors):
    """
    Try multiple selectors and return first available inner text.
    """

    for selector in selectors:
        try:
            element = page.query_selector(selector)

            if element:
                text = element.inner_text()

                if text:
                    return text.strip()

        except Exception:
            continue

    return None


def safe_attribute(page, selectors, attribute):
    """
    Try multiple selectors and return first available attribute value.
    """

    for selector in selectors:
        try:
            element = page.query_selector(selector)

            if element:
                value = element.get_attribute(attribute)

                if value:
                    return value.strip()

        except Exception:
            continue

    return None


def safe_all_inner_texts(page, selectors):
    """
    Get combined text from all matching elements.
    Useful because Google Maps often splits rating and reviews into many spans.
    """

    values = []

    for selector in selectors:
        try:
            elements = page.query_selector_all(selector)

            for element in elements:
                text = element.inner_text()

                if text:
                    text = text.strip()

                    if text:
                        values.append(text)

        except Exception:
            continue

    final_text = " ".join(values).strip()

    return final_text if final_text else None


def safe_all_attributes(page, selectors, attribute):
    """
    Get combined attribute values from all matching elements.
    Useful for aria-label values like:
    '4.8 stars 115 reviews'
    """

    values = []

    for selector in selectors:
        try:
            elements = page.query_selector_all(selector)

            for element in elements:
                value = element.get_attribute(attribute)

                if value:
                    value = value.strip()

                    if value:
                        values.append(value)

        except Exception:
            continue

    final_value = " ".join(values).strip()

    return final_value if final_value else None


def clean_text(value):
    """
    Clean Google Maps bad icon/private unicode text.
    """

    if not value:
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
    value = re.sub(r"\s+", " ", value).strip()

    return value if value else None


def clean_google_button_text(value):
    """
    Google Maps buttons sometimes return labels like:
    Website
    Directions
    Call
    Copy address

    This removes useless button text.
    """

    value = clean_text(value)

    if not value:
        return None

    unwanted = [
        "Website",
        "Directions",
        "Call",
        "Save",
        "Share",
        "Copy address",
        "Copy phone number",
        "Send to phone",
        "Send to your phone",
        "Open website",
        "Menu",
    ]

    if value.strip().lower() in [item.lower() for item in unwanted]:
        return None

    return value


def remove_label(value, labels):
    """
    Remove labels like:
    Phone:
    Address:
    Website:
    """

    value = clean_text(value)

    if not value:
        return None

    for label in labels:
        value = re.sub(
            rf"^\s*{re.escape(label)}\s*[:\-]?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

    value = re.sub(r"\s+", " ", value).strip()

    return value if value else None


def extract_rating(text):
    """
    Extract rating from Google Maps text.

    Examples:
    4.8
    4.8 stars
    Rated 4.8 stars
    """

    text = clean_text(text)

    if not text:
        return None

    try:
        match = re.search(r"\b([0-5](?:\.\d+)?)\b", text)

        if match:
            rating = float(match.group(1))

            if 0 <= rating <= 5:
                return rating

    except Exception:
        pass

    return None


def extract_review_count(text):
    """
    Extract review count from Google Maps text.

    Examples:
    115 reviews
    1,245 Google reviews
    (115)
    Rated 4.7 stars by 115 people
    115 ratings
    """

    text = clean_text(text)

    if not text:
        return None

    try:
        text = text.replace(",", "")

        # Strong patterns
        patterns = [
            r"(\d+)\s*(?:google\s+)?reviews?\b",
            r"(\d+)\s*ratings?\b",
            r"by\s+(\d+)\s+people",
            r"\((\d+)\)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                return int(match.group(1))

        # Avoid converting rating only like 4.8 into review count
        if re.fullmatch(r"[0-5](?:\.\d+)?", text.strip()):
            return None

        # Fallback only if words indicate reviews/ratings
        if re.search(r"reviews?|ratings?|people", text, flags=re.IGNORECASE):
            numbers = re.findall(r"\d+", text)

            if numbers:
                return int(numbers[-1])

    except Exception:
        pass

    return None


def extract_rating_and_reviews_from_f7nice(page):
    """
    Strong extractor from Google Maps .F7nice area.
    Usually contains rating and review count.
    """

    text = safe_all_inner_texts(page, [
        ".F7nice",
        ".F7nice span",
        ".F7nice button",
    ])

    if not text:
        return None, None

    rating = extract_rating(text)
    review_count = extract_review_count(text)

    return rating, review_count


def extract_rating_and_reviews_from_aria(page):
    """
    Strong aria-label fallback.

    Google often stores review count in aria-label like:
    '4.8 stars 115 reviews'
    '115 reviews'
    """

    text = safe_all_attributes(page, [
        'button[aria-label*="review"]',
        'button[aria-label*="Review"]',
        'span[aria-label*="review"]',
        'span[aria-label*="Review"]',
        'div[aria-label*="review"]',
        'div[aria-label*="Review"]',
        'button[aria-label*="rating"]',
        'button[aria-label*="Rating"]',
        'span[aria-label*="rating"]',
        'span[aria-label*="Rating"]',
        'div[aria-label*="rating"]',
        'div[aria-label*="Rating"]',
        'button[aria-label*="stars"]',
        'span[aria-label*="stars"]',
        'div[aria-label*="stars"]',
    ], "aria-label")

    if not text:
        return None, None

    rating = extract_rating(text)
    review_count = extract_review_count(text)

    return rating, review_count


def extract_rating_and_reviews_from_page_text(page):
    """
    Final fallback method.
    Reads main page text and tries to find rating/reviews.
    """

    try:
        main_text = safe_inner_text(page, [
            '[role="main"]',
            'div[role="main"]',
            'body',
        ])

        main_text = clean_text(main_text)

        if not main_text:
            return None, None

        rating = None
        review_count = None

        rating_match = re.search(
            r"\b([0-5](?:\.\d+)?)\s*(?:stars?|star)?\b",
            main_text,
            flags=re.IGNORECASE,
        )

        if rating_match:
            rating = extract_rating(rating_match.group(1))

        review_patterns = [
            r"([\d,]+)\s*(?:google\s+)?reviews?",
            r"([\d,]+)\s*ratings?",
            r"by\s+([\d,]+)\s+people",
            r"\(([\d,]+)\)",
        ]

        for pattern in review_patterns:
            match = re.search(pattern, main_text, flags=re.IGNORECASE)

            if match:
                try:
                    review_count = int(match.group(1).replace(",", ""))
                    break
                except Exception:
                    pass

        return rating, review_count

    except Exception:
        return None, None


def extract_business(page):
    """
    Extract business details from opened Google Maps result page.
    """

    human_delay(1, 2)

    # =========================
    # NAME
    # =========================
    name = safe_inner_text(page, [
        "h1.DUwDvf",
        "h1",
        '[role="main"] h1',
    ])

    name = clean_text(name)

    if name and name.lower().strip() in ["results", "google maps", "maps"]:
        name = None

    # =========================
    # CATEGORY
    # =========================
    category = safe_inner_text(page, [
        'button[jsaction*="category"]',
        'button[aria-label*="Category"]',
        'button[jsaction*="pane.rating.category"]',
        '.DkEaL',
    ])

    category = clean_google_button_text(category)

    # =========================
    # PHONE
    # =========================
    phone = safe_inner_text(page, [
        'button[data-item-id^="phone"]',
        '[data-item-id^="phone"]',
        '[aria-label^="Phone"]',
        'button[aria-label^="Phone"]',
        'button[data-tooltip*="phone"]',
        'button[data-tooltip*="Phone"]',
    ])

    if not phone:
        phone = safe_attribute(page, [
            'button[data-item-id^="phone"]',
            '[data-item-id^="phone"]',
            '[aria-label^="Phone"]',
            'button[aria-label^="Phone"]',
        ], "aria-label")

    phone = clean_google_button_text(phone)
    phone = remove_label(phone, [
        "Phone",
        "Phone number",
        "Call",
        "Copy phone number",
    ])

    # =========================
    # ADDRESS
    # =========================
    address = safe_inner_text(page, [
        'button[data-item-id="address"]',
        '[data-item-id="address"]',
        '[aria-label^="Address"]',
        'button[aria-label^="Address"]',
        'button[data-tooltip*="address"]',
        'button[data-tooltip*="Address"]',
    ])

    if not address:
        address = safe_attribute(page, [
            'button[data-item-id="address"]',
            '[data-item-id="address"]',
            '[aria-label^="Address"]',
            'button[aria-label^="Address"]',
        ], "aria-label")

    address = clean_google_button_text(address)
    address = remove_label(address, [
        "Address",
        "Copy address",
        "Directions",
    ])

    # =========================
    # WEBSITE
    # =========================
    website = safe_attribute(page, [
        'a[data-item-id="authority"]',
        'a[aria-label^="Website"]',
        'a[data-tooltip*="website"]',
        'a[data-tooltip*="Website"]',
    ], "href")

    if not website:
        website = safe_inner_text(page, [
            'a[data-item-id="authority"]',
            'a[aria-label^="Website"]',
            'a[data-tooltip*="website"]',
            'a[data-tooltip*="Website"]',
        ])

    website = clean_google_button_text(website)
    website = remove_label(website, [
        "Website",
        "Open website",
    ])

    # =========================
    # RATING + REVIEW COUNT
    # =========================
    rating = None
    review_count = None

    # 1. Strong .F7nice extraction
    f7_rating, f7_reviews = extract_rating_and_reviews_from_f7nice(page)

    if f7_rating is not None:
        rating = f7_rating

    if f7_reviews is not None:
        review_count = f7_reviews

    # 2. Direct rating selectors
    if rating is None:
        rating_text = safe_inner_text(page, [
            '.F7nice span[aria-hidden="true"]',
            '.F7nice span',
            'span[aria-hidden="true"]',
            'div.fontDisplayLarge',
        ])

        if not rating_text:
            rating_text = safe_attribute(page, [
                'div[aria-label*="stars"]',
                'span[aria-label*="stars"]',
                'button[aria-label*="stars"]',
            ], "aria-label")

        rating = extract_rating(rating_text)

    # 3. Direct review selectors
    if review_count is None:
        review_text = safe_inner_text(page, [
            'button[jsaction*="reviews"]',
            'button[aria-label*="reviews"]',
            'button[aria-label*="Reviews"]',
            'span[aria-label*="reviews"]',
            'span[aria-label*="Reviews"]',
            '.F7nice',
        ])

        if not review_text:
            review_text = safe_attribute(page, [
                'button[jsaction*="reviews"]',
                'button[aria-label*="reviews"]',
                'button[aria-label*="Reviews"]',
                'span[aria-label*="reviews"]',
                'span[aria-label*="Reviews"]',
                'div[aria-label*="reviews"]',
                'div[aria-label*="Reviews"]',
            ], "aria-label")

        review_count = extract_review_count(review_text)

    # 4. Aria-label fallback
    if rating is None or review_count is None:
        aria_rating, aria_reviews = extract_rating_and_reviews_from_aria(page)

        if rating is None and aria_rating is not None:
            rating = aria_rating

        if review_count is None and aria_reviews is not None:
            review_count = aria_reviews

    # 5. Full panel fallback
    if rating is None or review_count is None:
        fallback_rating, fallback_review_count = extract_rating_and_reviews_from_page_text(page)

        if rating is None:
            rating = fallback_rating

        if review_count is None:
            review_count = fallback_review_count

    # =========================
    # MAP LINK
    # =========================
    try:
        map_link = page.url
    except Exception:
        map_link = None

    return {
        "name": name,
        "category": category,
        "phone": phone,
        "address": address,
        "website": website,
        "rating": rating,
        "rating_count": review_count,
        "review_count": review_count,
        "map_link": map_link,
    }