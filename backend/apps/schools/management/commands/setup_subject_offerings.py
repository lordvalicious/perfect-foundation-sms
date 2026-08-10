from django.core.management.base import BaseCommand
from django.db import transaction

from apps.schools.models import (
    AcademicYear,
    Campus,
    Subject,
    SubjectOffering,
)


class Command(BaseCommand):
    help = "Create the correct subject offerings for each campus."

    # Subjects specifically required at Paris Road
    PARIS_ROAD_SUBJECTS = [
        ("English", "ENG"),
        ("Urdu", "URD"),
        ("Mathematics", "MATH"),
        ("Islamiyat", "ISL"),
        ("Pakistan Studies", "PAK"),
        ("Science", "SCI"),
    ]

    JUNIOR_SUBJECT = ("Reading & Writing", "RW")

    TARGET_CAMPUSES = [
        "Junior Campus",
        "Paris Road Campus",
        "Boys Campus",
        "Girls Campus",
        "Haripur Campus",
]

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE(
                "Setting up subject offerings..."
            )
        )

        # ---------------------------------------------------------
        # 1. Find the active academic year
        # ---------------------------------------------------------
        academic_year = (
            AcademicYear.objects
            .filter(status="active")
            .order_by("-start_date")
            .first()
        )

        if not academic_year:
            self.stdout.write(
                self.style.ERROR(
                    "No active Academic Year was found."
                )
            )
            self.stdout.write(
                "Create or activate an Academic Year first."
            )
            return

        self.stdout.write(
            f"Academic Year: {academic_year}"
        )

        # ---------------------------------------------------------
        # 2. Make sure Junior's Reading & Writing subject exists
        # ---------------------------------------------------------
        junior_subject, created = Subject.objects.get_or_create(
            code=self.JUNIOR_SUBJECT[1],
            defaults={
                "name": self.JUNIOR_SUBJECT[0],
                "subject_type": "general",
                "practical_required": False,
                "status": "active",
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "Created subject: Reading & Writing"
                )
            )
        else:
            self.stdout.write(
                "Subject already exists: Reading & Writing"
            )

        # ---------------------------------------------------------
        # 3. Make sure Paris Road subjects exist
        # ---------------------------------------------------------
        for subject_name, subject_code in self.PARIS_ROAD_SUBJECTS:
            subject, created = Subject.objects.get_or_create(
                code=subject_code,
                defaults={
                    "name": subject_name,
                    "subject_type": "general",
                    "practical_required": False,
                    "status": "active",
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created subject: {subject_name}"
                    )
                )

        # ---------------------------------------------------------
        # 4. Process each campus
        # ---------------------------------------------------------
        for campus_name in self.TARGET_CAMPUSES:
            try:
                campus = Campus.objects.get(name__iexact=campus_name)
            except Campus.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"Campus not found: {campus_name}"
                    )
                )
                continue

            self.stdout.write("")
            self.stdout.write(
                self.style.NOTICE(
                    f"Processing campus: {campus.name}"
                )
            )

            # Find all classes belonging to this campus.
            classes = (
                campus.academic_units
                .prefetch_related("classes")
                .all()
            )

            campus_classes = []

            for unit in classes:
                campus_classes.extend(
                    list(unit.classes.all())
                )

            if not campus_classes:
                self.stdout.write(
                    self.style.WARNING(
                        f"No classes found for {campus.name}"
                    )
                )
                continue

            # -----------------------------------------------------
            # Determine which subjects this campus receives
            # -----------------------------------------------------
            if campus.name.lower() == "junior campus":
                subjects = [junior_subject]

            elif campus.name.lower() == "paris road campus":
                subjects = list(
                    Subject.objects.filter(
                        code__in=[
                            code
                            for _, code in self.PARIS_ROAD_SUBJECTS
                        ]
                    )
                )

            else:
                # Boys, Girls and Haripur get ALL active subjects.
                subjects = list(
                    Subject.objects.filter(
                        status="active"
                    ).order_by("name")
                )

            # -----------------------------------------------------
            # Create offerings
            # -----------------------------------------------------
            created_count = 0
            existing_count = 0

            for class_obj in campus_classes:
                for subject in subjects:
                    _, created = SubjectOffering.objects.get_or_create(
                        subject=subject,
                        class_obj=class_obj,
                        academic_year=academic_year,
                    )

                    if created:
                        created_count += 1
                    else:
                        existing_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{campus.name}: "
                    f"{created_count} created, "
                    f"{existing_count} already existed."
                )
            )

        # ---------------------------------------------------------
        # Finished
        # ---------------------------------------------------------
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Subject offering setup completed successfully."
            )
        )