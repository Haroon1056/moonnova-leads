from rest_framework.permissions import BasePermission


class IsSearchOwner(BasePermission):
    """
    Allow access only to the owner of the search.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsAuthenticatedUser(BasePermission):
    """
    Allow only logged-in users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
class CanModifyRunningSearch(BasePermission):
    """
    Allow modifications only if search is not completed or cancelled.
    """

    def has_object_permission(self, request, view, obj):
        return obj.status in ["pending", "running"]