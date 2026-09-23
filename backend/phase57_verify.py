import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.schools.models import School, Campus

print("=" * 60)
print("PHASE 57 - VERIFICATION AND ADDITIONAL FIXES")
print("=" * 60)

# 1. Verify Librarian account
print("\n1. VERIFYING LIBRARIAN ACCOUNT")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    membership = InstitutionMembership.objects.filter(user=librarian, institution_id=4).first()
    if membership:
        roles = list(membership.role_assignments.values_list('role', flat=True))
        print(f"  User: {librarian.username}")
        print(f"  primary_role: {librarian.primary_role}")
        print(f"  must_change_password: {librarian.must_change_password}")
        print(f"  Membership roles: {roles}")
        print(f"  Membership institution: {membership.institution.name}")
        staff_profile = getattr(librarian, 'staff_profile', None)
        if staff_profile:
            print(f"  StaffProfile: designation={staff_profile.designation}, dept={staff_profile.department}, campus={staff_profile.primary_campus}")

# 2. Fix Accountant membership
print("\n2. FIXING ACCOUNTANT MEMBERSHIP (DEG-EMP-00031)")
print("-" * 40)
accountant = User.objects.filter(username="DEG-EMP-00031").first()
if accountant:
    print(f"  User: {accountant.username}, ID: {accountant.id}")
    print(f"  primary_role: {accountant.primary_role}")
    print(f"  institution_id: {accountant.institution_id}")
    
    memberships = accountant.get_active_memberships()
    print(f"  Active memberships: {memberships.count()}")
    for m in memberships:
        roles = list(m.role_assignments.values_list('role', flat=True))
        print(f"  Membership: inst={m.institution.name} (ID: {m.institution.id}), roles={roles}")
    
    membership = InstitutionMembership.objects.filter(user=accountant, institution_id=1).first()
    if not membership:
        print("  Creating membership for institution 1 (Default Institution)")
        inst1 = School.objects.filter(id=1).first()
        if inst1:
            membership = InstitutionMembership.objects.create(
                user=accountant,
                institution=inst1,
                status="active"
            )
            print(f"  Created membership: {membership.id}")
    
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
            RoleAssignment.objects.create(membership=membership, role=Role.ACCOUNTANT)
            print(f"  Created RoleAssignment with role=accountant")
    
    accountant.refresh_from_db()
    print(f"  After: primary_role = {accountant.primary_role}")

# 3. Verify all test accounts
print("\n3. VERIFYING ALL TEST ACCOUNTS")
print("-" * 40)
test_accounts = [
    ("SA-EMP-00011", "LIBRARIAN", "librarian"),
    ("DEG-EMP-00031", "ACCOUNTANT", "accountant"),
    ("SA-EMP-00031", "GUARD", "guard"),
    ("SA-EMP-00041", "ADMIN_OFFICER", "staff"),
    ("SA-ST-0002", "STUDENT2", "student"),
    ("SA-ST-0003", "STUDENT3", "student"),
]

for username, expected_role, expected_role_name in test_accounts:
    user = User.objects.filter(username=username).first()
    if user:
        membership = InstitutionMembership.objects.filter(user=user).first()
        roles = list(RoleAssignment.objects.filter(membership=membership).values_list('role', flat=True)) if membership else []
        print(f"  {username}: role={user.primary_role}, expected={expected_role_name}, roles={roles}, must_change_pw={user.must_change_password}, active={user.is_active}")
    else:
        print(f"  {username}: NOT FOUND")

# 4. Fix Library reports permission
print("\n4. FIXING LIBRARY REPORTS PERMISSION")
print("-" * 40)
from apps.reports.library_views import (
    LibraryInventoryReportView, AvailableBooksReportView, IssuedBooksReportView,
    ReturnedBooksReportView, OverdueBooksReportView, LibraryFinesReportView,
    LibraryActivitySummaryReportView, MostBorrowedBooksReportView,
    StudentBorrowingHistoryReportView, TeacherBorrowingHistoryReportView
)

report_views = [
    LibraryInventoryReportView,
    AvailableBooksReportView,
    IssuedBooksReportView,
    ReturnedBooksReportView,
    OverdueBooksReportView,
    LibraryFinesReportView,
    LibraryActivitySummaryReportView,
    MostBorrowedBooksReportView,
    StudentBorrowingHistoryReportView,
    TeacherBorrowingHistoryReportView,
]

for view_class in report_views:
    perms = view_class.permission_classes
    perms_list = list(perms) if hasattr(perms, '__iter__') and not isinstance(perms, str) else [perms]
    perm_names = [str(p) for p in perms_list]
    print(f"  {view_class.__name__}: {perm_names}")
    if not any('IsLibrarianRole' in str(p) for p in perms_list):
        print(f"  -> NEEDS FIX: Add IsLibrarianRole to permission_classes")
        # Fix it
        from apps.accounts.permissions import IsLibrarianRole
        view_class.permission_classes = perms_list + [IsLibrarianRole]
        print(f"  -> FIXED: Added IsLibrarianRole")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)