from datetime import date

from django.core.management.base import BaseCommand

from apps.attendance.models import Attendance
from apps.students.models import Enrollment


class Command(BaseCommand):
    help = "Create sample attendance records for existing student enrollments."

    def handle(self, *args, **options):
        attendance_date = date(2026, 8, 8)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSetting up attendance for {attendance_date}...\n"
            )
        )

        enrollments = (
            Enrollment.objects
            .filter(status="active")
            .select_related(
                "student",
                "academic_year",
                "campus",
                "class_obj",
                "section",
            )
            .order_by(
                "campus__name",
                "class_obj__level",
                "class_obj__name",
                "student__first_name",
            )
        )

        if not enrollments.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No active student enrollments were found."
                )
            )
            self.stdout.write(
                "Create student enrollments first."
            )
            return

        created_count = 0
        existing_count = 0

        statuses = [
            "present",
            "present",
            "present",
            "present",
            "late",
            "present",
            "absent",
            "present",
            "leave",
        ]

        for index, enrollment in enumerate(enrollments):
            status = statuses[index % len(statuses)]

            attendance, created = Attendance.objects.get_or_create(
                student=enrollment.student,
                date=attendance_date,
                defaults={
                    "enrollment": enrollment,
                    "academic_year": enrollment.academic_year,
                    "campus": enrollment.campus,
                    "class_obj": enrollment.class_obj,
                    "section": enrollment.section,
                    "status": status,
                    "notes": "",
                },
            )

            if created:
                created_count += 1

            else:
                existing_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Attendance setup completed successfully."
            )
        )

        self.stdout.write(
            f"Date: {attendance_date}"
        )

        self.stdout.write(
            f"Records created: {created_count}"
        )

        self.stdout.write(
            f"Records already existed: {existing_count}"
        )

