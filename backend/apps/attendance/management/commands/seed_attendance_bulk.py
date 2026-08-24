import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.attendance.models import Attendance
from apps.students.models import Enrollment


class Command(BaseCommand):
    help = (
        "Create attendance records for all active enrollments "
        "across the last 4 weeks of school days."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks",
            type=int,
            default=4,
            help="Number of past weeks to generate attendance for.",
        )

    def handle(self, *args, **options):
        weeks = max(options["weeks"], 1)

        today = date.today()
        start_date = today - timedelta(weeks=weeks)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSetting up attendance for {weeks} weeks "
                f"({start_date} to {today})...\n"
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
            return

        created_count = 0
        existing_count = 0

        statuses = [
            "present", "present", "present", "present", "present",
            "present", "present", "late", "present", "absent",
            "present", "present", "present", "late", "present",
            "leave", "present", "present", "present", "absent",
        ]

        current = start_date
        school_days = 0

        while current <= today:
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            school_days += 1

            for index, enrollment in enumerate(enrollments):
                day_seed = (current.toordinal() + enrollment.student.pk) % len(statuses)
                status = statuses[day_seed]

                attendance, created = Attendance.objects.get_or_create(
                    student=enrollment.student,
                    date=current,
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

            current += timedelta(days=1)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Attendance setup completed successfully."
            )
        )
        self.stdout.write(f"School days processed: {school_days}")
        self.stdout.write(f"Records created: {created_count}")
        self.stdout.write(f"Records already existed: {existing_count}")
