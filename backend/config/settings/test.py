"""Test settings that use SQLite so tests run without PostgreSQL."""
from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Ensure project-level templates are discoverable in tests (e.g., backend/templates/reports/print.html)
TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]

# Disable throttling for tests to avoid rate-limit interference
REST_FRAMEWORK = REST_FRAMEWORK.copy()
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000000/min",
    "user": "1000000/day",
    "login": "1000000/hour",
    "password_reset": "1000000/hour",
    "public_apply": "1000000/hour",
    "email_verify": "1000000/hour",
    "transfer_certificate_verify": "1000000/hour",
    "twofa_backup_verify": "1000000/hour",
    "run_migrations": "1000000/hour",  # F14: same-scope throttle target for the bearer-protected migration endpoint (mirrors transfer_certificate_verify / twofa_backup_verify)
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
