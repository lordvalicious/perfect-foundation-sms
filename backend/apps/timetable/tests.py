from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, Section, School, Subject, SubjectOffering
from apps.teachers.models import Teacher

from .models import Period, TimetableEntry


class TimetableModelTests(TestCase):
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
		subject = Subject.objects.create(name="English", code="ENG-TT")
		SubjectOffering.objects.create(
			subject=subject,
			class_obj=class_obj,
			academic_year=year,
		)
		teacher = Teacher.objects.create(
			employee_number="T-TT-001",
			first_name="Ayesha",
			last_name="Khan",
			gender="female",
			campus="Main Campus",
		)
		period = Period.objects.create(
			name="Period 1",
			number=1,
			start_time=time(8, 0),
			end_time=time(8, 45),
		)
		self.entry_data = {
			"academic_year": year,
			"campus": campus,
			"class_obj": class_obj,
			"section": section,
			"subject": subject,
			"teacher": teacher,
			"period": period,
			"day": "monday",
		}

	def test_timetable_rejects_break_period(self):
		self.entry_data["period"] = Period.objects.create(
			name="Break",
			number=2,
			start_time=time(8, 45),
			end_time=time(9, 0),
			is_break=True,
		)

		with self.assertRaises(ValidationError):
			TimetableEntry.objects.create(**self.entry_data)

	def test_timetable_rejects_duplicate_section_period(self):
		TimetableEntry.objects.create(**self.entry_data)

		with self.assertRaises(ValidationError):
			TimetableEntry.objects.create(**self.entry_data)
