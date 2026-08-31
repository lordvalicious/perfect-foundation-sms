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

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "FrostFire")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "lordvalicious@gmail.com")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()
    if not password:
        print("[ERROR] DJANGO_SUPERUSER_PASSWORD must be set.")
        sys.exit(1)

    # Create your account
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": "Frost",
            "last_name": "Fire",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
    )

    if created:
        user.set_password(password)
        user.save()
        print(f"[OK] Created user: {username}")
    else:
        # Update password if user exists
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        print(f"[OK] Updated existing user: {username}")

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
        user=user,
        school=school,
        defaults={"status": "active"}
    )

    # Assign SUPER_ADMIN role
    ra, _ = RoleAssignment.objects.get_or_create(
        membership=InstitutionMembership.objects.get(user__username=username, school=school),
        role=Role.objects.get(name="SUPER_ADMIN")
    )

    print("[OK] SUPER_ADMIN role assigned")
    print("")
    print("=" * 50)
    print("ACCOUNT CREATED SUCCESSFULLY!")
    print("=" * 50)
    print(f"   Username: {username}")
    print("   Password: (from DJANGO_SUPERUSER_PASSWORD)")
    print(f"   Email:    {email}")
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