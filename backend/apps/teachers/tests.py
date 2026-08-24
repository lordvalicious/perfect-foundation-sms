from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, Section, School, Subject

from .models import Teacher, TeacherAssignment


class TeacherAssignmentModelTests(TestCase):
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
        teacher = Teacher.objects.create(
            employee_number="T-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
        )
        subject = Subject.objects.create(name="English", code="ENG-TEACHER")
        self.assignment_data = {
            "teacher": teacher,
            "campus": campus,
            "class_obj": class_obj,
            "section": section,
            "subject": subject,
            "academic_year": year,
        }

    def test_assignment_rejects_class_from_another_campus(self):
        other_campus = Campus.objects.create(school=self.assignment_data["campus"].school, name="North Campus")
        other_unit = AcademicUnit.objects.create(campus=other_campus, name="Secondary")
        other_class = Class.objects.create(unit=other_unit, name="Grade 2")
        other_section = Section.objects.create(class_obj=other_class, name="A")
        assignment_data = self.assignment_data.copy()
        assignment_data["class_obj"] = other_class
        assignment_data["section"] = other_section
        assignment = TeacherAssignment(**assignment_data)

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_duplicate_assignment_is_rejected(self):
        TeacherAssignment.objects.create(**self.assignment_data)

        with self.assertRaises(ValidationError):
            TeacherAssignment.objects.create(**self.assignment_data)