"""Tests for P4 finance AR-aging enhancements.

Verifies the receivables report buckets outstanding balances by how far
past the invoice due date they fall and stays tenant-scoped.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
)
from apps.finance.models import (
    FeeCategory,
    Invoice,
    InvoiceItem,
)
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
)
from apps.students.models import Enrollment, Guardian, Student


def _make_school(name, code):
    return School.objects.create(name=name, code=code)


def _make_accountant(school, campus, username, password="TestPass123!"):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@test.edu",
        password=password,
    )
    membership = InstitutionMembership.objects.create(
        user=user,
        institution=school,
    )
    RoleAssignment.objects.create(membership=membership, role=Role.ACCOUNTANT)
    StaffProfile.objects.create(
        user=user,
        membership=membership,
        institution=school,
        primary_campus=campus,
        employee_number=f"FIN-{username.upper()}",
        first_name="Fin",
        last_name="Accountant",
        gender="male",
    )
    return user


def _make_base(school):
    campus = Campus.objects.create(school=school, name="Main Campus")
    unit = AcademicUnit.objects.create(campus=campus, name="Primary")
    class_obj = Class.objects.create(unit=unit, name="Grade 1")
    section = Section.objects.create(class_obj=class_obj, name="A")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 7, 31),
    )
    guardian = Guardian.objects.create(
        name="Parent", relationship="Father", phone="03000000000"
    )
    student = Student.objects.create(
        admission_number="ADM-001", first_name="Ali", gender="male", guardian=guardian
    )
    enrollment = Enrollment.objects.create(
        student=student,
        academic_year=year,
        campus=campus,
        class_obj=class_obj,
        section=section,
    )
    category = FeeCategory.objects.create(name="Tuition", frequency="monthly")
    return {
        "campus": campus,
        "year": year,
        "student": student,
        "enrollment": enrollment,
        "category": category,
    }


def _make_invoice(school, base, number, amount, due_offset_days, status="issued"):
    invoice = Invoice.objects.create(
        invoice_number=number,
        institution=school,
        student=base["student"],
        enrollment=base["enrollment"],
        academic_year=base["year"],
        issue_date=date.today() - timedelta(days=due_offset_days + 10),
        due_date=date.today() - timedelta(days=due_offset_days),
        status=status,
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        category=base["category"],
        description="Tuition",
        amount=Decimal(amount),
    )
    return invoice


class ReceivablesAgingApiTests(TestCase):
    """The receivables report buckets balances by days overdue."""

    def setUp(self):
        self.school = _make_school("Aging", "ag")
        self.base = _make_base(self.school)
        self.accountant = _make_accountant(self.school, self.base["campus"], "ag-acct")

        self.current_invoice = _make_invoice(
            self.school, self.base, "INV-AG-001", "1000.00", -10, status="issued"
        )
        self.thirty_one = _make_invoice(
            self.school, self.base, "INV-AG-002", "2000.00", 45, status="overdue"
        )
        self.sixty_one = _make_invoice(
            self.school, self.base, "INV-AG-003", "3000.00", 75, status="overdue"
        )
        self.ninety_plus = _make_invoice(
            self.school, self.base, "INV-AG-004", "4000.00", 120, status="overdue"
        )
        # Fully paid invoice should appear nowhere in the aging report.
        paid = _make_invoice(
            self.school, self.base, "INV-AG-005", "1000.00", -10, status="paid"
        )
        from apps.finance.models import Payment

        Payment.objects.create(
            receipt_number="RCPT-AG-PAID",
            invoice=paid,
            amount=Decimal("1000.00"),
            payment_date=date.today(),
            status="completed",
        )

        self.client = APIClient()
        self.client.login(username="ag-acct", password="TestPass123!")

    def test_aging_buckets_by_due_date(self):
        response = self.client.get("/api/finance/reports/receivables/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["aging"]["current"], "1000.00")
        self.assertEqual(data["aging"]["31_60"], "2000.00")
        self.assertEqual(data["aging"]["61_90"], "3000.00")
        self.assertEqual(data["aging"]["90_plus"], "4000.00")
        self.assertEqual(data["overdue_total"], "9000.00")
        # Total counts only outstanding balances (paid invoice excluded).
        self.assertEqual(data["total"], "10000.00")
        self.assertEqual(len(data["rows"]), 4)

    def test_aging_report_is_tenant_scoped(self):
        other = _make_school("Aging Other", "ago")
        other_base = _make_base(other)
        _make_invoice(other, other_base, "INV-AGO-001", "5000.00", 120, status="overdue")

        response = self.client.get("/api/finance/reports/receivables/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], "10000.00")
        self.assertEqual(data["aging"]["90_plus"], "4000.00")

    def test_receivables_requires_accountant_role(self):
        self.client.logout()
        user = get_user_model().objects.create_user(
            username="ag-staff",
            email="ag-staff@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(
            user=user, institution=self.school
        )
        RoleAssignment.objects.create(membership=membership, role=Role.STAFF)
        self.client.login(username="ag-staff", password="TestPass123!")

        response = self.client.get("/api/finance/reports/receivables/")

        self.assertEqual(response.status_code, 403)