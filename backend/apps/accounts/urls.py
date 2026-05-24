from django.urls import path

from .views import (
    RegisterAPIView,
    LoginAPIView,
    ProfileAPIView,
    VerifyEmailAPIView,
    ResendVerificationEmailAPIView,
    GoogleLoginAPIView,
    LogoutAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view()),
    path("login/", LoginAPIView.as_view()),
    path("profile/", ProfileAPIView.as_view()),

    # Email verification
    path("verify-email/<uuid:token>/", VerifyEmailAPIView.as_view()),
    path("resend-verification/", ResendVerificationEmailAPIView.as_view()),

    # Google login
    path("google/", GoogleLoginAPIView.as_view()),

    # Logout
    path("logout/", LogoutAPIView.as_view()),
]