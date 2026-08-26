from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedReadOnly(BasePermission):
    """Allow any authenticated user to read, admins to write."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.has_any_role(
            [
                "super_admin",
                "admin",
                "principal",
                "vice_principal",
                "campus_admin",
                "academic",
            ],
            institution=getattr(request, "institution", None),
        )


class HasRole(BasePermission):
    """Require one of the given roles in any active membership."""

    roles = []

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class HasActiveInstitution(BasePermission):
    """Require a verified active membership in the selected institution."""

    message = "Select an active institution before accessing this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request, "institution_membership", None)
        )


class IsAdminOrReadOnly(BasePermission):
    """Authenticated read access; write requires admin-level role."""

    admin_roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.has_any_role(
            self.admin_roles,
            institution=getattr(request, "institution", None),
        )


class IsAdminRole(BasePermission):
    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsAccountantRole(BasePermission):
    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "accountant",
        "hr",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsTeacherRole(BasePermission):
    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "teacher",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsLibrarianRole(BasePermission):
    """
    Librarians and teachers who can manage library resources.
    """
    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "librarian",
        "teacher",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsStaffRole(BasePermission):
    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "accountant",
        "hr",
        "receptionist",
        "teacher",
        "staff",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsAcademicMemberRole(BasePermission):
    """
    Any authenticated member of the school (staff, teacher,
    accountant, parent, student, ...). Intended only for views that
    apply their own scoping and never allow cross-record writes.
    """

    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "accountant",
        "hr",
        "receptionist",
        "teacher",
        "staff",
        "parent",
        "student",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsFinanceReaderRole(BasePermission):
    """
    Finance records are read by the accounts team and, scoped to
    their own records, by parents and students. Teachers, staff and
    receptionists are deliberately excluded.
    """

    roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "accountant",
        "hr",
        "parent",
        "student",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return request.user.has_any_role(
            self.roles,
            institution=getattr(request, "institution", None),
        )


class IsAnnouncementRole(BasePermission):
    """
    Announcements are readable by every active member of the school
    (scoped by the view), but only managers/accounts staff may create,
    edit or delete them.
    """

    read_roles = IsAcademicMemberRole.roles
    write_roles = [
        "super_admin",
        "admin",
        "principal",
        "vice_principal",
        "campus_admin",
        "academic",
        "accountant",
        "hr",
    ]

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        roles = (
            self.read_roles
            if request.method in SAFE_METHODS
            else self.write_roles
        )

        return request.user.has_any_role(
            roles,
            institution=getattr(request, "institution", None),
        )


class IsSuperAdmin(BasePermission):
    """Require super_admin role."""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.has_any_role(
            ["super_admin"],
            institution=getattr(request, "institution", None),
        )
