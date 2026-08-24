from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, Section, School
from apps.students.models import Enrollment, Guardian, Student

from .models import Attendance


class AttendanceModelTests(TestCase):
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
		guardian = Guardian.objects.create(
			name="Test Parent",
			relationship="Father",
			phone="03000000000",
		)
		self.student = Student.objects.create(
			admission_number="ADM-ATT-001",
			first_name="Ali",
			gender="male",
			guardian=guardian,
		)
		self.enrollment = Enrollment.objects.create(
			student=self.student,
			academic_year=self.year,
			campus=self.campus,
			class_obj=self.class_obj,
			section=self.section,
		)

	def test_attendance_rejects_student_mismatch(self):
		other_student = Student.objects.create(
			admission_number="ADM-ATT-002",
			first_name="Sara",
			gender="female",
			guardian=self.student.guardian,
		)
		attendance = Attendance(
			student=other_student,
			enrollment=self.enrollment,
			academic_year=self.year,
			campus=self.campus,
			class_obj=self.class_obj,
			section=self.section,
			date=date(2026, 9, 1),
		)

		with self.assertRaises(ValidationError):
			attendance.full_clean()

	def test_attendance_allows_one_record_per_student_per_day(self):
		attendance_data = {
			"student": self.student,
			"enrollment": self.enrollment,
			"academic_year": self.year,
			"campus": self.campus,
			"class_obj": self.class_obj,
			"section": self.section,
			"date": date(2026, 9, 1),
		}
		Attendance.objects.create(**attendance_data)

		with self.assertRaises(ValidationError):
			Attendance.objects.create(**attendance_data)
