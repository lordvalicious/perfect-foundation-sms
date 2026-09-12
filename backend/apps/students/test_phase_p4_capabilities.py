"""Tests for P4 enterprise capabilities added to the students app.

Covers batch graduation, the alumni-directory bridge, and strict
status-transition enforcement on the student edit endpoint.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment
from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, School, Section

from apps.alumni.models import AlumniProfile

from .models import (
    Enrollment,
    Guardian,
    Student,
    StudentAlumni,
    StudentLifecycleEvent,
)


def _make_school(name, code):
    return School.objects.create(name=name, code=code)


def _make_admin(school, username, password="TestPass123!"):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@test.edu",
        password=password,
    )
    membership = InstitutionMembership.objects.create(
        user=user,
        institution=school,
    )
    RoleAssignment.objects.create(membership=membership, role=Role.ADMIN)
    return user


def _make_structure(school, campus_name="Main"):
    campus = Campus.objects.create(school=school, name=campus_name)
    unit = AcademicUnit.objects.create(campus=campus, name="Primary")
    class_obj = Class.objects.create(unit=unit, name="Grade 6")
    section = Section.objects.create(class_obj=class_obj, name="A")
    year = AcademicYear.objects.create(
        school=school,
        name="2025-2026",
        start_date=date(2025, 8, 1),
        end_date=date(2026, 7, 31),
    )
    return campus, class_obj, section, year


def _make_student(school, campus, class_obj, section, year, **overrides):
    guardian = Guardian.objects.create(
        institution=school,
        name="Guardian",
        phone="0700000000",
        relationship="Parent",
    )
    student = Student.objects.create(
        institution=school,
        admission_number=overrides.pop("admission_number", "ADM-" + str(len(Student.objects.all()) + 1)),
        first_name=overrides.pop("first_name", "Student"),
        last_name=overrides.pop("last_name", "One"),
        gender="male",
        guardian=guardian,
        phone="0700000001",
        status=overrides.pop("status", "active"),
        **overrides,
    )
    Enrollment.objects.create(
        student=student,
        academic_year=year,
        campus=campus,
        class_obj=class_obj,
        section=section,
        status="active",
    )
    return student


class StudentBatchGraduateApiTests(TestCase):
    """The batch graduation endpoint graduates a set of students atomically."""

    def setUp(self):
        self.school = _make_school("Batch Graduation", "bg")
        self.user = _make_admin(self.school, username="bg-admin")
        self.campus, self.class_obj, self.section, self.year = _make_structure(self.school)

        self.student_a = _make_student(
            self.school, self.campus, self.class_obj, self.section, self.year,
            admission_number="ADM-1001",
        )
        self.student_b = _make_student(
            self.school, self.campus, self.class_obj, self.section, self.year,
            admission_number="ADM-1002",
        )
        self.student_c = _make_student(  # not in the batch
            self.school, self.campus, self.class_obj, self.section, self.year,
            admission_number="ADM-1003",
        )

        self.client = APIClient()
        self.client.login(username="bg-admin", password="TestPass123!")

    def test_batch_graduation_graduates_and_bridges_alumni(self):
        response = self.client.post(
            "/api/students/graduation/batch/",
            {
                "student_ids": [self.student_a.pk, self.student_b.pk],
                "graduation_date": "2026-06-30",
                "reason": "Completed Grade 6",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(len(data["graduated"]), 2)
        self.assertEqual(data["failed"], [])

        for student_pk in (self.student_a.pk, self.student_b.pk):
            student = Student.objects.get(pk=student_pk)
            self.assertEqual(student.status, "graduated")
            self.assertTrue(
                StudentAlumni.objects.filter(student=student).exists(),
                "Student must have an alumni record after graduation",
            )
            self.assertTrue(
                AlumniProfile.objects.filter(student=student).exists(),
                "Graduation must auto-create the alumni-directory profile",
            )

        # The out-of-batch student is untouched.
        self.student_c.refresh_from_db()
        self.assertEqual(self.student_c.status, "active")

    def test_batch_graduation_records_lifecycle_events(self):
        self.client.post(
            "/api/students/graduation/batch/",
            {
                "student_ids": [self.student_a.pk],
                "graduation_date": "2026-06-30",
            },
            format="json",
        )

        event = StudentLifecycleEvent.objects.filter(student=self.student_a).last()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, "graduated")

    def test_batch_graduation_rejects_missing_student_ids(self):
        response = self.client.post(
            "/api/students/graduation/batch/",
            {"student_ids": []},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("student_ids", response.json()["detail"])

    def test_batch_graduation_out_of_scope_student_reported_not_crashed(self):
        other_school = _make_school("Other Batch", "ob")
        other_campus, other_class, other_section, other_year = _make_structure(other_school)
        foreign = _make_student(
            other_school, other_campus, other_class, other_section, other_year,
            admission_number="ADM-9999",
        )

        response = self.client.post(
            "/api/students/graduation/batch/",
            {"student_ids": [self.student_a.pk, foreign.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(len(data["graduated"]), 1)
        self.assertEqual(len(data["failed"]), 1)
        # Foreign student is not graduated and no alumni row is created.
        foreign.refresh_from_db()
        self.assertEqual(foreign.status, "active")
        self.assertFalse(AlumniProfile.objects.filter(student=foreign).exists())
        self.assertFalse(StudentAlumni.objects.filter(student=foreign).exists())

    def test_batch_graduation_requires_admin_role(self):
        self.client.force_authenticate(user=None)
        user = get_user_model().objects.create_user(
            username="bg-teacher",
            email="bg-teacher@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(
            user=user,
            institution=self.school,
        )
        RoleAssignment.objects.create(membership=membership, role=Role.TEACHER)
        self.client.login(username="bg-teacher", password="TestPass123!")

        response = self.client.post(
            "/api/students/graduation/batch/",
            {"student_ids": [self.student_a.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 403)


class StudentStatusTransitionApiTests(TestCase):
    """PATCH on a student enforces the model's status-transition state machine."""

    def setUp(self):
        self.school = _make_school("Transitions", "tr")
        _make_admin(self.school, username="tr-admin")
        self.campus, self.class_obj, self.section, self.year = _make_structure(self.school)
        self.student = _make_student(
            self.school, self.campus, self.class_obj, self.section, self.year,
            admission_number="ADM-2001",
            status="active",
        )
        self.client = APIClient()
        self.client.login(username="tr-admin", password="TestPass123!")

    def test_invalid_status_transition_rejected(self):
        # graduated -> active is not an allowed transition.
        self.student.status = "graduated"
        self.student.save(update_fields=["status"])

        response = self.client.patch(
            f"/api/students/{self.student.pk}/",
            {"status": "active"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.json())
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "graduated")

    def test_valid_status_transition_accepted(self):
        response = self.client.patch(
            f"/api/students/{self.student.pk}/",
            {"status": "inactive"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "inactive")

    def test_unchanged_status_is_ignored(self):
        response = self.client.patch(
            f"/api/students/{self.student.pk}/",
            {"first_name": "Renamed", "status": "active"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, "active")
        self.assertEqual(self.student.first_name, "Renamed")


class AlumniBridgeModelTests(TestCase):
    """Graduating via the model helper creates the alumni-directory profile."""

    def setUp(self):
        self.school = _make_school("Alumni Bridge", "ab")
        self.user = _make_admin(self.school, username="ab-admin")
        self.campus, self.class_obj, self.section, self.year = _make_structure(self.school)
        self.student = _make_student(
            self.school, self.campus, self.class_obj, self.section, self.year,
            admission_number="ADM-3001",
        )

    def test_graduate_creates_alumni_profile_with_batch_year(self):
        graduation_date = timezone.now().date() - timedelta(days=10)
        alumni = StudentAlumni.create_from_graduation(
            self.student,
            self.user,
            graduation_date=graduation_date,
            reason="Graduated",
        )

        self.assertIsNotNone(alumni)
        profile = AlumniProfile.objects.get(student=self.student)
        self.assertEqual(profile.institution, self.school)
        self.assertEqual(profile.batch_year, graduation_date.year)
        self.assertEqual(profile.campus, self.campus)
        self.assertEqual(profile.full_name, self.student.full_name)

    def test_graduate_does_not_duplicate_existing_alumni_profile(self):
        first = AlumniProfile.objects.create(
            student=self.student,
            institution=self.school,
            campus=self.campus,
            full_name=self.student.full_name,
            batch_year=timezone.now().year,
        )

        StudentAlumni.create_from_graduation(
            self.student,
            self.user,
            graduation_date=timezone.now().date(),
        )

        self.assertEqual(AlumniProfile.objects.filter(student=self.student).count(), 1)
        self.assertEqual(AlumniProfile.objects.get(pk=first.pk).pk, first.pk)