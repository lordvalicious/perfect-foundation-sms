import os
import sys
import json
import django

sys.path.insert(0, r"C:\Users\Ryuk\Documents\perfect-foundation-sms\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ["DB_NAME"] = r"C:\Users\Ryuk\AppData\Local\Temp\opencode\sms_test.db"
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost"

import django

django.setup()

from django.test import Client
from apps.hostel.models import Hostel

client = Client(enforce_csrf_checks=False)
client.post(
    "/api/auth/login/",
    data=json.dumps({"username": "superadmin", "password": "SuperAdmin123!"}),
    content_type="application/json",
)

# Get the hostel
from apps.hostel.models import Hostel
hostels = Hostel.objects.all()
for h in hostels:
    print(f"Hostel {h.id}: {h.name}")

r = client.post(
    "/api/hostel/hostels/1/rooms/",
    data=json.dumps({"room_number": "101", "capacity": 2}),
    content_type="application/json",
)
print("Status:", r.status_code)
print("Content:", r.content[:500])