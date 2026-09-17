import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\config')

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'

import django
django.setup()

# Import using the full app path from INSTALLED_APPS
from apps.accounts.models import User

# Get all users
users = User.objects.all()
print(f"Total users: {users.count()}")
print()

# Print user details
print("User Account Details:")
print("-" * 80)
for user in users:
    print(f"Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  is_active: {user.is_active}")
    print(f"  is_superuser: {user.is_superuser}")
    print(f"  primary_role: {user.primary_role}")
    print()

# Get role assignments
from accounts.models import RoleAssignment, Role
print("Role Assignments:")
print("-" * 80)
ras = RoleAssignment.objects.select_related('role', 'membership__user', 'membership__institution').values('role__name', 'membership__user__username', 'membership__institution__name', 'membership__status')
for ra in ras:
    print(f"  Role: {ra['role__name']}, User: {ra['membership__user__username']}, Institution: {ra['membership__institution__name']}, Status: {ra['membership__status']}")

print()

# Get institution memberships
from accounts.models import InstitutionMembership
print("Institution Memberships:")
print("-" * 80)
memberships = InstitutionMembership.objects.select_related('user', 'institution').values('user__username', 'institution__name', 'status', 'role_assignments__role')
for m in memberships:
    print(f"  User: {m['user__username']}, Institution: {m['institution__name']}, Status: {m['status']}, Role: {m['role_assignments__role']}")