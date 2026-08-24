from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
	AcademicUnit,
	AcademicYear,
	Campus,
	Class,
	School,
	Section,
	Subject,
	SubjectOffering,
)


class AcademicStructureModelTests(TestCase):
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
		self.subject = Subject.objects.create(name="English", code="ENG-SCHOOL")

	def test_section_names_are_unique_within_a_class(self):
		duplicate = Section(class_obj=self.class_obj, name="A")

		with self.assertRaises(ValidationError):
			duplicate.full_clean()

	def test_subject_offering_is_unique_for_class_and_year(self):
		SubjectOffering.objects.create(
			subject=self.subject,
			class_obj=self.class_obj,
			academic_year=self.year,
		)
		duplicate = SubjectOffering(
			subject=self.subject,
			class_obj=self.class_obj,
			academic_year=self.year,
		)

		with self.assertRaises(ValidationError):
			duplicate.full_clean()
