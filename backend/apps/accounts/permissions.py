from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedReadOnly(BasePermission):
    """Allow any authenticated user to read, admins to write."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.has_any_role(
            ["super_admin", "admin", "principal", "academic"]
        )


class HasRole(BasePermission):
    """Require one of the given roles in any active membership."""

    roles = []

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(self.roles)


class IsAdminOrReadOnly(BasePermission):
    """Authenticated read access; write requires admin-level role."""

    admin_roles = ["super_admin", "admin", "principal", "academic"]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.has_any_role(self.admin_roles)


class IsAdminRole(BasePermission):
    roles = ["super_admin", "admin", "principal"]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(self.roles)


class IsAccountantRole(BasePermission):
    roles = ["super_admin", "admin", "principal", "accountant"]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(self.roles)


class IsTeacherRole(BasePermission):
    roles = ["super_admin", "admin", "principal", "academic", "teacher"]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(self.roles)


class IsStaffRole(BasePermission):
    roles = [
        "super_admin",
        "admin",
        "principal",
        "academic",
        "teacher",
        "staff",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(self.roles)
