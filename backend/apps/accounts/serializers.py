from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "password",
        ]

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")

        return value

    def validate_full_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError("Full name is required.")

        return value

    def create(self, validated_data):
        validated_data["email"] = validated_data["email"].lower().strip()

        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            password=validated_data["password"],
        )

        # Normal email/password users must verify email.
        user.auth_provider = "email"
        user.is_verified = False
        user.save(update_fields=["auth_provider", "is_verified"])

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, data):
        email = data["email"].lower().strip()
        password = data["password"]

        user = authenticate(
            email=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")

        if user.auth_provider == "email" and not user.is_verified:
            raise serializers.ValidationError(
                "Please verify your email address before login."
            )

        return {
            "user": user,
        }


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "is_verified",
            "auth_provider",
            "profile_picture",
            "date_joined",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_verified",
            "auth_provider",
            "profile_picture",
            "date_joined",
        ]


class GoogleLoginSerializer(serializers.Serializer):
    """
    Frontend will send Google account data after Google OAuth success.

    Expected payload:
    {
        "email": "user@gmail.com",
        "full_name": "User Name",
        "google_id": "google-sub-id",
        "profile_picture": "https://..."
    }
    """

    email = serializers.EmailField()
    full_name = serializers.CharField(required=False, allow_blank=True)
    google_id = serializers.CharField()
    profile_picture = serializers.URLField(required=False, allow_blank=True)

    def validate_email(self, value):
        return value.lower().strip()

    def validate_google_id(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Google ID is required.")

        return value

    def create_or_get_user(self):
        email = self.validated_data["email"]
        google_id = self.validated_data["google_id"]
        full_name = self.validated_data.get("full_name") or email.split("@")[0]
        profile_picture = self.validated_data.get("profile_picture") or None

        user = User.objects.filter(email=email).first()

        if user:
            user.auth_provider = "google"
            user.google_id = google_id
            user.is_verified = True

            if full_name:
                user.full_name = full_name

            if profile_picture:
                user.profile_picture = profile_picture

            user.save(
                update_fields=[
                    "auth_provider",
                    "google_id",
                    "is_verified",
                    "full_name",
                    "profile_picture",
                ]
            )

            return user

        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=None,
        )

        user.auth_provider = "google"
        user.google_id = google_id
        user.profile_picture = profile_picture
        user.is_verified = True
        user.save(
            update_fields=[
                "auth_provider",
                "google_id",
                "profile_picture",
                "is_verified",
            ]
        )

        return user