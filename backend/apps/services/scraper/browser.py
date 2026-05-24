import os
import sys
import asyncio
from playwright.sync_api import sync_playwright

# from .proxy import get_random_proxy

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

class BrowserManager:

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()

        # proxy = get_random_proxy()

        headless_value = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower()
        headless = headless_value in ["true", "1", "yes"]

        self.browser = self.playwright.chromium.launch(
            headless=headless,
            # proxy={"server": proxy},
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--start-maximized",
            ],
        )

        self.page = self.browser.new_page(
            viewport={
                "width": 1366,
                "height": 768,
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        self.page.set_default_timeout(30000)
        self.page.set_default_navigation_timeout(60000)

        return self.page

    def close(self):
        try:
            if self.page:
                self.page.close()
        except Exception:
            pass

        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass