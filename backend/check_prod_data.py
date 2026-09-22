import os
import sys

os.environ['DATABASE_URL'] = 'postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from django.conf import settings
from apps.schools.models import School, Campus
from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role

print("=== Checking institutions ===")
schools = School.objects.filter(status="active")
print(f"Active schools: {schools.count()}")
for s in schools:
    print(f"  School ID {s.id}: {s.name} (code: {s.code}, type: {s.institution_type})")

print("\n=== Checking campuses ===")
campuses = Campus.objects.filter(status="active")
print(f"Active campuses: {campuses.count()}")
for c in campuses:
    print(f"  Campus ID {c.id}: {c.name} (school_id: {c.school_id})")

print("\n=== Checking existing users ===")
# Check if finance-certification-accountant already exists
try:
    user = User.objects.get(username="finance-certification-accountant")
    print(f"User 'finance-certification-accountant' already exists: ID={user.id}, is_active={user.is_active}")
except User.DoesNotExist:
    print("User 'finance-certification-accountant' does NOT exist")

# Check existing staff profiles with institution 1
print("\n=== Staff profiles with institution 1 ===")
staff_with_inst1 = User.objects.filter(institution_id=1, is_staff=True)
print(f"Staff users with institution=1: {staff_with_inst1.count()}")
for u in staff_with_inst1[:5]:
    print(f"  User {u.id}: {u.username}, is_superuser={u.is_superuser}")

# Check role assignments
print("\n=== Role assignments ===")
from django.db.models import Count
role_assignments = RoleAssignment.objects.values('role').annotate(count=Count('role'))
for ra in role_assignments:
    print(f"  Role {ra['role']}: {ra['count']} assignments")