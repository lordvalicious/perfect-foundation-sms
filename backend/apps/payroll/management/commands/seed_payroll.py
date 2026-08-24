import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.payroll.models import PayrollRecord, SalaryStructure
from apps.teachers.models import Teacher


class Command(BaseCommand):
    help = "Seed payroll data: salary structures and monthly payroll records."

    ALLOWANCE_PRESETS = [
        {"housing": 25000, "transport": 10000, "medical": 5000},
        {"housing": 20000, "transport": 8000, "medical": 4000},
        {"housing": 30000, "transport": 12000, "medical": 6000},
        {"housing": 15000, "transport": 7000, "medical": 3000},
        {"housing": 22000, "transport": 9000, "medical": 4500},
    ]

    DEDUCTION_PRESETS = [
        {"pf": 3000, "tax": 2000},
        {"pf": 2500, "tax": 1500},
        {"pf": 4000, "tax": 3000},
        {"pf": 2000, "tax": 1000},
        {},
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding payroll data...\n"))

        teachers = list(Teacher.objects.filter(status="active"))
        if not teachers:
            self.stderr.write(self.style.ERROR("No active teachers found. Run teacher seed command first."))
            return

        structures_created = 0
        records_created = 0

        for teacher in teachers:
            basic = Decimal(str(random.choice([45000, 55000, 65000, 75000, 85000, 95000])))
            allowances = random.choice(self.ALLOWANCE_PRESETS)

            structure, created = SalaryStructure.objects.get_or_create(
                teacher=teacher,
                effective_date=date(2026, 8, 1),
                defaults={
                    "basic_salary": basic,
                    "allowances": allowances,
                    "status": "active",
                },
            )
            if created:
                structures_created += 1

            months_to_create = [
                (8, 2026),
                (7, 2026),
                (6, 2026),
            ]

            for month, year in months_to_create:
                deductions = random.choice(self.DEDUCTION_PRESETS)
                working_days = random.choice([22, 23, 24, 25, 26])
                paid_days = working_days - random.randint(0, 3)

                record, created = PayrollRecord.objects.get_or_create(
                    teacher=teacher,
                    month=month,
                    year=year,
                    defaults={
                        "structure": structure,
                        "working_days": working_days,
                        "paid_days": paid_days,
                        "deductions": deductions,
                        "status": random.choice(["paid", "paid", "processed", "draft"]),
                        "processed_at": timezone.now() if random.random() < 0.8 else None,
                    },
                )
                if created:
                    records_created += 1

        self.stdout.write(self.style.SUCCESS(f"\nSalary structures created: {structures_created}"))
        self.stdout.write(self.style.SUCCESS(f"Payroll records created: {records_created}"))
        self.stdout.write(self.style.SUCCESS("\nPayroll seeding completed.\n"))
