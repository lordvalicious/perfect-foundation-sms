import os
import sys
import django

os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-muddy-bar-az3etcoa-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
sys.path.insert(0, '.')

django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.schools.models import School, Campus

print("=" * 60)
print("PHASE 56B — REMEDIATION")
print("=" * 60)

# 1. Fix Librarian role assignment
print("\n1. Fixing Librarian role assignment...")
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    print(f"   Found Librarian: {librarian.username} (ID: {librarian.id})")
    print(f"   Current must_change_password: {librarian.must_change_password}")
    print(f"   Current primary_role: {librarian.primary_role}")
    
    # Fix must_change_password
    librarian.must_change_password = False
    librarian.save(update_fields=["must_change_password"])
    print(f"   Set must_change_password = False")
    
    # Fix role assignment
    membership = InstitutionMembership.objects.filter(user=librarian, institution_id=4).first()
    if membership:
        print(f"   Found membership: {membership.id} (institution: {membership.institution.name})")
        role_assignment = RoleAssignment.objects.filter(membership=membership).first()
        if role_assignment:
            print(f"   Current role: {role_assignment.role}")
            role_assignment.role = Role.LIBRARIAN
            role_assignment.save()
            print(f"   Updated role to: {role_assignment.role}")
        else:
            # Create role assignment
            RoleAssignment.objects.create(membership=membership, role=Role.LIBRARIAN)
            print(f"   Created new RoleAssignment with role=librarian")
    else:
        print(f"   No membership found for institution 4")
    
    # Check staff profile
    staff_profile = getattr(librarian, 'staff_profile', None)
    if staff_profile:
        print(f"   StaffProfile: {staff_profile.employee_number} - {staff_profile.full_name}")
        print(f"   Designation: {staff_profile.designation}")
        print(f"   Department: {staff_profile.department}")
        print(f"   Primary Campus: {staff_profile.primary_campus}")
    else:
        print(f"   No StaffProfile found")
    
    # Verify
    librarian.refresh_from_db()
    print(f"   Updated must_change_password: {librarian.must_change_password}")
    print(f"   Updated primary_role: {librarian.primary_role}")
else:
    print("   Librarian account not found!")

# 2. Fix must_change_password for other test accounts
print("\n2. Fixing must_change_password for other test accounts...")
test_accounts = [
    "DEG-EMP-00031",  # ACCOUNTANT
    "SA-EMP-00031",   # GUARD
    "SA-EMP-00041",   # ADMIN_OFFICER
    "SA-EMP-00003",   # TEACHER2
    "SA-EMP-00004",   # TEACHER3
    "SA-ST-0002",     # STUDENT2
    "SA-ST-0003",     # STUDENT3
]

for username in test_accounts:
    user = User.objects.filter(username=username).first()
    if user:
        if user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
            print(f"   Fixed {username}: must_change_password = False")
        else:
            print(f"   {username}: already must_change_password=False")
    else:
        print(f"   {username}: not found")

# 3. Verify Librarian account
print("\n3. Verifying Librarian account...")
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    membership = InstitutionMembership.objects.filter(user=librarian).first()
    if membership:
        roles = list(RoleAssignment.objects.filter(membership=membership).values_list("role", flat=True))
        print(f"   Roles: {roles}")
    print(f"   must_change_password: {librarian.must_change_password}")
    print(f"   primary_role: {librarian.primary_role}")
    print(f"   is_active: {librarian.is_active}")

print("\n" + "=" * 60)
print("REMEDIATION COMPLETE")
print("=" * 60)