import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import CSRF_COOKIE_SAMESITE, MIDDLEWARE

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a secure value in production."
    )

ALLOWED_HOSTS = [
    host
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "*",
    ).split(",")
    if host
]

# CSRF trusted origins are set in base.py for reliability;
# production.py inherits them from base.py rather than reading from env vars.

SESSION_COOKIE_SECURE = (
    os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "1") == "1"
)
CSRF_COOKIE_SECURE = (
    os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "1") == "1"
)
# The frontend reads the csrf token from document.cookie and sends
# it back as the X-CSRFToken header, so it must not be HttpOnly.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = CSRF_COOKIE_SAMESITE

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

# Set to 0 when testing locally over plain HTTP (no terminating proxy).
SECURE_SSL_REDIRECT = (
    os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
)

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE,
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = os.environ.get(
    "DJANGO_MEDIA_ROOT",
    str(BASE_DIR / "media"),
)

# Transactional email via SMTP (set the DJANGO_EMAIL_* variables).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "1") == "1"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
