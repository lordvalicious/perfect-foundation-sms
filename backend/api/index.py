"""
Vercel serverless entry for the Perfect Foundation Django backend.

Vercel's Python runtime imports this module, loads ``asgi`` (and ``handler``
as a fallback) and routes every request to Django. Static files are handled
by WhiteNoise inside the Django WSGI/ASGI stack, so ``/api/*``, ``/admin/*``,
``/media/*`` and ``/static/*`` all resolve here.
"""
import os
from pathlib import Path

# Ensure the backend directory is importable and Django uses production
# settings while running on Vercel.
BASE = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
os.environ.setdefault("PYTHONPATH", str(BASE))

# Keep a single settings resolution for both local and Vercel runtimes.
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", ".vercel.app,localhost,127.0.0.1")

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()

# Alias expected by Vercel's Python function runtime.
asgi = application


def handler(event, context):
    """WSGI-style fallback if the runtime resolves ``handler`` instead of
    ``asgi``. Uses the synchronous WSGI app as a compatible entry point."""
    from django.core.wsgi import get_wsgi_application

    return get_wsgi_application()(
        {
            "REQUEST_METHOD": event.get("httpMethod", "GET"),
            "SCRIPT_NAME": "",
            "PATH_INFO": event.get("rawPath", "/"),
            "QUERY_STRING": event.get("rawQueryString", ""),
            "SERVER_NAME": "vercel",
            "SERVER_PORT": "443",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "https",
            "wsgi.input": type("In", (), {"read": lambda self, *a, **k: b""})(),
            "wsgi.errors": type("E", (), {"write": lambda self, *a, **k: None})(),
            "wsgi.multithread": True,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }
    )