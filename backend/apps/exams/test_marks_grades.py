from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
)
from apps.reportcards.models import GradeBand, GradeScale
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

from .models import Exam, ExamSubject, StudentResult
from .services import GradeService, MarksService


class MarksCalculationBase(TestCase):
    """Shared, canonical grading-scale setup for deterministic tests."""

    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 1")
        self.section = Section.objects.create(class_obj=self.class_obj, name="A")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )

        self.scale = GradeScale.objects.create(
            institution=self.school,
            name="Deterministic (A-F)",
            is_default=True,
        )
        # minimum inclusive, maximum exclusive (canonical contract)
        for letter, gpa, lo, hi in [
            ("A", "4.00", 80, 100),
            ("B", "3.00", 60, 80),
            ("C", "2.00", 40, 60),
            ("F", "0.00", 0, 40),
        ]:
            GradeBand.objects.create(
                scale=self.scale,
                letter_grade=letter,
                grade_point=gpa,
                minimum_percentage=lo,
                maximum_percentage=hi,
            )

        self.exam = Exam.objects.create(
            name="Midterm",
            exam_type="midterm",
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
        )

        self.guardian = Guardian.objects.create(
            name="Parent",
            relationship="Father",
            phone="03000000000",
        )
        self.student = Student.objects.create(
            admission_number="ADM-MARKS-001",
            first_name="Ali",
            gender="male",
            guardian=self.guardian,
        )
        Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
        )

    def make_subject_result(self, subject_code, maximum, obtained, is_absent=False):
        subject = Subject.objects.create(name=f"S{subject_code}", code=subject_code)
        SubjectOffering.objects.create(
            subject=subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )
        exam_subject = ExamSubject.objects.create(
            exam=self.exam,
            subject=subject,
            maximum_marks=maximum,
            passing_marks=Decimal(str(int(maximum * 0.4))),
        )
        return StudentResult.objects.create(
            exam=self.exam,
            student=self.student,
            exam_subject=exam_subject,
            obtained_marks=Decimal(str(obtained)),
            is_absent=is_absent,
        )


class PercentageCalculationTests(MarksCalculationBase):
    def test_percentage_exact(self):
        self.assertEqual(
            MarksService().percentage(Decimal("75"), Decimal("100")),
            Decimal("75.00"),
        )

    def test_percentage_rounds_half_up(self):
        self.assertEqual(
            MarksService().percentage(Decimal("25"), Decimal("40")),
            Decimal("62.50"),
        )

    def test_percentage_zero_maximum(self):
        self.assertEqual(
            MarksService().percentage(Decimal("10"), Decimal("0")),
            Decimal("0.00"),
        )

    def test_percentage_full_marks(self):
        self.assertEqual(
            MarksService().percentage(Decimal("80"), Decimal("80")),
            Decimal("100.00"),
        )


class GradeBoundaryTests(MarksCalculationBase):
    def test_grade_lower_inclusive_boundary(self):
        service = MarksService(institution=self.school)
        self.assertEqual(service.grade(Decimal("40.00")), "C")
        self.assertEqual(service.grade(Decimal("60.00")), "B")
        self.assertEqual(service.grade(Decimal("80.00")), "A")

    def test_grade_upper_exclusive_boundary(self):
        service = MarksService(institution=self.school)
        self.assertEqual(service.grade(Decimal("59.99")), "C")
        self.assertEqual(service.grade(Decimal("79.99")), "B")

    def test_grade_in_range(self):
        service = MarksService(institution=self.school)
        self.assertEqual(service.grade(Decimal("50.00")), "C")
        self.assertEqual(service.grade(Decimal("70.00")), "B")
        self.assertEqual(service.grade(Decimal("90.00")), "A")

    def test_grade_point_matches_band(self):
        service = MarksService(institution=self.school)
        self.assertEqual(service.grade_point(Decimal("90.00")), Decimal("4.00"))
        self.assertEqual(service.grade_point(Decimal("50.00")), Decimal("2.00"))
        self.assertEqual(service.grade_point(Decimal("30.00")), Decimal("0.00"))


class GpaCalculationTests(MarksCalculationBase):
    def test_gpa_averages_grade_points(self):
        math = self.make_subject_result("MATH-M", 100, 90)   # A -> 4.0
        eng = self.make_subject_result("ENG-M", 100, 70)     # B -> 3.0
        sci = self.make_subject_result("SCI-M", 100, 50)     # C -> 2.0

        service = MarksService(institution=self.school)
        self.assertEqual(service.gpa([math, eng, sci]), Decimal("3.00"))

    def test_gpa_excludes_absent_subjects(self):
        math = self.make_subject_result("MATH-G", 100, 90)               # A -> 4.0
        absent = self.make_subject_result("ABS-G", 100, 0, is_absent=True)

        service = MarksService(institution=self.school)
        self.assertEqual(service.gpa([math, absent]), Decimal("4.00"))

    def test_gpa_empty_returns_zero(self):
        service = MarksService(institution=self.school)
        self.assertEqual(service.gpa([]), Decimal("0.00"))

    def test_gpa_all_absent_returns_zero(self):
        absent = self.make_subject_result("ABS2-G", 100, 0, is_absent=True)
        service = MarksService(institution=self.school)
        self.assertEqual(service.gpa([absent]), Decimal("0.00"))


class PassFailTests(MarksCalculationBase):
    def test_overall_pass_only_when_all_subjects_pass(self):
        math = self.make_subject_result("MATH-P", 100, 90)
        eng = self.make_subject_result("ENG-P", 100, 70)

        service = MarksService(institution=self.school)
        overall = service.overall([math, eng])
        self.assertTrue(overall["is_pass"])
        self.assertEqual(overall["overall_result"], "Pass")

    def test_overall_fails_when_any_subject_fails(self):
        math = self.make_subject_result("MATH-F", 100, 90)
        failing = self.make_subject_result("ENG-F", 100, 20)

        service = MarksService(institution=self.school)
        overall = service.overall([math, failing])
        self.assertFalse(overall["is_pass"])
        self.assertEqual(overall["overall_result"], "Fail")

    def test_subject_result_reports_pass_and_fail(self):
        service = MarksService(institution=self.school)
        passed = self.make_subject_result("SUB-PA", 100, 70)
        self.assertTrue(service.subject_result(passed)["is_pass"])

        failed = self.make_subject_result("SUB-FA", 100, 10)
        self.assertFalse(service.subject_result(failed)["is_pass"])


class InvalidMarksTests(MarksCalculationBase):
    def test_absent_must_be_zero(self):
        with self.assertRaises(ValidationError):
            self.make_subject_result("ABS-B", 100, 50, is_absent=True)

    def test_marks_above_maximum_rejected(self):
        with self.assertRaises(ValidationError):
            self.make_subject_result("OVER-B", 100, 101)

    def test_negative_marks_rejected(self):
        with self.assertRaises(ValidationError):
            self.make_subject_result("NEG-B", 100, -5)


class GradeServiceDelegationTests(MarksCalculationBase):
    def test_get_grade_bands_reflects_configured_scale(self):
        service = GradeService(institution=self.school)
        bands = service.get_grade_bands()
        self.assertEqual(len(bands), 4)
        self.assertEqual(bands[0]["grade"], "A")
        self.assertEqual(bands[-1]["grade"], "F")

    def test_calculate_grade_uses_configured_scale(self):
        service = GradeService(institution=self.school)
        self.assertEqual(service.calculate_grade(Decimal("90"))["grade"], "A")
        self.assertEqual(service.calculate_grade(Decimal("50"))["grade"], "C")
        self.assertEqual(service.calculate_grade(Decimal("50"))["gpa"], Decimal("2.00"))

    def test_calculate_gpa_delegates_to_configured_scale(self):
        math = self.make_subject_result("MATH-CG", 100, 90)  # A -> 4.0
        eng = self.make_subject_result("ENG-CG", 100, 50)    # C -> 2.0

        service = GradeService(institution=self.school)
        self.assertEqual(service.calculate_gpa([math, eng]), Decimal("3.00"))


class MarksAuthorizationTests(MarksCalculationBase):
    def setUp(self):
        super().setUp()
        self.teacher_user = get_user_model().objects.create_user(
            username="marks-teacher",
            email="teacher@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(
            user=self.teacher_user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=Role.TEACHER,
        )

        self.other_user = get_user_model().objects.create_user(
            username="marks-other",
            email="other@test.edu",
            password="TestPass123!",
        )
        other_membership = InstitutionMembership.objects.create(
            user=self.other_user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=other_membership,
            role=Role.TEACHER,
        )

        self.math_subject = Subject.objects.create(name="Maths", code="MATH-AUTH")
        SubjectOffering.objects.create(
            subject=self.math_subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )
        self.exam_subject = ExamSubject.objects.create(
            exam=self.exam,
            subject=self.math_subject,
            maximum_marks=100,
            passing_marks=40,
        )

    def test_teacher_without_assignment_cannot_write_marks(self):
        # A teacher with no TeacherAssignment for this subject/campus
        # is rejected at the write path.
        from apps.exams.views import teacher_can_manage_exam_subject

        self.assertFalse(
            teacher_can_manage_exam_subject(
                self.other_user,
                self.exam_subject,
            )
        )
