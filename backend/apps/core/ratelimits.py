from functools import wraps

from django.conf import settings
from django.http import JsonResponse


try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    try:
        from ratelimit.decorators import ratelimit
    except ImportError:
        ratelimit = None


def rate_limit_key(group_name):
    limits = getattr(settings, "RATE_LIMITS", {})
    return limits.get(group_name, "60/h")


def api_ratelimit(group_name, key="user_or_ip", method="ALL", block=False):
    """
    Reusable API rate limit decorator.

    If django-ratelimit import is unavailable or rate limiting is disabled,
    this decorator will not block the request.
    """

    rate = rate_limit_key(group_name)

    def decorator(view_func):
        if ratelimit is None or not getattr(settings, "RATELIMIT_ENABLE", True):
            return view_func

        @ratelimit(key=key, rate=rate, method=method, block=block)
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if getattr(request, "limited", False):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Too many requests. Please try again later.",
                        "errors": {
                            "rate_limit": f"Rate limit exceeded: {rate}",
                        },
                        "status_code": 429,
                    },
                    status=429,
                )

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator