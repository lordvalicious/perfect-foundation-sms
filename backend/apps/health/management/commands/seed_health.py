import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.health.models import HealthRecord
from apps.students.models import Enrollment


class Command(BaseCommand):
    help = "Seed demo health records."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20)

    def handle(self, *args, **options):
        count = options["count"]

        enrollments = list(
            Enrollment.objects.filter(status="active").select_related("campus")
        )

        if not enrollments:
            self.stderr.write(
                self.style.ERROR("No active enrollments. Seed students first.")
            )
            return

        types = [choice[0] for choice in HealthRecord.TYPE_CHOICES]
        today = timezone.localdate()
        created = 0

        for _ in range(count):
            enrollment = random.choice(enrollments)

            HealthRecord.objects.create(
                institution=enrollment.campus.school,
                student=enrollment.student,
                campus=enrollment.campus,
                record_type=random.choice(types),
                record_date=today - timedelta(days=random.randint(0, 120)),
                notes="Auto-generated demo health record.",
                height_cm=random.randint(110, 165),
                weight_kg=random.randint(25, 60),
                temperature_c=(
                    round(random.uniform(36.2, 38.4), 1)
                    if random.random() < 0.6
                    else None
                ),
                treated_by=random.choice(
                    ["School Nurse", "Dr. Ahmed", "First Aid Team"]
                ),
            )

            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Health records created: {created}")
        )
