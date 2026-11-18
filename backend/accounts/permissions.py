from rest_framework.permissions import BasePermission


def require_access(code, minimum="view"):
    class RoleAccess(BasePermission):
        message = "No tienes permiso para esta acción."

        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.has_access(code, minimum))

    RoleAccess.__name__ = f"Access_{code}_{minimum}"
    return RoleAccess
