from rest_framework.response import Response
from rest_framework.views import APIView

from .models import School, SchoolSettings


class PublicTenantConfigView(APIView):
    """Return only branding needed to render a tenant's login page."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        code = request.query_params.get("school_code", "").strip().lower()
        school = School.objects.filter(code=code, status="active").first()
        if school is None:
            return Response({"detail": "School not found."}, status=404)

        settings, _ = SchoolSettings.objects.get_or_create(school=school)
        return Response({
            "school_code": school.code,
            "school_name": school.name,
            "address": school.address,
            "city": school.city,
            "motto": settings.motto,
            "logo_url": request.build_absolute_uri(settings.logo.url) if settings.logo else None,
            "favicon_url": request.build_absolute_uri(settings.favicon.url) if settings.favicon else None,
            "primary_color": settings.primary_color,
            "secondary_color": settings.secondary_color,
            "accent_color": settings.accent_color,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            "contact_website": settings.contact_website,
        })