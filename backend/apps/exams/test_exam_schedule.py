from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
    Subject,
    SubjectOffering,
    Term,
)

from .models import Exam, ExamSchedule, ExamSubject


class ExamScheduleBase(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 1")
        self.section_a = Section.objects.create(class_obj=self.class_obj, name="A")
        self.section_b = Section.objects.create(class_obj=self.class_obj, name="B")

        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )
        self.term = Term.objects.create(
            academic_year=self.year,
            name="Term 1",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 31),
        )

        self.exam = Exam.objects.create(
            name="Midterm",
            exam_type="midterm",
            academic_year=self.year,
            term=self.term,
            campus=self.campus,
            class_obj=self.class_obj,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
        )

        self.subject = Subject.objects.create(name="English", code="ENG-EXAM-SCHED", institution=self.school)
        SubjectOffering.objects.create(
            subject=self.subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )
        self.exam_subject = ExamSubject.objects.create(
            exam=self.exam,
            subject=self.subject,
        )

    def schedule(
        self,
        section=None,
        exam_subject=None,
        slot_date=None,
        start=time(9, 0),
        end=time(11, 0),
        room="Hall 1",
    ):
        return ExamSchedule.objects.create(
            exam=self.exam,
            section=section or self.section_a,
            exam_subject=exam_subject or self.exam_subject,
            date=slot_date or date(2026, 10, 1),
            start_time=start,
            end_time=end,
            room=room,
        )

    def assert_rejected(self, **kwargs):
        with self.assertRaises(ValidationError):
            self.schedule(**kwargs)


class ExamScheduleConflictTests(ExamScheduleBase):
    def test_same_section_overlapping_time_rejected(self):
        self.schedule(start=time(9, 0), end=time(11, 0))
        self.assert_rejected(start=time(10, 0), end=time(12, 0))

    def test_same_section_adjacent_times_allowed(self):
        self.schedule(start=time(9, 0), end=time(11, 0))
        self.schedule(start=time(11, 0), end=time(13, 0))

    def test_different_sections_same_time_allowed(self):
        self.schedule(section=self.section_a, room="Hall 1", start=time(9, 0), end=time(11, 0))
        self.schedule(section=self.section_b, room="Hall 2", start=time(9, 0), end=time(11, 0))

    def test_same_room_overlapping_time_rejected(self):
        self.schedule(section=self.section_a, room="Hall 1", start=time(9, 0), end=time(11, 0))
        self.assert_rejected(
            section=self.section_b,
            room="Hall 1",
            start=time(10, 0),
            end=time(12, 0),
        )

    def test_different_room_same_time_allowed(self):
        self.schedule(section=self.section_a, room="Hall 1")
        self.schedule(section=self.section_b, room="Hall 2")


class ExamScheduleValidationTests(ExamScheduleBase):
    def test_end_time_before_start_time_rejected(self):
        self.assert_rejected(start=time(11, 0), end=time(9, 0))

    def test_date_outside_exam_period_rejected(self):
        self.assert_rejected(slot_date=date(2026, 9, 30))

    def test_section_outside_exam_class_rejected(self):
        other_unit = AcademicUnit.objects.create(
            campus=self.campus, name="Secondary"
        )
        other_class = Class.objects.create(unit=other_unit, name="Grade 9")
        other_section = Section.objects.create(class_obj=other_class, name="A")
        self.assert_rejected(section=other_section)

    def test_exam_subject_from_other_exam_rejected(self):
        other_exam = Exam.objects.create(
            name="Other",
            exam_type="final",
            academic_year=self.year,
            term=self.term,
            campus=self.campus,
            class_obj=self.class_obj,
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 5),
        )
        other_subject = Subject.objects.create(
            name="Maths", code="MATH-EXAM-SCHED", institution=self.school
        )
        SubjectOffering.objects.create(
            subject=other_subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )
        other_exam_subject = ExamSubject.objects.create(
            exam=other_exam,
            subject=other_subject,
        )

        with self.assertRaises(ValidationError):
            self.schedule(exam_subject=other_exam_subject)


class ExamTermValidationTests(ExamScheduleBase):
    def test_exam_term_must_belong_to_academic_year(self):
        other_year = AcademicYear.objects.create(
            school=self.school,
            name="2027-2028",
            start_date=date(2027, 8, 1),
            end_date=date(2028, 7, 31),
        )
        other_term = Term.objects.create(
            academic_year=other_year,
            name="Term 1",
            start_date=date(2027, 8, 1),
            end_date=date(2027, 12, 31),
        )

        exam = Exam(
            name="Bad Term",
            exam_type="midterm",
            academic_year=self.year,
            term=other_term,
            campus=self.campus,
            class_obj=self.class_obj,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
        )

        with self.assertRaises(ValidationError):
            exam.full_clean()
