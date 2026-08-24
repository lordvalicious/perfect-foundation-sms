from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.schools.models import (
	AcademicUnit,
	AcademicYear,
	Campus,
	Class,
	Section,
	School,
	Subject,
	SubjectOffering,
)
from apps.students.models import Enrollment, Guardian, Student

from .models import Exam, ExamSubject, StudentResult


class ExamAndResultModelTests(TestCase):
	def setUp(self):
		school = School.objects.create(name="Test School")
		campus = Campus.objects.create(school=school, name="Main Campus")
		unit = AcademicUnit.objects.create(campus=campus, name="Primary")
		class_obj = Class.objects.create(unit=unit, name="Grade 1")
		section = Section.objects.create(class_obj=class_obj, name="A")
		year = AcademicYear.objects.create(
			school=school,
			name="2026-2027",
			start_date=date(2026, 8, 1),
			end_date=date(2027, 7, 31),
		)
		guardian = Guardian.objects.create(
			name="Test Parent",
			relationship="Father",
			phone="03000000000",
		)
		student = Student.objects.create(
			admission_number="ADM-EXAM-001",
			first_name="Ali",
			gender="male",
			guardian=guardian,
		)
		Enrollment.objects.create(
			student=student,
			academic_year=year,
			campus=campus,
			class_obj=class_obj,
			section=section,
		)
		subject = Subject.objects.create(name="English", code="ENG-EXAM")
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
			start_date=date(2026, 10, 1),
			end_date=date(2026, 10, 5),
		)
		self.student = student
		self.exam = exam
		self.exam_subject = ExamSubject.objects.create(
			exam=exam,
			subject=subject,
			maximum_marks=100,
			passing_marks=40,
		)

	def test_exam_subject_rejects_passing_marks_above_maximum(self):
		exam_subject = ExamSubject(
			exam=self.exam,
			subject=self.exam_subject.subject,
			maximum_marks=30,
			passing_marks=40,
		)

		with self.assertRaises(ValidationError):
			exam_subject.full_clean()

	def test_student_result_calculates_pass_status_and_percentage(self):
		result = StudentResult.objects.create(
			exam=self.exam,
			student=self.student,
			exam_subject=self.exam_subject,
			obtained_marks=Decimal("75.00"),
		)

		self.assertTrue(result.is_pass)
		self.assertEqual(result.percentage, Decimal("75.00"))

	def test_student_result_rejects_marks_above_maximum(self):
		result = StudentResult(
			exam=self.exam,
			student=self.student,
			exam_subject=self.exam_subject,
			obtained_marks=Decimal("101.00"),
		)

		with self.assertRaises(ValidationError):
			result.full_clean()
