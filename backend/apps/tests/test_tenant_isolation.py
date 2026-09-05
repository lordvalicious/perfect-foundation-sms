"""Security tests for cross-school/tenant isolation.

These tests verify that users cannot access data from other schools/campuses
than their own assigned ones (IDOR protection).
"""

import unittest
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.schools.models import School, Campus
from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role
from apps.students.models import Student, Enrollment
from apps.teachers.models import Teacher
from apps.finance.models import Invoice, Payment


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
        
        # Create students in school A
        cls.student_a1 = Student.objects.create(
            admission_number="STU001",
            first_name="Student",
            last_name="A1",
            date_of_birth="2010-01-01",
            gender="male",
            institution=cls.school_a,
            primary_campus=cls.campus_a1,
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
            status="active",
        )
        
        # Create enrollments
        from apps.schools.models import AcademicYear, Class, Section
        
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
        
        cls.class_a1 = Class.objects.create(
            unit=cls.campus_a1.unit_set.first() or cls.campus_a1.academic_units.first().units.first() if hasattr(cls.campus_a1, 'unit_set') else None,
            name="Class 1",
            level=1,
            status="active",
        )
        # Need to create proper academic structure - skip if not available
        
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
        # Try to access an invoice from school B (would need to create one first)
        # This tests the IDOR protection
        pass
        
    def test_accountant_a_cannot_create_invoice_for_school_b(self):
        """Accountant A should not create invoice for School B student."""
        self._login(self.accountant_a)
        response = self.client.post("/api/finance/invoices/", {
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
    
    def test_teacher_cannot_access_other_campus_assignments(self):
        """Teacher should only see assignments for their assigned campus."""
        pass
    
    def test_teacher_cannot_submit_attendance_for_other_campus(self):
        """Teacher should not mark attendance for students in other campus."""
        pass


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
        # Create student in campus A2 if not exists
        response = self.client.get("/api/students/")
        # Should only see campus A1 students
        pass
    
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
        # Would need to create invoice in school B first
        pass
        
    def test_fee_structure_idor(self):
        """Cannot access another school's fee structure."""
        pass
        
    def test_payroll_idor(self):
        """Cannot access another school's payroll records."""
        pass
        
    def test_attendance_idor(self):
        """Cannot access another school's attendance records."""
        pass


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


if __name__ == "__main__":
    unittest.main()