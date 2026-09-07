"""Platform administration: manage schools/tenants and their modules."""

from django.db.models import Count, Q
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Campus, School, SchoolSettings
from .modules import ALL_MODULES


class IsPlatformAdmin(BasePermission):
    """Platform layer = superuser OR the super_admin role."""

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        return user.is_superuser or user.has_any_role(["super_admin"])


def _school_stats(school):
    from apps.students.models import Student

    return {
        "campuses": Campus.objects.filter(school=school).count(),
        "students": Student.objects.filter(
            enrollments__campus__school=school,
            enrollments__status="active",
        ).distinct().count(),
    }


class TenantListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        rows = []

        for school in School.objects.all().order_by("name"):
            stats = _school_stats(school)

            rows.append({
                "id": school.id,
                "name": school.name,
                "code": school.code,
                "status": school.status,
                "is_paused": school.is_paused,
                "paused_at": (
                    school.paused_at.isoformat()
                    if school.paused_at else None
                ),
                "paused_by": (
                    school.paused_by.username
                    if school.paused_by_id else None
                ),
                "city": school.city,
                "enabled_modules": school.enabled_modules or [],
                "stats": stats,
                "created_at": school.created_at.isoformat(),
            })

        return Response({
            "all_modules": ALL_MODULES,
            "tenants": rows,
        })

    def post(self, request):
        name = (request.data.get("name") or "").strip()

        if not name:
            return Response(
                {"detail": "name is required."}, status=400
            )

        code = (request.data.get("code") or "").strip() or None
        enabled = request.data.get("enabled_modules")

        if enabled is not None and not isinstance(enabled, list):
            return Response(
                {"detail": "enabled_modules must be a list."}, status=400
            )

        invalid = [
            m for m in (enabled or [])
            if m not in ALL_MODULES
        ]

        if invalid:
            return Response(
                {"detail": f"Unknown modules: {', '.join(invalid)}"},
                status=400,
            )

        school = School.objects.create(
            name=name,
            code=code,
            status="active",
            city=(request.data.get("city") or "").strip(),
            enabled_modules=enabled or [],
        )

        SchoolSettings.objects.get_or_create(school=school)

        campus_name = (request.data.get("first_campus") or "").strip()

        if campus_name:
            from .models import Campus

            Campus.objects.create(
                school=school,
                name=campus_name,
                status="active",
            )

        # Create school admin if admin data provided
        admin_data = request.data.get("admin")
        if admin_data:
            admin_user, admin_password = self._create_school_admin(school, admin_data)
            if admin_user:
                return Response(
                    {
                        "id": school.id,
                        "name": school.name,
                        "code": school.code,
                        "detail": "Tenant created with admin user.",
                        "admin": {
                            "id": admin_user.id,
                            "username": admin_user.username,
                            "email": admin_user.email,
                            "password": admin_password,
                        },
                    },
                    status=201,
                )

        return Response(
            {
                "id": school.id,
                "name": school.name,
                "code": school.code,
                "detail": "Tenant created.",
            },
            status=201,
        )

    def _create_school_admin(self, school, admin_data):
        """Create a user account and assign ADMIN role linked to the school."""
        from django.db import transaction
        from django.db.utils import IntegrityError
        from rest_framework.exceptions import ValidationError
        from apps.accounts.services import create_user_with_username
        from apps.accounts.models import Role, InstitutionMembership, RoleAssignment

        username = (admin_data.get("username") or "").strip()
        email = (admin_data.get("email") or "").strip()
        password = admin_data.get("password") or ""
        first_name = (admin_data.get("first_name") or "").strip()
        last_name = (admin_data.get("last_name") or "").strip()
        phone = (admin_data.get("phone") or "").strip()

        if not username or not email or not password:
            return None, None

        try:
            with transaction.atomic():
                user, generated_username, generated_password = create_user_with_username(
                    base=username,
                    institution=school,
                    email=email,
                    password=password,
                    first_name=first_name or "School",
                    last_name=last_name or school.name,
                    must_change_password=False,
                )
                if phone:
                    user.phone = phone
                    user.save(update_fields=["phone"])

                membership, _ = InstitutionMembership.objects.get_or_create(
                    user=user,
                    institution=school,
                    defaults={"status": "active"},
                )
                RoleAssignment.objects.get_or_create(
                    membership=membership,
                    role=Role.ADMIN,
                )

                return user, generated_password
        except IntegrityError:
            return None, None


class TenantDetailView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get_object(self, pk):
        return School.objects.filter(pk=pk).first()

    def patch(self, request, pk):
        school = self.get_object(pk)

        if school is None:
            return Response({"detail": "Not found."}, status=404)

        changes = {}

        for field in ("name", "city", "status"):
            value = request.data.get(field)

            if value is not None:
                setattr(school, field, str(value).strip())
                changes[field] = True

        if "is_paused" in request.data:
            paused = bool(request.data.get("is_paused"))

            if paused:
                school.pause(request.user)
            else:
                school.activate()
            changes["is_paused"] = True

        if "code" in request.data:
            school.code = (
                request.data.get("code") or ""
            ).strip() or None
            changes["code"] = True

        if "enabled_modules" in request.data:
            enabled = request.data.get("enabled_modules")

            if not isinstance(enabled, list):
                return Response(
                    {"detail": "enabled_modules must be a list."},
                    status=400,
                )

            invalid = [m for m in enabled if m not in ALL_MODULES]

            if invalid:
                return Response(
                    {"detail": f"Unknown modules: {', '.join(invalid)}"},
                    status=400,
                )

            school.enabled_modules = enabled
            changes["enabled_modules"] = True

        # Create admin user if admin data provided
        admin_data = request.data.get("admin")
        admin_created = None
        if admin_data:
            admin_user, admin_password = self._create_school_admin(school, admin_data)
            if admin_user:
                admin_created = {
                    "id": admin_user.id,
                    "username": admin_user.username,
                    "email": admin_user.email,
                    "password": admin_password,
                }
                changes["admin_created"] = True

        school.save()

        response = {
            "id": school.id,
            "status": school.status,
            "enabled_modules": school.enabled_modules or [],
            "updated": sorted(changes.keys()),
        }

        if admin_created:
            response["admin"] = admin_created

        return Response(response)


class CurrentModulesView(APIView):
    """GET /api/schools/modules/current/

    Tells the frontend which modules are on for the caller's active
    institution, plus whether they are a platform admin.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        institution = getattr(request, "institution", None)
        is_platform = bool(user.is_superuser or user.has_any_role(["super_admin"]))

        enabled = list(institution.enabled_modules) if (
            institution is not None and institution.enabled_modules
        ) else []

        if not enabled:
            enabled = list(ALL_MODULES)

        return Response({
            "is_platform_admin": is_platform,
            "all_modules": ALL_MODULES,
            "enabled": enabled,
            "school_status": (
                institution.status if institution else "active"
            ),
        })
