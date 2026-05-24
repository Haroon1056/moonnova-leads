# apps/accounts/utils.py

from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for user.
    Used for:
    - normal login
    - email verification login
    - Google login
    """

    refresh = RefreshToken.for_user(user)

    # Add useful user info inside token
    refresh["email"] = user.email
    refresh["full_name"] = user.full_name
    refresh["is_verified"] = user.is_verified
    refresh["auth_provider"] = getattr(user, "auth_provider", "email")

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def normalize_email(email):
    """
    Normalize email before saving/checking.
    """

    if not email:
        return ""

    return str(email).lower().strip()