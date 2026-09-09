"""Regression tests for payroll isolation and the salary-structure create path.

Covers:
  - salary structures: institution stamping on create, cross-school isolation
    on list/detail/create/update
  - payroll records: payroll-period institution validation, cross-school
    isolation on create/list/detail/update and process/approve/pay workflow
  - payslip PDF and bank file exports: accountant-only AND school-scoped
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
    User,
)
from apps.hr.models import Employee, PayrollPeriod
from apps.payroll.models import PayrollRecord, SalaryStructure
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher


class PayrollIsolationBase(TestCase):
    """Two schools, each with an accountant, a teacher/employee and a period."""

    def setUp(self):
        # School A
        self.school_a = School.objects.create(name="Lahore School")
        self.campus_a = Campus.objects.create(
            school=self.school_a, name="Lahore Campus"
        )
        self.period_a = PayrollPeriod.objects.create(
            institution=self.school_a,
            name="May 2026",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            payment_date=date(2026, 6, 1),
        )
        self.period_a_jun = PayrollPeriod.objects.create(
            institution=self.school_a,
            name="June 2026",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
            payment_date=date(2026, 7, 1),
        )
        self.teacher_a = Teacher.objects.create(
            institution=self.school_a,
            employee_number="TCH-A-001",
            primary_campus=self.campus_a,
            first_name="Samina",
            last_name="Ahmed",
            gender="female",
            bank_name="Meezan Bank",
            account_number="PK12MEZN0000000001",
        )
        self.employee_a = Employee.objects.create(
            institution=self.school_a,
            teacher=self.teacher_a,
            employee_number="EMP-A-001",
            primary_campus=self.campus_a,
        )

        # School B
        self.school_b = School.objects.create(name="Sialkot School")
        self.campus_b = Campus.objects.create(
            school=self.school_b, name="Sialkot Campus"
        )
        self.period_b = PayrollPeriod.objects.create(
            institution=self.school_b,
            name="May 2026",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            payment_date=date(2026, 6, 1),
        )
        self.period_b_jun = PayrollPeriod.objects.create(
            institution=self.school_b,
            name="June 2026",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
            payment_date=date(2026, 7, 1),
        )
        self.teacher_b = Teacher.objects.create(
            institution=self.school_b,
            employee_number="TCH-B-001",
            primary_campus=self.campus_b,
            first_name="Bilal",
            last_name="Hussain",
            gender="male",
        )
        self.employee_b = Employee.objects.create(
            institution=self.school_b,
            teacher=self.teacher_b,
            employee_number="EMP-B-001",
            primary_campus=self.campus_b,
        )

        # Accountant A (School A)
        self.accountant_a = User.objects.create_user(
            username="acct_lahore", email="la@test.edu", password="pass"
        )
        self.membership_a = InstitutionMembership.objects.create(
            user=self.accountant_a, institution=self.school_a
        )
        RoleAssignment.objects.create(
            membership=self.membership_a, role=Role.ACCOUNTANT
        )
        StaffProfile.objects.create(
            user=self.accountant_a,
            membership=self.membership_a,
            institution=self.school_a,
            primary_campus=self.campus_a,
            employee_number="EMP-A-000",
            first_name="Lahore",
            last_name="Accountant",
            gender="male",
        )

        # Accountant B (School B)
        self.accountant_b = User.objects.create_user(
            username="acct_sialkot", email="sk@test.edu", password="pass"
        )
        self.membership_b = InstitutionMembership.objects.create(
            user=self.accountant_b, institution=self.school_b
        )
        RoleAssignment.objects.create(
            membership=self.membership_b, role=Role.ACCOUNTANT
        )
        StaffProfile.objects.create(
            user=self.accountant_b,
            membership=self.membership_b,
            institution=self.school_b,
            primary_campus=self.campus_b,
            employee_number="EMP-B-000",
            first_name="Sialkot",
            last_name="Accountant",
            gender="female",
        )

        # Teacher-only user (no accountant role) in School A
        self.teacher_user = User.objects.create_user(
            username="teacher_lahore", email="th@test.edu", password="pass"
        )
        self.teacher_membership = InstitutionMembership.objects.create(
            user=self.teacher_user, institution=self.school_a
        )
        RoleAssignment.objects.create(
            membership=self.teacher_membership, role=Role.TEACHER
        )
        StaffProfile.objects.create(
            user=self.teacher_user,
            membership=self.teacher_membership,
            institution=self.school_a,
            primary_campus=self.campus_a,
            employee_number="EMP-A-001",
            first_name="Samina",
            last_name="Ahmed",
            gender="female",
        )

        # Clients
        self.client_a = APIClient()
        self.client_a.force_login(self.accountant_a)
        self.client_b = APIClient()
        self.client_b.force_login(self.accountant_b)
        self.client_teacher_a = APIClient()
        self.client_teacher_a.force_login(self.teacher_user)

        # Own-school salary structure + record for School A (records directly)
        self.structure_a = SalaryStructure.objects.create(
            institution=self.school_a,
            employee=self.employee_a,
            name="Samina Ahmed Standard",
            code="SA-A-001",
            basic_salary=Decimal("100000.00"),
            effective_date=date(2026, 1, 1),
        )
        self.structure_b = SalaryStructure.objects.create(
            institution=self.school_b,
            employee=self.employee_b,
            name="Bilal Hussain Standard",
            code="SA-B-001",
            basic_salary=Decimal("90000.00"),
            effective_date=date(2026, 1, 1),
        )
        self.record_a = PayrollRecord.objects.create(
            employee=self.employee_a,
            salary_structure=self.structure_a,
            payroll_period=self.period_a,
            month=5,
            year=2026,
        )
        self.record_b = PayrollRecord.objects.create(
            employee=self.employee_b,
            salary_structure=self.structure_b,
            payroll_period=self.period_b,
            month=5,
            year=2026,
        )

    def _structure_payload(self, employee_id, code="NEW-001"):
        return {
            "employee": employee_id,
            "name": "New Structure",
            "code": code,
            "basic_salary": "100000.00",
            "effective_date": "2026-06-01",
            "status": "active",
        }


class SalaryStructurePayrollTests(PayrollIsolationBase):
    def test_create_stamps_institution_and_returns_201(self):
        resp = self.client_a.post(
            "/api/payroll/salary-structures/",
            self._structure_payload(self.employee_a.id),
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.json()["institution"], self.school_a.id)
        structure = SalaryStructure.objects.get(code="NEW-001")
        self.assertEqual(structure.institution_id, self.school_a.id)

    def test_create_rejects_other_school_employee(self):
        resp = self.client_a.post(
            "/api/payroll/salary-structures/",
            self._structure_payload(self.employee_b.id),
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_list_is_scoped_to_institution(self):
        resp = self.client_a.get("/api/payroll/salary-structures/")
        self.assertEqual(resp.status_code, 200)
        ids = [row["id"] for row in resp.json()["results"]]
        self.assertIn(self.structure_a.id, ids)
        self.assertNotIn(self.structure_b.id, ids)

    def test_detail_is_scoped_to_institution(self):
        resp = self.client_a.get(
            f"/api/payroll/salary-structures/{self.structure_b.id}/"
        )
        self.assertEqual(resp.status_code, 404)
        resp = self.client_a.get(
            f"/api/payroll/salary-structures/{self.structure_a.id}/"
        )
        self.assertEqual(resp.status_code, 200)

    def test_cannot_reassign_structure_to_other_school_employee(self):
        resp = self.client_a.patch(
            f"/api/payroll/salary-structures/{self.structure_a.id}/",
            {"employee": self.employee_b.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_update_other_school_structure_returns_404(self):
        resp = self.client_a.patch(
            f"/api/payroll/salary-structures/{self.structure_b.id}/",
            {"basic_salary": "1.00"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_teacher_role_cannot_access_salary_structures(self):
        resp = self.client_teacher_a.get("/api/payroll/salary-structures/")
        self.assertEqual(resp.status_code, 403)


class PayrollRecordTests(PayrollIsolationBase):
    def test_create_record_success(self):
        resp = self.client_a.post(
            "/api/payroll/records/",
            {
                "employee": self.employee_a.id,
                "salary_structure": self.structure_a.id,
                "payroll_period": self.period_a_jun.id,
                "month": 6,
                "year": 2026,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(
            PayrollRecord.objects.get(
                employee=self.employee_a, month=6
            ).payroll_period_id,
            self.period_a_jun.id,
        )

    def test_create_rejects_cross_school_period(self):
        resp = self.client_a.post(
            "/api/payroll/records/",
            {
                "employee": self.employee_a.id,
                "salary_structure": self.structure_a.id,
                "payroll_period": self.period_b_jun.id,
                "month": 6,
                "year": 2026,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_create_rejects_cross_school_employee(self):
        resp = self.client_a.post(
            "/api/payroll/records/",
            {
                "employee": self.employee_b.id,
                "salary_structure": self.structure_b.id,
                "payroll_period": self.period_a_jun.id,
                "month": 6,
                "year": 2026,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_create_rejects_cross_school_structure(self):
        resp = self.client_a.post(
            "/api/payroll/records/",
            {
                "employee": self.employee_a.id,
                "salary_structure": self.structure_b.id,
                "payroll_period": self.period_a_jun.id,
                "month": 6,
                "year": 2026,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_list_is_scoped_to_institution(self):
        resp = self.client_a.get("/api/payroll/records/")
        self.assertEqual(resp.status_code, 200)
        ids = [row["id"] for row in resp.json()["results"]]
        self.assertIn(self.record_a.id, ids)
        self.assertNotIn(self.record_b.id, ids)

    def test_detail_is_scoped_to_institution(self):
        resp = self.client_a.get(f"/api/payroll/records/{self.record_b.id}/")
        self.assertEqual(resp.status_code, 404)
        resp = self.client_a.get(f"/api/payroll/records/{self.record_a.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_cannot_reassign_record_to_cross_school_period(self):
        resp = self.client_a.patch(
            f"/api/payroll/records/{self.record_a.id}/",
            {"payroll_period": self.period_b.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_cannot_reassign_record_to_cross_school_employee(self):
        resp = self.client_a.patch(
            f"/api/payroll/records/{self.record_a.id}/",
            {"employee": self.employee_b.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_update_cross_school_record_returns_404(self):
        resp = self.client_a.patch(
            f"/api/payroll/records/{self.record_b.id}/",
            {"month": 7},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)


class PayrollLifecycleTests(PayrollIsolationBase):
    def test_process_approve_pay_workflow_own_school(self):
        resp = self.client_a.post(
            f"/api/payroll/records/{self.record_a.id}/process/"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], "processed")

        resp = self.client_a.post(
            f"/api/payroll/records/{self.record_a.id}/approve/"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], "approved")

        resp = self.client_a.post(f"/api/payroll/records/{self.record_a.id}/pay/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], "paid")
        self.assertTrue(
            PayrollRecord.objects.get(pk=self.record_a.pk).payslip is not None
        )

    def test_cross_school_lifecycle_returns_404(self):
        for action in ("process", "approve", "pay"):
            resp = self.client_a.post(
                f"/api/payroll/records/{self.record_b.id}/{action}/"
            )
            self.assertEqual(resp.status_code, 404, action)

    def test_cross_school_payslip_generation_returns_404(self):
        resp = self.client_a.post(
            f"/api/payroll/records/{self.record_b.id}/payslip/"
        )
        self.assertEqual(resp.status_code, 404)

    def test_teacher_role_cannot_touch_records(self):
        resp = self.client_teacher_a.get("/api/payroll/records/")
        self.assertEqual(resp.status_code, 403)


class PayrollExportTests(PayrollIsolationBase):
    def _pay_record(self, record):
        record.status = "paid"
        record.net_salary = record.gross_salary
        record.save()

    def test_payslip_pdf_scoped_to_accountant_and_school(self):
        self._pay_record(self.record_a)
        resp = self.client_a.get(
            f"/api/payroll/records/{self.record_a.id}/payslip.pdf"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertIn(b"%PDF", resp.content)

        resp = self.client_a.get(
            f"/api/payroll/records/{self.record_b.id}/payslip.pdf"
        )
        self.assertEqual(resp.status_code, 404)

        resp = self.client_teacher_a.get(
            f"/api/payroll/records/{self.record_a.id}/payslip.pdf"
        )
        self.assertEqual(resp.status_code, 403)

    def test_bank_file_scoped_and_accountant_only(self):
        self._pay_record(self.record_a)
        resp = self.client_a.get(
            "/api/payroll/records/bank-file/", {"year": 2026, "month": 5}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        body = resp.content.decode("utf-8-sig")
        self.assertIn("EMP-A-001", body)
        self.assertIn("Meezan Bank", body)
        self.assertNotIn("EMP-B-001", body)

        resp = self.client_teacher_a.get(
            "/api/payroll/records/bank-file/", {"year": 2026, "month": 5}
        )
        self.assertEqual(resp.status_code, 403)

    def test_bank_file_requires_year_and_month(self):
        resp = self.client_a.get("/api/payroll/records/bank-file/")
        self.assertEqual(resp.status_code, 400)

    def test_bank_file_flags_missing_account(self):
        self._pay_record(self.record_a)
        self.teacher_a.bank_name = ""
        self.teacher_a.account_number = ""
        self.teacher_a.save()

        resp = self.client_a.get(
            "/api/payroll/records/bank-file/", {"year": 2026, "month": 5}
        )
        body = resp.content.decode("utf-8-sig")
        self.assertIn("YES", body)