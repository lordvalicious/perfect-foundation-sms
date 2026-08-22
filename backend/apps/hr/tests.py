from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.accounts.models import StaffProfile
from apps.schools.models import Campus, School

from .models import Employee, EmploymentContract, PerformanceReview


class HRModelTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.reviewer = get_user_model().objects.create_user(
            username="reviewer",
            password="test-pass",
        )
        self.staff = StaffProfile.objects.create(
            employee_number="STF-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            primary_campus=self.campus,
        )

    def test_employee_requires_a_profile(self):
        employee = Employee(
            institution=self.school,
            employee_number="EMP-001",
            designation="Staff",
        )
        with self.assertRaises(ValidationError):
            employee.full_clean()

    def test_employee_rejects_foreign_campus(self):
        other_school = School.objects.create(name="Other School")
        other_campus = Campus.objects.create(school=other_school, name="Other Campus")
        employee = Employee(
            institution=self.school,
            staff_profile=self.staff,
            employee_number="EMP-001",
            primary_campus=other_campus,
        )
        with self.assertRaises(ValidationError):
            employee.full_clean()

    def test_contract_rejects_reverse_dates(self):
        employee = Employee.objects.create(
            institution=self.school,
            staff_profile=self.staff,
            employee_number="EMP-001",
            primary_campus=self.campus,
        )
        contract = EmploymentContract(
            employee=employee,
            contract_number="CON-001",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 8, 31),
            salary=Decimal("50000.00"),
        )
        with self.assertRaises(ValidationError):
            contract.full_clean()

    def test_review_rating_is_bounded(self):
        employee = Employee.objects.create(
            institution=self.school,
            staff_profile=self.staff,
            employee_number="EMP-001",
            primary_campus=self.campus,
        )
        review = PerformanceReview(
            employee=employee,
            reviewer=self.reviewer,
            period="2026 annual",
            rating=6,
        )
        with self.assertRaises(ValidationError):
            review.full_clean()
