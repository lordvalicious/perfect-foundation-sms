"""Regression tests for the Phase 45 student-performance remediation.

Guards against re-introducing:

  * the claimed attendance latency storm, i.e. per-role-per-check
    ``RoleAssignment`` lookups and the duplicated role-queries served to
    student-facing list endpoints,
  * the broken ``results__practical_results`` prefetch that made
    ``/api/exams/`` 500 as soon as an exam existed,
  * per-exam/per-result counting and practical-result lookups inside
    serializers (N+1),
  * loss of student self-scoping when bulk result preloading is active.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
)
from apps.attendance.models import Attendance
from apps.exams.models import Exam, ExamSubject, PracticalResult, StudentResult
from apps.reportcards.models import ReportCard
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
    Subject,
    SubjectOffering,
)
from apps.students.models import Enrollment, Guardian, Student


def _member(user, school, role):
    membership = InstitutionMembership.objects.create(
        user=user,
        institution=school,
        status="active",
    )
    RoleAssignment.objects.create(membership=membership, role=role)
    return membership


class StudentPerformanceRegressionTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Springfield Academy",
            institution_type="school",
            status="active",
        )
        self.campus = Campus.objects.create(
            school=self.school, name="Main Campus", status="active"
        )
        self.unit = AcademicUnit.objects.create(
            campus=self.campus, name="Primary"
        )
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 1")
        self.section = Section.objects.create(
            class_obj=self.class_obj, name="A"
        )
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
        )

        User = get_user_model()
        self.user = User.objects.create_user(
            username="stu1", email="stu1@test.edu", password="Test#Strong2026"
        )
        _member(self.user, self.school, Role.STUDENT)

        self.guardian = Guardian.objects.create(
            name="Parent", relationship="Father", phone="03000000000"
        )
        self.student = Student.objects.create(
            admission_number="STU-0001",
            first_name="Arthur",
            last_name="Pendragon",
            gender="male",
            guardian=self.guardian,
            user=self.user,
            institution=self.school,
            primary_campus=self.campus,
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
            status="active",
        )

        subjects = []
        for i in range(6):
            subject = Subject.objects.create(
                name=f"Subject {i}", code=f"SUB{i}", institution=self.school
            )
            SubjectOffering.objects.create(
                subject=subject,
                class_obj=self.class_obj,
                academic_year=self.year,
            )
            subjects.append(subject)

        self.exam = Exam.objects.create(
            name="Midterm",
            exam_type="midterm",
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
        )
        self.exam_subjects = [
            ExamSubject.objects.create(
                exam=self.exam,
                subject=subject,
                maximum_marks=100,
                passing_marks=40,
            )
            for subject in subjects
        ]

        for i, exam_subject in enumerate(self.exam_subjects):
            StudentResult.objects.create(
                exam=self.exam,
                student=self.student,
                exam_subject=exam_subject,
                obtained_marks=Decimal("75"),
                is_absent=False,
            )

        for exam_subject in self.exam_subjects[:4]:
            PracticalResult.objects.create(
                exam=self.exam,
                student=self.student,
                exam_subject=exam_subject,
                obtained_marks=Decimal("10"),
                maximum_marks=20,
            )

        self.card = ReportCard.objects.create(
            student=self.student, exam=self.exam, status="published"
        )

        for i in range(4):
            Attendance.objects.create(
                student=self.student,
                enrollment=self.enrollment,
                academic_year=self.year,
                campus=self.campus,
                class_obj=self.class_obj,
                section=self.section,
                date=timezone.now().date() + timedelta(days=i),
                status="present",
                marked_by=self.user,
            )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _count_queries(self, path):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(path)
        return response, ctx.captured_queries

    def test_role_checks_are_memoized_per_request(self):
        self.assertTrue(
            self.user.has_any_role([Role.ADMIN, Role.STUDENT], self.school)
        )
        with CaptureQueriesContext(connection) as ctx:
            for _ in range(5):
                self.assertTrue(
                    self.user.has_any_role(
                        [Role.ADMIN, Role.STUDENT], self.school
                    )
                )
                self.assertTrue(self.user.has_any_role([Role.STUDENT]))
        self.assertLessEqual(len(ctx.captured_queries), 3)

    def test_attendance_list_is_lean_and_self_scoped(self):
        response, queries = self._count_queries("/api/attendance/")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 30)
        rows = response.json().get("results", response.json())
        self.assertEqual(len(rows), 4)

    def test_exams_list_returns_200_with_data_and_lean_counts(self):
        response, queries = self._count_queries("/api/exams/")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 30)
        rows = response.json().get("results", response.json())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["subject_count"], 6)
        self.assertEqual(rows[0]["result_count"], 6)

    def test_exam_results_are_bulk_loaded_and_self_scoped(self):
        response, queries = self._count_queries("/api/exams/results/")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 18)
        rows = response.json().get("results", response.json())
        self.assertEqual(len(rows), 6)
        practical_subjects = {es.pk for es in self.exam_subjects[:4]}
        for row in rows:
            if row["exam_subject"] in practical_subjects:
                self.assertIsNotNone(row["practical_marks"])
            else:
                self.assertIsNone(row["practical_marks"])

    def test_report_cards_list_is_lean(self):
        response, queries = self._count_queries("/api/report-cards/")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 30)
        rows = response.json().get("results", response.json())
        self.assertEqual(len(rows), 1)


class StudentIsolationRegressionTests(TestCase):
    def test_other_student_results_never_leak(self):
        school = School.objects.create(
            name="Other Academy",
            institution_type="school",
            status="active",
        )
        User = get_user_model()
        alice = User.objects.create_user(
            username="alice", email="alice@test.edu", password="Test#Strong2026"
        )
        bob = User.objects.create_user(
            username="bob", email="bob@test.edu", password="Test#Strong2026"
        )
        _member(alice, school, Role.STUDENT)
        _member(bob, school, Role.STUDENT)

        campus = Campus.objects.create(
            school=school, name="Main Campus", status="active"
        )
        unit = AcademicUnit.objects.create(campus=campus, name="Primary")
        class_obj = Class.objects.create(unit=unit, name="Grade 1")
        year = AcademicYear.objects.create(
            school=school,
            name="2026-2027",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
        )
        guardian = Guardian.objects.create(
            name="Parent", relationship="Father", phone="03000000000"
        )
        alice_student = Student.objects.create(
            admission_number="AL-0001",
            first_name="Alice",
            gender="female",
            guardian=guardian,
            user=alice,
            institution=school,
            primary_campus=campus,
        )
        bob_student = Student.objects.create(
            admission_number="BO-0001",
            first_name="Bob",
            gender="male",
            guardian=guardian,
            user=bob,
            institution=school,
            primary_campus=campus,
        )
        Enrollment.objects.create(
            student=alice_student,
            academic_year=year,
            campus=campus,
            class_obj=class_obj,
            section=Section.objects.create(class_obj=class_obj, name="A"),
            status="active",
        )
        Enrollment.objects.create(
            student=bob_student,
            academic_year=year,
            campus=campus,
            class_obj=class_obj,
            section=Section.objects.create(class_obj=class_obj, name="B"),
            status="active",
        )
        subject = Subject.objects.create(
            name="English", code="ENG", institution=school
        )
        SubjectOffering.objects.create(
            subject=subject,
            class_obj=class_obj,
            academic_year=year,
        )
        exam = Exam.objects.create(
            name="Midterm",
            exam_type="midterm",
            academic_year=year,
            campus=campus,
            class_obj=class_obj,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
        )
        es = ExamSubject.objects.create(
            exam=exam, subject=subject, maximum_marks=100, passing_marks=40
        )
        StudentResult.objects.create(
            exam=exam,
            student=alice_student,
            exam_subject=es,
            obtained_marks=Decimal("90"),
        )
        StudentResult.objects.create(
            exam=exam,
            student=bob_student,
            exam_subject=es,
            obtained_marks=Decimal("10"),
        )

        client = APIClient()
        client.force_authenticate(user=alice)
        response = client.get("/api/exams/results/")
        self.assertEqual(response.status_code, 200)
        rows = response.json().get("results", response.json())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["student"], alice_student.pk)