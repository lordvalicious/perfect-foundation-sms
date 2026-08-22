from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, School, Section

from .models import (
	AdmissionApplication,
	Guardian,
	Student,
	StudentGuardian,
	StudentLeaveRequest,
	StudentLifecycleEvent,
)


class StudentLifecycleModelTests(TestCase):
	def setUp(self):
		self.school = School.objects.create(name="Test School")
		self.campus = Campus.objects.create(school=self.school, name="Main Campus")
		unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
		self.class_obj = Class.objects.create(unit=unit, name="Grade 1")
		self.section = Section.objects.create(class_obj=self.class_obj, name="A")
		self.year = AcademicYear.objects.create(
			school=self.school,
			name="2026-2027",
			start_date=date(2026, 8, 1),
			end_date=date(2027, 7, 31),
		)
		self.guardian = Guardian.objects.create(
			name="Test Parent",
			relationship="Father",
			phone="03000000000",
		)
		self.student = Student.objects.create(
			admission_number="ADM-001",
			first_name="Ali",
			gender="male",
			guardian=self.guardian,
		)

	def test_admission_application_exposes_applicant_name(self):
		application = AdmissionApplication.objects.create(
			application_number="APP-001",
			first_name="Sara",
			last_name="Khan",
			gender="female",
			guardian=self.guardian,
			campus=self.campus,
			academic_year=self.year,
			class_obj=self.class_obj,
			section=self.section,
		)

		self.assertEqual(application.applicant_name, "Sara Khan")

	def test_admission_application_rejects_wrong_section(self):
		other_class = Class.objects.create(unit=self.class_obj.unit, name="Grade 2")
		other_section = Section.objects.create(class_obj=other_class, name="A")
		application = AdmissionApplication(
			application_number="APP-002",
			first_name="Sara",
			gender="female",
			campus=self.campus,
			academic_year=self.year,
			class_obj=self.class_obj,
			section=other_section,
		)

		with self.assertRaises(ValidationError):
			application.full_clean()

	def test_student_can_have_multiple_guardians_but_not_duplicate_links(self):
		second_guardian = Guardian.objects.create(
			name="Test Mother",
			relationship="Mother",
			phone="03111111111",
		)
		StudentGuardian.objects.create(
			student=self.student,
			guardian=self.guardian,
			relationship="Father",
			is_primary=True,
		)
		StudentGuardian.objects.create(
			student=self.student,
			guardian=second_guardian,
			relationship="Mother",
		)

		self.assertEqual(self.student.guardian_links.count(), 2)
		with self.assertRaises(IntegrityError):
			StudentGuardian.objects.create(
				student=self.student,
				guardian=self.guardian,
				relationship="Father",
			)

	def test_lifecycle_event_preserves_reason_and_student(self):
		event = StudentLifecycleEvent.objects.create(
			student=self.student,
			event_type="withdrawn",
			effective_date=date(2026, 9, 1),
			reason="Family relocation",
		)

		self.assertEqual(event.student, self.student)
		self.assertEqual(event.reason, "Family relocation")

	def test_leave_request_rejects_reverse_date_range(self):
		leave = StudentLeaveRequest(
			student=self.student,
			start_date=date(2026, 9, 10),
			end_date=date(2026, 9, 9),
			reason="Medical appointment",
		)

		with self.assertRaises(ValidationError):
			leave.full_clean()
