from django.conf import settings
from django.utils import timezone
from django.contrib.auth import logout
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import EmailVerificationToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    GoogleLoginSerializer,
)
from .utils import get_tokens_for_user


def create_email_verification_token(user):
    """
    Create a new email verification token.
    Old unused tokens will be marked as used.
    """

    EmailVerificationToken.objects.filter(
        user=user,
        is_used=False,
    ).update(is_used=True)

    token = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    return token


def build_verification_link(request, token):
    """
    Build frontend verification link.

    Add this in settings.py later:
    FRONTEND_URL = "http://localhost:5173"
    """

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    return f"{frontend_url}/verify-email/{token.token}"


def send_verification_email(user, verification_link):
    """
    Basic email verification sender.

    This uses Django email settings.
    You need SMTP settings in settings.py for real sending.
    """

    from django.core.mail import send_mail

    subject = "Verify your LeadGen Pro account"

    message = f"""
Hi {user.full_name},

Please verify your email address to activate your LeadGen Pro account.

Verification link:
{verification_link}

This link will expire in 24 hours.

Thanks,
LeadGen Pro Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            verification_token = create_email_verification_token(user)
            verification_link = build_verification_link(request, verification_token)

            send_verification_email(user, verification_link)

            return Response(
                {
                    "message": "Account created successfully. Please verify your email before login.",
                    "user": UserSerializer(user).data,
                    "verification_required": True,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailAPIView(APIView):
    """
    Verify email endpoint.

    URL:
    GET /api/auth/verify-email/<token>/
    """
    
    permission_classes = [AllowAny]

    def get(self, request, token):
        verification_token = EmailVerificationToken.objects.filter(
            token=token,
            is_used=False,
        ).select_related("user").first()

        if not verification_token:
            return Response(
                {"error": "Invalid or already used verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification_token.is_expired():
            return Response(
                {"error": "Verification link has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = verification_token.user
        user.is_verified = True
        user.save(update_fields=["is_verified"])

        verification_token.is_used = True
        verification_token.save(update_fields=["is_used"])

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "message": "Email verified successfully.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class ResendVerificationEmailAPIView(APIView):
    """
    Resend email verification link.

    URL:
    POST /api/auth/resend-verification/

    Body:
    {
        "email": "user@example.com"
    }
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .models import User

        user = User.objects.filter(email=email.lower().strip()).first()

        if not user:
            return Response(
                {"error": "No account found with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_verified:
            return Response(
                {"message": "This email is already verified."},
                status=status.HTTP_200_OK,
            )

        verification_token = create_email_verification_token(user)
        verification_link = build_verification_link(request, verification_token)

        send_verification_email(user, verification_link)

        return Response(
            {"message": "Verification email sent again."},
            status=status.HTTP_200_OK,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "message": "Login successful.",
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginAPIView(APIView):
    """
    Google login endpoint.

    Frontend Google OAuth should send:
    {
        "email": "user@gmail.com",
        "full_name": "User Name",
        "google_id": "google-sub-id",
        "profile_picture": "https://..."
    }

    URL:
    POST /api/auth/google/
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.create_or_get_user()
            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "message": "Google login successful.",
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    Simple logout endpoint.

    Frontend should also remove access/refresh token from localStorage.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)