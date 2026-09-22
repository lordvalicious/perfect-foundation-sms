import os
import sys

# Set DATABASE_URL before anything else - this contains the password
os.environ['DATABASE_URL'] = 'postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Set the settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

# Add the backend directory to path
sys.path.insert(0, '.')

import django
django.setup()

from django.db import connection, connection as django_connection
from django.conf import settings

print("=" * 60)
print("PRODUCTION DATABASE CONNECTION")
print("=" * 60)
print(f"ENGINE: {settings.DATABASES['default']['ENGINE']}")
print(f"NAME: {settings.DATABASES['default']['NAME']}")
print(f"HOST: {settings.DATABASES['default']['HOST']}")
print(f"USER: {settings.DATABASES['default']['USER']}")
print()

# Now let's verify we can query
with django_connection.cursor() as cursor:
    cursor.execute("SELECT 1 as test")
    result = cursor.fetchone()
    print(f"Database query result: {result}")
    print("Database connection VERIFIED!")
print()

# Now let's work with the models
from apps.schools.models import School, Campus
from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from django.db.models import Count

print("=" * 60)
print("PRODUCTION DATA INVENTORY")
print("=" * 60)

# Check institutions
print("\n--- Active Schools ---")
schools = School.objects.filter(status="active")
for s in schools:
    print(f"  School ID {s.id}: {s.name} (code: {s.code}, type: {s.institution_type}, active: {s.status})")

# Check campuses
print("\n--- Active Campuses ---")
campuses = Campus.objects.filter(status="active")
for c in campuses:
    print(f"  Campus ID {c.id}: {c.name} (school_id: {c.school_id})")

# Check if finance-certification-accountant already exists
print("\n--- Checking for existing test account ---")
try:
    existing = User.objects.get(username="finance-certification-accountant")
    print(f"  User 'finance-certification-accountant' already exists: ID={existing.id}, is_active={existing.is_active}")
    print(f"  Username: {existing.username}, email: {existing.email}")
    print(f"  is_superuser: {existing.is_superuser}, is_staff: {existing.is_staff}")
except User.DoesNotExist:
    print("  User 'finance-certification-accountant' does NOT exist - safe to create")

# Check role assignments
print("\n--- Role Assignments Summary ---")
role_assignments = RoleAssignment.objects.values('role').annotate(count=Count('role'))
for ra in role_assignments:
    role_name = dict(Role.choices).get(ra['role'], ra['role'])
    print(f"  Role {ra['role']} ({role_name}): {ra['count']} assignments")

# Check institution 1 details
print("\n--- Institution 1 Details ---")
inst1 = School.objects.filter(id=1).first()
if inst1:
    print(f"  School ID 1: {inst1.name} (code: {inst1.code}, type: {inst1.institution_type})")
    # Check memberships in institution 1
    memberships = InstitutionMembership.objects.filter(institution_id=1)
    print(f"  Memberships in institution 1: {memberships.count()}")
    for m in memberships[:3]:
        print(f"    Membership: {m.user.username} @ {m.institution.name}, status: {m.status}, roles: {list(m.role_assignments.values_list('role', flat=True))}")
else:
    print("  School ID 1 does NOT exist")

# Check staff profiles
print("\n--- Staff Profiles ---")
staff_profiles = StaffProfile.objects.filter(status="active")
print(f"  Active staff profiles: {staff_profiles.count()}")
for sp in staff_profiles[:3]:
    print(f"  Staff {sp.employee_number}: {sp.full_name}, institution: {sp.institution}, campus: {sp.primary_campus}, user: {sp.user.username if sp.user else 'None'}")

print("\n" + "=" * 60)
print("PRODUCTION DATA INVENTORY COMPLETE")
print("=" * 60)