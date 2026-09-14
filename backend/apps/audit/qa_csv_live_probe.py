import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection
from apps.schools.models import School

User = get_user_model()


def main():
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM django_migrations")
        print("MIGRATIONS_COUNT:", cur.fetchone()[0])

    school, _ = School.objects.get_or_create(
        code="QA-CSV-LIVE-4",
        defaults={"name": "QA CSV Live 4", "is_active": True},
    )
    user, _ = User.objects.get_or_create(
        username="csv_live_dev2d",
        defaults={"is_superuser": True, "is_staff": True, "is_active": True},
    )

    client = Client()
    client.force_login(user)
    sess = client.session
    sess["active_institution_id"] = str(school.id)
    sess.save()

    try:
        resp = client.get("/api/audit/", {"format": "csv"})
        print("STATUS:", resp.status_code)
        print("CONTENT_TYPE:", resp.get("Content-Type"))
        body = resp.content
        print("BODY_BYTES:", len(body))
        text = body.decode("utf-8", "replace")
        print("BODY_HEAD:", text[:200].replace("\r\n", "\\r\\n").replace("\n", "\\n")[:200])
        if resp.status_code == 200 and "text/csv" in (resp.get("Content-Type") or "").lower():
            lines = text.splitlines()
            print("CSV_HEADER:", lines[0] if lines else "(empty)")
            print("CSV_ROW_COUNT:", max(len(lines) - 1, 0))
            rows = lines[1:] if len(lines) > 1 else []
            ok = all(school.code in row for row in rows) if rows else True
            print("CSV_TENANT_SCOPE_OK:", ok)
        else:
            print("CSV_NON_200_OR_NON_CSV: TRUE")
    except Exception:
        import traceback

        print("=== SERVER-SIDE EXCEPTION (re-raised by request client) ===")
        traceback.print_exc()


if __name__ == "__main__":
    main()
