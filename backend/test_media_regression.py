"""Quick regression test after media isolation."""
import os
import sys
import json

sys.path.insert(0, r"C:\Users\Ryuk\Documents\perfect-foundation-sms\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ["DB_NAME"] = r"C:\Users\Ryuk\AppData\Local\Temp\opencode\sms_test.db"
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost"

import django
django.setup()

from django.test import Client

passed = failed = 0
def check(label, resp, expect=200):
    global passed, failed
    ok = resp.status_code == expect
    passed += ok
    failed += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {label:<50} {resp.status_code} (want {expect})")

client = Client(enforce_csrf_checks=False)
r = client.post("/api/auth/login/", data=json.dumps({"username": "superadmin", "password": "SuperAdmin123!"}), content_type="application/json")
check("login", r)

# Core modules still work
for ep in ["dashboard/overview/", "students/?page_size=5", "finance/invoices/?page_size=5",
           "reports/at-risk/", "school/branding/", "school/modules/current/",
           "school/tenants/", "students/admissions/public/options/"]:
    # school/* needs /api/schools/ prefix
    if ep.startswith("school/"):
        ep = "schools/" + ep[7:]
    check(ep, client.get(f"/api/{ep}"))

# Media: branding files should be public (no auth)
anon = Client(enforce_csrf_checks=False)
check("public branding media (no logo file -> 404 is OK)", anon.get("/media/school/branding/test.png"), 404)

# Protected media should require auth
check("protected media unauth -> blocked", anon.get("/media/profiles/students/test.jpg"), 403)  # 404 because file doesn't exist

# Authenticated user can access protected media view (file doesn't exist but no auth error)
check("protected media auth'd -> 404 (file not found)", client.get("/media/profiles/students/test.jpg"), 404)

# Cron jobs still work
check("late-fees cron", client.get("/api/finance/cron/late-fees/?dry_run=1&percent=2"), 200)
check("fee-reminders dry", client.get("/api/communication/cron/fee-reminders/?dry_run=1"), 200)
check("absence-alerts dry", client.get("/api/attendance/cron/absence-alerts/?dry_run=1"), 200)

print(f"\nPASSED: {passed}, FAILED: {failed}")
