"""Seed demo staff attendance and leave requests."""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import StaffAttendance, StaffLeave, StaffProfile


class Command(BaseCommand):
    help = "Seed demo staff attendance and leave requests."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=10)

    def handle(self, *args, **options):
        days = options["days"]

        profiles = list(StaffProfile.objects.filter(status="active"))

        if not profiles:
            self.stderr.write(
                self.style.ERROR(
                    "No active staff profiles found. Run seed_staff first."
                )
            )
            return

        today = timezone.localdate()
        created_att = 0
        created_leave = 0

        for offset in range(days):
            day = today - timedelta(days=offset)

            for profile in profiles:
                status_roll = random.random()

                if status_roll < 0.82:
                    status = "present"
                elif status_roll < 0.9:
                    status = "late"
                elif status_roll < 0.95:
                    status = "absent"
                else:
                    status = "half_day"

                _, created = StaffAttendance.objects.get_or_create(
                    staff=profile,
                    date=day,
                    defaults={
                        "status": status,
                        "check_in": (
                            f"{random.randint(7,8)}:{random.randint(10,59):02d}"
                            if status in ("present", "late")
                            else None
                        ),
                        "check_out": (
                            f"{random.randint(14,17)}:{random.randint(10,59):02d}"
                            if status != "absent"
                            else None
                        ),
                    },
                )

                if created:
                    created_att += 1

        reviewers = [
            p for p in profiles
            if (p.designation or "").lower() in ("principal", "hr manager", "admin")
        ] or profiles[:1]

        leave_types = ["casual", "sick", "annual", "unpaid"]

        for profile in random.sample(profiles, min(4, len(profiles))):
            start = today + timedelta(days=random.randint(-20, 15))

            leave, created = StaffLeave.objects.get_or_create(
                staff=profile,
                start_date=start,
                end_date=start + timedelta(days=random.randint(1, 3)),
                leave_type=random.choice(leave_types),
                defaults={
                    "reason": "Auto-generated demo request.",
                    "status": random.choice(
                        ["pending", "pending", "approved", "rejected"]
                    ),
                    "reviewed_by": random.choice(reviewers).user,
                },
            )

            if created:
                created_leave += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Attendance records created: {created_att}, "
                f"leave requests created: {created_leave}"
            )
        )
