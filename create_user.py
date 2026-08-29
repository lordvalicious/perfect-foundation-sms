#!/usr/bin/env python
"""Create FrostFire superadmin user on Vercel database"""
import os
import sys
import time

# Add project root and backend to path
PROJECT_ROOT = r"C:\Users\Ryuk\Documents\perfect-foundation-sms"
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_ROOT)

# Load Vercel env vars
env_file = os.path.join(PROJECT_ROOT, "backend", ".env.production")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                os.environ[k] = v

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.production")

import django
django.setup()

from apps.accounts.models import User, Role, RoleAssignment, InstitutionMembership
from apps.schools.models import School

def create_user():
    print("[INFO] Connecting to database...")
    
    # Create your account
    user, created = User.objects.get_or_create(
        username="FrostFire",
        defaults={
            "email": "lordvalicious@gmail.com",
            "first_name": "Frost",
            "last_name": "Fire",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
    )

    if created:
        user.set_password("ra2a1s345")
        user.save()
        print("[OK] Created user: FrostFire")
    else:
        # Update password if user exists
        user.set_password("ra2a1s345")
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        print("[OK] Updated existing user: FrostFire")

    # Assign SUPER_ADMIN role
    role, _ = Role.objects.get_or_create(name="SUPER_ADMIN")

    # Get or create school
    school = School.objects.first()
    if school is None:
        school = School.objects.create(
            name="Perfect Foundation",
            code="PF",
            address="Default Address",
            city="Default City",
            is_active=True
        )
        print("[OK] Created default school")

    # Create institution membership
    membership, _ = InstitutionMembership.objects.get_or_create(
        user=User.objects.get(username="FrostFire"),
        school=School.objects.first(),
        defaults={"status": "active"}
    )

    # Assign SUPER_ADMIN role
    ra, _ = RoleAssignment.objects.get_or_create(
        membership=InstitutionMembership.objects.get(user__username="FrostFire", school=School.objects.first()),
        role=Role.objects.get(name="SUPER_ADMIN")
    )

    print("[OK] SUPER_ADMIN role assigned")
    print("")
    print("=" * 50)
    print("ACCOUNT CREATED SUCCESSFULLY!")
    print("=" * 50)
    print("   Username: FrostFire")
    print("   Password: ra2a1s345")
    print("   Email:    lordvalicious@gmail.com")
    print("   Role:     SUPER_ADMIN")
    print("=" * 50)

if __name__ == "__main__":
    try:
        create_user()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)