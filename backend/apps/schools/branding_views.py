"""API views for school branding settings."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole

from .models import School, SchoolSettings


class SchoolBrandingView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def _get_settings(self, request):
        school = getattr(request, "institution", None)
        if not school:
            return None, school
        settings, _ = SchoolSettings.objects.get_or_create(school=school)
        return settings, school

    def get(self, request):
        settings, school = self._get_settings(request)
        if not settings:
            return Response({"detail": "No school configured."}, status=status.HTTP_404_NOT_FOUND)

        request_build = request.build_absolute_uri if hasattr(request, "build_absolute_uri") else None

        logo_url = None
        if settings.logo:
            logo_url = request.build_absolute_uri(settings.logo.url) if request_build else settings.logo.url

        favicon_url = None
        if settings.favicon:
            favicon_url = request.build_absolute_uri(settings.favicon.url) if request_build else settings.favicon.url

        return Response({
            "school_code": school.code,
            "school_name": school.name,
            "motto": settings.motto,
            "logo_url": logo_url,
            "favicon_url": favicon_url,
            "primary_color": settings.primary_color,
            "secondary_color": settings.secondary_color,
            "accent_color": settings.accent_color,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            "contact_website": settings.contact_website,
            "address_line": settings.address_line,
            "footer_text": settings.footer_text,
            "sidebar_color": settings.sidebar_color,
            "header_color": settings.header_color,
        })

    def put(self, request):
        settings, school = self._get_settings(request)
        if not settings:
            return Response({"detail": "No school configured."}, status=status.HTTP_404_NOT_FOUND)

        settings.motto = request.data.get("motto", settings.motto)
        settings.primary_color = request.data.get("primary_color", settings.primary_color)
        settings.secondary_color = request.data.get("secondary_color", settings.secondary_color)
        settings.accent_color = request.data.get("accent_color", settings.accent_color)
        settings.contact_email = request.data.get("contact_email", settings.contact_email)
        settings.contact_phone = request.data.get("contact_phone", settings.contact_phone)
        settings.contact_website = request.data.get("contact_website", settings.contact_website)
        settings.address_line = request.data.get("address_line", settings.address_line)
        settings.footer_text = request.data.get("footer_text", settings.footer_text)
        settings.sidebar_color = request.data.get("sidebar_color", settings.sidebar_color)
        settings.header_color = request.data.get("header_color", settings.header_color)

        if "logo" in request.FILES:
            settings.logo = request.FILES["logo"]
        if "favicon" in request.FILES:
            settings.favicon = request.FILES["favicon"]

        settings.save()

        if "school_name" in request.data and school:
            school.name = request.data["school_name"]
            school.save()

        return Response({"detail": "Branding settings updated."})
