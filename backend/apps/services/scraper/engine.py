from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus
import re
import unicodedata

from django.db import close_old_connections
from django.db.models import F

from apps.searches.models import Search, SearchQueryTask
from apps.leads.models import Lead
from apps.leads.services import save_lead
from apps.realtime.events import send_lead_found, send_search_progress

from apps.usage.services import (
    check_account_allowed,
    check_can_save_lead,
)

from .browser import BrowserManager
from .anti_block import human_delay
from .extractor import extract_business
from .parser import BusinessParser
from .utils import retry, ScraperCancelled, ScraperPaused
from .logger import log, error


# =====================================================
# SAFE DATABASE RUNNER
# =====================================================
def run_db_safe(func, *args, **kwargs):
    """
    Run Django ORM/database code safely in a separate thread.

    This helps avoid stale DB connections while Playwright/browser work
    is running for a long time.
    """

    def wrapper():
        close_old_connections()

        try:
            return func(*args, **kwargs)

        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(wrapper)
        return future.result()


# =====================================================
# TEXT CLEANING HELPERS
# =====================================================
def clean_text(value):
    """
    Clean Google Maps UI icons/private unicode characters.
    """

    if value is None:
        return None

    if not isinstance(value, str):
        return value

    text = value

    bad_tokens = [
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
    ]

    for token in bad_tokens:
        text = text.replace(token, " ")

    cleaned_chars = []

    for char in text:
        category = unicodedata.category(char)

        if category in {"Co", "Cs", "Cc"}:
            if char in {"\n", "\r", "\t"}:
                cleaned_chars.append(" ")
            continue

        cleaned_chars.append(char)

    text = "".join(cleaned_chars)

    text = re.sub(
        r"^\s*(address|phone|website|hours|directions)\s*[:\-]?\s*",
        "",
        text,
        flags=re.I,
    )

    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None


def clean_address(value):
    """
    Clean address before saving/exporting.
    """

    text = clean_text(value)

    if not text:
        return None

    text = re.sub(r"\s+", " ", text).strip(" ,")

    return text if text else None


def remove_invalid_lead_alias_fields(data):
    """
    Remove parser aliases that are not real Lead model fields.

    Lead model has:
    - review_count
    - rating_count

    It does not have:
    - reviews
    - reviews_count
    - total_reviews
    - reviews_total
    """

    if not data:
        return data

    data.pop("reviews", None)
    data.pop("reviews_count", None)
    data.pop("total_reviews", None)
    data.pop("reviews_total", None)

    return data


def extract_review_count_from_text(value):
    """
    Extract review count from Google Maps text.
    """

    if not value:
        return None

    text = clean_text(str(value))

    if not text:
        return None

    text = text.replace(",", "")

    patterns = [
        r"(\d+)\s+(?:google\s+)?reviews?\b",
        r"(\d+)\s+ratings?\b",
        r"by\s+(\d+)\s+people",
        r"\((\d+)\)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)

        if match:
            try:
                return int(match.group(1))
            except Exception:
                continue

    return None


def normalize_review_count(value):
    """
    Normalize review count safely.
    Avoid converting rating values like 4.8 into review count.
    """

    if value in [None, ""]:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    text = clean_text(str(value))

    if not text:
        return None

    text = text.replace(",", "")

    if re.fullmatch(r"[0-5](?:\.\d+)?", text.strip()):
        return None

    review_count = extract_review_count_from_text(text)

    if review_count is not None:
        return review_count

    try:
        return int(text)
    except Exception:
        return None


def normalize_lead_data(data, raw_data=None):
    """
    Clean all scraped string fields and improve review count before saving.
    """

    if not data:
        return data

    data = dict(data)

    for key, value in list(data.items()):
        if isinstance(value, str):
            data[key] = clean_text(value)

    if data.get("address"):
        data["address"] = clean_address(data.get("address"))

    review_keys = [
        "review_count",
        "reviews_count",
        "reviews",
        "total_reviews",
        "reviews_total",
        "rating_count",
    ]

    review_count = None

    for key in review_keys:
        if key in data and data.get(key) not in [None, ""]:
            review_count = normalize_review_count(data.get(key))

            if review_count is not None:
                break

    if review_count is None and raw_data:
        if isinstance(raw_data, dict):
            for value in raw_data.values():
                review_count = extract_review_count_from_text(value)

                if review_count is not None:
                    break

        elif isinstance(raw_data, str):
            review_count = extract_review_count_from_text(raw_data)

    if review_count is not None:
        data["review_count"] = review_count
        data["rating_count"] = review_count

    data = remove_invalid_lead_alias_fields(data)

    return data


# =====================================================
# DATABASE HELPERS
# =====================================================
def db_get_search_status(search_id):
    search = Search.objects.filter(id=search_id).only("status").first()

    if not search:
        return None

    return search.status


def db_mark_query_task_running(query_task_id):
    if not query_task_id:
        return

    SearchQueryTask.objects.filter(id=query_task_id).update(
        status=SearchQueryTask.STATUS_RUNNING
    )


def db_mark_query_task_completed(query_task_id):
    if not query_task_id:
        return

    SearchQueryTask.objects.filter(id=query_task_id).update(
        status=SearchQueryTask.STATUS_COMPLETED
    )


def db_mark_query_task_failed(query_task_id, message=None):
    if not query_task_id:
        return

    SearchQueryTask.objects.filter(id=query_task_id).update(
        status=SearchQueryTask.STATUS_FAILED,
        error_message=message,
    )


def db_update_query_task_progress(query_task_id, leads_found=None, processed_index=None):
    if not query_task_id:
        return

    update_data = {}

    if leads_found is not None:
        update_data["leads_found"] = leads_found

    if processed_index is not None:
        update_data["processed_index"] = processed_index

    if update_data:
        SearchQueryTask.objects.filter(id=query_task_id).update(**update_data)

    query_task = (
        SearchQueryTask.objects.filter(id=query_task_id)
        .select_related("search", "search__user")
        .first()
    )

    if query_task:
        send_search_progress(query_task.search.user_id, query_task.search, query_task)


def db_get_search_config(search_id):
    search = Search.objects.get(id=search_id)

    max_leads = getattr(search, "max_leads", 100)
    scrape_mode = getattr(search, "scrape_mode", "safe")
    email_enrichment = getattr(search, "email_enrichment", False)

    try:
        max_leads = int(max_leads)
    except Exception:
        max_leads = 100

    if max_leads <= 0:
        max_leads = 100

    if scrape_mode not in ["safe", "balanced", "deep"]:
        scrape_mode = "safe"

    return {
        "max_leads": max_leads,
        "scrape_mode": scrape_mode,
        "email_enrichment": bool(email_enrichment),
    }


def db_get_existing_leads_for_query(search_id, keyword, location):
    """
    Used for pause/resume.

    If user paused after 6 saved leads, resume starts from result index 6,
    not from result index 0.
    """

    leads = Lead.objects.filter(
        search_id=search_id,
        keyword__iexact=keyword,
        location__iexact=location,
    ).order_by("id")

    lead_keys = []

    for lead in leads:
        name = str(lead.name or "").strip().lower()
        phone = str(lead.phone or "").strip().lower()
        website = str(lead.website or "").strip().lower()
        address = str(lead.address or "").strip().lower()

        lead_keys.append(f"{name}|{phone}|{website}|{address}")

    return {
        "count": leads.count(),
        "keys": lead_keys,
    }


def db_is_search_cancelled(search_id):
    status = db_get_search_status(search_id)
    return status == "cancelled"


def db_is_search_paused(search_id):
    status = db_get_search_status(search_id)
    return status == "paused"


def db_mark_running(search_id):
    """
    Mark search as running.
    Never override paused/cancelled/completed/failed.
    """

    Search.objects.filter(id=search_id).exclude(
        status__in=["paused", "cancelled", "completed", "failed"]
    ).update(status="running")


def db_mark_failed(search_id, message=None):
    """
    Mark search as failed.
    Never override paused/cancelled/completed.
    """

    update_data = {
        "status": "failed",
    }

    if message:
        update_data["error_message"] = message

    Search.objects.filter(id=search_id).exclude(
        status__in=["paused", "cancelled", "completed"]
    ).update(**update_data)


def db_mark_completed_with_message(search_id, message=None):
    """
    Mark search completed safely.
    Used when usage limit is reached.
    """

    search = Search.objects.filter(id=search_id).first()

    if not search:
        return None

    if search.status in ["paused", "cancelled", "completed", "failed"]:
        return search.status

    search.status = "completed"

    update_fields = ["status", "updated_at"]

    if message:
        search.error_message = message
        update_fields.append("error_message")

    search.save(update_fields=update_fields)

    return search.status


def db_mark_query_completed(search_id):
    """
    Mark one query completed.
    """

    search = Search.objects.get(id=search_id)

    if search.status in ["paused", "cancelled"]:
        return search.status

    Search.objects.filter(id=search_id).update(
        completed_tasks=F("completed_tasks") + 1
    )

    search.refresh_from_db()

    if search.status in ["paused", "cancelled"]:
        return search.status

    if search.completed_tasks >= search.total_tasks:
        search.status = "completed"
    else:
        search.status = "running"

    search.save(update_fields=["status", "updated_at"])

    return search.status


def db_check_account_allowed(search_id):
    search = Search.objects.select_related("user").get(id=search_id)
    return check_account_allowed(search.user)


def db_check_lead_limit(search_id):
    search = Search.objects.select_related("user").get(id=search_id)
    return check_can_save_lead(search.user)


def db_save_single_lead(search_id, data):
    """
    Save one lead immediately so frontend can show it live.

    Returns:
    - lead id if saved or duplicate found
    - None if invalid/duplicate not found
    - "LIMIT_REACHED" if user reached lead usage limit
    """

    search = Search.objects.select_related("user").get(id=search_id)

    if search.status in ["paused", "cancelled"]:
        return None

    limit_check = check_can_save_lead(search.user)

    if not limit_check.allowed:
        log(f"Lead limit reached for user {search.user_id}: {limit_check.message}")
        return "LIMIT_REACHED"

    data = dict(data)
    data = remove_invalid_lead_alias_fields(data)

    lead = save_lead(search, data)

    if lead:
        log(f"Saved lead immediately: {data.get('name')}")
        send_lead_found(search.user_id, lead)
        return lead.id

    name = data.get("name")
    phone = data.get("phone")
    website = data.get("website")

    lead_query = Lead.objects.filter(search=search)

    if name:
        lead_query = lead_query.filter(name=name)

    if phone:
        lead_query = lead_query.filter(phone=phone)

    if website:
        lead_query = lead_query.filter(website=website)

    lead = lead_query.order_by("-id").first()

    if lead:
        log(f"Saved lead immediately: {data.get('name')}")
        send_lead_found(search.user_id, lead)
        return lead.id

    return None


def get_search_status(search_id):
    try:
        return run_db_safe(db_get_search_status, search_id)
    except Exception as e:
        error(f"Search status check failed: {e}")
        return None


def get_existing_leads_for_query(search_id, keyword, location):
    try:
        return run_db_safe(
            db_get_existing_leads_for_query,
            search_id,
            keyword,
            location,
        )
    except Exception as e:
        error(f"Existing leads check failed: {e}")
        return {"count": 0, "keys": []}


def is_search_cancelled(search_id):
    try:
        return run_db_safe(db_is_search_cancelled, search_id)
    except Exception as e:
        error(f"Cancel check failed: {e}")
        return False


def is_search_paused(search_id):
    try:
        return run_db_safe(db_is_search_paused, search_id)
    except Exception as e:
        error(f"Pause check failed: {e}")
        return False


def raise_if_stopped(search_id):
    """
    Stop scraper safely based on current search status.
    """

    status = get_search_status(search_id)

    if status == "paused":
        raise ScraperPaused("Search was paused by user")

    if status == "cancelled":
        raise ScraperCancelled("Search was cancelled by user")


def raise_if_usage_blocked(search_id):
    """
    Stop scraper when account is suspended/blocked or lead limit is reached.
    """

    account_check = run_db_safe(db_check_account_allowed, search_id)

    if not account_check.allowed:
        raise ScraperCancelled(account_check.message)

    lead_check = run_db_safe(db_check_lead_limit, search_id)

    if not lead_check.allowed:
        raise ScraperCancelled(lead_check.message)


def raise_if_cancelled(search_id, message="Search was cancelled by user"):
    """
    Backward-compatible helper name.
    """

    status = get_search_status(search_id)

    if status == "paused":
        raise ScraperPaused("Search was paused by user")

    if status == "cancelled":
        raise ScraperCancelled(message)


# =====================================================
# QUERY HELPER
# =====================================================
def split_query(query):
    lower_query = query.lower()

    if " in " in lower_query:
        index = lower_query.find(" in ")
        keyword = query[:index].strip()
        location = query[index + 4:].strip()
    else:
        keyword = query.strip()
        location = "unknown"

    return keyword, location


def build_google_maps_search_url(query):
    encoded_query = quote_plus(query)
    return f"https://www.google.com/maps/search/{encoded_query}"


# =====================================================
# SCRAPE MODE SETTINGS
# =====================================================
def get_scrape_settings(scrape_mode, max_leads):
    if scrape_mode == "deep":
        return {
            "max_results": max_leads,
            "max_scrolls": max(80, int(max_leads / 4)),
            "scroll_amount": 4200,
            "scroll_wait": 1800,
            "result_wait": 2200,
            "same_count_limit": 8,
            "initial_wait": 3500,
            "card_wait": 15000,
        }

    if scrape_mode == "balanced":
        return {
            "max_results": max_leads,
            "max_scrolls": max(60, int(max_leads / 5)),
            "scroll_amount": 3800,
            "scroll_wait": 1500,
            "result_wait": 1800,
            "same_count_limit": 6,
            "initial_wait": 3000,
            "card_wait": 12000,
        }

    return {
        "max_results": max_leads,
        "max_scrolls": max(45, int(max_leads / 6)),
        "scroll_amount": 3200,
        "scroll_wait": 1500,
        "result_wait": 1800,
        "same_count_limit": 5,
        "initial_wait": 3000,
        "card_wait": 12000,
    }


# =====================================================
# GOOGLE MAPS HELPERS
# =====================================================
def wait_for_google_maps_results(page, timeout=12000):
    selectors = [
        'div[role="article"]',
        "div.Nv2PK",
        'a[href*="/maps/place/"]',
    ]

    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            continue

    return False


def get_result_cards(page):
    selectors = [
        'div[role="article"]',
        "div.Nv2PK",
    ]

    for selector in selectors:
        try:
            cards = page.query_selector_all(selector)

            if cards:
                return cards

        except Exception:
            continue

    return []


def get_results_feed(page):
    feed_selectors = [
        'div[role="feed"]',
        "div.m6QErb[aria-label]",
        'div[aria-label*="Results"]',
        'div[aria-label*="results"]',
    ]

    for selector in feed_selectors:
        try:
            feed = page.query_selector(selector)

            if feed:
                return feed

        except Exception:
            continue

    return None


def scroll_results_panel(page, scroll_amount=3200, scroll_wait=1500):
    try:
        feed = get_results_feed(page)

        if feed:
            try:
                box = feed.bounding_box()

                if box:
                    page.mouse.move(
                        box["x"] + box["width"] / 2,
                        box["y"] + box["height"] / 2,
                    )

            except Exception:
                pass

        page.mouse.wheel(0, scroll_amount)
        page.wait_for_timeout(scroll_wait)

        return True

    except Exception as e:
        error(f"Result panel scroll failed: {e}")
        return False


def close_place_panel_if_needed(page):
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass


def make_lead_key(data):
    name = str(data.get("name") or "").strip().lower()
    phone = str(data.get("phone") or "").strip().lower()
    website = str(data.get("website") or "").strip().lower()
    address = str(data.get("address") or "").strip().lower()

    return f"{name}|{phone}|{website}|{address}"


# =====================================================
# MAIN SCRAPER
# =====================================================
def run_scraper(search_id, query, query_task_id=None):
    """
    Main Google Maps scraper.

    Professional rule:
    This scraper only scrapes and saves leads.
    It does not enrich websites/emails.
    Enrichment starts later from apps.searches.tasks after all scraping is done,
    and only if search.email_enrichment=True.
    """

    parser = BusinessParser()
    browser = BrowserManager()

    saved_count = 0
    processed_index = 0
    same_count_times = 0
    last_result_count = 0
    scroll_count = 0
    seen_leads = set()

    scrape_failed = False
    scrape_error = None
    scrape_cancelled = False
    scrape_paused = False
    usage_limit_reached = False

    page = None

    config = run_db_safe(db_get_search_config, search_id)

    max_leads = config["max_leads"]
    scrape_mode = config["scrape_mode"]
    email_enrichment = config["email_enrichment"]

    scrape_settings = get_scrape_settings(scrape_mode, max_leads)

    log(
        f"G Map Extractor config for {query}: "
        f"max_leads={max_leads}, "
        f"scrape_mode={scrape_mode}, "
        f"email_enrichment={email_enrichment}"
    )

    run_db_safe(db_mark_query_task_running, query_task_id)

    try:
        raise_if_stopped(search_id)
        raise_if_usage_blocked(search_id)

        run_db_safe(db_mark_running, search_id)

        keyword, location = split_query(query)

        # =====================================================
        # RESUME CHECKPOINT
        # =====================================================
        existing = get_existing_leads_for_query(search_id, keyword, location)

        existing_count = int(existing.get("count") or 0)
        existing_keys = existing.get("keys") or []

        saved_count = existing_count
        processed_index = existing_count
        seen_leads = set(existing_keys)

        log(
            f"Resume checkpoint for {query}: "
            f"existing_saved={existing_count}, "
            f"starting_processed_index={processed_index}"
        )

        if saved_count >= max_leads:
            log(f"Query already has {saved_count}/{max_leads} leads. Marking query completed.")
            run_db_safe(db_mark_query_task_completed, query_task_id)
            run_db_safe(db_mark_query_completed, search_id)
            return

        maps_url = build_google_maps_search_url(query)

        log(f"Opening Google Maps direct search URL for: {query}")
        log(f"Maps URL: {maps_url}")

        page = browser.start()

        raise_if_stopped(search_id)
        raise_if_usage_blocked(search_id)

        page.goto(
            maps_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(scrape_settings["initial_wait"])

        raise_if_stopped(search_id)
        raise_if_usage_blocked(search_id)

        has_results = wait_for_google_maps_results(
            page,
            timeout=scrape_settings["card_wait"],
        )

        if not has_results:
            page.wait_for_timeout(3000)
            has_results = wait_for_google_maps_results(page, timeout=5000)

        if not has_results:
            raise Exception("Google Maps results not found")

        log(f"Google Maps results loaded. Starting extractor mode for: {query}")

        while saved_count < max_leads:
            raise_if_stopped(search_id)
            raise_if_usage_blocked(search_id)

            fresh_results = get_result_cards(page)
            current_count = len(fresh_results)

            log(
                f"Visible results: {current_count} | "
                f"Processed index: {processed_index} | "
                f"Saved: {saved_count}/{max_leads}"
            )

            if processed_index < current_count:
                try:
                    result_number = processed_index + 1
                    result = fresh_results[processed_index]

                    try:
                        result.scroll_into_view_if_needed()
                        page.wait_for_timeout(400)
                    except Exception:
                        pass

                    raise_if_stopped(search_id)
                    raise_if_usage_blocked(search_id)

                    log(f"Opening business #{result_number}: {query}")

                    result.click()
                    page.wait_for_timeout(scrape_settings["result_wait"])

                    raise_if_stopped(search_id)
                    raise_if_usage_blocked(search_id)

                    raw_data = retry(lambda: extract_business(page))

                    processed_index += 1

                    run_db_safe(
                        db_update_query_task_progress,
                        query_task_id,
                        saved_count,
                        processed_index,
                    )

                    if not raw_data:
                        error(f"No raw data found for business #{result_number}")
                        close_place_panel_if_needed(page)
                        continue

                    data = parser.parse(
                        raw_data,
                        keyword=keyword,
                        location=location,
                    )

                    data = normalize_lead_data(data, raw_data=raw_data)
                    data = remove_invalid_lead_alias_fields(data)

                    if not parser.is_valid(data):
                        error(f"Invalid lead skipped: {data}")
                        close_place_panel_if_needed(page)
                        continue

                    lead_key = make_lead_key(data)

                    if lead_key in seen_leads:
                        log(f"Duplicate lead skipped: {data.get('name')}")
                        close_place_panel_if_needed(page)
                        continue

                    raise_if_stopped(search_id)
                    raise_if_usage_blocked(search_id)

                    lead_id = run_db_safe(db_save_single_lead, search_id, data)

                    if lead_id == "LIMIT_REACHED":
                        usage_limit_reached = True
                        scrape_error = "Lead usage limit reached."
                        log(f"Stopping scraper because usage limit reached: {query}")
                        break

                    if not lead_id:
                        raise_if_stopped(search_id)

                        error(f"Lead was not saved: {data.get('name')}")
                        close_place_panel_if_needed(page)
                        continue

                    saved_count += 1
                    seen_leads.add(lead_key)

                    run_db_safe(
                        db_update_query_task_progress,
                        query_task_id,
                        saved_count,
                        processed_index,
                    )

                    log(
                        f"Saved live lead: {data.get('name')} "
                        f"| Lead ID: {lead_id} "
                        f"| {saved_count}/{max_leads}"
                    )

                    close_place_panel_if_needed(page)

                    human_delay(0.5, 1.0)

                except ScraperPaused:
                    raise

                except ScraperCancelled:
                    raise

                except Exception as e:
                    error(f"Business processing failed at #{processed_index}: {e}")
                    close_place_panel_if_needed(page)
                    continue

            else:
                if current_count == last_result_count:
                    same_count_times += 1
                else:
                    same_count_times = 0

                last_result_count = current_count

                if same_count_times >= scrape_settings["same_count_limit"]:
                    log("No more new results loading. Stopping extractor.")
                    break

                if scroll_count >= scrape_settings["max_scrolls"]:
                    log("Reached max scroll limit. Stopping extractor.")
                    break

                raise_if_stopped(search_id)
                raise_if_usage_blocked(search_id)

                log(f"Scrolling for more businesses: {query}")

                scroll_results_panel(
                    page,
                    scroll_amount=scrape_settings["scroll_amount"],
                    scroll_wait=scrape_settings["scroll_wait"],
                )

                scroll_count += 1

        log(f"Finished G Map Extractor mode for {query}. Saved {saved_count} leads.")

    except ScraperPaused as e:
        scrape_paused = True
        scrape_error = str(e)
        log(f"Scraper paused by user: {query} | {e}")

    except ScraperCancelled as e:
        scrape_cancelled = True
        scrape_error = str(e)
        log(f"Scraper cancelled/stopped: {query} | {e}")

    except Exception as e:
        scrape_failed = True
        scrape_error = str(e)
        error(f"Scraper crashed on {query}: {e}")

    finally:
        try:
            browser.close()
        except Exception as e:
            error(f"Browser close failed: {e}")

    # =====================================================
    # FINAL SEARCH STATUS UPDATE
    # =====================================================
    if usage_limit_reached:
        try:
            run_db_safe(db_mark_query_task_completed, query_task_id)
            run_db_safe(
                db_mark_completed_with_message,
                search_id,
                "Lead usage limit reached.",
            )
            log(f"Search completed because usage limit was reached: {query}")
        except Exception as db_error:
            error(f"Failed to mark search completed after usage limit: {db_error}")

        return

    if scrape_paused or is_search_paused(search_id):
        log(f"Query stopped because search is paused: {query}")
        return

    if scrape_cancelled or is_search_cancelled(search_id):
        log(f"Query stopped because search is cancelled or account blocked: {query}")
        return

    if scrape_failed:
        try:
            run_db_safe(db_mark_query_task_failed, query_task_id, scrape_error)
            run_db_safe(db_mark_failed, search_id, scrape_error)
        except Exception as db_error:
            error(f"Failed to mark search failed: {db_error}")

        raise Exception(scrape_error)

    try:
        run_db_safe(db_mark_query_task_completed, query_task_id)
        run_db_safe(db_mark_query_completed, search_id)

        search = run_db_safe(lambda sid: Search.objects.get(id=sid), search_id)
        send_search_progress(search.user_id, search)

        log(f"Completed query: {query}. Saved {saved_count} leads.")

    except Exception as e:
        error(f"Database update failed for {query}: {e}")

        try:
            run_db_safe(db_mark_query_task_failed, query_task_id, str(e))
            run_db_safe(db_mark_failed, search_id, str(e))
        except Exception as db_error:
            error(f"Failed to mark search failed after DB error: {db_error}")

        raise


if __name__ == "__main__":
    print("This scraper engine file should be run through Celery task, not directly.")