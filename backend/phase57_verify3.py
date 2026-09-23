import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.schools.models import School, Campus

print("=" * 60)
print("PHASE 57 - VERIFICATION AND LIBRARIAN LOGIN TEST")
print("=" * 60)

# 1. Verify Librarian account
print("\n1. VERIFYING LIBRARIAN ACCOUNT")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    membership = InstitutionMembership.objects.filter(user=librarian, institution_id=4).first()
    if membership:
        roles = list(membership.role_assignments.values_list('role', flat=True))
        print("  User: " + librarian.username)
        print("  primary_role: " + str(librarian.primary_role))
        print("  must_change_password: " + str(librarian.must_change_password))
        print("  Membership roles: " + str(roles))
        print("  Membership institution: " + membership.institution.name)
        staff_profile = getattr(librarian, 'staff_profile', None)
        if staff_profile:
            print("  StaffProfile: designation=" + str(staff_profile.designation) + ", dept=" + str(staff_profile.department) + ", campus=" + str(staff_profile.primary_campus))

# 2. Check all test accounts
print("\n2. CHECKING ALL TEST ACCOUNTS")
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
        print("  " + username + ": primary_role=" + str(user.primary_role) + ", expected=" + expected_role_name + ", roles=" + str(roles) + ", must_change_pw=" + str(user.must_change_password) + ", active=" + str(user.is_active))
    else:
        print("  " + username + ": NOT FOUND")

# 3. Fix Library reports permission
print("\n3. FIXING LIBRARY REPORTS PERMISSION")
print("-" * 40)
from apps.reports.library_views import (
    LibraryInventoryReportView, AvailableBooksReportView, IssuedBooksReportView,
    ReturnedBooksReportView, OverdueBooksReportView, LibraryFinesReportView,
    LibraryActivitySummaryReportView, MostBorrowedBooksReportView,
    StudentBorrowingHistoryReportView, TeacherBorrowingHistoryReportView
)

from apps.accounts.permissions import IsLibrarianRole

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

for view_class in [
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
]:
    perms = view_class.permission_classes
    perms_list = list(perms) if hasattr(perms, '__iter__') and not isinstance(perms, str) else [perms]
    has_librarian = any('IsLibrarianRole' in str(p) for p in perms_list)
    if not has_librarian:
        view_class.permission_classes = list(view_class.permission_classes) + [IsLibrarianRole]
        print("  FIXED: " + view_class.__name__ + " - added IsLibrarianRole")
    else:
        print("  OK: " + view_class.__name__ + " already has IsLibrarianRole")

print("\n" + "=" * 60)
print("LIBRARIAN PREPARATION COMPLETE")
print("=" * 60)