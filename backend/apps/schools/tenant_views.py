from rest_framework.response import Response
from rest_framework.views import APIView

from .models import School, SchoolSettings
from django.http import HttpRequest


class PublicTenantConfigView(APIView):
    """Return only branding needed to render a tenant's login page."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        code = request.query_params.get("school_code", "").strip().lower()

        # 1) Explicit school_code query param
        school = None
        if code:
            school = School.objects.filter(code=code, status="active").first()

        # 2) Fallback: resolve by hostname
        if school is None:
            host = getattr(request, "get_host", lambda: "")().split(":")[0].lower()
            school = School.objects.filter(
                custom_domain__iexact=request.get_host().split(":")[0],
                status="active",
            ).first()

            if not school:
                # subdomain pattern: code.vercel.app
                host = request.get_host().split(":")[0].lower()
                if host.endswith(".vercel.app"):
                    subdomain = host[: -len(".vercel.app")]
                    school = School.objects.filter(
                        code__iexact=host.split(".")[0],
                        status="active",
                    ).first()

        if school is None:
            return Response({"detail": "School not found."}, status=404)

        settings, _ = SchoolSettings.objects.get_or_create(school=school)
        return Response({
            "school_code": school.code,
            "school_name": school.name,
            "short_name": settings.short_name,
            "address": school.address,
            "city": school.city,
            "motto": settings.motto,
            "logo_url": request.build_absolute_uri(settings.logo.url) if settings.logo else None,
            "favicon_url": request.build_absolute_uri(settings.favicon.url) if settings.favicon else None,
            "primary_color": settings.primary_color,
            "second_color": settings.secondary_color,
            "accent_color": settings.accent_color,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            "contact_website": settings.contact_website,
            "short_name": settings.short_name,
            "language": settings.language,
        })