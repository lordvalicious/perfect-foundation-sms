"""
Shared Django settings for the School Management System.

All environments import from this module.
"""

import os
import tempfile
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from the backend directory.
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-x=lj&ur9!fz1zx-1#g9ctlw6t!!jie$*s6lzwu=&svrf55q=9g",
)

DEBUG = False

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
).split(",")

INSTALLED_APPS = [
    "apps.accounts",
    "apps.schools",
    "apps.students",
    "apps.teachers",
    "apps.attendance",
    "apps.finance",
    "apps.exams",
    "apps.reportcards",
    "apps.timetable",
    "apps.events",
    "apps.communication",
    "apps.audit",
    "apps.dashboard",

    "apps.library",
    "apps.transport",
    "apps.inventory",
    "apps.payroll",
    "apps.hr",
    "apps.reports",
    "apps.search",
    "apps.documents",
    "apps.discipline",
    "apps.health",
    "apps.alumni",
    "apps.hostel",
    "apps.lms",
    "apps.homework",
    "apps.portal",
    "apps.workflow",
    "apps.white_label",
    "apps.helpdesk",
    "apps.visitors",
    "apps.digital_ids",
    # "django_ratelimit",  # Temporarily disabled - requires Redis for production

    "corsheaders",
    "rest_framework",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
"whitenoise.middleware.WhiteNoiseMiddleware",
    # "ratelimit.middleware.RatelimitMiddleware",  # Temporarily disabled for migrations
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.ActiveInstitutionMiddleware",
    "apps.accounts.campus_middleware.CampusAccessMiddleware",
    "apps.schools.middleware.ModuleAccessMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.LoginAttemptAuditMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
database_url = os.environ.get("DATABASE_URL")

if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get(
                "DB_ENGINE",
                "django.db.backends.postgresql",
            ),
            "NAME": os.environ.get("DB_NAME", "perfect_foundation"),
            "USER": os.environ.get("DB_USER", "school_admin"),
            "PASSWORD": os.environ.get(
                "DB_PASSWORD",
                "school_password",
            ),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = os.environ.get(
    "DJANGO_STATIC_ROOT",
    str(BASE_DIR / "staticfiles"),
)

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = os.environ.get(
    "DJANGO_MEDIA_ROOT",
    str(BASE_DIR / "media"),
)

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.authentication.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "2000/day",
        "login": "60/hour",
        "password_reset": "10/hour",
        "public_apply": "20/hour",
    },
}

CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

CSRF_TRUSTED_ORIGINS = [
    "https://*.vercel.app",
    "https://perfect-foundation-sms.vercel.app",
    "https://perfect-foundation-api.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Cache (for django-ratelimit)
CACHE_DIR = os.environ.get("DJANGO_CACHE_DIR", tempfile.gettempdir())

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(CACHE_DIR, "django_cache"),
    },
    "ratelimit": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(CACHE_DIR, "django_ratelimit_cache"),
    },
}

# Email
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "no-reply@school.local",
)

# Development default: print emails to the console.
# config.settings.production switches to SMTP.
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

# Twilio SMS
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")

# Stripe Online Payments
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
