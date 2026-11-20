from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Members can read a project. Only the owner can change it."""

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.owner_id == request.user.id
