import os
import sys

# Use the production DATABASE_URL that was working earlier
os.environ['DATABASE_URL'] = 'postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from django.conf import settings

print(f"ENGINE: {settings.DATABASES['default']['ENGINE']}")
print(f"NAME: {settings.DATABASES['default']['NAME']}")
print(f"HOST: {settings.DATABASES['default']['HOST']}")
print()

from django.db import connection

# Try to list tables - might fail if no migrations, but let's see
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename LIMIT 20")
        tables = cursor.fetchall()
        print(f"Tables found: {len(tables)}")
        for t in tables:
            print(f"  {t[0]}")
except Exception as e:
    print(f"Error listing tables: {type(e).__name__}: {str(e)[:100]}")
print()

# Try to query existing users - this might work if there's data
try:
    from apps.accounts.models import User
    users = User.objects.all()[:10]
    print(f"Users found: {User.objects.count()}")
    for u in users:
        print(f"  User {u.id}: {u.username}, is_active={u.is_active}, is_staff={u.is_staff}, is_superuser={u.is_superuser}")
        print(f"    primary_role: {u.primary_role}")
        print(f"    institution: {u.primary_institution}")
except Exception as e:
    print(f"Error querying users: {type(e).__name__}: {str(e)[:100]}")
print()

# Try to check role assignments
try:
    from apps.accounts.models import RoleAssignment
    ra_count = RoleAssignment.objects.count()
    print(f"RoleAssignment count: {ra_count}")
    # Show a few
    for ra in RoleAssignment.objects.all()[:5]:
        print(f"  RoleAssignment: membership={ra.membership_id}, role={ra.role}")
except Exception as e:
    print(f"Error querying role assignments: {type(e).__name__}: {str(e)[:100]}")
print()

# Check institutions
try:
    from apps.schools.models import School
    schools = School.objects.all()
    print(f"Schools found: {schools.count()}")
    for s in schools:
        print(f"  School {s.id}: {s.name}, status={s.status}, type={s.institution_type}")
        # Check campuses
        campuses = s.campus_set.filter(status="active")
        print(f"    Campuses: {campuses.count()}")
        for c in campuses:
            print(f"      Campus {c.id}: {c.name}")
except Exception as e:
    print(f"Error querying schools: {type(e).__name__}: {str(e)[:100]}")