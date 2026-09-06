"""Regression tests for reported production bugs.

Covers:
  * Teacher list/detail no longer 500s (broken ``institutionmembership``
    lookup) and remains school-scoped, enabling teacher profile + delete.
  * Staff leave creation accepts a request without a `staff` field (derived
    from the authenticated staff profile) and staff attendance mark uses the
    effective staff member.
  * Health record campus is derived from the student's active enrollment and
    cannot be set arbitrarily by the client.
  * HR employee creation endpoint works.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffAttendance,
    StaffLeave,
    StaffProfile,
)
from apps.health.models import HealthRecord
from apps.hr.models import Employee
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    Section,
    School,
    Subject,
)
from apps.students.models import Enrollment, Student, Guardian
from apps.teachers.models import Teacher

PASSWORD = "Test#Strong2026"


def _school(name, code):
    return School.objects.create(
        name=name,
        code=code,
        institution_type="school",
        status="active",
    )


def _member(user, school, role=Role.ADMIN):
    membership = InstitutionMembership.objects.create(
        user=user,
        institution=school,
        status="active",
    )
    RoleAssignment.objects.create(
        membership=membership,
        role=role,
    )
    return membership


class StaffPortalRegressionTests(TestCase):
    def setUp(self):
        self.school = _school("Riverdale High", "RIV")
        self.campus = Campus.objects.create(
            school=self.school, name="Main Campus", status="active"
        )

        self.admin = self._make_user("admin.riv", Role.ADMIN)
        self.hr = self._make_user("hr.riv", Role.HR)
        self.staff_member = self._make_user("staff.riv", Role.STAFF)

        self.staff_profile = StaffProfile.objects.create(
            user=self.staff_member,
            institution=self.school,
            employee_number="STF-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            primary_campus=self.campus,
        )

        self.client = APIClient()

    def _make_user(self, username, role):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            email=f"{username}@test.edu",
            password=PASSWORD,
            institution=self.school,
        )
        _member(user, self.school, role)
        return user

    def _login(self, user):
        self.client.force_login(user)
        # Bind the session to the active school like the middleware does.
        session = self.client.session
        session["active_institution_id"] = self.school.id
        session.save()

    def test_staff_can_submit_own_leave_without_staff_field(self):
        self._login(self.staff_member)
        response = self.client.post(
            "/api/staff/leave/",
            {
                "leave_type": "casual",
                "start_date": "2026-09-05",
                "end_date": "2026-09-05",
                "reason": "Family errand",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        leave = StaffLeave.objects.get()
        self.assertEqual(leave.staff, self.staff_profile)
        self.assertEqual(leave.institution, self.school)

    def test_admin_can_create_attendance_for_selected_staff(self):
        self._login(self.admin)
        response = self.client.post(
            "/api/staff/attendance/",
            {
                "staff": self.staff_profile.id,
                "date": "2026-09-05",
                "status": "present",
                "check_in": "08:00:00",
                "check_out": "16:00:00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        record = StaffAttendance.objects.get()
        self.assertEqual(record.staff, self.staff_profile)
        self.assertEqual(record.marked_by, self.admin)

    def test_attendance_register_loads_without_error(self):
        self._login(self.admin)
        response = self.client.get("/api/staff/attendance/?date=2026-09-05")
        self.assertEqual(response.status_code, 200, response.content)

    def test_leave_register_remains_school_scoped(self):
        other = _school("Other School", "OTH")
        other_campus = Campus.objects.create(
            school=other, name="Other Campus", status="active"
        )
        other_user = self._make_user("staff.oth", Role.STAFF)
        StaffProfile.objects.create(
            user=other_user,
            institution=other,
            employee_number="STF-OTH-1",
            first_name="Zara",
            last_name="Malik",
            gender="female",
            primary_campus=other_campus,
        )

        self._login(self.admin)
        response = self.client.get("/api/staff/leave/")
        self.assertEqual(response.status_code, 200, response.content)
        # School B staff cannot create leave in school A via this admin.
        response = self.client.post(
            "/api/staff/leave/",
            {
                "staff": other_user.staff_profile.id,
                "leave_type": "casual",
                "start_date": "2026-09-05",
                "end_date": "2026-09-06",
                "reason": "Cross-school attempt",
            },
            format="json",
        )
        self.assertIn(response.status_code, (400, 404), response.content)


class TeacherDetailRegressionTests(TestCase):
    def setUp(self):
        self.school = _school("Riverdale High", "RIV")
        self.admin = self._make_admin()
        self.campus = Campus.objects.create(
            school=self.school, name="Main Campus", status="active"
        )
        self.teacher = Teacher.objects.create(
            institution=self.school,
            employee_number="T-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            primary_campus=self.campus,
        )
        self.client = APIClient()
        self.client.force_login(self.admin)
        session = self.client.session
        session["active_institution_id"] = self.school.id
        session.save()

    def _make_admin(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="admin.teacher",
            email="admin.teacher@test.edu",
            password=PASSWORD,
            institution=self.school,
        )
        _member(user, self.school, Role.ADMIN)
        return user

    def test_teacher_detail_no_longer_500s(self):
        response = self.client.get(f"/api/teachers/{self.teacher.id}/")
        self.assertEqual(response.status_code, 200, response.content)

    def test_teacher_delete_soft_deletes(self):
        response = self.client.delete(f"/api/teachers/{self.teacher.id}/")
        self.assertEqual(response.status_code, 204, response.content)
        self.teacher.refresh_from_db()
        self.assertIsNotNone(self.teacher.deleted_at)

    def test_teacher_list_is_school_scoped(self):
        other = _school("Other School", "OTH")
        Teacher.objects.create(
            institution=other,
            employee_number="T-OTH",
            first_name="Zara",
            last_name="Malik",
            gender="female",
        )
        response = self.client.get("/api/teachers/")
        self.assertEqual(response.status_code, 200, response.content)
        ids = [row["id"] for row in response.data.get("results", [])]
        self.assertEqual(ids, [self.teacher.id])


class HealthRecordCampusFromEnrollmentTests(TestCase):
    def setUp(self):
        self.school = _school("Riverdale High", "RIV")
        self.campus = Campus.objects.create(
            school=self.school, name="Main Campus", status="active"
        )
        self.academic_year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date="2026-08-01",
            end_date="2027-07-31",
        )
        unit = AcademicUnit.objects.create(
            campus=self.campus, name="Primary"
        )
        class_obj = Class.objects.create(unit=unit, name="Grade 1")
        section = Section.objects.create(class_obj=class_obj, name="A")
        self.subject = Subject.objects.create(name="English", code="ENG-1")

        self.health_user = self._make_user("nurse.riv", Role.STAFF)
        StaffProfile.objects.create(
            user=self.health_user,
            institution=self.school,
            employee_number="STF-NURSE-1",
            first_name="Sana",
            last_name="Nurse",
            gender="female",
            primary_campus=self.campus,
        )
        self.guardian = Guardian.objects.create(
            institution=self.school,
            name="Imran Raza",
            relationship="Father",
            phone="0300-0000000",
        )
        self.student = Student.objects.create(
            admission_number="STU-001",
            first_name="Ali",
            last_name="Raza",
            gender="male",
            guardian=self.guardian,
        )
        Enrollment.objects.create(
            student=self.student,
            campus=self.campus,
            class_obj=class_obj,
            section=section,
            academic_year=self.academic_year,
            status="active",
        )

        self.client = APIClient()

    def _make_user(self, username, role):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            email=f"{username}@test.edu",
            password=PASSWORD,
            institution=self.school,
        )
        _member(user, self.school, role)
        return user

    def _login(self):
        self.client.force_login(self.health_user)
        session = self.client.session
        session["active_institution_id"] = self.school.id
        session.save()

    def test_campus_derived_from_active_enrollment(self):
        self._login()
        response = self.client.post(
            "/api/health-records/records/",
            {
                "student": self.student.id,
                "record_type": "checkup",
                "record_date": "2026-09-05",
                "notes": "Routine checkup",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        record = HealthRecord.objects.get()
        self.assertEqual(record.campus, self.campus)
        self.assertEqual(record.institution, self.school)


class HREmployeeCreationTests(TestCase):
    def setUp(self):
        self.school = _school("Riverdale High", "RIV")
        self.campus = Campus.objects.create(
            school=self.school, name="Main Campus", status="active"
        )
        self.admin = self._make_user("admin.hr", Role.ADMIN)
        self.client = APIClient()
        self.client.force_login(self.admin)
        session = self.client.session
        session["active_institution_id"] = self.school.id
        session.save()

    def _make_user(self, username, role):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            email=f"{username}@test.edu",
            password=PASSWORD,
            institution=self.school,
        )
        _member(user, self.school, role)
        return user

    def test_create_employee_from_staff_profile(self):
        staff_user = self._make_user("staff.hr", Role.STAFF)
        profile = StaffProfile.objects.create(
            user=staff_user,
            institution=self.school,
            employee_number="STF-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            primary_campus=self.campus,
        )

        response = self.client.post(
            "/api/hr/employees/",
            {
                "staff_profile": profile.id,
                "employment_type": "permanent",
                "status": "active",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        employee = Employee.objects.get()
        self.assertEqual(employee.institution, self.school)
        self.assertEqual(employee.staff_profile, profile)
        self.assertTrue(employee.employee_number)

    def test_employee_creation_requires_profile_link(self):
        response = self.client.post(
            "/api/hr/employees/",
            {
                "employment_type": "permanent",
                "status": "active",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
