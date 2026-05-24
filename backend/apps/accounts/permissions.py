# apps/accounts/permissions.py

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Allow access only to the owner of the object.
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsVerifiedUser(BasePermission):
    """
    Allow only verified users (future use: email verification).
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified