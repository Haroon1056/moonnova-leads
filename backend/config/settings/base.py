"""
Base Django settings for LeadGen Pro.
Shared by development and production.
"""

import os
import ssl
from datetime import timedelta
from pathlib import Path
import sys
import dj_database_url
import asyncio

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)

    return [item.strip() for item in value.split(",") if item.strip()]


# SECURITY
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# APPLICATIONS
INSTALLED_APPS = [
    "daphne",
    
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "channels",
    
    # Local apps
    "apps.accounts",
    "apps.core",
    "apps.searches",
    "apps.leads",
    "apps.services",
    "apps.usage",
    "apps.realtime",
    "apps.admin_dashboard",
    "apps.monitoring",
    "apps.ai",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# AUTH
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", True)

RATE_LIMITS = {
    "auth_login": os.getenv("RATE_LIMIT_AUTH_LOGIN", "5/m"),
    "auth_register": os.getenv("RATE_LIMIT_AUTH_REGISTER", "5/h"),
    "auth_resend_email": os.getenv("RATE_LIMIT_AUTH_RESEND_EMAIL", "3/h"),
    "search_create": os.getenv("RATE_LIMIT_SEARCH_CREATE", "10/h"),
    "lead_export": os.getenv("RATE_LIMIT_LEAD_EXPORT", "10/h"),
    "enrichment": os.getenv("RATE_LIMIT_ENRICHMENT", "30/h"),
    "default_write": os.getenv("RATE_LIMIT_DEFAULT_WRITE", "60/h"),
}


# DJANGO REST FRAMEWORK
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("API_PAGE_SIZE", "25")),

    # API docs
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    # Safer error/output behavior
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "LeadGen Pro API",
    "DESCRIPTION": "Backend API for LeadGen Pro SaaS.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "AUTHENTICATION_WHITELIST": [],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}


# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS", "7"))
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "leadgen_saas_db"),
            "USER": os.getenv("POSTGRES_USER", "leadgen_user"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "leadgen_password_123"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
        }
    }

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# LANGUAGE / TIME
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True


# STATIC / MEDIA
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EXPORTS_ROOT = MEDIA_ROOT / "exports"

EXPORT_MAX_SYNC_ROWS = int(os.getenv("EXPORT_MAX_SYNC_ROWS", "500"))
EXPORT_RETENTION_DAYS = int(os.getenv("EXPORT_RETENTION_DAYS", "7"))

# CELERY / REDIS
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6380/0")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "3600"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "3300"))
CELERY_WORKER_PREFETCH_MULTIPLIER = int(
    os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")
)

# Required for Upstash / TLS Redis URLs that start with rediss://
# Upstash TLS Redis support
if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_NONE,
    }

if CELERY_RESULT_BACKEND.startswith("rediss://"):
    CELERY_REDIS_BACKEND_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_NONE,
    }


CELERY_BEAT_SCHEDULE = {
    "cleanup-all-users-data-daily": {
        "task": "apps.leads.tasks.cleanup_all_users_data_task",
        "schedule": 60 * 60 * 24,
    },
    "finalize-enrichment-jobs-every-5-minutes": {
        "task": "apps.leads.tasks.finalize_enrichment_jobs_task",
        "schedule": 60 * 5,
    },
    "monitoring-health-check-every-5-minutes": {
        "task": "apps.monitoring.tasks.monitoring_health_check_task",
        "schedule": 60 * 5,
    },
    "auto-resolve-old-info-events-daily": {
        "task": "apps.monitoring.tasks.auto_resolve_old_info_events_task",
        "schedule": 60 * 60 * 24,
    },
    "cleanup-old-system-events-weekly": {
        "task": "apps.monitoring.tasks.cleanup_old_system_events_task",
        "schedule": 60 * 60 * 24 * 7,
    },
    "finalize-ai-jobs-every-5-minutes": {
        "task": "apps.ai.tasks.finalize_ai_jobs_task",
        "schedule": 60 * 5,
    },
}


# DJANGO CHANNELS / WEBSOCKET
CHANNEL_LAYERS_REDIS_URL = os.getenv("CHANNEL_LAYERS_REDIS_URL", REDIS_URL)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [CHANNEL_LAYERS_REDIS_URL],
        },
    },
}

# # CELERY / REDIS
# CELERY_BROKER_URL = os.getenv(
#     "CELERY_BROKER_URL",
#     "redis://localhost:6379/0",
# )

# CELERY_RESULT_BACKEND = os.getenv(
#     "CELERY_RESULT_BACKEND",
#     "redis://localhost:6379/0",
# )

# CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "3600"))
# CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "3300"))
# CELERY_WORKER_PREFETCH_MULTIPLIER = int(
#     os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")
# )

# CELERY_BEAT_SCHEDULE = {
#     "cleanup-all-users-data-daily": {
#         "task": "apps.leads.tasks.cleanup_all_users_data_task",
#         "schedule": 60 * 60 * 24,
#     },
#     "finalize-enrichment-jobs-every-5-minutes": {
#         "task": "apps.leads.tasks.finalize_enrichment_jobs_task",
#         "schedule": 60 * 5,
#     },
#     "monitoring-health-check-every-5-minutes": {
#         "task": "apps.monitoring.tasks.monitoring_health_check_task",
#         "schedule": 60 * 5,
#     },
#     "auto-resolve-old-info-events-daily": {
#         "task": "apps.monitoring.tasks.auto_resolve_old_info_events_task",
#         "schedule": 60 * 60 * 24,
#     },
#     "cleanup-old-system-events-weekly": {
#         "task": "apps.monitoring.tasks.cleanup_old_system_events_task",
#         "schedule": 60 * 60 * 24 * 7,
#     },
#     "finalize-ai-jobs-every-5-minutes": {
#         "task": "apps.ai.tasks.finalize_ai_jobs_task",
#         "schedule": 60 * 5,
#     },
# }

# import os

# REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6380/0")

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [REDIS_URL],
#         },
#     },
# }

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer",
#     },
# }
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [
#                 (
#                     os.getenv("REDIS_HOST", "127.0.0.1"),
#                     int(os.getenv("REDIS_PORT", "6379")),
#                 )
#             ],
#         },
#     },
# }


# REAL TIME SETTINGS
REALTIME_ENABLED = env_bool("REALTIME_ENABLED", True)

# CORS / CSRF
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)


# EMAIL
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "LeadGen Pro <noreply@leadgenpro.com>",
)


# GOOGLE LOGIN
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


# SCRAPER
PLAYWRIGHT_HEADLESS = env_bool("PLAYWRIGHT_HEADLESS", True)

SCRAPER_MAX_GLOBAL_WORKERS = int(
    os.getenv("SCRAPER_MAX_GLOBAL_WORKERS", "2")
)

SCRAPER_MAX_ACTIVE_SEARCHES_PER_USER = int(
    os.getenv("SCRAPER_MAX_ACTIVE_SEARCHES_PER_USER", "1")
)


# LOGGING
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{levelname}] {asctime} {name} "
                      "{module}.{funcName}:{lineno} - {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },

        "django_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },

        "scraper_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "scraper.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },

        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "errors.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
        },
    },

    "loggers": {
        "django": {
            "handlers": ["console", "django_file", "error_file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },

        "apps": {
            "handlers": ["console", "django_file", "error_file"],
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },

        "scraper": {
            "handlers": ["console", "scraper_file", "error_file"],
            "level": os.getenv("SCRAPER_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        
        "monitoring": {
            "handlers": ["console", "django_file", "error_file"],
            "level": os.getenv("MONITORING_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# =====================================================
# Monitoring / Sentry
# =====================================================

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))

HEALTH_CHECK_REDIS_URL = os.getenv(
    "HEALTH_CHECK_REDIS_URL",
    os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6380/0"),
)

HEALTH_CHECK_CELERY_TIMEOUT = int(os.getenv("HEALTH_CHECK_CELERY_TIMEOUT", "5"))

# =====================================================
# AI / Gemini
# =====================================================

AI_ENABLED = env_bool("AI_ENABLED", True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

AI_BULK_MAX_LEADS = int(os.getenv("AI_BULK_MAX_LEADS", "50"))

AI_DEFAULT_MONTHLY_CREDITS = int(os.getenv("AI_DEFAULT_MONTHLY_CREDITS", "500"))

AI_CREDIT_COSTS = {
    "lead_insight": int(os.getenv("AI_COST_LEAD_INSIGHT", "3")),
    "full_personalization": int(os.getenv("AI_COST_FULL_PERSONALIZATION", "5")),
}