# Data migration: seed the platform superuser from environment variables.
# Configure DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD (plus optional
# DJANGO_SUPERUSER_USERNAME / FIRST_NAME / LAST_NAME). No credentials are
# hardcoded here.
import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def _superuser_config():
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()
    if not email or not password:
        return None
    return {
        "username": os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip() or "admin",
        "email": email,
        "password": password,
        "first_name": os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Platform"),
        "last_name": os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "Administrator"),
    }


def create_superuser(apps, schema_editor):
    config = _superuser_config()
    if config is None:
        print("DJANGO_SUPERUSER_EMAIL/PASSWORD not set - skipping superuser creation.")
        return
    User = apps.get_model("accounts", "User")
    RoleAssignment = apps.get_model("accounts", "RoleAssignment")
    InstitutionMembership = apps.get_model("accounts", "InstitutionMembership")
    School = apps.get_model("schools", "School")

    user, created = User.objects.get_or_create(
        username=config["username"],
        defaults={
            "email": config["email"],
            "first_name": config["first_name"],
            "last_name": config["last_name"],
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
            "password": make_password(config["password"]),
        },
    )
    if not created:
        user.email = config["email"]
        user.first_name = config["first_name"]
        user.last_name = config["last_name"]
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.password = make_password(config["password"])
        user.save()

    school = School.objects.first()
    if school is None:
        school = School.objects.create(
            name="Perfect Foundation",
            code="PF",
            address="Default Address",
            city="Default City",
            status="active",
        )

    membership, _ = InstitutionMembership.objects.get_or_create(
        user=user,
        institution=school,
        defaults={"status": "active"},
    )

    RoleAssignment.objects.get_or_create(
        membership=membership,
        role="super_admin",
    )


def reverse_func(apps, schema_editor):
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip() or "admin"
    User = apps.get_model("accounts", "User")
    User.objects.filter(username=username).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_merge_20260829_1001"),
    ]

    operations = [
        migrations.RunPython(create_superuser, reverse_func),
    ]