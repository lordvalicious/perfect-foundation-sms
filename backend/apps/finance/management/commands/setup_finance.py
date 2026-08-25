
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from apps.finance.models import (
    FeeCategory,
    FeeStructure,
    Invoice,
    InvoiceItem,
    Payment,
)
from apps.schools.models import AcademicYear, Campus
from apps.students.models import Enrollment


class Command(BaseCommand):
    help = "Create realistic fee structures, invoices and payments."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "\nSetting up finance data...\n"
            )
        )

        academic_year = AcademicYear.objects.filter(
            name="2026-2027"
        ).first()

        if not academic_year:
            academic_year = AcademicYear.objects.order_by(
                "-start_date"
            ).first()

        if not academic_year:
            self.stdout.write(
                self.style.ERROR(
                    "No academic year found."
                )
            )
            return

        self.stdout.write(
            f"Academic Year: {academic_year.school.name} - "
            f"{academic_year.name}\n"
        )

        categories = self.create_categories()

        self.create_fee_structures(
            academic_year,
            categories,
        )

        self.create_invoices(
            academic_year,
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Finance setup completed successfully."
            )
        )

    def create_categories(self):
        category_data = [
            (
                "Admission Fee",
                "one_time",
                "One-time admission charge.",
            ),
            (
                "Monthly Tuition",
                "monthly",
                "Monthly tuition fee.",
            ),
            (
                "Annual Fee",
                "annual",
                "Annual school charges.",
            ),
            (
                "Exam Fee",
                "term",
                "Examination and assessment fee.",
            ),
            (
                "Transport Fee",
                "monthly",
                "Monthly transportation fee.",
            ),
        ]

        categories = {}

        for name, frequency, description in category_data:
            category, created = FeeCategory.objects.get_or_create(
                name=name,
                defaults={
                    "frequency": frequency,
                    "description": description,
                    "status": "active",
                },
            )

            categories[name] = category

            if created:
                self.stdout.write(
                    f"Created fee category: {name}"
                )
            else:
                self.stdout.write(
                    f"Fee category already exists: {name}"
                )

        return categories

    def create_fee_structures(
        self,
        academic_year,
        categories,
    ):
        campus_amounts = {
            "Junior Campus": {
                "Monthly Tuition": Decimal("3000.00"),
                "Annual Fee": Decimal("5000.00"),
                "Exam Fee": Decimal("1500.00"),
            },
            "Paris Road Campus": {
                "Monthly Tuition": Decimal("4500.00"),
                "Annual Fee": Decimal("7000.00"),
                "Exam Fee": Decimal("2000.00"),
            },
            "Girls Campus": {
                "Monthly Tuition": Decimal("5000.00"),
                "Annual Fee": Decimal("8000.00"),
                "Exam Fee": Decimal("2500.00"),
            },
            "Boys Campus": {
                "Monthly Tuition": Decimal("5000.00"),
                "Annual Fee": Decimal("8000.00"),
                "Exam Fee": Decimal("2500.00"),
            },
            "Haripur Campus": {
                "Monthly Tuition": Decimal("4000.00"),
                "Annual Fee": Decimal("6500.00"),
                "Exam Fee": Decimal("2000.00"),
            },
        }

        structures_created = 0
        structures_existing = 0

        campuses = Campus.objects.all()

        for campus in campuses:
            amounts = campus_amounts.get(
                campus.name,
                {
                    "Monthly Tuition": Decimal("4000.00"),
                    "Annual Fee": Decimal("6500.00"),
                    "Exam Fee": Decimal("2000.00"),
                },
            )

            classes = []

            for unit in campus.academic_units.all():
                classes.extend(unit.classes.all())

            self.stdout.write(
                f"\nProcessing fee structures: {campus.name}"
            )

            for class_obj in classes:
                for category_name in [
                    "Monthly Tuition",
                    "Annual Fee",
                    "Exam Fee",
                ]:
                    category = categories[category_name]
                    amount = amounts[category_name]

                    _, created = FeeStructure.objects.get_or_create(
                        academic_year=academic_year,
                        campus=campus,
                        class_obj=class_obj,
                        category=category,
                        defaults={
                            "amount": amount,
                            "due_day": 10,
                            "status": "active",
                        },
                    )

                    if created:
                        structures_created += 1
                    else:
                        structures_existing += 1

        self.stdout.write(
            f"Fee structures created: {structures_created}"
        )

        self.stdout.write(
            f"Fee structures already existed: "
            f"{structures_existing}"
        )

    def create_invoices(self, academic_year):
        enrollments = (
            Enrollment.objects
            .filter(
                academic_year=academic_year,
                status="active",
            )
            .select_related(
                "student",
                "campus",
                "class_obj",
                "section",
            )
            .order_by("student__admission_number")
        )

        if not enrollments.exists():
            self.stdout.write(
                self.style.WARNING(
                    "\nNo active enrollments found."
                )
            )
            return

        created_count = 0
        existing_count = 0
        payments_created = 0

        invoice_date = date(2026, 8, 1)
        due_date = date(2026, 8, 10)

        for index, enrollment in enumerate(enrollments):
            invoice_number = (
                f"PF-{academic_year.name.replace('-', '')}-"
                f"{enrollment.student.admission_number}-08"
            )

            invoice, created = Invoice.objects.get_or_create(
                invoice_number=invoice_number,
                defaults={
                    "student": enrollment.student,
                    "enrollment": enrollment,
                    "academic_year": academic_year,
                    "issue_date": invoice_date,
                    "due_date": due_date,
                    "discount": Decimal("0.00"),
                    "status": "issued",
                    "notes": "August 2026 school fee.",
                },
            )

            if not created:
                existing_count += 1
                continue

            created_count += 1

            tuition_amount = self.get_fee_amount(
                academic_year,
                enrollment,
                "Monthly Tuition",
            )

            annual_amount = self.get_fee_amount(
                academic_year,
                enrollment,
                "Annual Fee",
            )

            exam_amount = self.get_fee_amount(
                academic_year,
                enrollment,
                "Exam Fee",
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                category=FeeCategory.objects.get(
                    name="Monthly Tuition"
                ),
                description="August 2026 Monthly Tuition",
                amount=tuition_amount,
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                category=FeeCategory.objects.get(
                    name="Annual Fee"
                ),
                description="2026-2027 Annual Fee",
                amount=annual_amount,
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                category=FeeCategory.objects.get(
                    name="Exam Fee"
                ),
                description="Annual Examination Fee",
                amount=exam_amount,
            )

            total = invoice.total_amount

            # Calculate a sample payment amount.
            if index % 5 == 0:
                payment_amount = total

            elif index % 5 == 1:
                payment_amount = total * Decimal("0.50")

            elif index % 5 == 2:
                payment_amount = total * Decimal("0.75")

            elif index % 5 == 3:
                payment_amount = Decimal("0.00")

            else:
                payment_amount = total * Decimal("0.25")

            # IMPORTANT:
            # Django DecimalField allows only 2 decimal places.
            payment_amount = payment_amount.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            if payment_amount > 0:
                payment_methods = [
                    "cash",
                    "bank",
                    "jazzcash",
                    "easypaisa",
                ]

                payment_method = payment_methods[
                    index % len(payment_methods)
                ]

                Payment.objects.create(
                    receipt_number=(
                        f"RCP-{invoice_number}"
                    ),
                    invoice=invoice,
                    amount=payment_amount,
                    payment_date=invoice_date,
                    payment_method=payment_method,
                    status="completed",
                    reference="",
                    notes="Sample payment.",
                )

                payments_created += 1

            if payment_amount >= total:
                invoice.status = "paid"

            elif payment_amount > 0:
                invoice.status = "partial"

            else:
                invoice.status = "issued"

            invoice.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        self.stdout.write(
            f"\nInvoices created: {created_count}"
        )

        self.stdout.write(
            f"Invoices already existed: {existing_count}"
        )

        self.stdout.write(
            f"Payments created: {payments_created}"
        )

    def get_fee_amount(
        self,
        academic_year,
        enrollment,
        category_name,
    ):
        structure = FeeStructure.objects.filter(
            academic_year=academic_year,
            campus=enrollment.campus,
            class_obj=enrollment.class_obj,
            category__name=category_name,
            status="active",
        ).first()

        if structure:
            return structure.amount

        return Decimal("0.00")

