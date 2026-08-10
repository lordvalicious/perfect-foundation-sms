from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    User,
)
from apps.schools.models import School


class Command(BaseCommand):
    help = (
        "Create demo users with roles for local development. "
        "Run with --reset to recreate them."
    )

    DEMO_USERS = [
        {
            "username": "superadmin",
            "email": "superadmin@perfectfoundation.edu",
            "password": "SuperAdmin123!",
            "first_name": "Platform",
            "last_name": "Administrator",
            "roles": [Role.SUPER_ADMIN],
        },
        {
            "username": "admin",
            "email": "admin@perfectfoundation.edu",
            "password": "Admin123!",
            "first_name": "School",
            "last_name": "Administrator",
            "roles": [Role.ADMIN],
        },
        {
            "username": "academic",
            "email": "academic@perfectfoundation.edu",
            "password": "Academic123!",
            "first_name": "Academic",
            "last_name": "Officer",
            "roles": [Role.ACADEMIC],
        },
        {
            "username": "accountant",
            "email": "accountant@perfectfoundation.edu",
            "password": "Accountant123!",
            "first_name": "Accounts",
            "last_name": "Officer",
            "roles": [Role.ACCOUNTANT],
        },
        {
            "username": "teacher",
            "email": "teacher@perfectfoundation.edu",
            "password": "Teacher123!",
            "first_name": "Classroom",
            "last_name": "Teacher",
            "roles": [Role.TEACHER],
        },
        {
            "username": "student",
            "email": "student@perfectfoundation.edu",
            "password": "Student123!",
            "first_name": "Student",
            "last_name": "User",
            "roles": [Role.STUDENT],
        },
        {
            "username": "staff",
            "email": "staff@perfectfoundation.edu",
            "password": "Staff123!",
            "first_name": "Office",
            "last_name": "Staff",
            "roles": [Role.STAFF],
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo users before recreating.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            User.objects.filter(
                username__in=[
                    item["username"]
                    for item in self.DEMO_USERS
                ]
            ).delete()

        school = School.objects.first()

        if school is None:
            school = School.objects.create(
                name="Perfect Foundation School",
                address="Default Campus Address",
                city="Default City",
            )

        for item in self.DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=item["username"],
                defaults={
                    "email": item["email"],
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "is_staff": (
                        item["username"] == "superadmin"
                    ),
                    "is_superuser": (
                        item["username"] == "superadmin"
                    ),
                },
            )

            if created:
                user.set_password(item["password"])
                user.save()

            membership, _ = (
                InstitutionMembership.objects.get_or_create(
                    user=user,
                    institution=school,
                    defaults={"status": "active"},
                )
            )

            for role in item["roles"]:
                RoleAssignment.objects.get_or_create(
                    membership=membership,
                    role=role,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{'created' if created else 'exists'} "
                    f"{item['username']} / {item['password']}"
                )
            )
