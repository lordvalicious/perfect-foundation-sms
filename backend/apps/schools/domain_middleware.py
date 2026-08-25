"""Middleware to resolve tenant from request hostname (subdomain or custom domain)."""

from django.http import HttpResponseNotFound
from django.utils.deprecation import MiddlewareMixin

from apps.schools.models import School


class TenantHostMiddleware(MiddlewareMixin):
    """Resolve the active school from the request's hostname.

    Supports:
    - Subdomain pattern: `schoolcode.perfect-foundation-sms.vercel.app`
    - Custom domain: `school.example.com` (requires DNS + Vercel domain config)
    - Fallback: `?school_code=` query parameter (legacy)
    """

    def process_request(self, request):
        host = request.get_host().split(":")[0].lower()
        school_code = None

        # 1) Exact match against registered custom domains
        from apps.schools.models import School
        school = School.objects.filter(
            custom_domain__iexact=host,
            status="active",
        ).first()

        if school:
            request.school_code = school.code
            return None

        # 2) Subdomain pattern: <code>.perfect-foundation-sms.vercel.app
        # or custom domain with prefix
        if host.endswith(".vercel.app"):
            subdomain = host[: -len(".vercel.app")]
            # subdomain is the school code
            school = School.objects.filter(
                code__iexact=host.split(".")[0],
                status="active",
            ).first()
            if school:
                request.school_code = school.code
                return None

        # 3) Fallback: query parameter (existing behaviour)
        code = getattr(request, "GET", {}).get("school_code")
        if code:
            school = School.objects.filter(
                code__iexact=code, status="active"
            ).first()
            if school:
                request.school_code = school.code
                return None

        # No tenant resolved — request.school_code stays None,
        # downstream views handle missing tenant (404 or generic UI)
        return None