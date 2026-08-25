"""Per-school module access enforcement.

Runs after ActiveInstitutionMiddleware so ``request.institution`` is
resolved. Any /api/<module-prefix>/… request whose module is disabled
for the requesting school gets a 403 — regardless of role. Platform
(superuser) accounts bypass, as do anonymous requests (DRF auth still
applies downstream).
"""

from django.http import JsonResponse

from .modules import ALL_MODULES, module_for_path


class ModuleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self._enforce(request)

        if response is not None:
            return response

        return self.get_response(request)

    def _enforce(self, request):
        path = request.path

        if not path.startswith("/api/"):
            return None

        module = module_for_path(path[len("/api/"):])

        if module is None:
            return None  # core SIS surface — always available

        user = getattr(request, "user", None)

        if getattr(user, "is_superuser", False):
            return None

        institution = getattr(request, "institution", None)

        if institution is None:
            return None  # pre-tenant contexts handled by DRF auth

        if institution.status != "active":
            return JsonResponse(
                {"detail": "This school account is inactive."},
                status=403,
            )

        enabled = institution.enabled_modules or []

        if not enabled or module in enabled:
            return None

        return JsonResponse(
            {
                "detail": (
                    f"The '{module}' module is not enabled for your "
                    "school. Contact your platform administrator."
                )
            },
            status=403,
        )
