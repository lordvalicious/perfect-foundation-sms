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
            "link_teacher": True,
        },
        {
            "username": "student",
            "email": "student@perfectfoundation.edu",
            "password": "Student123!",
            "first_name": "Student",
            "last_name": "User",
            "roles": [Role.STUDENT],
            "link_student": True,
        },
        {
            "username": "staff",
            "email": "staff@perfectfoundation.edu",
            "password": "Staff123!",
            "first_name": "Office",
            "last_name": "Staff",
            "roles": [Role.STAFF],
        },
        {
            "username": "parent",
            "email": "parent@perfectfoundation.edu",
            "password": "Parent123!",
            "first_name": "Guardian",
            "last_name": "Demo",
            "roles": [Role.PARENT],
            "link_guardian": True,
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

            if item.get("link_teacher"):
                from apps.teachers.models import Teacher

                teacher = (
                    Teacher.objects.filter(user__isnull=True)
                    .order_by("id")
                    .first()
                )

                if teacher is None:
                    self.stdout.write(
                        self.style.WARNING(
                            "No unlinked teacher profile found; "
                            "the teacher demo user has no profile."
                        )
                    )
                else:
                    teacher.user = user
                    teacher.membership = membership
                    teacher.save(update_fields=["user", "membership"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"linked teacher account to "
                            f"{teacher.full_name}"
                        )
                    )

            if item.get("link_student"):
                from apps.students.models import Student

                student = (
                    Student.objects.filter(user__isnull=True)
                    .order_by("id")
                    .first()
                )

                if student is None:
                    self.stdout.write(
                        self.style.WARNING(
                            "No unlinked student profile found; "
                            "the student demo user has no profile."
                        )
                    )
                else:
                    student.user = user
                    student.membership = membership
                    student.save(update_fields=["user", "membership"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"linked student account to "
                            f"{student.full_name}"
                        )
                    )

            if item.get("link_guardian"):
                from django.db.models import Count

                from apps.students.models import Guardian

                guardian = (
                    Guardian.objects
                    .filter(user__isnull=True)
                    .annotate(child_count=Count("students"))
                    .order_by("child_count", "id")
                    .first()
                )

                if guardian is None:
                    self.stdout.write(
                        self.style.WARNING(
                            "No unlinked guardian found; "
                            "the parent demo user has no children."
                        )
                    )
                elif created or not guardian.user_id:
                    guardian.user = user
                    guardian.save(update_fields=["user"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"linked parent account to guardian "
                            f"{guardian.name}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{'created' if created else 'exists'} "
                    f"{item['username']} / {item['password']}"
                )
            )
