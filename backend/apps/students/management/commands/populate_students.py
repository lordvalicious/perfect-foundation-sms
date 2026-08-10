from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.schools.models import AcademicYear, Campus, Section
from apps.students.models import Enrollment, Guardian, Student


class Command(BaseCommand):
    help = "Populate fictional students, guardians, and enrollments."

    STUDENTS_PER_CLASS = 4

    FIRST_NAMES = [
        "Aether",
        "Lyra",
        "Kael",
        "Elara",
        "Orion",
        "Seren",
        "Arden",
        "Nova",
        "Zayden",
        "Aurelia",
        "Riven",
        "Selene",
        "Evren",
        "Liora",
        "Cassian",
        "Nyra",
        "Ezra",
        "Vesper",
        "Rowan",
        "Mira",
    ]

    LAST_NAMES = [
        "Moonveil",
        "Starfall",
        "Silverwind",
        "Dawnmere",
        "Nightbloom",
        "Stormvale",
        "Ravencrest",
        "Frostmere",
        "Emberfall",
        "Skylark",
        "Ashbourne",
        "Wintermere",
    ]

    GUARDIAN_NAMES = [
        "Aldric Moonveil",
        "Seraphina Starfall",
        "Theron Silverwind",
        "Elowen Dawnmere",
        "Kaelen Stormvale",
        "Mirabel Ravencrest",
        "Orlan Frostmere",
        "Celestia Emberfall",
        "Darian Skylark",
        "Lyanna Ashbourne",
    ]

    RELATIONSHIPS = [
        "Father",
        "Mother",
        "Guardian",
    ]

    def handle(self, *args, **options):
        self.stdout.write("Creating fictional student data...")

        try:
            academic_year = AcademicYear.objects.get(name="2026-2027")
        except AcademicYear.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Academic Year 2026-2027 was not found."
                )
            )
            return

        student_number = 1

        for campus in Campus.objects.all().order_by("id"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nProcessing {campus.name}..."
                )
            )

            sections = Section.objects.filter(
                class_obj__unit__campus=campus
            ).select_related(
                "class_obj",
                "class_obj__unit",
            )

            campus_count = 0

            for section in sections:
                for i in range(self.STUDENTS_PER_CLASS):
                    admission_number = (
                        f"PF-{academic_year.name.replace('-', '')}-"
                        f"{student_number:04d}"
                    )

                    if Student.objects.filter(
                        admission_number=admission_number
                    ).exists():
                        student_number += 1
                        continue

                    first_name = self.FIRST_NAMES[
                        (student_number - 1) % len(self.FIRST_NAMES)
                    ]

                    last_name = self.LAST_NAMES[
                        (student_number - 1) % len(self.LAST_NAMES)
                    ]

                    guardian_name = self.GUARDIAN_NAMES[
                        (student_number - 1) % len(self.GUARDIAN_NAMES)
                    ]

                    guardian, _ = Guardian.objects.get_or_create(
                        name=guardian_name,
                        defaults={
                            "relationship": self.RELATIONSHIPS[
                                (student_number - 1)
                                % len(self.RELATIONSHIPS)
                            ],
                            "phone": f"0300-{student_number:07d}",
                            "email": "",
                            "address": f"{campus.city or 'Punjab'}",
                        },
                    )

                    gender = (
                        "female"
                        if student_number % 2 == 0
                        else "male"
                    )

                    student = Student.objects.create(
                        admission_number=admission_number,
                        first_name=first_name,
                        last_name=last_name,
                        date_of_birth=date(
                            2012 + (student_number % 8),
                            ((student_number - 1) % 12) + 1,
                            ((student_number - 1) % 25) + 1,
                        ),
                        gender=gender,
                        guardian=guardian,
                        address=campus.city or "",
                        status="active",
                        admission_date=date(2026, 8, 1),
                    )

                    Enrollment.objects.create(
                        student=student,
                        academic_year=academic_year,
                        campus=campus,
                        class_obj=section.class_obj,
                        section=section,
                        status="active",
                    )

                    campus_count += 1
                    student_number += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{campus.name}: created {campus_count} students."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\nFictional student population created successfully."
            )
        )

