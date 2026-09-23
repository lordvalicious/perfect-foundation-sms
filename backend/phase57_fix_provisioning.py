import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.schools.models import School, Campus

print("=" * 60)
print("PHASE 57 - PROVISIONING REMEDIATION")
print("=" * 60)

# 1. Fix Librarian account
print("\n1. FIXING LIBRARIAN ACCOUNT (SA-EMP-00011)")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    print(f"  Before: role={librarian.primary_role}, must_change_password={librarian.must_change_password}")
    
    # Fix must_change_password
    librarian.must_change_password = False
    librarian.save(update_fields=["must_change_password"])
    print(f"  Fixed: must_change_password = False")
    
    # Fix role assignment
    membership = InstitutionMembership.objects.filter(user=librarian, institution_id=4).first()
    if membership:
        role_assignment = RoleAssignment.objects.filter(membership=membership).first()
        if role_assignment:
            print(f"  Before: role={role_assignment.role}")
            role_assignment.role = Role.LIBRARIAN
            role_assignment.save()
            print(f"  Fixed: role = librarian")
        else:
            RoleAssignment.objects.create(membership=membership, role=Role.LIBRARIAN)
            print(f"  Created new RoleAssignment with role=librarian")
    else:
        print(f"  ERROR: No membership found for institution 4")
    
    # Verify
    librarian.refresh_from_db()
    membership.refresh_from_db()
    roles = list(membership.role_assignments.values_list('role', flat=True))
    print(f"  After: role={librarian.primary_role}, roles={roles}, must_change_password={librarian.must_change_password}")
else:
    print("  ERROR: Librarian account NOT FOUND")

# 2. Fix must_change_password for all test accounts
print("\n2. FIXING must_change_password FOR ALL TEST ACCOUNTS")
print("-" * 40)
test_accounts = [
    ("DEG-EMP-00031", "ACCOUNTANT"),
    ("SA-EMP-00031", "GUARD"),
    ("SA-EMP-00041", "ADMIN_OFFICER"),
    ("SA-ST-0002", "STUDENT2"),
    ("SA-ST-0003", "STUDENT3"),
]

for username, role_name in test_accounts:
    user = User.objects.filter(username=username).first()
    if user:
        if user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
            print(f"  Fixed {username} ({role_name}): must_change_password = False")
        else:
            print(f"  {username} ({role_name}): already must_change_password=False")
    else:
        print(f"  {username} ({role_name}): NOT FOUND")

# Also fix the Librarian's staff profile if needed
print("\n3. VERIFYING LIBRARIAN STAFF PROFILE")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    staff_profile = getattr(librarian, 'staff_profile', None)
    if staff_profile:
        print(f"  StaffProfile: {staff_profile.employee_number}")
        print(f"  Designation: {staff_profile.designation}")
        print(f"  Department: {staff_profile.department}")
        print(f"  Primary Campus: {staff_profile.primary_campus}")
        print(f"  Status: {staff_profile.status}")
    else:
        print("  No StaffProfile found")

# Fix Accountant role (DEG-EMP-00031 shows role=staff but should be accountant)
print("\n4. FIXING ACCOUNTANT ROLE (DEG-EMP-00031)")
print("-" * 40)
accountant = User.objects.filter(username="DEG-EMP-00031").first()
if accountant:
    print(f"  Before: role={accountant.primary_role}, must_change_password={accountant.must_change_password}")
    membership = InstitutionMembership.objects.filter(user=accountant, institution_id=1).first()
    if membership:
        role_assignment = RoleAssignment.objects.filter(membership=membership).first()
        if role_assignment:
            print(f"  Current role: {role_assignment.role}")
            if role_assignment.role != Role.ACCOUNTANT:
                role_assignment.role = Role.ACCOUNTANT
                role_assignment.save()
                print(f"  Fixed: role = accountant")
            else:
                print(f"  Already correct: role = accountant")
        else:
            RoleAssignment.objects.create(membership=membership, role=Role.ACCOUNTANT)
            print(f"  Created new RoleAssignment with role=accountant")
    else:
        print("  No membership found for institution 1")
    accountant.refresh_from_db()
    print(f"  After: role={accountant.primary_role}")

# Fix Guard role (SA-EMP-00031)
print("\n5. FIXING GUARD ROLE (SA-EMP-00031)")
print("-" * 40)
guard = User.objects.filter(username="SA-EMP-00031").first()
if guard:
    print(f"  Before: role={guard.primary_role}")
    membership = InstitutionMembership.objects.filter(user=guard, institution_id=4).first()
    if membership:
        role_assignment = RoleAssignment.objects.filter(membership=membership).first()
        if role_assignment:
            print(f"  Current role: {role_assignment.role}")
            if role_assignment.role != Role.GUARD:
                role_assignment.role = Role.GUARD
                role_assignment.save()
                print(f"  Fixed: role = guard")
            else:
                print(f"  Already correct: role = guard")
        else:
            RoleAssignment.objects.create(membership=membership, role=Role.GUARD)
            print(f"  Created new RoleAssignment with role=guard")
    else:
        print("  No membership found for institution 4")

# Fix Admin Officer role (SA-EMP-00041)
print("\n4. FIXING ADMIN_OFFICER ROLE (SA-EMP-00041)")
print("-" * 40)
admin_officer = User.objects.filter(username="SA-EMP-00041").first()
if admin_officer:
    print(f"  Before: role={admin_officer.primary_role}")
    membership = InstitutionMembership.objects.filter(user=admin_officer, institution_id=4).first()
    if membership:
        role_assignment = RoleAssignment.objects.filter(membership=membership).first()
        if role_assignment:
            print(f"  Current role: {role_assignment.role}")
            if role_assignment.role != Role.STAFF:
                role_assignment.role = Role.STAFF
                role_assignment.save()
                print(f"  Fixed: role = staff")
            else:
                print(f"  Already correct: role = staff")
        else:
            RoleAssignment.objects.create(membership=membership, role=Role.STAFF)
            print(f"  Created new RoleAssignment with role=staff")

# Fix Students
print("\n5. FIXING STUDENT ROLES (SA-ST-0002, SA-ST-0003)")
print("-" * 40)
for username in ["SA-ST-0002", "SA-ST-0003"]:
    student = User.objects.filter(username=username).first()
    if student:
        print(f"  {username}: before role={student.primary_role}")
        membership = InstitutionMembership.objects.filter(user=student, institution_id=4).first()
        if membership:
            role_assignment = RoleAssignment.objects.filter(membership=membership).first()
            if role_assignment and role_assignment.role != Role.STUDENT:
                role_assignment.role = Role.STUDENT
                role_assignment.save()
                print(f"  Fixed {username}: role = student")
            elif not role_assignment:
                RoleAssignment.objects.create(membership=membership, role=Role.STUDENT)
                print(f"  Created RoleAssignment for {username}: role = student")
            else:
                print(f"  {username}: already correct")

# Fix Teacher2 and Teacher3 if they exist
print("\n6. CHECKING TEACHER2/TEACHER3")
print("-" * 40)
for username in ["SA-EMP-00003", "SA-EMP-00004"]:
    teacher = User.objects.filter(username=username).first()
    if teacher:
        print(f"  {username}: found, role={teacher.primary_role}")
        membership = InstitutionMembership.objects.filter(user=teacher, institution_id=4).first()
        if membership:
            role_assignment = RoleAssignment.objects.filter(membership=membership).first()
            if role_assignment and role_assignment.role != Role.TEACHER:
                role_assignment.role = Role.TEACHER
                role_assignment.save()
                print(f"  Fixed {username}: role = teacher")
            elif not role_assignment:
                RoleAssignment.objects.create(membership=membership, role=Role.TEACHER)
                print(f"  Created RoleAssignment for {username}: role = teacher")
            else:
                print(f"  {username}: already correct")
    else:
        print(f"  {username}: NOT FOUND")

print("\n" + "=" * 60)
print("DATABASE REMEDIATION COMPLETE")
print("=" * 60)