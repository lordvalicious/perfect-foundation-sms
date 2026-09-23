import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.schools.models import School, Campus

print("=" * 60)
print("PHASE 57 - PRODUCTION DATABASE AUDIT")
print("=" * 60)

# 1. Check Librarian account
print("\n1. LIBRARIAN ACCOUNT (SA-EMP-00011)")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    print(f"  User ID: {librarian.id}")
    print(f"  Username: {librarian.username}")
    print(f"  Email: {librarian.email}")
    print(f"  Name: {librarian.first_name} {librarian.last_name}")
    print(f"  is_active: {librarian.is_active}")
    print(f"  must_change_password: {librarian.must_change_password}")
    print(f"  primary_role: {librarian.primary_role}")
    print(f"  primary_institution: {librarian.primary_institution}")
    
    # Check memberships
    memberships = librarian.get_active_memberships()
    print(f"  Active memberships: {memberships.count()}")
    for m in memberships:
        roles = list(m.role_assignments.values_list('role', flat=True))
        print(f"  - Institution: {m.institution.name} (ID: {m.institution.id})")
        print(f"    Roles: {roles}")
        print(f"    Status: {m.status}")
    
    # Check StaffProfile
    staff_profile = getattr(librarian, 'staff_profile', None)
    if staff_profile:
        print(f"  StaffProfile: {staff_profile.employee_number}")
        print(f"  Designation: {staff_profile.designation}")
        print(f"  Department: {staff_profile.department}")
        print(f"  Primary Campus: {staff_profile.primary_campus}")
        print(f"  Status: {staff_profile.status}")
    else:
        print("  No StaffProfile found")
else:
    print("  Librarian account NOT FOUND")

# 2. Check other test accounts with must_change_password=True
print("\n2. TEST ACCOUNTS WITH must_change_password=True")
print("-" * 40)
test_usernames = [
    "DEG-EMP-00031",  # ACCOUNTANT
    "SA-EMP-00031",   # GUARD
    "SA-EMP-00041",   # ADMIN_OFFICER
    "SA-EMP-00003",   # TEACHER2
    "SA-EMP-00004",   # TEACHER3
    "SA-ST-0002",     # STUDENT2
    "SA-ST-0003",     # STUDENT3
]

for username in test_usernames:
    user = User.objects.filter(username=username).first()
    if user:
        print(f"  {username}: must_change_password={user.must_change_password}, role={user.primary_role}, active={user.is_active}")
    else:
        print(f"  {username}: NOT FOUND")

# 3. Check Librarian role assignment
print("\n3. LIBRARIAN ROLE ASSIGNMENT CHECK")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    memberships = InstitutionMembership.objects.filter(user=librarian, status="active")
    for m in memberships:
        roles = list(m.role_assignments.values_list('role', flat=True))
        print(f"  Membership {m.id}: Institution={m.institution.name}, Roles={roles}")

# 4. Check Role model choices
print("\n4. ROLE MODEL CHOICES")
print("-" * 40)
for role in Role.choices:
    print(f"  {role[0]}: {role[1]}")

# 5. Check Library permissions
print("\n5. LIBRARY PERMISSIONS CHECK")
print("-" * 40)
from apps.accounts.permissions import IsLibrarianRole
print(f"IsLibrarianRole roles: {IsLibrarianRole.roles}")

# 6. Check Library reports permissions
print("\n6. LIBRARY REPORTS PERMISSIONS")
print("-" * 40)
from apps.reports.library_views import LibraryInventoryReportView
print(f"LibraryInventoryReportView permission_classes: {LibraryInventoryReportView.permission_classes}")

# 7. Check Library URLs
print("\n7. LIBRARY URL ROUTES")
print("-" * 40)
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    if 'library' in str(pattern.pattern):
        print(f"  {pattern.pattern}")

print("\n" + "=" * 60)
print("DATABASE AUDIT COMPLETE")
print("=" * 60)