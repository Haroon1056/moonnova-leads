from rest_framework.permissions import BasePermission


class IsAdminUserOnly(BasePermission):
    """
    Allow only authenticated staff/admin users.

    This protects all admin-dashboard APIs from normal users.
    """

    message = "Only admin or staff users can access this admin dashboard."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_staff or user.is_superuser)
        )