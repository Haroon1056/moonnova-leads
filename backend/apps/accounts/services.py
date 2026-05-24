# apps/accounts/services.py

from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

from .models import User


def create_user(email: str, full_name: str, password: str) -> User:
    """
    Create normal email/password user.
    Email users should verify email before login.
    """

    user = User.objects.create_user(
        email=email,
        full_name=full_name,
        password=password,
        auth_provider="email",
        is_verified=False,
    )

    return user


def login_user(email: str, password: str) -> User:
    """
    Login normal email/password user.
    """

    user = authenticate(
        email=email.lower().strip(),
        password=password,
    )

    if not user:
        raise AuthenticationFailed("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationFailed("User account is disabled.")

    if user.auth_provider == "email" and not user.is_verified:
        raise AuthenticationFailed("Please verify your email before login.")

    return user


def update_user_profile(user: User, data: dict) -> User:
    """
    Update basic user profile.
    """

    full_name = data.get("full_name")

    if full_name:
        user.full_name = full_name.strip()

    user.save(update_fields=["full_name"])

    return user


def create_or_update_google_user(
    email: str,
    full_name: str,
    google_id: str,
    profile_picture: str = None,
) -> User:
    """
    Create or update Google login user.
    """

    email = email.lower().strip()

    user = User.objects.filter(email=email).first()

    if user:
        user.full_name = full_name or user.full_name
        user.google_id = google_id
        user.profile_picture = profile_picture or user.profile_picture
        user.auth_provider = "google"
        user.is_verified = True

        user.save(
            update_fields=[
                "full_name",
                "google_id",
                "profile_picture",
                "auth_provider",
                "is_verified",
            ]
        )

        return user

    user = User.objects.create_user(
        email=email,
        full_name=full_name or email.split("@")[0],
        password=None,
        auth_provider="google",
        google_id=google_id,
        profile_picture=profile_picture,
        is_verified=True,
    )

    return user