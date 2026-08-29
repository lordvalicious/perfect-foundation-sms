from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.exams.models import Exam, ExamSubject, StudentResult
from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, Section, School, Subject, SubjectOffering
from apps.students.models import Enrollment, Guardian, Student

from .models import ReportCard


class ReportCardModelTests(TestCase):
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
			admission_number="ADM-CARD-001",
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
		subject = Subject.objects.create(name="English", code="ENG-CARD", institution=school)
		SubjectOffering.objects.create(
			subject=subject,
			class_obj=class_obj,
			academic_year=year,
		)
		exam = Exam.objects.create(
			name="Final",
			exam_type="final",
			academic_year=year,
			campus=campus,
			class_obj=class_obj,
			start_date=date(2027, 3, 1),
			end_date=date(2027, 3, 5),
		)
		exam_subject = ExamSubject.objects.create(
			exam=exam,
			subject=subject,
			maximum_marks=100,
			passing_marks=40,
		)
		self.student = student
		self.exam = exam
		self.exam_subject = exam_subject

	def test_report_card_aggregates_marks_and_passes(self):
		StudentResult.objects.create(
			exam=self.exam,
			student=self.student,
			exam_subject=self.exam_subject,
			obtained_marks=Decimal("80.00"),
		)
		card = ReportCard.objects.create(student=self.student, exam=self.exam)

		self.assertEqual(card.total_marks, Decimal("80.00"))
		self.assertEqual(card.percentage, Decimal("80.00"))
		self.assertTrue(card.is_pass)
		self.assertTrue(card.is_complete)

	def test_published_report_card_cannot_be_edited(self):
		card = ReportCard.objects.create(
			student=self.student,
			exam=self.exam,
			status="published",
		)

		self.assertFalse(card.can_edit)
