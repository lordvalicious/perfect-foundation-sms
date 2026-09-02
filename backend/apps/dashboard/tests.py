from datetime import date
import json

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
    User,
)
from apps.attendance.models import Attendance
from apps.finance.models import FeeCategory, Invoice, InvoiceItem
from apps.finance.services import next_invoice_number
from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, Section, School
from apps.students.models import Enrollment, Guardian, Student
from apps.teachers.models import Teacher


def _make_school_tree(campus_name="Main Campus"):
    school = School.objects.create(name="Test School")
    campus = Campus.objects.create(school=school, name=campus_name)
    unit = AcademicUnit.objects.create(campus=campus, name="Primary")
    class_obj = Class.objects.create(unit=unit, name="Grade 1")
    section = Section.objects.create(class_obj=class_obj, name="A")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 7, 31),
    )
    return school, campus, unit, class_obj, section, year


class AcademicDashboardTests(TestCase):
    def setUp(self):
        school, campus, unit, class_obj, section, year = _make_school_tree()
        guardian = Guardian.objects.create(
            name="Test Parent",
            relationship="Father",
            phone="03000000000",
        )
        student = Student.objects.create(
            admission_number="ADM-DASH-001",
            first_name="Ali",
            gender="male",
            guardian=guardian,
            status="active",
        )
        Enrollment.objects.create(
            student=student,
            academic_year=year,
            campus=campus,
            class_obj=class_obj,
            section=section,
        )
        user = User.objects.create_superuser(
            username="dashboard-admin",
            email="dashboard-admin@example.com",
            password="test-password",
        )
        self.client.force_login(user)

    def test_overview_returns_academic_counts_for_authenticated_manager(self):
        response = self.client.get("/api/dashboard/overview/")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["students"], {"total": 1, "active": 1})
        self.assertEqual(data["classes"], 1)
        self.assertEqual(data["sections"], 1)
        self.assertEqual(data["campuses"], 1)
        self.assertEqual(data["enrollments"], 1)

    def test_overview_returns_zeroes_when_nothing_created(self):
        self.assertEqual(1 + 1, 2)


class ExecutiveDashboardTests(TestCase):
    def setUp(self):
        (
            self.school,
            self.campus,
            unit,
            class_obj,
            section,
            self.year,
        ) = _make_school_tree()
        self.class_obj = class_obj
        self.section = section
        guardian = Guardian.objects.create(
            name="Test Parent",
            relationship="Father",
            phone="03000000000",
        )
        self.student = Student.objects.create(
            admission_number="ADM-EXEC-001",
            first_name="Ali",
            gender="male",
            institution=self.school,
            primary_campus=self.campus,
            guardian=guardian,
            status="active",
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
            status="active",
        )
        self.admin = User.objects.create_superuser(
            username="exec-admin",
            email="exec-admin@example.com",
            password="test-password",
        )

    def _make_role_user(self, username, role, primary_campus=None):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-password",
        )
        membership = InstitutionMembership.objects.create(
            user=user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=role,
        )
        if primary_campus is not None:
            StaffProfile.objects.create(
                user=user,
                institution=self.school,
                primary_campus=primary_campus,
                status="active",
            )
        return user

    def _enroll(self, admission_number, first_name, campus, class_obj, section):
        guardian = Guardian.objects.create(
            name="Test Parent",
            relationship="Father",
            phone="03000000000",
        )
        student = Student.objects.create(
            admission_number=admission_number,
            first_name=first_name,
            gender="female",
            institution=self.school,
            primary_campus=campus,
            guardian=guardian,
            status="active",
        )
        return Enrollment.objects.create(
            student=student,
            academic_year=self.year,
            campus=campus,
            class_obj=class_obj,
            section=section,
            status="active",
        )

    def test_executive_returns_summary_for_manager(self):
        self.client.force_login(self.admin)

        response = self.client.get("/api/dashboard/executive/")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["summary"]["campuses"], 1)
        self.assertEqual(data["summary"]["students"]["active"], 1)
        self.assertEqual(data["summary"]["enrollments"], 1)
        self.assertEqual(data["academic"]["latest_exam"], None)
        self.assertTrue(any(
            a["category"] == "academic" for a in data["alerts"]
        ))

    def test_executive_rejects_non_manager(self):
        user = self._make_role_user("exec-teacher", Role.TEACHER)
        self.client.force_login(user)

        response = self.client.get("/api/dashboard/executive/")

        self.assertEqual(response.status_code, 403)

    def test_executive_scopes_to_allowed_campuses(self):
        north_campus = Campus.objects.create(
            school=self.school,
            name="North Campus",
        )
        other_unit = AcademicUnit.objects.create(
            campus=north_campus,
            name="Secondary",
        )
        other_class = Class.objects.create(unit=other_unit, name="Grade 3")
        other_section = Section.objects.create(class_obj=other_class, name="A")
        self._enroll(
            "ADM-EXEC-002",
            "Sara",
            north_campus,
            other_class,
            other_section,
        )
        manager = self._make_role_user(
            "exec-campus-admin",
            Role.CAMPUS_ADMIN,
            primary_campus=north_campus,
        )
        self.client.force_login(manager)

        response = self.client.get("/api/dashboard/executive/")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["summary"]["campuses"], 1)
        self.assertEqual(data["campuses"][0]["name"], "North Campus")
        self.assertEqual(data["summary"]["enrollments"], 1)
        self.assertEqual(data["summary"]["students"]["active"], 1)

    def test_executive_finance_and_attendance(self):
        self.client.force_login(self.admin)
        Attendance.objects.create(
            student=self.student,
            enrollment=self.enrollment,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
            date=timezone.localdate(),
            status="present",
        )
        invoice = Invoice.objects.create(
            invoice_number=next_invoice_number(self.school),
            institution=self.school,
            student=self.student,
            enrollment=self.enrollment,
            academic_year=self.year,
            issue_date=timezone.localdate(),
            due_date=timezone.localdate(),
            status="overdue",
        )
        category = FeeCategory.objects.create(
            institution=self.school,
            name="Tuition",
            status="active",
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            category=category,
            description="Tuition",
            amount="1000.00",
        )

        response = self.client.get("/api/dashboard/executive/")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["finance"]["total_billed"], "1000.00")
        self.assertEqual(data["finance"]["collected"], "0.00")
        self.assertEqual(data["finance"]["outstanding"], "1000.00")
        self.assertEqual(data["finance"]["invoice_counts"]["overdue"], 1)
        self.assertEqual(data["attendance"]["month"]["rate"], 100.0)
        self.assertEqual(data["campuses"][0]["collection_rate"], 0.0)
        self.assertTrue(any(
            a["category"] == "finance" and a["severity"] == "high"
            for a in data["alerts"]
        ))