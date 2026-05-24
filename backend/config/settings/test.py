from .dev import *  # noqa

# Use SQLite for local automated tests.
# This avoids PostgreSQL CREATE DATABASE permission issues.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery async behavior during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable rate limit during tests
RATELIMIT_ENABLE = False

# Use local memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Keep tests simple
DEBUG = False