import html
import json
import re
import time
import random
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup


EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    flags=re.IGNORECASE,
)

OBFUSCATED_EMAIL_REGEXES = [
    re.compile(
        r"([a-zA-Z0-9_.%+\-]+)\s*(?:\[at\]|\(at\)|\{at\}|\sat\s|\s@\s)\s*"
        r"([a-zA-Z0-9\-]+)\s*(?:\[dot\]|\(dot\)|\{dot\}|\sdot\s|\s\.\s)\s*"
        r"([a-zA-Z]{2,})",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"([a-zA-Z0-9_.%+\-]+)\s*\[\s*@\s*\]\s*"
        r"([a-zA-Z0-9\-]+)\s*\[\s*\.\s*\]\s*"
        r"([a-zA-Z]{2,})",
        flags=re.IGNORECASE,
    ),
]

BAD_EMAIL_KEYWORDS = [
    "example.com",
    "domain.com",
    "email.com",
    "test.com",
    "yourdomain.com",
    "your-email",
    "name@",
    "user@",
    "sample@",
    "sentry.io",
    "wixpress.com",
    "wix.com",
    "wordpress.com",
    "shopify.com",
    "schema.org",
    "google.com",
    "gstatic.com",
    "googleapis.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "cloudflare.com",
    "cdnjs.com",
    "bootstrap",
    "jquery",
    "no-reply",
    "noreply",
    "donotreply",
    "do-not-reply",
    "privacy@",
    "abuse@",
    "postmaster@",
    "webmaster@",
    "support@google",
]

LOW_PRIORITY_EMAIL_PREFIXES = [
    "privacy@",
    "legal@",
    "abuse@",
    "postmaster@",
    "webmaster@",
    "noreply@",
    "no-reply@",
    "donotreply@",
    "do-not-reply@",
]

GOOD_EMAIL_PREFIXES = [
    "info@",
    "hello@",
    "contact@",
    "office@",
    "service@",
    "services@",
    "support@",
    "sales@",
    "admin@",
    "bookings@",
    "booking@",
    "estimate@",
    "estimates@",
    "quotes@",
    "quote@",
]

CONTACT_PAGE_KEYWORDS = [
    "contact",
    "contact-us",
    "contactus",
    "about",
    "about-us",
    "aboutus",
    "support",
    "service-area",
    "service-areas",
    "services",
    "team",
    "staff",
    "location",
    "locations",
    "get-in-touch",
    "connect",
    "request-service",
    "schedule",
    "booking",
    "book",
    "estimate",
    "free-estimate",
    "quote",
    "request-quote",
    "appointment",
]

COMMON_CONTACT_PATHS = [
    "/contact",
    "/contact/",
    "/contact-us",
    "/contact-us/",
    "/contactus",
    "/about",
    "/about/",
    "/about-us",
    "/about-us/",
    "/team",
    "/staff",
    "/locations",
    "/location",
    "/service-area",
    "/service-areas",
    "/request-service",
    "/schedule-service",
    "/book-online",
    "/booking",
    "/free-estimate",
    "/estimate",
    "/request-estimate",
    "/quote",
    "/request-quote",
]

BAD_FILE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
    ".rar",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    ".css",
    ".js",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
]

SOCIAL_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
]


class EmailExtractor:
    def __init__(self, timeout=15, max_pages=10, max_emails=5):
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_emails = max_emails
        self.session = requests.Session()

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
        }

    # =====================================================
    # URL HELPERS
    # =====================================================
    def normalize_url(self, website):
        if not website:
            return None

        website = str(website).strip()

        if not website:
            return None

        if website.lower() in ["website", "directions", "call", "save", "share"]:
            return None

        if website.startswith("mailto:") or website.startswith("tel:"):
            return None

        if website.startswith("//"):
            website = "https:" + website

        if not website.startswith(("http://", "https://")):
            website = "https://" + website

        return website

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)

            if not parsed.netloc:
                return False

            if parsed.scheme not in ["http", "https"]:
                return False

            lower_url = url.lower()
            lower_path = parsed.path.lower()

            if any(domain in lower_url for domain in SOCIAL_DOMAINS):
                return False

            for ext in BAD_FILE_EXTENSIONS:
                if lower_path.endswith(ext):
                    return False

            return True

        except Exception:
            return False

    def same_domain(self, base_url, target_url):
        try:
            parsed_base = urlparse(base_url)
            parsed_target = urlparse(target_url)

            base_domain = parsed_base.netloc.lower().replace("www.", "")
            target_domain = parsed_target.netloc.lower().replace("www.", "")

            return base_domain == target_domain

        except Exception:
            return False

    def domain_from_url(self, url):
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")

            if ":" in domain:
                domain = domain.split(":")[0]

            return domain

        except Exception:
            return ""

    # =====================================================
    # FETCHING
    # =====================================================
    def fetch_page(self, url):
        """
        Fetch page with HTTPS first. If SSL/connection fails, try HTTP fallback.
        Returns: html_text, final_url, status_code
        """

        candidates = [url]

        if url.startswith("https://"):
            candidates.append(url.replace("https://", "http://", 1))

        for candidate in candidates:
            try:
                response = self.session.get(
                    candidate,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                content_type = response.headers.get("content-type", "").lower()

                if response.status_code >= 500:
                    continue

                if response.status_code in [401, 403]:
                    return None, response.url, response.status_code

                if response.status_code >= 400:
                    continue

                if (
                    "text/html" not in content_type
                    and "application/xhtml" not in content_type
                    and content_type
                ):
                    continue

                if not response.text:
                    continue

                return response.text, response.url, response.status_code

            except requests.exceptions.SSLError:
                continue

            except requests.exceptions.RequestException:
                continue

            except Exception:
                continue

        return None, url, None

    # =====================================================
    # EMAIL CLEANING / VALIDATION
    # =====================================================
    def clean_email(self, email):
        if not email:
            return None

        email = str(email).strip().lower()

        email = html.unescape(email)
        email = unquote(email)

        email = email.replace("mailto:", "")
        email = email.replace("&#64;", "@")
        email = email.replace("&#x40;", "@")
        email = email.replace("&commat;", "@")
        email = email.replace("%40", "@")

        email = email.split("?")[0]
        email = email.split("&")[0]

        email = email.strip(".,;:()[]{}<>\"'`|\\")

        if not EMAIL_REGEX.fullmatch(email):
            return None

        if ".." in email:
            return None

        if email.count("@") != 1:
            return None

        local, domain = email.split("@", 1)

        if len(local) < 2:
            return None

        if "." not in domain:
            return None

        for bad in BAD_EMAIL_KEYWORDS:
            if bad in email:
                return None

        if email.endswith(
            (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".svg",
                ".css",
                ".js",
            )
        ):
            return None

        return email

    def prioritize_emails(self, emails, website=None):
        """
        Prefer business-domain and business-intent emails.
        """

        unique = []

        for email in emails:
            email = self.clean_email(email)

            if email and email not in unique:
                unique.append(email)

        website_domain = self.domain_from_url(website) if website else ""

        def score(email):
            value = 0

            if website_domain and email.endswith("@" + website_domain):
                value += 50

            for prefix in GOOD_EMAIL_PREFIXES:
                if email.startswith(prefix):
                    value += 30
                    break

            for prefix in LOW_PRIORITY_EMAIL_PREFIXES:
                if email.startswith(prefix):
                    value -= 40
                    break

            if any(
                generic in email
                for generic in ["info@", "hello@", "contact@", "sales@"]
            ):
                value += 10

            return value

        unique.sort(key=score, reverse=True)

        return unique[: self.max_emails]

    def calculate_confidence(self, emails, source_pages, website=None):
        if not emails:
            return 0

        confidence = 50

        website_domain = self.domain_from_url(website) if website else ""

        for email in emails:
            if website_domain and email.endswith("@" + website_domain):
                confidence += 30
                break

        if source_pages:
            confidence += 10

        if len(emails) >= 2:
            confidence += 10

        return min(confidence, 100)

    # =====================================================
    # DECODE HELPERS
    # =====================================================
    def decode_cloudflare_email(self, encoded_string):
        """
        Decode Cloudflare protected email:
        /cdn-cgi/l/email-protection#...
        """

        try:
            encoded_string = encoded_string.split("#")[-1]

            key = int(encoded_string[:2], 16)
            decoded = ""

            for i in range(2, len(encoded_string), 2):
                decoded += chr(int(encoded_string[i:i + 2], 16) ^ key)

            return self.clean_email(decoded)

        except Exception:
            return None

    def extract_cloudflare_emails(self, html_text):
        emails = []

        if not html_text:
            return emails

        patterns = [
            r"/cdn-cgi/l/email-protection#([a-fA-F0-9]+)",
            r'data-cfemail=["\']([a-fA-F0-9]+)["\']',
        ]

        for pattern in patterns:
            for encoded in re.findall(pattern, html_text):
                email = self.decode_cloudflare_email(encoded)

                if email and email not in emails:
                    emails.append(email)

        return emails

    def decode_unicode_escapes(self, text):
        if not text:
            return ""

        try:
            text = text.replace("\\x40", "@")
            text = text.replace("\\u0040", "@")
            text = text.replace("&#64;", "@")
            text = text.replace("&#x40;", "@")
            text = html.unescape(text)
        except Exception:
            pass

        return text

    def decode_obfuscated_emails(self, text):
        if not text:
            return []

        text = self.decode_unicode_escapes(text)

        emails = []

        try:
            for regex in OBFUSCATED_EMAIL_REGEXES:
                matches = regex.findall(text)

                for local, domain, tld in matches:
                    email = f"{local}@{domain}.{tld}"
                    email = self.clean_email(email)

                    if email and email not in emails:
                        emails.append(email)

        except Exception:
            pass

        return emails

    # =====================================================
    # EXTRACTION HELPERS
    # =====================================================
    def extract_emails_from_text(self, text):
        if not text:
            return []

        text = self.decode_unicode_escapes(text)

        found = EMAIL_REGEX.findall(text)
        clean_emails = []

        for email in found:
            email = self.clean_email(email)

            if email and email not in clean_emails:
                clean_emails.append(email)

        for email in self.decode_obfuscated_emails(text):
            if email not in clean_emails:
                clean_emails.append(email)

        for email in self.extract_cloudflare_emails(text):
            if email not in clean_emails:
                clean_emails.append(email)

        return clean_emails

    def extract_mailto_emails(self, soup):
        emails = []

        try:
            mailto_links = soup.select('a[href*="mailto:"]')

            for link in mailto_links:
                href = link.get("href", "")

                href = html.unescape(unquote(href))
                href = href.replace("mailto:", "")
                href = href.split("?")[0]
                href = href.replace("%40", "@")

                found = self.extract_emails_from_text(href)

                for email in found:
                    if email not in emails:
                        emails.append(email)

        except Exception:
            pass

        return emails

    def extract_data_attributes(self, soup):
        emails = []

        try:
            for tag in soup.find_all(True):
                for attr_name, attr_value in tag.attrs.items():
                    if not attr_value:
                        continue

                    if isinstance(attr_value, list):
                        attr_value = " ".join(attr_value)

                    attr_text = str(attr_value)

                    should_check = (
                        "@"
                        in attr_text
                        or "mailto:"
                        in attr_text.lower()
                        or "[at]"
                        in attr_text.lower()
                        or "(at)"
                        in attr_text.lower()
                        or "data-cfemail"
                        in attr_name.lower()
                    )

                    if should_check:
                        found = self.extract_emails_from_text(attr_text)

                        for email in found:
                            if email not in emails:
                                emails.append(email)

                    if attr_name.lower() == "data-cfemail":
                        email = self.decode_cloudflare_email(attr_text)

                        if email and email not in emails:
                            emails.append(email)

        except Exception:
            pass

        return emails

    def extract_json_ld_emails(self, soup):
        emails = []

        try:
            scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

            for script in scripts:
                content = script.string or script.get_text() or ""

                found = self.extract_emails_from_text(content)

                for email in found:
                    if email not in emails:
                        emails.append(email)

                try:
                    data = json.loads(content)
                    json_text = json.dumps(data)

                    found = self.extract_emails_from_text(json_text)

                    for email in found:
                        if email not in emails:
                            emails.append(email)

                except Exception:
                    pass

        except Exception:
            pass

        return emails

    def extract_script_text_emails(self, soup):
        emails = []

        try:
            scripts = soup.find_all("script")

            for script in scripts:
                content = script.string or script.get_text() or ""

                if (
                    "@"
                    not in content
                    and "\\x40" not in content
                    and "\\u0040" not in content
                ):
                    continue

                found = self.extract_emails_from_text(content)

                for email in found:
                    if email not in emails:
                        emails.append(email)

        except Exception:
            pass

        return emails

    def extract_from_page(self, url):
        html_text, final_url, status_code = self.fetch_page(url)

        if not html_text:
            return [], None, final_url, status_code

        try:
            soup = BeautifulSoup(html_text, "html.parser")
        except Exception:
            return (
                self.extract_emails_from_text(html_text),
                html_text,
                final_url,
                status_code,
            )

        emails = []

        emails.extend(self.extract_mailto_emails(soup))
        emails.extend(self.extract_data_attributes(soup))
        emails.extend(self.extract_json_ld_emails(soup))
        emails.extend(self.extract_script_text_emails(soup))

        try:
            text = soup.get_text(" ", strip=True)
        except Exception:
            text = ""

        emails.extend(self.extract_emails_from_text(text))
        emails.extend(self.extract_emails_from_text(html_text))

        unique_emails = []

        for email in emails:
            email = self.clean_email(email)

            if email and email not in unique_emails:
                unique_emails.append(email)

        return unique_emails, html_text, final_url, status_code

    # =====================================================
    # PAGE DISCOVERY
    # =====================================================
    def discover_contact_pages(self, base_url, html_text):
        urls = []

        try:
            soup = BeautifulSoup(html_text, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                text = link.get_text(" ", strip=True).lower()

                if not href:
                    continue

                if href.startswith("#"):
                    continue

                if href.startswith(("tel:", "sms:", "mailto:", "javascript:")):
                    continue

                full_url = urljoin(base_url, href)

                if not self.is_valid_url(full_url):
                    continue

                if not self.same_domain(base_url, full_url):
                    continue

                href_lower = href.lower()
                full_url_lower = full_url.lower()

                is_contact_page = any(
                    keyword in href_lower
                    or keyword in text
                    or keyword in full_url_lower
                    for keyword in CONTACT_PAGE_KEYWORDS
                )

                if is_contact_page and full_url not in urls:
                    urls.append(full_url)

        except Exception:
            pass

        for path in COMMON_CONTACT_PATHS:
            fallback_url = urljoin(base_url, path)

            if (
                self.is_valid_url(fallback_url)
                and self.same_domain(base_url, fallback_url)
                and fallback_url not in urls
            ):
                urls.append(fallback_url)

        return urls[: self.max_pages]

    # =====================================================
    # MAIN
    # =====================================================
    def extract(self, website):
        website = self.normalize_url(website)

        if not website or not self.is_valid_url(website):
            return {
                "emails": [],
                "source_pages": [],
                "checked_pages": [],
                "errors": ["Invalid website URL"],
                "confidence": 0,
            }

        all_emails = []
        source_pages = []
        checked_pages = []
        errors = []
        visited_pages = set()

        homepage_emails, homepage_html, final_url, status_code = self.extract_from_page(
            website
        )

        visited_pages.add(website)

        checked_pages.append(
            {
                "url": website,
                "final_url": final_url,
                "status_code": status_code,
                "method": "requests",
            }
        )

        if homepage_html:
            source_pages.append(final_url or website)

        for email in homepage_emails:
            if email not in all_emails:
                all_emails.append(email)

        if len(all_emails) >= self.max_emails:
            final_emails = self.prioritize_emails(all_emails, website)

            return {
                "emails": final_emails,
                "source_pages": source_pages,
                "checked_pages": checked_pages,
                "errors": errors,
                "confidence": self.calculate_confidence(
                    final_emails,
                    source_pages,
                    website,
                ),
            }

        if homepage_html:
            contact_pages = self.discover_contact_pages(
                final_url or website,
                homepage_html,
            )
        else:
            errors.append(f"Homepage fetch failed or protected. Status: {status_code}")
            contact_pages = [urljoin(website, path) for path in COMMON_CONTACT_PATHS]

        for page_url in contact_pages:
            if len(all_emails) >= self.max_emails:
                break

            if page_url in visited_pages:
                continue

            visited_pages.add(page_url)

            time.sleep(random.uniform(0.5, 1.2))

            page_emails, page_html, page_final_url, page_status_code = self.extract_from_page(
                page_url
            )

            checked_pages.append(
                {
                    "url": page_url,
                    "final_url": page_final_url,
                    "status_code": page_status_code,
                    "method": "requests",
                }
            )

            if page_html:
                source_pages.append(page_final_url or page_url)

            for email in page_emails:
                if email not in all_emails:
                    all_emails.append(email)

        final_emails = self.prioritize_emails(all_emails, website)

        return {
            "emails": final_emails,
            "source_pages": source_pages,
            "checked_pages": checked_pages,
            "errors": errors,
            "confidence": self.calculate_confidence(
                final_emails,
                source_pages,
                website,
            ),
        }


def extract_emails_from_website(website):
    extractor = EmailExtractor()
    return extractor.extract(website)