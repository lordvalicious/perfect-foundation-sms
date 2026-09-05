import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from apps.accounts.models import InstitutionMembership, RoleAssignment, User
from apps.schools.models import School


class Command(BaseCommand):
    help = (
        "Create or update the platform superuser from DJANGO_SUPERUSER_* "
        "environment variables (EMAIL and PASSWORD required). Safe to run "
        "repeatedly; also used to rotate the superuser password."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-membership",
            action="store_true",
            help="Only manage the user record; skip school/membership/role seeding.",
        )

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()
        if not email or not password:
            self.stderr.write(
                self.style.ERROR(
                    "DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD must be set."
                )
            )
            raise SystemExit(1)

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip() or "admin"
        first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Platform")
        last_name = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "Administrator")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "password": make_password(password),
            },
        )
        if not created:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.password = make_password(password)
            user.save(update_fields=[
                "email",
                "first_name",
                "last_name",
                "is_staff",
                "is_superuser",
                "is_active",
                "password",
            ])

        if options["no_membership"]:
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{user.username}' ensured ({'created' if created else 'updated'}).")
            )
            return

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

        # The env-provisioned account is the singular platform Super Admin.
        # If another account had (incorrectly) been granted the role, demote it
        # to admin so exactly one Super Admin always exists.
        other_super_admins = RoleAssignment.objects.filter(
            role="super_admin",
        ).exclude(membership=membership)
        for ra in other_super_admins:
            ra.role = "admin"
            ra.save(update_fields=["role"])
            self.stdout.write(
                self.style.WARNING(
                    f"Demoted '{ra.membership.user.username}' from super_admin "
                    "to admin (platform allows exactly one Super Admin)."
                )
            )

        RoleAssignment.objects.get_or_create(
            membership=membership,
            role="super_admin",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{user.username}' ensured with super_admin membership "
                f"(school: {school.name})."
            )
        )