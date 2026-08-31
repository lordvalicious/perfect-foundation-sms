"""API tests for exam management (create/edit exams, subjects,
schedules with invigilators, and seating allocation)."""

from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment
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
from apps.students.models import Enrollment, Guardian, Student
from apps.teachers.models import Teacher

from .models import Exam, ExamSchedule, ExamSeating, ExamSubject


class ExamManagementBase(TestCase):
    """Shared school, users and exam fixtures for management tests."""

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

        self.subject = Subject.objects.create(
            name="English",
            code="ENG-MGMT",
            institution=self.school,
        )
        SubjectOffering.objects.create(
            subject=self.subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )

        # Manager (superuser) sees everything and may write.
        User = get_user_model()
        self.manager = User.objects.create_superuser(
            username="exam-manager",
            email="manager@test.edu",
            password="TestPass123!",
        )
        manager_membership = InstitutionMembership.objects.create(
            user=self.manager,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=manager_membership,
            role=Role.SUPER_ADMIN,
        )

        # Non-manager teacher may read but not manage exams.
        self.teacher_user = User.objects.create_user(
            username="exam-teacher",
            email="teacher@test.edu",
            password="TestPass123!",
        )
        teacher_membership = InstitutionMembership.objects.create(
            user=self.teacher_user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=teacher_membership,
            role=Role.TEACHER,
        )

        self.invigilator = Teacher.objects.create(
            institution=self.school,
            employee_number="T-EXAM-1",
            first_name="Proctor",
            last_name="One",
            email="proctor@test.edu",
            gender="female",
        )

        self.client = APIClient()

    def login_manager(self):
        self.client.force_login(self.manager)

    def login_teacher(self):
        self.client.force_login(self.teacher_user)

    def exam_payload(self, **overrides):
        payload = {
            "name": "Midterm 2026",
            "exam_type": "midterm",
            "academic_year": self.year.id,
            "term": self.term.id,
            "campus": self.campus.id,
            "class_obj": self.class_obj.id,
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
            "status": "draft",
        }
        payload.update(overrides)
        return payload

    def create_exam(self, status="draft"):
        return Exam.objects.create(
            name="Midterm 2026",
            exam_type="midterm",
            academic_year=self.year,
            term=self.term,
            campus=self.campus,
            class_obj=self.class_obj,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
            status=status,
        )

    def create_exam_subject(self, exam=None, subject=None):
        return ExamSubject.objects.create(
            exam=exam or self.create_exam(),
            subject=subject or self.subject,
            maximum_marks=100,
            passing_marks=40,
        )

    def make_student(self, admission, section):
        guardian = Guardian.objects.create(
            name="Parent",
            relationship="Father",
            phone="03000000000",
        )
        student = Student.objects.create(
            admission_number=admission,
            first_name=f"Student {admission}",
            gender="male",
            guardian=guardian,
        )
        Enrollment.objects.create(
            student=student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=section,
        )
        return student


class ExamCrudApiTests(ExamManagementBase):
    def test_manager_can_create_exam(self):
        self.login_manager()
        response = self.client.post(
            "/api/exams/",
            self.exam_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        self.assertEqual(data["name"], "Midterm 2026")
        self.assertEqual(data["exam_type"], "midterm")
        self.assertEqual(data["status"], "draft")
        self.assertTrue(Exam.objects.filter(pk=data["id"]).exists())

    def test_teacher_cannot_create_exam(self):
        self.login_teacher()
        response = self.client.post(
            "/api/exams/",
            self.exam_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_list_exams(self):
        self.create_exam()
        self.login_teacher()
        response = self.client.get("/api/exams/")
        self.assertEqual(response.status_code, 200)
        # A teacher without a class-teacher assignment is scoped to no
        # classes, so the response is readable but empty.
        self.assertEqual(response.json()["count"], 0)

    def test_exam_cross_institution_campus_rejected(self):
        other_school = School.objects.create(name="Other School")
        other_campus = Campus.objects.create(school=other_school, name="Other Campus")
        self.login_manager()
        response = self.client.post(
            "/api/exams/",
            self.exam_payload(campus=other_campus.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        # assert_campus_allowed raises for unauthorised campus first.
        self.assertIn(response.status_code, (400, 403))

    def test_manager_can_edit_and_delete_exam(self):
        exam = self.create_exam()
        self.login_manager()

        update = self.client.patch(
            f"/api/exams/{exam.id}/",
            {"name": "Renamed Midterm"},
            format="json",
        )
        self.assertEqual(update.status_code, 200, update.content)
        exam.refresh_from_db()
        self.assertEqual(exam.name, "Renamed Midterm")

        delete = self.client.delete(f"/api/exams/{exam.id}/")
        self.assertEqual(delete.status_code, 204)
        self.assertFalse(Exam.objects.filter(pk=exam.id).exists())

    def test_teacher_cannot_update_exam(self):
        exam = self.create_exam()
        self.login_teacher()
        response = self.client.patch(
            f"/api/exams/{exam.id}/",
            {"name": "Hacked"},
            format="json",
        )
        # Teachers are scoped out of exams for classes they do not
        # teach, so the object is not visible at all.
        self.assertEqual(response.status_code, 404)


class ExamSubjectApiTests(ExamManagementBase):
    def test_manager_can_add_subject_to_draft_exam(self):
        exam = self.create_exam(status="draft")
        self.login_manager()
        response = self.client.post(
            "/api/exams/subjects/",
            {
                "exam": exam.id,
                "subject": self.subject.id,
                "maximum_marks": 100,
                "passing_marks": 40,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["subject_name"], "English")

    def test_subject_requires_offering(self):
        exam = self.create_exam(status="draft")
        unoffered = Subject.objects.create(
            name="Unavailable",
            code="UNAVAIL",
            institution=self.school,
        )
        self.login_manager()
        response = self.client.post(
            "/api/exams/subjects/",
            {
                "exam": exam.id,
                "subject": unoffered.id,
                "maximum_marks": 100,
                "passing_marks": 40,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_subject_changes_blocked_outside_draft(self):
        exam = self.create_exam(status="scheduled")
        self.login_manager()
        response = self.client.post(
            "/api/exams/subjects/",
            {
                "exam": exam.id,
                "subject": self.subject.id,
                "maximum_marks": 100,
                "passing_marks": 40,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_subject_delete_blocked_once_scheduled(self):
        exam_subject = self.create_exam_subject(exam=self.create_exam(status="scheduled"))
        self.login_manager()
        response = self.client.delete(f"/api/exams/subjects/{exam_subject.id}/")
        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_add_subject(self):
        exam = self.create_exam(status="draft")
        self.login_teacher()
        response = self.client.post(
            "/api/exams/subjects/",
            {
                "exam": exam.id,
                "subject": self.subject.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_subject_unique_per_exam(self):
        exam = self.create_exam(status="draft")
        self.create_exam_subject(exam=exam)
        self.login_manager()
        response = self.client.post(
            "/api/exams/subjects/",
            {
                "exam": exam.id,
                "subject": self.subject.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class ExamScheduleApiTests(ExamManagementBase):
    def test_manager_can_create_schedule_with_invigilator(self):
        exam = self.create_exam(status="scheduled")
        exam_subject = self.create_exam_subject(exam=exam)
        self.login_manager()

        response = self.client.post(
            "/api/exams/schedules/",
            {
                "exam": exam.id,
                "section": self.section_a.id,
                "exam_subject": exam_subject.id,
                "date": "2026-10-01",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "room": "Hall 1",
                "invigilator": self.invigilator.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        self.assertEqual(data["invigilator_name"], "Proctor One")
        self.assertEqual(data["subject_name"], "English")

    def test_schedule_conflict_rejected(self):
        exam = self.create_exam(status="draft")
        self.login_manager()
        payload = {
            "exam": exam.id,
            "section": self.section_a.id,
            "date": "2026-10-01",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "room": "Hall 1",
        }
        first = self.client.post(
            "/api/exams/schedules/",
            payload,
            format="json",
        )
        self.assertEqual(first.status_code, 201)

        conflicting = self.client.post(
            "/api/exams/schedules/",
            {**payload, "room": "Hall 2"},
            format="json",
        )
        self.assertEqual(conflicting.status_code, 400)

    def test_schedule_blocked_for_completed_exam(self):
        exam = self.create_exam(status="completed")
        self.login_manager()
        response = self.client.post(
            "/api/exams/schedules/",
            {
                "exam": exam.id,
                "section": self.section_a.id,
                "date": "2026-10-01",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "room": "Hall 1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class ExamSeatingApiTests(ExamManagementBase):
    def setUp(self):
        super().setUp()
        self.exam = self.create_exam(status="scheduled")
        self.student_a = self.make_student("SEAT-A", self.section_a)
        self.student_b = self.make_student("SEAT-B", self.section_a)

    def test_manager_can_assign_single_seat(self):
        self.login_manager()
        response = self.client.post(
            "/api/exams/seating/",
            {
                "exam": self.exam.id,
                "section": self.section_a.id,
                "student": self.student_a.id,
                "seat_number": 5,
                "room": "Hall 1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["student_name"], "Student SEAT-A")

    def test_non_manager_cannot_assign_seats(self):
        self.login_teacher()
        response = self.client.post(
            "/api/exams/seating/",
            {
                "exam": self.exam.id,
                "section": self.section_a.id,
                "student": self.student_a.id,
                "seat_number": 5,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_bulk_seating_assignment(self):
        self.login_manager()
        response = self.client.post(
            "/api/exams/seating/bulk/",
            {
                "exam": self.exam.id,
                "section": self.section_a.id,
                "items": [
                    {"student": self.student_a.id, "seat_number": 1, "room": "Hall 1"},
                    {"student": self.student_b.id, "seat_number": 2, "room": "Hall 1"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["count"], 2)
        self.assertEqual(ExamSeating.objects.filter(exam=self.exam).count(), 2)

    def test_bulk_duplicate_seat_rejected(self):
        self.login_manager()
        response = self.client.post(
            "/api/exams/seating/bulk/",
            {
                "exam": self.exam.id,
                "section": self.section_a.id,
                "items": [
                    {"student": self.student_a.id, "seat_number": 1},
                    {"student": self.student_b.id, "seat_number": 1},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_student_seat_per_exam_rejected(self):
        ExamSeating.objects.create(
            exam=self.exam,
            section=self.section_a,
            student=self.student_a,
            seat_number=1,
        )
        self.login_manager()
        response = self.client.post(
            "/api/exams/seating/",
            {
                "exam": self.exam.id,
                "section": self.section_a.id,
                "student": self.student_a.id,
                "seat_number": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_student_not_enrolled_rejected(self):
        other = self.make_student("SEAT-X", self.section_b)
        other.enrollments.all().delete()
        self.login_manager()
        response = self.client.post(
            "/api/exams/seating/",
            {
                "exam": self.exam.id,
                "section": self.section_a.id,
                "student": other.id,
                "seat_number": 9,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)