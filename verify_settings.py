#!/usr/bin/env python
"""Quick settings verification for Phase 19 QA"""
import os
import sys

# Set Django settings module BEFORE importing django
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.config.settings'

import django
django.setup()

from django.conf import settings

print("=" * 60)
print("PHASE 19: SETTINGS VERIFICATION")
print("=" * 60)

print("\n--- Authentication ---")
print(f"  AUTHENTICATION_BACKENDS: {len(settings.AUTHENTICATION_BACKENDS)} backends")
backend_list = list(settings.AUTHENTICATION_BACKENDS)
print(f"  Backends: {backend_list}")

print("\n--- Rate Limiting ---")
print(f"  'ratelimit' in INSTALLED_APPS: {'ratelimit' in str(settings.INSTALLED_APPS)}")
print(f"  'RatelimitMiddleware' in MIDDLEWARE: {'RatelimitMiddleware' in str(settings.MIDDLEWARE)}")
throttle_rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', 'NOT CONFIGURED')
print(f"  DEFAULT_THROTTLE_RATES: {throttle_rates}")

print("\n--- Session Security ---")
print(f"  SESSION_COOKIE_HTTPONLY: {settings.SESSION_COOKIE_HTTPONLY}")
print(f"  SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', 'NOT SET (use DJANGO_SESSION_COOKIE_SECURE env var)')}")

print("\n--- XSS / Templates ---")
tc = getattr(settings, 'TEMPLATES', [{}])[0]
autoescape = tc.get('OPTIONS', {}).get('autoescape', True)
print(f"  Template auto-escape: {'ON' if autoescape else 'OFF'}")

print("\n--- Database ---")
print(f"  DATABASES config: {settings.DATABASES}")

print("\n--- RBAC / Roles ---")
from django.db import connection
try:
    with connection.cursor() as c:
        c.execute("SELECT COUNT(*) FROM django_content_type")
        count = c.fetchone()[0]
    print(f"  Django content types: {count}")
except Exception as e:
    print(f"  Database query error: {e}")

print("\n--- Campus / Org Isolation ---")
try:
    with connection.cursor() as c:
        c.execute("SELECT COUNT(*) FROM students_student WHERE primary_campus IS NOT NULL")
        students_with_campus = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM accounts_institutionmembership")
        memberships = c.fetchone()[0]
    print(f"  Students with campus: {students_with_campus}")
    print(f"  Institution memberships: {memberships}")
except Exception as e:
    print(f"  Database query error: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)