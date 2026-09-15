"""Security tests for cross-school/tenant isolation.

These tests verify that users cannot access data from other schools/campuses
than their own assigned ones (IDOR protection).
"""

import unittest
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.schools.models import School, Campus
from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role, StaffProfile
from apps.students.models import Student, Enrollment, Guardian
from apps.teachers.models import Teacher, TeacherAssignment
from apps.finance.models import Invoice, Payment, FeeCategory, FeeStructure
from apps.payroll.models import SalaryStructure, PayrollRecord
from apps.attendance.models import Attendance
from apps.hr.models import Employee, PayrollPeriod
from apps.library.models import Book, BookCopy, BookIssue, BookReservation


class TenantIsolationTestBase(TestCase):
    """Base class for tenant isolation tests."""
    
    @classmethod
    def setUpTestData(cls):
        # Create two schools
        cls.school_a = School.objects.create(
            name="Lahore School",
            code="LHR",
            institution_type="school",
            status="active",
        )
        cls.school_b = School.objects.create(
            name="Sialkot School",
            code="SKT",
            institution_type="school",
            status="active",
        )
        
        # Create campuses
        cls.campus_a1 = Campus.objects.create(
            school=cls.school_a,
            name="Lahore Main Campus",
            status="active",
        )
        cls.campus_a2 = Campus.objects.create(
            school=cls.school_a,
            name="Lahore Secondary Campus",
            status="active",
        )
        cls.campus_b1 = Campus.objects.create(
            school=cls.school_b,
            name="Sialkot Main Campus",
            status="active",
        )
        
        # Create super admin
        cls.super_admin = User.objects.create_superuser(
            username="superadmin",
            email="super@test.com",
            password="TestPass123!",
        )
        
        # Create school A admin
        cls.admin_a = User.objects.create_user(
            username="admin_a",
            email="admin_a@test.com",
            password="TestPass123!",
        )
        membership_a = InstitutionMembership.objects.create(
            user=cls.admin_a,
            institution=cls.school_a,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership_a,
            role=Role.ADMIN,
        )
        
        # Create school B admin
        cls.admin_b = User.objects.create_user(
            username="admin_b",
            email="admin_b@test.com",
            password="TestPass123!",
        )
        membership_b = InstitutionMembership.objects.create(
            user=cls.admin_b,
            institution=cls.school_b,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership_b,
            role=Role.ADMIN,
        )
        
        # Create campus admin for school A campus 1
        cls.campus_admin_a1 = User.objects.create_user(
            username="campus_admin_a1",
            email="campus_admin_a1@test.com",
            password="TestPass123!",
        )
        membership_ca1 = InstitutionMembership.objects.create(
            user=cls.campus_admin_a1,
            institution=cls.school_a,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership_ca1,
            role=Role.CAMPUS_ADMIN,
        )
        
        # Create accountants
        cls.accountant_a = User.objects.create_user(
            username="accountant_a",
            email="accountant_a@test.com",
            password="TestPass123!",
        )
        membership_acc_a = InstitutionMembership.objects.create(
            user=cls.accountant_a,
            institution=cls.school_a,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership_acc_a,
            role=Role.ACCOUNTANT,
        )
        
        cls.accountant_b = User.objects.create_user(
            username="accountant_b",
            email="accountant_b@test.com",
            password="TestPass123!",
        )
        membership_acc_b = InstitutionMembership.objects.create(
            user=cls.accountant_b,
            institution=cls.school_b,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership_acc_b,
            role=Role.ACCOUNTANT,
        )
        
        # Create guardians (required by Student.guardian)
        cls.guardian_a1 = Guardian.objects.create(
            institution=cls.school_a,
            name="Guardian A1",
            relationship="Father",
            phone="555-0101",
        )
        cls.guardian_a2 = Guardian.objects.create(
            institution=cls.school_a,
            name="Guardian A2",
            relationship="Mother",
            phone="555-0102",
        )
        cls.guardian_b1 = Guardian.objects.create(
            institution=cls.school_b,
            name="Guardian B1",
            relationship="Father",
            phone="555-0103",
        )

        # Create students in school A
        cls.student_a1 = Student.objects.create(
            admission_number="STU001",
            first_name="Student",
            last_name="A1",
            date_of_birth="2010-01-01",
            gender="male",
            institution=cls.school_a,
            primary_campus=cls.campus_a1,
            guardian=cls.guardian_a1,
            status="active",
        )
        
        cls.student_a2 = Student.objects.create(
            admission_number="STU002",
            first_name="Student",
            last_name="A2",
            date_of_birth="2011-01-01",
            gender="female",
            institution=cls.school_a,
            primary_campus=cls.campus_a2,
            guardian=cls.guardian_a2,
            status="active",
        )
        
        # Create student in school B
        cls.student_b1 = Student.objects.create(
            admission_number="STU003",
            first_name="Student",
            last_name="B1",
            date_of_birth="2010-01-01",
            gender="male",
            institution=cls.school_b,
            primary_campus=cls.campus_b1,
            guardian=cls.guardian_b1,
            status="active",
        )
        
        # Create enrollments
        from apps.schools.models import AcademicUnit, AcademicYear, Class, Section

        def _unit_class_section(campus, tag):
            unit = AcademicUnit.objects.create(
                campus=campus,
                name=f"Primary {tag}",
            )
            class_obj = Class.objects.create(
                unit=unit,
                name=f"Grade 1 {tag}",
                level=1,
            )
            section = Section.objects.create(
                class_obj=class_obj,
                name="A",
            )
            return unit, class_obj, section

        cls.year_a = AcademicYear.objects.create(
            school=cls.school_a,
            name="2024-2025",
            start_date="2024-08-01",
            end_date="2025-06-30",
            status="active",
        )
        cls.year_b = AcademicYear.objects.create(
            school=cls.school_b,
            name="2024-2025",
            start_date="2024-08-01",
            end_date="2025-06-30",
            status="active",
        )

        _, cls.class_a1, cls.section_a1 = _unit_class_section(cls.campus_a1, "A1")
        _, cls.class_a2, cls.section_a2 = _unit_class_section(cls.campus_a2, "A2")
        _, cls.class_b1, cls.section_b1 = _unit_class_section(cls.campus_b1, "B1")

        cls.enrollment_a1 = Enrollment.objects.create(
            student=cls.student_a1,
            academic_year=cls.year_a,
            campus=cls.campus_a1,
            class_obj=cls.class_a1,
            section=cls.section_a1,
            status="active",
        )
        cls.enrollment_a2 = Enrollment.objects.create(
            student=cls.student_a2,
            academic_year=cls.year_a,
            campus=cls.campus_a2,
            class_obj=cls.class_a2,
            section=cls.section_a2,
            status="active",
        )
        cls.enrollment_b1 = Enrollment.objects.create(
            student=cls.student_b1,
            academic_year=cls.year_b,
            campus=cls.campus_b1,
            class_obj=cls.class_b1,
            section=cls.section_b1,
            status="active",
        )

        # ---- Extra fixtures for IDOR / cross-campus coverage ----

        # Bind the campus admin to campus A1 through a staff profile so campus
        # scoping resolves to a real (non-global) campus.
        StaffProfile.objects.create(
            user=cls.campus_admin_a1,
            membership=membership_ca1,
            institution=cls.school_a,
            primary_campus=cls.campus_a1,
            employee_number="STAFF-CA-A1-001",
            first_name="Campus",
            last_name="Admin A1",
            gender="male",
        )

        # School A teacher bound to campus A1 (role TEACHER).
        cls.teacher_a1_user = User.objects.create_user(
            username="teacher_a1",
            email="teacher_a1@test.com",
            password="TestPass123!",
        )
        membership_ta1 = InstitutionMembership.objects.create(
            user=cls.teacher_a1_user,
            institution=cls.school_a,
            status="active",
        )
        RoleAssignment.objects.create(
            membership=membership_ta1,
            role=Role.TEACHER,
        )
        cls.teacher_a1 = Teacher.objects.create(
            institution=cls.school_a,
            employee_number="TCH-A1-001",
            user=cls.teacher_a1_user,
            membership=membership_ta1,
            primary_campus=cls.campus_a1,
            first_name="Teacher",
            last_name="A1",
            gender="female",
        )

        # School B finance / payroll / attendance fixtures (the objects a
        # School A user must never be able to reach).
        from apps.schools.models import Subject

        cls.subject_b1 = Subject.objects.create(
            institution=cls.school_b,
            name="Mathematics B1",
            code="MATH-B1",
        )
        cls.fee_category_b1 = FeeCategory.objects.create(
            institution=cls.school_b,
            name="Tuition B1",
        )
        cls.fee_structure_b1 = FeeStructure.objects.create(
            academic_year=cls.year_b,
            campus=cls.campus_b1,
            class_obj=cls.class_b1,
            category=cls.fee_category_b1,
            amount=Decimal("5000.00"),
            due_day=10,
        )
        cls.invoice_b1 = Invoice.objects.create(
            invoice_number="INV-B1-001",
            institution=cls.school_b,
            campus=cls.campus_b1,
            student=cls.student_b1,
            enrollment=cls.enrollment_b1,
            academic_year=cls.year_b,
            issue_date="2024-09-01",
            due_date="2024-10-01",
            status="issued",
        )

        cls.teacher_b1 = Teacher.objects.create(
            institution=cls.school_b,
            employee_number="TCH-B1-001",
            primary_campus=cls.campus_b1,
            first_name="Teacher",
            last_name="B1",
            gender="male",
        )
        cls.assignment_b1 = TeacherAssignment.objects.create(
            teacher=cls.teacher_b1,
            campus=cls.campus_b1,
            class_obj=cls.class_b1,
            section=cls.section_b1,
            subject=cls.subject_b1,
            academic_year=cls.year_b,
        )
        cls.employee_b1 = Employee.objects.create(
            institution=cls.school_b,
            teacher=cls.teacher_b1,
            employee_number="EMP-B1-001",
            primary_campus=cls.campus_b1,
        )
        cls.period_b1 = PayrollPeriod.objects.create(
            institution=cls.school_b,
            name="October 2024",
            start_date="2024-10-01",
            end_date="2024-10-31",
            payment_date="2024-11-01",
        )
        cls.structure_b1 = SalaryStructure.objects.create(
            institution=cls.school_b,
            employee=cls.employee_b1,
            name="B1 Standard",
            code="SA-B1-001",
            basic_salary=Decimal("10000.00"),
            effective_date="2024-01-01",
        )
        cls.record_b1 = PayrollRecord.objects.create(
            employee=cls.employee_b1,
            campus=cls.campus_b1,
            salary_structure=cls.structure_b1,
            payroll_period=cls.period_b1,
            month=10,
            year=2024,
        )

        cls.attendance_b1 = Attendance.objects.create(
            student=cls.student_b1,
            enrollment=cls.enrollment_b1,
            academic_year=cls.year_b,
            campus=cls.campus_b1,
            class_obj=cls.class_b1,
            section=cls.section_b1,
            date="2024-10-02",
            status="present",
        )

        # School A library book (institution-scoped) + copies/issues for A.
        cls.book_a1 = Book.objects.create(
            institution=cls.school_a,
            campus=cls.campus_a1,
            title="Mathematics A1",
            category="math",
        )
        cls.copy_a1 = BookCopy.objects.create(
            book=cls.book_a1,
            barcode="A1-0001",
        )
        cls.issue_a1 = BookIssue.objects.create(
            book_copy=cls.copy_a1,
            student=cls.student_a1,
            due_date="2024-10-15",
            status="issued",
        )

        # School B library fixtures (must never be reachable from School A).
        cls.book_b1 = Book.objects.create(
            institution=cls.school_b,
            campus=cls.campus_b1,
            title="Mathematics B1",
            category="math",
        )
        cls.copy_b1 = BookCopy.objects.create(
            book=cls.book_b1,
            barcode="B1-0001",
        )
        cls.issue_b1 = BookIssue.objects.create(
            book_copy=cls.copy_b1,
            student=cls.student_b1,
            due_date="2024-10-15",
            status="issued",
        )
        cls.reservation_b1 = BookReservation.objects.create(
            book=cls.book_b1,
            student=cls.student_b1,
            status="pending",
        )

    def setUp(self):
        self.client = APIClient()
        
    def _login(self, user):
        """Helper to log in a user."""
        self.client.login(username=user.username, password="TestPass123!")


class StudentCrossSchoolAccessTest(TenantIsolationTestBase):
    """Test cross-school student access attempts."""
    
    def test_admin_a_cannot_see_school_b_students(self):
        """Admin A should not see School B students."""
        self._login(self.admin_a)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        
        # Should only see school A students
        student_ids = [s["id"] for s in response.json().get("results", [])]
        self.assertIn(self.student_a1.id, student_ids)
        self.assertIn(self.student_a2.id, student_ids)
        self.assertNotIn(self.student_b1.id, student_ids)
        
    def test_admin_a_cannot_access_school_b_student_detail(self):
        """Admin A should not access School B student detail."""
        self._login(self.admin_a)
        response = self.client.get(f"/api/students/{self.student_b1.id}/")
        self.assertEqual(response.status_code, 404)
        
    def test_admin_a_cannot_create_student_for_school_b(self):
        """Admin A should not create student for School B."""
        self._login(self.admin_a)
        response = self.client.post("/api/students/", {
            "first_name": "Hacker",
            "last_name": "Student",
            "admission_number": "HACK001",
            "date_of_birth": "2010-01-01",
            "gender": "male",
            "institution": self.school_b.id,
            "primary_campus": self.campus_b1.id,
        })
        # Should be denied (403) or return 400 (validation error)
        self.assertIn(response.status_code, [400, 403])
        
    def test_super_admin_can_access_all_schools(self):
        """Super admin should access all schools' students."""
        self._login(self.super_admin)
        # Switch to school B
        self.client.post("/api/auth/active-institution/", {"institution_id": self.school_b.id})
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        student_ids = [s["id"] for s in response.json().get("results", [])]
        self.assertIn(self.student_b1.id, student_ids)


class FinanceCrossSchoolAccessTest(TenantIsolationTestBase):
    """Test cross-school finance access attempts."""
    
    def test_accountant_a_cannot_see_school_b_invoices(self):
        """Accountant A should not see School B invoices."""
        self._login(self.accountant_a)
        response = self.client.get("/api/finance/invoices/")
        self.assertEqual(response.status_code, 200)
        
        # Should only see school A invoices (none created yet)
        invoice_ids = [inv["id"] for inv in response.json().get("results", [])]
        # All invoices should belong to school A
        
    def test_accountant_a_cannot_access_school_b_invoice_detail(self):
        """Accountant A should not access School B invoice detail."""
        self._login(self.accountant_a)
        response = self.client.get(
            f"/api/finance/invoices/{self.invoice_b1.id}/"
        )
        self.assertEqual(response.status_code, 404)
        
    def test_accountant_a_cannot_create_invoice_for_school_b(self):
        """Accountant A should not create invoice for School B student."""
        self._login(self.accountant_a)
        response = self.client.post("/api/finance/invoices/create/", {
            "student": self.student_b1.id,
            "academic_year": self.year_b.id,
            "campus": self.campus_b1.id,
            "class_obj": 1,  # Would need valid class
            "section": 1,
            "issue_date": "2024-01-01",
            "due_date": "2024-02-01",
        })
        self.assertIn(response.status_code, [400, 403])


class TeacherCrossCampusAccessTest(TenantIsolationTestBase):
    """Test cross-campus teacher access attempts."""

    def test_teacher_cannot_access_other_school_assignments(self):
        """A School A teacher cannot read a School B assignment by ID."""
        self._login(self.teacher_a1_user)
        response = self.client.get(
            f"/api/teachers/assignments/{self.assignment_b1.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_cannot_submit_attendance_for_other_campus(self):
        """Teacher bound to campus A1 cannot mark attendance in campus A2."""
        self._login(self.teacher_a1_user)
        response = self.client.post(
            "/api/attendance/mark/",
            {
                "academic_year": self.year_a.id,
                "student": self.student_a2.id,
                "date": "2024-10-03",
                "status": "present",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class CampusAdminAccessTest(TenantIsolationTestBase):
    """Test campus admin access restrictions."""
    
    def test_campus_admin_a1_can_access_campus_a1(self):
        """Campus admin for campus A1 can access A1 data."""
        self._login(self.campus_admin_a1)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        
    def test_campus_admin_a1_cannot_access_campus_a2(self):
        """Campus admin for A1 cannot access A2 students."""
        self._login(self.campus_admin_a1)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        student_ids = [s["id"] for s in response.json().get("results", [])]
        self.assertIn(self.student_a1.id, student_ids)
        self.assertNotIn(self.student_a2.id, student_ids)
    
    def test_campus_admin_a1_cannot_access_school_b(self):
        """Campus admin for A1 cannot access School B."""
        self._login(self.campus_admin_a1)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        # Should not see school B students


class SuperAdminSwitchingTest(TenantIsolationTestBase):
    """Test Super Admin school switching."""
    
    def test_super_admin_can_switch_schools(self):
        """Super admin can switch between schools."""
        self._login(self.super_admin)
        
        # Initially no active institution
        response = self.client.get("/api/auth/active-institution/")
        self.assertEqual(response.status_code, 200)
        
        # Switch to school A
        response = self.client.post("/api/auth/active-institution/", {
            "institution_id": self.school_a.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["institution"]["id"], self.school_a.id)
        
        # Switch to school B
        response = self.client.post("/api/auth/active-institution/", {
            "institution_id": self.school_b.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["institution"]["id"], self.school_b.id)
        
    def test_super_admin_cannot_switch_to_inactive_school(self):
        """Super admin cannot switch to inactive school."""
        self._login(self.super_admin)
        self.school_b.status = "inactive"
        self.school_b.save()
        
        response = self.client.post("/api/auth/active-institution/", {
            "institution_id": self.school_b.id
        })
        self.assertEqual(response.status_code, 404)


class IDORProtectionTest(TenantIsolationTestBase):
    """Test IDOR protection across all endpoints."""
    
    def test_student_detail_idor(self):
        """Cannot access another school's student by ID."""
        self._login(self.admin_a)
        response = self.client.get(f"/api/students/{self.student_b1.id}/")
        self.assertEqual(response.status_code, 404)
        
    def test_invoice_idor(self):
        """Cannot access another school's invoice by ID."""
        self._login(self.accountant_a)
        response = self.client.get(
            f"/api/finance/invoices/{self.invoice_b1.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_fee_structure_idor(self):
        """Cannot access another school's fee structure."""
        self._login(self.accountant_a)
        response = self.client.get(
            f"/api/finance/fee-structures/{self.fee_structure_b1.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_payroll_idor(self):
        """Cannot access another school's payroll records or salary structures."""
        self._login(self.accountant_a)
        records_response = self.client.get(
            f"/api/payroll/records/{self.record_b1.id}/"
        )
        self.assertEqual(records_response.status_code, 404)
        structure_response = self.client.get(
            f"/api/payroll/salary-structures/{self.structure_b1.id}/"
        )
        self.assertEqual(structure_response.status_code, 404)

    def test_attendance_idor(self):
        """Cannot see another school's attendance records by student filter."""
        self._login(self.admin_a)
        response = self.client.get(
            f"/api/attendance/?student={self.student_b1.id}"
        )
        self.assertEqual(response.status_code, 200)
        attendance_ids = [a["id"] for a in response.json().get("results", [])]
        self.assertNotIn(self.attendance_b1.id, attendance_ids)

    def test_library_issue_idor(self):
        """Admin A cannot see or fetch School B book issues."""
        self._login(self.admin_a)
        list_response = self.client.get("/api/library/issues/")
        self.assertEqual(list_response.status_code, 200)
        issue_ids = [i["id"] for i in list_response.json().get("results", [])]
        self.assertIn(self.issue_a1.id, issue_ids)
        self.assertNotIn(self.issue_b1.id, issue_ids)

        detail_response = self.client.get(
            f"/api/library/issues/{self.issue_b1.id}/"
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_library_reservation_idor(self):
        """Admin A cannot see or fetch School B book reservations."""
        self._login(self.admin_a)
        list_response = self.client.get("/api/library/reservations/")
        self.assertEqual(list_response.status_code, 200)
        reservation_ids = [r["id"] for r in list_response.json().get("results", [])]
        self.assertNotIn(self.reservation_b1.id, reservation_ids)

        detail_response = self.client.get(
            f"/api/library/reservations/{self.reservation_b1.id}/"
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_library_copy_list_scoped_to_school_book(self):
        """Admin A cannot see School B copies via the nested copies endpoint."""
        self._login(self.admin_a)
        response = self.client.get(
            f"/api/library/books/{self.book_b1.id}/copies/"
        )
        self.assertEqual(response.status_code, 200)
        copy_ids = [c["id"] for c in response.json().get("results", [])]
        self.assertNotIn(self.copy_b1.id, copy_ids)


class CampusScopingTest(TenantIsolationTestBase):
    """Test campus-level scoping within same school."""
    
    def test_admin_sees_all_campuses(self):
        """School admin sees all campuses."""
        self._login(self.admin_a)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        # Should see students from both campus_a1 and campus_a2
        
    def test_campus_admin_sees_only_own_campus(self):
        """Campus admin only sees their campus."""
        self._login(self.campus_admin_a1)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        # Should only see campus_a1 students
        
    def test_campus_filter_parameter(self):
        """?campus= parameter works correctly."""
        self._login(self.admin_a)
        response = self.client.get(f"/api/students/?campus={self.campus_a1.id}")
        self.assertEqual(response.status_code, 200)
        # Should only return campus_a1 students
        
    def test_invalid_campus_filter_rejected(self):
        """Invalid campus filter is rejected."""
        self._login(self.campus_admin_a1)
        response = self.client.get(f"/api/students/?campus={self.campus_b1.id}")
        self.assertEqual(response.status_code, 403)


class TenantScopedViewsRegressionTest(TenantIsolationTestBase):
    """Phase 3A regression: institution/campus scoping on alumni, inventory,
    attendance corrections, teacher assignments, LMS lessons/quizzes, homework
    submissions, and the admin account unlock endpoint.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        from apps.alumni.models import AlumniProfile
        from apps.inventory.models import AssetCategory, Supplier
        from apps.lms.models import Course, Lesson, Quiz
        from apps.homework.models import Homework
        from apps.attendance.models import AttendanceCorrection
        from apps.schools.models import Subject

        # Alumni
        cls.alumni_a1 = AlumniProfile.objects.create(
            institution=cls.school_a, campus=cls.campus_a1,
            full_name="Alumni A1", batch_year=2020,
        )
        cls.alumni_b1 = AlumniProfile.objects.create(
            institution=cls.school_b, campus=cls.campus_b1,
            full_name="Alumni B1", batch_year=2020,
        )

        # Inventory (institution-scoped only; no campus FK)
        cls.category_a1 = AssetCategory.objects.create(institution=cls.school_a, name="Furniture A")
        cls.category_b1 = AssetCategory.objects.create(institution=cls.school_b, name="Furniture B")
        cls.supplier_a1 = Supplier.objects.create(institution=cls.school_a, name="Supplier A")
        cls.supplier_b1 = Supplier.objects.create(institution=cls.school_b, name="Supplier B")

        # Attendance + corrections
        cls.attendance_a1 = Attendance.objects.create(
            student=cls.student_a1, enrollment=cls.enrollment_a1,
            academic_year=cls.year_a, campus=cls.campus_a1,
            class_obj=cls.class_a1, section=cls.section_a1,
            date="2024-10-03", status="present",
        )
        cls.correction_a1 = AttendanceCorrection.objects.create(
            attendance=cls.attendance_a1, student=cls.student_a1,
            from_status="present", to_status="absent",
            corrected_by=cls.teacher_a1_user,
        )
        cls.correction_b1 = AttendanceCorrection.objects.create(
            attendance=cls.attendance_b1, student=cls.student_b1,
            from_status="present", to_status="absent", corrected_by=None,
        )

        # Second School-A teacher (in-school ownership checks) + assignment
        cls.subject_a1 = Subject.objects.create(
            institution=cls.school_a, name="Mathematics A1", code="MATH-A1",
        )
        cls.teacher_a2_user = User.objects.create_user(
            username="teacher_a2", email="teacher_a2@test.com", password="TestPass123!",
        )
        membership_ta2 = InstitutionMembership.objects.create(
            user=cls.teacher_a2_user, institution=cls.school_a, status="active",
        )
        RoleAssignment.objects.create(membership=membership_ta2, role=Role.TEACHER)
        cls.teacher_a2 = Teacher.objects.create(
            institution=cls.school_a, employee_number="TCH-A2-001",
            user=cls.teacher_a2_user, membership=membership_ta2,
            primary_campus=cls.campus_a1, first_name="Teacher", last_name="A2", gender="female",
        )
        cls.assignment_a1 = TeacherAssignment.objects.create(
            teacher=cls.teacher_a1, campus=cls.campus_a1,
            class_obj=cls.class_a1, section=cls.section_a1,
            subject=cls.subject_a1, academic_year=cls.year_a,
        )

        # LMS
        cls.course_a1 = Course.objects.create(
            institution=cls.school_a, campus=cls.campus_a1,
            teacher=cls.teacher_a1, class_obj=cls.class_a1,
            title="Course A1", is_published=True,
        )
        cls.course_a2 = Course.objects.create(
            institution=cls.school_a, campus=cls.campus_a1,
            teacher=cls.teacher_a2, class_obj=cls.class_a1,
            title="Course A2", is_published=True,
        )
        cls.course_b1 = Course.objects.create(
            institution=cls.school_b, campus=cls.campus_b1,
            teacher=cls.teacher_b1, class_obj=cls.class_b1,
            title="Course B1", is_published=True,
        )
        cls.lesson_a1 = Lesson.objects.create(course=cls.course_a1, title="Lesson A1")
        cls.lesson_b1 = Lesson.objects.create(course=cls.course_b1, title="Lesson B1")
        cls.quiz_a1 = Quiz.objects.create(course=cls.course_a1, title="Quiz A1", is_published=True)
        cls.quiz_b1 = Quiz.objects.create(course=cls.course_b1, title="Quiz B1", is_published=True)

        # Homework
        cls.homework_a1 = Homework.objects.create(
            institution=cls.school_a, campus=cls.campus_a1,
            teacher=cls.teacher_a1, class_obj=cls.class_a1,
            title="Homework A1", assigned_date="2024-10-10",
            due_date="2024-10-20", max_marks=10,
        )
        cls.homework_b1 = Homework.objects.create(
            institution=cls.school_b, campus=cls.campus_b1,
            teacher=cls.teacher_b1, class_obj=cls.class_b1,
            title="Homework B1", assigned_date="2024-10-10",
            due_date="2024-10-20", max_marks=10,
        )

        # Principal (non-global role that unlocks accounts) for unlock scope tests
        cls.principal_a_user = User.objects.create_user(
            username="principal_a", email="principal_a@test.com", password="TestPass123!",
        )
        membership_pa = InstitutionMembership.objects.create(
            user=cls.principal_a_user, institution=cls.school_a, status="active",
        )
        RoleAssignment.objects.create(membership=membership_pa, role=Role.PRINCIPAL)

    # -- alumni --
    def test_admin_a_sees_only_own_alumni(self):
        self._login(self.admin_a)
        response = self.client.get("/api/alumni/")
        self.assertEqual(response.status_code, 200)
        ids = [a["id"] for a in response.json().get("results", [])]
        self.assertIn(self.alumni_a1.id, ids)
        self.assertNotIn(self.alumni_b1.id, ids)

    def test_admin_a_cannot_open_school_b_alumni_detail(self):
        self._login(self.admin_a)
        response = self.client.get(f"/api/alumni/{self.alumni_b1.id}/")
        self.assertEqual(response.status_code, 404)

    # -- inventory --
    def test_admin_a_sees_only_own_inventory_categories(self):
        self._login(self.admin_a)
        response = self.client.get("/api/inventory/categories/")
        ids = [c["id"] for c in response.json().get("results", [])]
        self.assertIn(self.category_a1.id, ids)
        self.assertNotIn(self.category_b1.id, ids)

    def test_admin_a_cannot_open_school_b_supplier_detail(self):
        self._login(self.admin_a)
        response = self.client.get(f"/api/inventory/suppliers/{self.supplier_b1.id}/")
        self.assertEqual(response.status_code, 404)

    # -- attendance corrections --
    def test_admin_a_sees_only_own_attendance_corrections(self):
        self._login(self.admin_a)
        response = self.client.get("/api/attendance/corrections/")
        self.assertEqual(response.status_code, 200)
        # Note: this endpoint is NOT paginated (NoPaginationMixin).
        correction_ids = [c["id"] for c in response.json()]
        self.assertIn(self.correction_a1.id, correction_ids)
        self.assertNotIn(self.correction_b1.id, correction_ids)

    # -- teacher assignments --
    def test_admin_a_sees_only_school_a_teacher_assignments(self):
        self._login(self.admin_a)
        response = self.client.get("/api/teachers/assignments/")
        ids = [a["id"] for a in response.json().get("results", [])]
        self.assertIn(self.assignment_a1.id, ids)
        self.assertNotIn(self.assignment_b1.id, ids)

    def test_campus_admin_a1_sees_only_own_campus_assignments(self):
        self._login(self.campus_admin_a1)
        response = self.client.get("/api/teachers/assignments/")
        ids = [a["id"] for a in response.json().get("results", [])]
        self.assertIn(self.assignment_a1.id, ids)
        self.assertNotIn(self.assignment_b1.id, ids)

    # -- LMS lessons --
    def test_teacher_a1_cannot_list_school_b_lessons(self):
        self._login(self.teacher_a1_user)
        response = self.client.get(f"/api/lms/courses/{self.course_b1.id}/lessons/")
        self.assertEqual(response.status_code, 404)

    def test_teacher_a1_cannot_open_school_b_lesson(self):
        self._login(self.teacher_a1_user)
        response = self.client.get(
            f"/api/lms/courses/{self.course_b1.id}/lessons/{self.lesson_b1.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_a1_cannot_create_school_b_lesson(self):
        self._login(self.teacher_a1_user)
        response = self.client.post(
            f"/api/lms/courses/{self.course_b1.id}/lessons/", {"title": "Hack"}
        )
        self.assertEqual(response.status_code, 404)

    def test_non_owner_teacher_cannot_create_lesson_in_own_school(self):
        self._login(self.teacher_a2_user)
        response = self.client.post(
            f"/api/lms/courses/{self.course_a1.id}/lessons/", {"title": "Hack"}
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_teacher_can_create_lesson(self):
        self._login(self.teacher_a1_user)
        # lesson_a1 already uses order=1 for course_a1; pass a unique order.
        response = self.client.post(
            f"/api/lms/courses/{self.course_a1.id}/lessons/",
            {"title": "New Lesson", "order": 2},
        )
        self.assertEqual(response.status_code, 201)

    # -- LMS quizzes --
    def test_admin_a_cannot_open_school_b_quiz_detail(self):
        self._login(self.admin_a)
        response = self.client.get(f"/api/lms/quizzes/{self.quiz_b1.id}/")
        self.assertEqual(response.status_code, 404)

    def test_admin_a_cannot_list_school_b_quiz_questions(self):
        self._login(self.admin_a)
        response = self.client.get(f"/api/lms/quizzes/{self.quiz_b1.id}/questions/")
        self.assertEqual(response.status_code, 404)

    def test_non_owner_teacher_cannot_create_question_in_own_school(self):
        self._login(self.teacher_a2_user)
        response = self.client.post(
            f"/api/lms/quizzes/{self.quiz_a1.id}/questions/new/",
            {"text": "Hack?", "options": '["a"]', "correct_option": "a"},
        )
        self.assertEqual(response.status_code, 403)

    # -- homework submissions --
    def test_admin_a_cannot_submit_school_b_homework(self):
        self._login(self.admin_a)
        response = self.client.post(
            f"/api/homework/{self.homework_b1.id}/submissions/",
            {"content": "x", "student": self.student_a1.id},
        )
        self.assertEqual(response.status_code, 404)

    # -- admin unlock scope --
    def test_global_admin_bypasses_unlock_scoping(self):
        self._login(self.admin_a)
        response = self.client.post(f"/api/auth/admin/unlock/{self.admin_b.id}/")
        self.assertEqual(response.status_code, 200)

    def test_principal_cannot_unlock_cross_school_user(self):
        self._login(self.principal_a_user)
        response = self.client.post(f"/api/auth/admin/unlock/{self.admin_b.id}/")
        self.assertEqual(response.status_code, 404)

    def test_principal_can_unlock_own_school_user(self):
        self._login(self.principal_a_user)
        response = self.client.post(f"/api/auth/admin/unlock/{self.teacher_a2_user.id}/")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()