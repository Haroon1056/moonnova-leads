from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, email, full_name, password=None, **extra_fields):
        """
        Create normal email/password user or Google user.

        password=None is allowed for Google login users.
        """

        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email).lower().strip()

        if not full_name:
            full_name = email.split("@")[0]

        user = self.model(
            email=email,
            full_name=full_name,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        return user

    def create_superuser(self, email, full_name, password, **extra_fields):
        """
        Create Django admin/superuser.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("auth_provider", "email")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(
            email=email,
            full_name=full_name,
            password=password,
            **extra_fields,
        )

        return user