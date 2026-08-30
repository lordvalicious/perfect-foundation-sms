"""Campus-level access control middleware.

This middleware enforces campus isolation at the request level by:
1. Validating that any campus_id in query params/body belongs to the user's allowed campuses
2. Rejecting requests that attempt to access unauthorized campuses
3. Setting the active campus on the request for downstream use
"""

import logging
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from apps.accounts.access import (
    assert_campus_allowed,
    user_allowed_campus_ids,
    is_global,
)

logger = logging.getLogger(__name__)

# Endpoints that should skip campus validation
CAMPUS_VALIDATION_EXEMPT_PATHS = [
    "/api/auth/",
    "/api/schools/",
    "/api/health/",
    "/admin/",
    "/api/auth/google/",
]

# Methods that typically don't modify data
SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


class CampusAccessMiddleware:
    """
    Middleware to enforce campus-level access control.
    
    This runs after ActiveInstitutionMiddleware so request.institution is available.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for exempt paths
        if any(request.path.startswith(path) for path in CAMPUS_VALIDATION_EXEMPT_PATHS):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        # Get user's allowed campus IDs
        allowed_campus_ids = user_allowed_campus_ids(user)

        # If user has no campus access and is not global, they can only see school-wide data
        if not allowed_campus_ids and not is_global(user):
            request.allowed_campus_ids = set()
            request.is_global_user = False
            return self.get_response(request)

        # Check for campus parameter in query params
        campus_param = request.GET.get("campus") or request.GET.get("campus_id")
        if campus_param:
            try:
                campus_id = int(campus_param)
            except (TypeError, ValueError):
                return JsonResponse(
                    {"detail": "Invalid campus ID."},
                    status=400,
                )

            # Validate campus access
            try:
                assert_campus_allowed(user, campus_id)
            except PermissionDenied as e:
                return JsonResponse(
                    {"detail": str(e)},
                    status=403,
                )

        # Check for campus in request body (POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            body_campus = None
            if hasattr(request, "data") and isinstance(request.data, dict):
                body_campus = request.data.get("campus") or request.data.get("campus_id")
            
            if body_campus is not None:
                try:
                    campus_id = int(body_campus)
                except (TypeError, ValueError):
                    return JsonResponse(
                        {"detail": "Invalid campus ID in request body."},
                        status=400,
                    )

                # Validate campus access for write operations
                try:
                    assert_campus_allowed(user, campus_id)
                except PermissionDenied as e:
                    return JsonResponse(
                        {"detail": str(e)},
                        status=403,
                    )

        # Attach campus info to request for downstream use
        request.allowed_campus_ids = allowed_campus_ids
        request.is_global_user = is_global(user)

        return self.get_response(request)


def get_user_campus_from_request(request, user=None):
    """
    Helper to determine the appropriate campus for the current request.
    
    Priority:
    1. Explicit campus parameter in query params
    2. User's primary campus (if only one)
    3. First allowed campus
    """
    if user is None:
        user = request.user

    if not user or not user.is_authenticated:
        return None

    # Check query param first
    campus_param = request.GET.get("campus") or request.GET.get("campus_id")
    if campus_param:
        try:
            return int(campus_param)
        except (TypeError, ValueError):
            pass

    allowed = user_allowed_campus_ids(user)
    
    if not allowed:
        return None

    if len(allowed) == 1:
        return next(iter(allowed))

    # For users with multiple campuses, check if they have a primary
    if hasattr(user, "staff_profile") and user.staff_profile and user.staff_profile.primary_campus_id:
        if user.staff_profile.primary_campus_id in allowed:
            return user.staff_profile.primary_campus_id

    if hasattr(user, "teacher_profile") and user.teacher_profile and user.teacher_profile.primary_campus_id:
        if user.teacher_profile.primary_campus_id in allowed:
            return user.teacher_profile.primary_campus_id

    if hasattr(user, "student_profile") and user.student_profile and user.student_profile.primary_campus_id:
        if user.student_profile.primary_campus_id in allowed:
            return user.student_profile.primary_campus_id

    return next(iter(allowed))