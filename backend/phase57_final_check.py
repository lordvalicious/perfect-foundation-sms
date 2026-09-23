import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.schools.models import School, Campus

print("=" * 60)
print("PHASE 57 - FINAL VERIFICATION")
print("=" * 60)

# 1. Verify Librarian
print("\n1. LIBRARIAN ACCOUNT")
print("-" * 40)
librarian = User.objects.filter(username="SA-EMP-00011").first()
if librarian:
    membership = InstitutionMembership.objects.filter(user=librarian, institution_id=4).first()
    if membership:
        roles = list(membership.role_assignments.values_list('role', flat=True))
        print("User: " + librarian.username)
        print("primary_role (property): " + str(librarian.primary_role))
        print("must_change_password: " + str(librarian.must_change_password))
        print("get_roles(): " + str(librarian.get_roles()))
        print("Membership roles: " + str(roles))
        print("Membership institution: " + membership.institution.name)
        if 'librarian' in roles and not librarian.must_change_password:
            print("STATUS: READY FOR LOGIN")
        else:
            print("STATUS: NOT READY")

# 3. Final verification of all accounts
print("\n3. FINAL VERIFICATION OF ALL TEST ACCOUNTS")
print("-" * 40)
test_accounts = [
    ("SA-EMP-00011", "LIBRARIAN", "librarian", 4),
    ("DEG-EMP-00031", "ACCOUNTANT", "accountant", 2),
    ("SA-EMP-00031", "GUARD", "guard", 4),
    ("SA-EMP-00041", "ADMIN_OFFICER", "staff", 4),
    ("SA-ST-0002", "STUDENT2", "student", 4),
    ("SA-ST-0003", "STUDENT3", "student", 4),
]

for username, expected_role, expected_role_name, expected_inst in test_accounts:
    user = User.objects.filter(username=username).first()
    if user:
        membership = InstitutionMembership.objects.filter(user=user, institution_id=expected_inst).first()
        roles = list(RoleAssignment.objects.filter(membership=membership).values_list('role', flat=True)) if membership else []
        status = "READY" if (user.primary_role == expected_role_name or expected_role_name in roles) and not user.must_change_password and user.is_active else "NOT READY"
        print(username + ": role=" + str(user.primary_role) + ", roles=" + str(roles) + ", must_change_pw=" + str(user.must_change_password) + ", active=" + str(user.is_active) + " -> " + status)
    else:
        print(username + ": NOT FOUND")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)