from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.users.models import User


class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and getattr(user, "role", None) in (
            User.Role.OWNER,
            User.Role.ADMIN,
        )


class ReadOnlyOrOwnerAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.role in ("owner", "admin"))
