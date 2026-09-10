"""Platform administration: manage schools/tenants and their modules.

Every tenant write goes through ``provision_school_with_admin`` (accounts
services) so school + settings + admin + membership + role are created inside
ONE transaction — partial provisioning can never leak out.
"""

from django.db import transaction
from django.db.models import Count
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
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


def _school_stats_map():
    """Aggregated stats for all schools in 2 queries (no per-school N+1)."""
    from apps.students.models import Student

    campus_counts = dict(
        Campus.objects.values("school_id")
        .annotate(n=Count("id"))
        .values_list("school_id", "n")
    )
    student_counts = dict(
        Student.objects.filter(
            enrollments__status="active",
            enrollments__campus__school__isnull=False,
        )
        .values("enrollments__campus__school_id")
        .annotate(n=Count("id", distinct=True))
        .values_list("enrollments__campus__school_id", "n")
    )
    return campus_counts, student_counts


class TenantListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        campus_counts, student_counts = _school_stats_map()
        rows = []

        for school in School.objects.all().order_by("name"):
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
                "stats": {
                    "campuses": campus_counts.get(school.id, 0),
                    "students": student_counts.get(school.id, 0),
                },
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

        school_data = {
            "name": name,
            "code": (request.data.get("code") or "").strip() or None,
            "city": (request.data.get("city") or "").strip(),
            "institution_type": request.data.get("institution_type") or "school",
            "timezone": request.data.get("timezone") or "UTC",
            "enabled_modules": enabled or [],
            "status": "active",
        }

        campus_name = (request.data.get("first_campus") or "").strip()
        admin_data = request.data.get("admin")

        from apps.accounts.services import provision_school_with_admin
        from apps.audit.models import record_audit

        if admin_data:
            try:
                school, admin_user, admin_username, password = (
                    provision_school_with_admin(school_data, admin_data)
                )
            except (IntegrityError, RuntimeError, DjangoValidationError) as exc:
                record_audit(
                    request=request,
                    action="school_create_failed",
                    model_name="School",
                    object_repr=name,
                    details={"reason": "Admin provisioning failed; school rolled back."},
                )
                message = getattr(exc, "messages", [str(exc)])
                return Response(
                    {
                        "detail": (
                            "School creation rolled back: the admin account "
                            "could not be provisioned. Check that the "
                            "email/username is available and the password is "
                            "valid, then retry."
                        ),
                        "errors": message if not isinstance(message, str) else None,
                    },
                    status=400,
                )
            if campus_name:
                Campus.objects.create(
                    school=school, name=campus_name, status="active"
                )
            record_audit(
                request=request,
                action="school_create",
                model_name="School",
                object_id=str(school.pk),
                object_repr=school.name,
                details={"school_code": school.code},
            )
            return Response(
                {
                    "id": school.id,
                    "name": school.name,
                    "code": school.code,
                    "detail": "Tenant created with admin user.",
                    "admin": {
                        "id": admin_user.id,
                        "username": admin_username,
                        "email": admin_user.email,
                        "password": password,
                    },
                    "stats": {
                        "campuses": Campus.objects.filter(school=school).count(),
                        "students": 0,
                    },
                },
                status=201,
            )

        # No admin requested: create school + settings + optional first campus
        # atomically (no admin user to provision).
        try:
            with transaction.atomic():
                school = School.objects.create(**school_data)
                SchoolSettings.objects.get_or_create(school=school)
                if campus_name:
                    Campus.objects.create(
                        school=school, name=campus_name, status="active"
                    )
        except IntegrityError as exc:
            return Response(
                {"detail": f"Could not create tenant: {exc}"}, status=400
            )

        record_audit(
            request=request,
            action="school_create",
            model_name="School",
            object_id=str(school.pk),
            object_repr=school.name,
            details={"school_code": school.code},
        )

        return Response(
            {
                "id": school.id,
                "name": school.name,
                "code": school.code,
                "detail": "Tenant created.",
                "stats": {
                    "campuses": Campus.objects.filter(school=school).count(),
                    "students": 0,
                },
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
        pending_pause = None

        for field in ("name", "city", "status"):
            value = request.data.get(field)

            if value is not None:
                setattr(school, field, str(value).strip())
                changes[field] = True

        if "is_paused" in request.data:
            raw = request.data.get("is_paused")
            if isinstance(raw, str):
                paused = raw.strip().lower() in ("1", "true", "yes", "on")
            else:
                paused = bool(raw)
            changes["is_paused"] = True
            # Applied below, only after admin provisioning succeeds, so a
            # failed admin payload never persists a partial edit.
            pending_pause = paused

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

        # Create admin user if admin data provided (transactional, so a bad
        # admin payload never leaves an orphaned/partially-edited school).
        admin_data = request.data.get("admin")
        admin_created = None
        if admin_data:
            from apps.accounts.models import InstitutionMembership, Role, RoleAssignment
            from apps.accounts.services import create_user_with_username

            try:
                with transaction.atomic():
                    base_username = (
                        (admin_data.get("username") or "").strip()
                        or f"admin-{school.code.lower()}"
                    )
                    admin_user, admin_username, password = create_user_with_username(
                        base=base_username,
                        institution=school,
                        email=admin_data.get("email") or None,
                        password=admin_data.get("password") or None,
                        first_name=(admin_data.get("first_name") or "School"),
                        last_name=(admin_data.get("last_name") or school.name),
                    )
                    if admin_data.get("phone"):
                        admin_user.phone = admin_data["phone"]
                        admin_user.save(update_fields=["phone"])
                    membership, _ = InstitutionMembership.objects.get_or_create(
                        user=admin_user,
                        institution=school,
                        defaults={"status": "active"},
                    )
                    RoleAssignment.objects.get_or_create(
                        membership=membership,
                        role=Role.ADMIN,
                    )
                admin_created = {
                    "id": admin_user.id,
                    "username": admin_username,
                    "email": admin_user.email,
                    "password": password,
                }
                changes["admin_created"] = True
            except (IntegrityError, RuntimeError, DjangoValidationError):
                return Response(
                    {
                        "detail": (
                            "Admin provisioning failed and was rolled back. "
                            "Check email/username availability and password "
                            "strength."
                        )
                    },
                    status=400,
                )

        if pending_pause is not None:
            if pending_pause:
                school.pause(request.user)
            else:
                school.activate()

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