from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta

from apps.schools.models import School, AcademicYear


class Command(BaseCommand):
    help = "Seed past academic years for the school."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("Seeding past academic years...")
        )

        schools = School.objects.filter(status="active")
        
        for school in schools:
            self.stdout.write(f"\nProcessing school: {school.name}")

            # Check if there are existing academic years
            existing_years = AcademicYear.objects.filter(school=school).order_by("-start_date")
            
            # If there's already an active year, find the most recent one
            active_year = AcademicYear.objects.filter(school=school, status="active").first()
            
            if not active_year:
                self.stdout.write(
                    self.style.WARNING(f"  No active academic year for {school.name}. Creating 2024-2025 as active.")
                )
                active_year = AcademicYear.objects.create(
                    school=school,
                    name="2024-2025",
                    start_date=date(2024, 4, 1),
                    end_date=date(2025, 3, 31),
                    status="active",
                )
            else:
                self.stdout.write(f"  Active year: {active_year}")

            # Create past academic years (2020-2021 through 2023-2024)
            past_years = [
                ("2023-2024", date(2023, 4, 1), date(2024, 3, 31), "completed"),
                ("2022-2023", date(2022, 4, 1), date(2023, 3, 31), "completed"),
                ("2021-2022", date(2021, 4, 1), date(2022, 3, 31), "completed"),
                ("2020-2021", date(2020, 4, 1), date(2021, 3, 31), "completed"),
            ]

            for name, start, end, status in past_years:
                ay, created = AcademicYear.objects.get_or_create(
                    school=school,
                    name=name,
                    defaults={
                        "start_date": start,
                        "end_date": end,
                        "status": status,
                    },
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"  Created academic year: {ay}")
                    )
                else:
                    self.stdout.write(f"  Already exists: {ay}")

        self.stdout.write(
            self.style.SUCCESS("\nAcademic year seeding completed.")
        )