import os
import sys

# Set up Django environment
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\config')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'

import django
django.setup()

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
    print(f"  primary_role: {user.primary_role if hasattr(user, 'primary_role') else 'N/A'}")
    print()