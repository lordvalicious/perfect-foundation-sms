#!/usr/bin/env python
import os
import sys
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.config.settings'
import django
django.setup()
from django.conf import settings

print('=== PHASE 18/19 SYSTEM VERIFICATION ===')
print()

# 1. Rate limiting
ir = 'ratelimit' in str(settings.INSTALLED_APPS)
print(f'1. ratelimit in INSTALLED_APPS: {ir}')

# 2. Middleware
mr = 'RatelimitMiddleware' in str(settings.MIDDLEWARE)
print(f'2. RatelimitMiddleware in MIDDLEWARE: {mr}')

# 3. Session HttpOnly
sh = settings.SESSION_COOKIE_HTTPONLY
print(f'3. SESSION_COOKIE_HTTPONLY: {sh}')

# 4. Session Secure in production.py
pw = open(r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\config\settings\production.py').read()
ss = 'DJANGO_SESSION_COOKIE_SECURE' in pw
print(f'4. production.py has DJANGO_SESSION_COOKIE_SECURE: {ss}')

# 5. Throttle rates
tr = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', 'NOT SET')
print(f'5. DEFAULT_THROTTLE_RATES: {tr}')

print()
all_pass = ir and mr and sh and ss
result_str = 'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'
print(f'=== RESULT: {result_str} ===')