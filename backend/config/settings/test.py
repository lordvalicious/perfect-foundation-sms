"""Test settings that use SQLite so tests run without PostgreSQL."""
from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable throttling for tests to avoid rate-limit interference
REST_FRAMEWORK = REST_FRAMEWORK.copy()
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
