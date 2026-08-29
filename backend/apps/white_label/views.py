from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, assert_campus_allowed, get_institution
from apps.accounts.permissions import IsSuperAdmin
from apps.audit.models import record_audit
from apps.schools.models import School

from .models import (
    WhiteLabelBranding,
    SchoolSettings,
    DomainMapping,
    WhiteLabelAuditLog,
)
from .serializers import (
    WhiteLabelBrandingSerializer,
    WhiteLabelBrandingCreateUpdateSerializer,
    SchoolSettingsSerializer,
    SchoolSettingsUpdateSerializer,
    DomainMappingSerializer,
    DomainMappingCreateSerializer,
    WhiteLabelAuditLogSerializer,
    ThemePreviewSerializer,
)


def get_active_school(request):
    """Get the active school/institution from the request."""
    institution = get_institution(request)
    if institution is not None:
        return institution
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return getattr(user, "primary_institution", None)
    return None


class WhiteLabelBrandingView(APIView):
    """Get and update white-label branding for the active institution."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get branding configuration for the active institution."""
        school = get_active_school(request)
        if not school:
            return Response(
                {"detail": "No active institution found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        branding, created = WhiteLabelBranding.objects.get_or_create(
            school=school,
            defaults={"created_by": request.user},
        )

        serializer = WhiteLabelBrandingSerializer(branding)
        return Response(serializer.data)

    @transaction.atomic
    def put(self, request):
        """Update branding configuration (Super Admin only)."""
        if not (request.user.is_superuser or request.user.is_staff):
            raise PermissionDenied("Only administrators can update branding.")

        school = get_active_school(request)
        if not school:
            return Response(
                {"detail": "No active institution found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        branding = WhiteLabelBranding.objects.filter(school=school).first()
        if not branding:
            return Response(
                {"detail": "Branding configuration not found. Create first via POST."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WhiteLabelBrandingCreateUpdateSerializer(
            branding, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        old_data = WhiteLabelBrandingSerializer(branding).data
        branding = serializer.save(updated_by=request.user)

        # Audit log
        new_data = WhiteLabelBrandingSerializer(branding).data
        record_audit(
            request=request,
            action="update",
            model_name="WhiteLabelBranding",
            object_id=str(branding.id),
            object_repr=str(branding),
            details={"changes": {"old": old_data, "new": new_data}},
        )

        return Response(WhiteLabelBrandingSerializer(branding).data)

    @transaction.atomic
    def post(self, request):
        """Create initial branding configuration (Super Admin only)."""
        if not (request.user.is_superuser or request.user.is_staff):
            raise PermissionDenied("Only administrators can create branding.")

        school = get_active_school(request)
        if not school:
            return Response(
                {"detail": "No active institution found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if WhiteLabelBranding.objects.filter(school=school).exists():
            return Response(
                {"detail": "Branding already exists. Use PUT to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WhiteLabelBrandingCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branding = serializer.save(school=school, created_by=request.user, updated_by=request.user)

        record_audit(
            request=request,
            action="create",
            model_name="WhiteLabelBranding",
            object_id=str(branding.id),
            object_repr=str(branding),
            details={"branding": WhiteLabelBrandingSerializer(branding).data},
        )

        return Response(
            WhiteLabelBrandingSerializer(branding).data,
            status=status.HTTP_201_CREATED,
        )


class ThemePreviewView(APIView):
    """Lightweight theme preview for login page preview."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = get_active_school(request)
        if not school:
            return Response(
                {"detail": "No active institution found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        branding = WhiteLabelBranding.objects.filter(school=school).first()
        if not branding:
            # Return default theme
            return Response({
                "css_variables": {
                    "--color-primary": "#2563EB",
                    "--color-secondary": "#0F172A",
                    "--color-accent": "#10B981",
                    "--color-background": "#FFFFFF",
                    "--color-surface": "#F8FAFC",
                    "--color-text-primary": "#0F172A",
                    "--color-text-secondary": "#64748B",
                    "--color-border": "#E2E8F0",
                    "--color-error": "#EF4444",
                    "--color-success": "#10B981",
                    "--color-warning": "#F59E0B",
                    "--font-family": "Inter, system-ui, sans-serif",
                    "--font-family-mono": "JetBrains Mono, monospace",
                    "--font-size-base": "14px",
                    "--font-size-lg": "18px",
                    "--font-size-xl": "24px",
                    "--border-radius-sm": "4px",
                    "--border-radius-md": "8px",
                    "--border-radius-lg": "12px",
                    "--spacing-unit": "4px",
                },
                "logo_url": None,
                "favicon_url": None,
                "login_background_image_url": None,
                "login_title": "Welcome to Your School",
                "login_subtitle": "Sign in to access your account",
                "login_background_color": "#F8FAFC",
            })

        return Response(ThemePreviewSerializer(branding).data)


class SchoolSettingsView(APIView):
    """Get and update school settings for the active institution."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = get_active_school(request)
        if not school:
            return Response(
                {"detail": "No active institution found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={"created_by": request.user},
        )

        serializer = SchoolSettingsSerializer(settings)
        return Response(serializer.data)

    @transaction.atomic
    def put(self, request):
        if not (request.user.is_superuser or request.user.is_staff):
            raise PermissionDenied("Only administrators can update school settings.")

        school = get_active_school(request)
        if not school:
            return Response(
                {"detail": "No active institution found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        settings_obj = SchoolSettings.objects.filter(school=school).first()
        if not settings_obj:
            return Response(
                {"detail": "Settings not found. Create first via POST."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SchoolSettingsUpdateSerializer(
            settings_obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        old_data = SchoolSettingsSerializer(settings_obj).data
        settings_obj = serializer.save(updated_by=request.user)

        record_audit(
            request=request,
            action="update",
            model_name="SchoolSettings",
            object_id=str(settings_obj.id),
            object_repr=str(settings_obj),
            details={"changes": {"old": old_data, "new": SchoolSettingsSerializer(settings_obj).data}},
        )

        return Response(SchoolSettingsSerializer(settings_obj).data)


class DomainMappingListCreateView(generics.ListCreateAPIView):
    """List and create domain mappings for the active institution."""

    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DomainMappingCreateSerializer
        return DomainMappingSerializer

    def get_queryset(self):
        school = get_active_school(self.request)
        if not school:
            return DomainMapping.objects.none()
        return DomainMapping.objects.filter(school=school).select_related("school")

    def perform_create(self, serializer):
        school = get_active_school(self.request)
        if not school:
            raise PermissionDenied("No active institution found.")
        serializer.save(school=school)


class DomainMappingDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = DomainMappingSerializer

    def get_queryset(self):
        school = get_active_school(self.request)
        if not school:
            return DomainMapping.objects.none()
        return DomainMapping.objects.filter(school=school).select_related("school")


class SchoolBrandingPublicView(APIView):
    """Public endpoint to get branding for a school by subdomain (for login page)."""

    permission_classes = []  # Public access
    authentication_classes = []  # No authentication required

    def get(self, request, subdomain):
        """Get public branding for a school by subdomain."""
        try:
            branding = WhiteLabelBranding.objects.select_related("school").get(subdomain=subdomain)
            school = branding.school
        except WhiteLabelBranding.DoesNotExist:
            return Response(
                {"detail": "School not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not branding:
            return Response(
                {"detail": "Branding not configured for this school."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Return only public-safe data
        return Response({
            "school_name": branding.school.name,
            "subdomain": branding.subdomain,
            "colors": {
                "primary": branding.primary_color,
                "secondary": branding.secondary_color,
                "accent": branding.accent_color,
                "background": branding.background_color,
                "surface": branding.surface_color,
                "text_primary": branding.text_primary,
                "text_secondary": branding.text_secondary,
                "border": branding.border_color,
                "error": branding.error_color,
                "success": branding.success_color,
                "warning": branding.warning_color,
            },
            "typography": {
                "font_family": branding.font_family,
                "font_family_mono": branding.font_family_mono,
                "font_size_base": branding.font_size_base,
                "font_size_lg": branding.font_size_lg,
                "font_size_xl": branding.font_size_xl,
            },
            "border_radius": {
                "sm": branding.border_radius_sm,
                "md": branding.border_radius_md,
                "lg": branding.border_radius_lg,
            },
            "spacing_unit": branding.spacing_unit,
            "logo_url": branding.logo.url if branding.logo else None,
            "logo_dark_url": branding.logo_dark.url if branding.logo_dark else None,
            "favicon_url": branding.favicon.url if branding.favicon else None,
            "login": {
                "background_image_url": branding.login_background_image.url if branding.login_background_image else None,
                "background_color": branding.login_background_color,
                "title": branding.login_title,
                "subtitle": branding.login_subtitle,
                "show_powered_by": branding.login_show_powered_by,
                "custom_css": branding.login_custom_css,
            },
            "favicon_url": branding.favicon.url if branding.favicon else None,
        }
        )

class WhiteLabelAuditLogView(generics.ListAPIView):
    """Audit log for white-label configuration changes."""

    permission_classes = [IsSuperAdmin]
    serializer_class = WhiteLabelAuditLogSerializer

    def get_queryset(self):
        school = get_active_school(self.request)
        if not school:
            return WhiteLabelAuditLog.objects.none()
        return WhiteLabelAuditLog.objects.filter(school=school).select_related("user")


class WhiteLabelAuditLogDetailView(generics.RetrieveAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = WhiteLabelAuditLogSerializer

    def get_queryset(self):
        school = get_active_school(self.request)
        if not school:
            return WhiteLabelAuditLog.objects.none()
        return WhiteLabelAuditLog.objects.filter(school=school).select_related("user")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def branding_css_variables(request):
    """Get CSS variables for the active institution's theme."""
    school = get_active_school(request)
    if not school:
        return Response(
            {"detail": "No active institution found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    branding = WhiteLabelBranding.objects.filter(school=school).first()
    if not branding:
        return Response(
            {"detail": "Branding not configured."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({"css_variables": branding.css_variables})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def school_branding_config(request):
    """Get full branding config for the active institution (for frontend theme initialization)."""
    school = get_active_school(request)
    if not school:
        return Response(
            {"detail": "No active institution found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    branding = WhiteLabelBranding.objects.filter(school=school).first()
    if not branding:
        return Response(
            {"detail": "Branding not configured."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(branding.to_dict())