import sys
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Run ALL seed commands in the correct order. "
        "Use --skip-users to skip user creation."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-users",
            action="store_true",
            help="Skip demo user creation.",
        )
        parser.add_argument(
            "--skip-attendance",
            action="store_true",
            help="Skip attendance seeding.",
        )

    def handle(self, *args, **options):
        start = time.time()

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("  PERFECT FOUNDATION SMS - FULL DATA SEED"))
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))

        steps = [
            ("Demo Users", "create_demo_users", {"reset": True}),
            ("Teacher Assignments", "setup_teacher_assignments", {}),
            ("Subject Offerings", "setup_subject_offerings", {}),
            ("Students", "seed_students", {"count": 50}),
            ("Staff", "seed_staff", {"count": 10}),
            ("Attendance (4 weeks)", "seed_attendance_bulk", {"weeks": 4}),
            ("Finance", "setup_finance", {}),
            ("Exams", "setup_exams", {}),
            ("Report Cards", "setup_reportcards", {}),
            ("Timetable", "setup_timetable", {}),
            ("Library", "seed_library", {}),
            ("Transport", "seed_transport", {}),
            ("Inventory", "seed_inventory", {}),
            ("Communication", "seed_communication", {}),
            ("Events", "seed_events", {}),
            ("HR", "seed_hr", {}),
            ("Payroll", "seed_payroll", {}),
            ("Parent Demo", "seed_parent_demo", {}),
        ]

        for i, (label, command, kwargs) in enumerate(steps, 1):
            if options["skip_users"] and command in ("create_demo_users", "seed_parent_demo"):
                self.stdout.write(self.style.WARNING(f"\n[{i}/{len(steps)}] Skipping {label}..."))
                continue

            if options["skip_attendance"] and "attendance" in command.lower():
                self.stdout.write(self.style.WARNING(f"\n[{i}/{len(steps)}] Skipping {label}..."))
                continue

            self.stdout.write(self.style.SUCCESS(f"\n[{i}/{len(steps)}] Running: {label}"))
            self.stdout.write("-" * 40)

            try:
                call_command(command, **kwargs, verbosity=1)
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"  ERROR in {label}: {exc}")
                )

        elapsed = time.time() - start
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f"  SEED COMPLETE in {elapsed:.1f} seconds"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))
