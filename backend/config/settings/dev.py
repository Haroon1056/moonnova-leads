"""
Development settings for LeadGen Pro.
Use this for local development only.
"""

from .base import *  # noqa: F403,F401


DEBUG = True

ALLOWED_HOSTS = env_list(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,0.0.0.0",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Local scraping is easier to debug with visible browser.
PLAYWRIGHT_HEADLESS = env_bool("PLAYWRIGHT_HEADLESS", False)  # noqa: F405