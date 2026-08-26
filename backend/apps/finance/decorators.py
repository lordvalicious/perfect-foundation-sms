"""Shared view decorators for gateway endpoints."""

from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def require_post_json(view):
    """Like require_POST, but answers JSON so API clients never get HTML.

    Payment-gateway callbacks are POST-only; a stray GET (someone typing
    the URL, a health probe) previously received Django's HTML 405 page.
    """

    @csrf_exempt
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.method != "POST":
            return JsonResponse(
                {"detail": "Method not allowed. Use POST."},
                status=405,
            )
        return view(request, *args, **kwargs)

    return wrapper
