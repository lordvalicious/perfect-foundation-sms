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

        return Response(
            {
                "id": school.id,
                "name": school.name,
                "code": school.code,
                "detail": "Tenant created.",
            },
            status=201,
        )


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

        school.save()

        return Response({
            "id": school.id,
            "status": school.status,
            "enabled_modules": school.enabled_modules or [],
            "updated": sorted(changes.keys()),
        })


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
