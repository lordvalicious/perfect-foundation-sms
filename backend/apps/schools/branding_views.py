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
            "short_name": settings.short_name,
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
            # tenant-level localization/settings
            "currency": school.currency,
            "timezone": school.timezone,
            "date_format": settings.date_format,
            "language": settings.language,
            "working_days": settings.working_days or [
                "mon", "tue", "wed", "thu", "fri",
            ],
            "email_from_name": settings.email_from_name,
            "email_from_address": settings.email_from_address,
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

        # --- tenant-level localization / white-label email ---
        if "short_name" in request.data:
            settings.short_name = (request.data.get("short_name") or "").strip()[:50]

        valid_formats = {choice[0] for choice in SchoolSettings.DATE_FORMAT_CHOICES}

        if "date_format" in request.data:
            value = request.data.get("date_format")

            settings.date_format = value if value in valid_formats else settings.date_format

        valid_languages = {choice[0] for choice in SchoolSettings.LANGUAGE_CHOICES}

        if "language" in request.data:
            value = request.data.get("language")

            settings.language = value if value in valid_languages else settings.language

        working_days = request.data.get("working_days")

        if isinstance(working_days, str):
            import json as _json

            try:
                working_days = _json.loads(working_days)
            except ValueError:
                working_days = None

        if isinstance(working_days, list):
            valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
            cleaned = [str(day).lower()[:3] for day in working_days if str(day).lower()[:3] in valid_days]
            settings.working_days = cleaned

        if "email_from_name" in request.data:
            settings.email_from_name = (
                request.data.get("email_from_name") or ""
            ).strip()[:120]

        if "email_from_address" in request.data:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError

            address = (request.data.get("email_from_address") or "").strip()

            try:
                if address:
                    validate_email(address)

                settings.email_from_address = address
            except DjangoValidationError:
                return Response(
                    {"detail": "email_from_address is not a valid email."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # school-level currency/timezone live on the School row
        if "currency" in request.data and school:
            currency = (request.data.get("currency") or "").strip().upper()

            if 3 <= len(currency) <= 3:
                school.currency = currency
                school.save(update_fields=["currency"])

        if "timezone" in request.data and school:
            timezone_value = (request.data.get("timezone") or "").strip()

            if timezone_value:
                school.timezone = timezone_value
                school.save(update_fields=["timezone"])

        if "logo" in request.FILES:
            settings.logo = request.FILES["logo"]
        if "favicon" in request.FILES:
            settings.favicon = request.FILES["favicon"]

        settings.save()

        if "school_name" in request.data and school:
            school.name = request.data["school_name"]
            school.save()

        return Response({"detail": "Branding settings updated."})
