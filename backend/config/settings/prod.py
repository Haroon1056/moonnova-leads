"""
Production settings for MoonNova Leads.
Use this only on live server.
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403,F401


DEBUG = False


REQUIRED_ENV_VARS = [
    "DJANGO_SECRET_KEY",
    "DJANGO_ALLOWED_HOSTS",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "CHANNEL_LAYERS_REDIS_URL",
    "CORS_ALLOWED_ORIGINS",
    "CSRF_TRUSTED_ORIGINS",
]


missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]

if missing:
    raise ImproperlyConfigured(
        "Missing required production environment variables: "
        + ", ".join(missing)
    )


if SECRET_KEY == "django-insecure-dev-only-change-me":  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be changed in production."
    )


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Keep this False on Render free/demo first to avoid redirect issues during testing.
# After frontend/backend are fully working, you can change SECURE_SSL_REDIRECT=True in Render env.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)  # noqa: F405

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)  # noqa: F405
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)  # noqa: F405

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

# Production should run Playwright headless.
PLAYWRIGHT_HEADLESS = env_bool("PLAYWRIGHT_HEADLESS", True)  # noqa: F405


import sentry_sdk

from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration


if SENTRY_DSN:  # noqa: F405
    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        environment=SENTRY_ENVIRONMENT,  # noqa: F405
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,  # noqa: F405
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,  # noqa: F405
        send_default_pii=False,
    )