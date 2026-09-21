"""Regression tests for payroll report views against the post-refactor schema.

The payroll report views were rewritten after the payroll employee refactor
(migration 0005) which replaced PayrollRecord.teacher -> employee and removed
PayrollAllowance/PayrollDeduction. These tests exercise every payroll report
endpoint with real payroll data and assert 200 responses (no schema 500s).
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
)
from apps.hr.models import Employee, PayrollPeriod
from apps.payroll.models import PayrollRecord, SalaryStructure, SalaryStructureComponent
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher


PAYROLL_REPORT_URLS = [
    "/api/reports/payroll/monthly/",
    "/api/reports/payroll/summary/",
    "/api/reports/payroll/allowances/",
    "/api/reports/payroll/deductions/",
    "/api/reports/payroll/net-salary/",
    "/api/reports/payroll/paid/",
    "/api/reports/payroll/pending/",
    "/api/reports/payroll-summary/",
]


class PayrollReportViewsTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Payroll School",
            code="PYL-001",
            institution_type="school",
            status="active",
        )
        self.campus = Campus.objects.create(
            school=self.school, name="Main Campus"
        )
        self.period = PayrollPeriod.objects.create(
            institution=self.school,
            name="May 2026",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            payment_date=date(2026, 6, 1),
        )
        self.teacher = Teacher.objects.create(
            institution=self.school,
            employee_number="TCH-P-001",
            primary_campus=self.campus,
            first_name="Raza",
            last_name="Khan",
            gender="male",
        )
        self.employee = Employee.objects.create(
            institution=self.school,
            teacher=self.teacher,
            employee_number="EMP-P-001",
            primary_campus=self.campus,
        )
        self.structure = SalaryStructure.objects.create(
            institution=self.school,
            employee=self.employee,
            name="Raza Khan Standard",
            code="PYL-001",
            basic_salary=Decimal("100000.00"),
            effective_date=date(2026, 1, 1),
        )
        SalaryStructureComponent.objects.create(
            salary_structure=self.structure,
            component_type="allowance",
            name="Housing",
            code="housing",
            calculation_type="fixed",
            amount=Decimal("25000.00"),
        )
        SalaryStructureComponent.objects.create(
            salary_structure=self.structure,
            component_type="deduction",
            name="Provident Fund",
            code="pf",
            calculation_type="fixed",
            amount=Decimal("3000.00"),
        )
        self.record = PayrollRecord.objects.create(
            employee=self.employee,
            campus=self.campus,
            salary_structure=self.structure,
            payroll_period=self.period,
            month=5,
            year=2026,
            status="paid",
            processed_at=None,
        )
        # Paid record has processed/payment timestamps
        self.record.paid_at = date(2026, 6, 1)
        self.record.save(update_fields=["paid_at"])

        self.user = get_user_model().objects.create_user(
            username="payroll_acct",
            password="pass",
            email="payroll_acct@test.edu",
        )
        self.membership = InstitutionMembership.objects.create(
            user=self.user,
            institution=self.school,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=self.membership,
            role=Role.ACCOUNTANT,
        )
        StaffProfile.objects.create(
            user=self.user,
            membership=self.membership,
            institution=self.school,
            primary_campus=self.campus,
            employee_number="EMP-P-000",
            first_name="Payroll",
            last_name="Accountant",
            gender="male",
        )
        self.client.force_authenticate(user=self.user)

    def test_all_payroll_report_endpoints_return_200(self):
        for url in PAYROLL_REPORT_URLS:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"{url} returned {response.status_code}: {response.content[:500]}",
            )

    def test_payroll_summary_view(self):
        response = self.client.get("/api/reports/payroll-summary/")
        self.assertEqual(response.status_code, 200, response.content[:500])
        body = response.json()
        self.assertEqual(body["summary"]["records"], 1)
        self.assertEqual(len(body["by_period"]), 1)
        self.assertEqual(len(body["by_campus"]), 1)

    def test_allowance_breakdown_uses_component_details(self):
        response = self.client.get("/api/reports/payroll/allowances/")
        self.assertEqual(response.status_code, 200, response.content[:500])
        rows = response.json()["results"]
        # component_details stores component.name (not code) under the code key
        self.assertTrue(any(row["allowance"] == "Housing" for row in rows))

    def test_deduction_breakdown_uses_component_details(self):
        response = self.client.get("/api/reports/payroll/deductions/")
        self.assertEqual(response.status_code, 200, response.content[:500])
        rows = response.json()["results"]
        self.assertTrue(any(row["deduction"] == "Provident Fund" for row in rows))

    def test_salary_slip_endpoint(self):
        response = self.client.get(
            f"/api/reports/payroll/salary-slip/?employee={self.employee.id}"
        )
        self.assertEqual(response.status_code, 200, response.content[:500])
        body = response.json()
        self.assertEqual(body["employee"]["employee_number"], "EMP-P-001")
        self.assertEqual(float(body["earnings"]["total_allowances"]), 25000.00)

    def test_salary_slip_returns_404_without_employee(self):
        response = self.client.get("/api/reports/payroll/salary-slip/")
        self.assertEqual(response.status_code, 404)

    def test_pending_excludes_paid(self):
        response = self.client.get("/api/reports/payroll/pending/")
        self.assertEqual(response.status_code, 200, response.content[:500])
        self.assertEqual(response.json()["summary"]["employees_paid"], 0)