import os
import sys

# Set up Django environment
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\config')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'

import django
django.setup()

from apps.accounts.models import User, RoleAssignment, InstitutionMembership, Role

# Get all role assignments - using role field directly
print("=== ALL ROLE ASSIGNMENTS ===")
ras = RoleAssignment.objects.select_related('membership__user', 'membership__institution').values('role', 'membership__user__username', 'membership__institution__name', 'membership__status')
for ra in ras:
    print(f"Role: {ra['role']}, User: {ra['membership__user__username']}, Institution: {ra['membership__institution__name']}, Status: {ra['membership__status']}")

print()

# Find users with role = admin (not super_admin)
print("=== USERS WITH role=admin ===")
admin_ras = RoleAssignment.objects.filter(role='admin').select_related('membership__user', 'membership__institution')
admin_users_found = []
for ra in admin_ras:
    user = ra.membership.user
    admin_users_found.append(user)
    print(f"Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  is_active: {user.is_active}")
    print(f"  is_superuser: {user.is_superuser}")
    # Get primary role
    roles = user.get_roles()
    print(f"  primary_role: {user.primary_role if hasattr(user, 'primary_role') else 'N/A'}")
    print(f"  All roles: {roles}")
    # Get institution memberships
    memberships = user.get_active_memberships()
    for m in memberships:
        print(f"  Institution: {m.institution}, Status: {m.status}")
    print()

# Find users with role = super_admin
print("=== USERS WITH role=super_admin ===")
super_admin_ras = RoleAssignment.objects.filter(role='super_admin').select_related('membership__user', 'membership__institution')
for ra in super_admin_ras:
    user = ra.membership.user
    print(f"Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  is_active: {user.is_active}")
    print(f"  is_superuser: {user.is_superuser}")
    print(f"  primary_role: {user.primary_role if hasattr(user, 'primary_role') else 'N/A'}")
    print(f"  All roles: {user.get_roles()}")
    print()

# Check the specific admin username
print("=== CHECKING 'admin' username specifically ===")
admin_user = User.objects.get(username='admin')
print(f"Username: {admin_user.username}")
print(f"Email: {admin_user.email}")
print(f"is_active: {admin_user.is_active}")
print(f"is_superuser: {admin_user.is_superuser}")
print(f"primary_role: {admin_user.primary_role if hasattr(admin_user, 'primary_role') else 'N/A'}")
print(f"All roles: {admin_user.get_roles()}")

# Check if any user has role=admin and is_superuser=False
print()
print("=== CHECKING FOR GENUINE NORMAL ADMIN ===")
for user in admin_users_found:
    if not user.is_superuser:
        print(f"GENUINE NORMAL ADMIN FOUND: {user.username}")
        print(f"  is_superuser=False: YES")
    else:
        print(f"Super Admin account: {user.username}")
        print(f"  is_superuser=True: YES")