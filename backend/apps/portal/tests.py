from datetime import date
from itertools import count

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment, User
from apps.attendance.models import Attendance
from apps.communication.models import Announcement
from apps.exams.models import Exam, ExamSubject, StudentResult
from apps.finance.models import FeeCategory, Invoice, InvoiceItem, Payment
from apps.homework.models import Homework, Submission
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
from apps.students.models import (
    Enrollment,
    Guardian,
    Student,
    StudentLeaveRequest,
)
from apps.teachers.models import Teacher, TeacherAssignment
from apps.transport.models import Route, RouteStop, TransportAssignment

_user_seq = count(1)
_student_seq = count(1)


class PortalTestCase(TestCase):
    def _add_membership(self, user, school, role):
        membership = InstitutionMembership.objects.create(
            user=user,
            institution=school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=role,
        )
        return membership

    def _make_school(self):
        school = School.objects.create(name="Sunrise High")
        campus = Campus.objects.create(school=school, name="Main Campus")
        unit = AcademicUnit.objects.create(campus=campus, name="Primary")
        class_obj = Class.objects.create(unit=unit, name="Grade 7")
        section = Section.objects.create(class_obj=class_obj, name="A")
        year = AcademicYear.objects.create(
            school=school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )
        subject = Subject.objects.create(name="English", code="ENG-PORTAL")
        return {
            "school": school,
            "campus": campus,
            "class_obj": class_obj,
            "section": section,
            "year": year,
            "subject": subject,
        }

    def _make_user(self, role, school, label):
        n = next(_user_seq)
        user = User.objects.create_user(
            username=f"{label}{n}",
            email=f"{label}{n}@test.edu",
            password="TestPass123!",
        )
        membership = self._add_membership(user, school, role)
        return user, membership

    def _make_teacher_user(self, school):
        user, membership = self._make_user(Role.TEACHER, school, "tportal")
        teacher = Teacher.objects.create(
            employee_number="T-PORTAL-1",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            user=user,
            membership=membership,
            institution=school,
        )
        return user, teacher

    def _make_student_user(self, school):
        user, membership = self._make_user(Role.STUDENT, school, "sportal")
        student = Student.objects.create(
            institution=school,
            admission_number=f"ADM-{next(_student_seq)}",
            first_name="Ali",
            last_name="Reza",
            gender="male",
            guardian=Guardian.objects.create(
                name="Guardian One",
                relationship="Parent",
                phone="0711111111",
            ),
            user=user,
            membership=membership,
        )
        return user, student

    def _make_parent_user(self, school):
        user, membership = self._make_user(Role.PARENT, school, "pportal")
        guardian = Guardian.objects.create(
            name="Guardian Parent",
            relationship="Parent",
            phone="0712222222",
            user=user,
        )
        return user, guardian

    def _make_child(self, school, guardian, first_name):
        return Student.objects.create(
            institution=school,
            admission_number=f"ADM-P-{next(_student_seq)}",
            first_name=first_name,
            last_name="Child",
            gender="female",
            guardian=guardian,
        )

    def _authed_client(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client


class TeacherPortalTests(PortalTestCase):
    def setUp(self):
        self.data = self._make_school()
        self.user, self.teacher = self._make_teacher_user(self.data["school"])
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            subject=self.data["subject"],
            academic_year=self.data["year"],
            role="class_teacher",
            status="active",
        )

    def _enroll_student(self):
        student = Student.objects.create(
            institution=self.data["school"],
            admission_number=f"ADM-{next(_student_seq)}",
            first_name="Student",
            last_name="One",
            gender="male",
            guardian=Guardian.objects.create(
                name="Guardian One",
                relationship="Parent",
                phone="0711111111",
            ),
        )
        Enrollment.objects.create(
            student=student,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
        )
        return student

    def test_requires_teacher_profile(self):
        admin, _ = self._make_user(Role.ADMIN, self.data["school"], "adminportal")
        resp = self._authed_client(admin).get(reverse("portal-teacher"))
        self.assertEqual(resp.status_code, 403)
        self.assertIn("teacher profile", resp.json().get("detail", "").lower())

    def test_teacher_portal_payload(self):
        self._enroll_student()
        resp = self._authed_client(self.user).get(reverse("portal-teacher"))
        self.assertEqual(resp.status_code, 200)

        payload = resp.json()
        self.assertEqual(payload["portal"], "teacher")
        self.assertEqual(payload["academic_year"], "2026-2027")
        self.assertEqual(payload["profile"]["employee_number"], "T-PORTAL-1")
        self.assertEqual(payload["profile"]["full_name"], "Ayesha Khan")
        self.assertEqual(payload["stats"]["students"], 1)
        self.assertEqual(payload["stats"]["sections"], 1)
        self.assertEqual(payload["stats"]["classes"], 1)
        self.assertEqual(payload["stats"]["subjects"], 1)
        self.assertEqual(len(payload["assignments"]), 1)
        assignment = payload["assignments"][0]
        self.assertEqual(assignment["class_name"], "Grade 7")
        self.assertEqual(assignment["section_name"], "A")
        self.assertEqual(assignment["subject_name"], "English")

    def test_student_count_only_active_assignments(self):
        self._enroll_student()
        math = Subject.objects.create(name="Math", code="MATH-PORTAL")
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            subject=math,
            academic_year=self.data["year"],
            role="class_teacher",
            status="inactive",
        )
        resp = self._authed_client(self.user).get(reverse("portal-teacher"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["stats"]["students"], 1)


class StudentPortalTests(PortalTestCase):
    def setUp(self):
        self.data = self._make_school()
        self.user, self.student = self._make_student_user(self.data["school"])
        Enrollment.objects.create(
            student=self.student,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
        )

    def test_requires_student_profile(self):
        admin, _ = self._make_user(Role.ADMIN, self.data["school"], "adminportal2")
        resp = self._authed_client(admin).get(reverse("portal-student"))
        self.assertEqual(resp.status_code, 403)
        self.assertIn("student profile", resp.json().get("detail", "").lower())

    def test_student_portal_payload(self):
        resp = self._authed_client(self.user).get(reverse("portal-student"))
        self.assertEqual(resp.status_code, 200)

        payload = resp.json()
        self.assertEqual(payload["portal"], "student")
        self.assertEqual(payload["profile"]["admission_number"], self.student.admission_number)
        self.assertEqual(payload["profile"]["full_name"], "Ali Reza")
        self.assertEqual(payload["profile"]["enrollment"]["class_name"], "Grade 7")
        self.assertEqual(payload["profile"]["enrollment"]["section_name"], "A")
        self.assertEqual(payload["stats"]["recorded_days"], 0)
        self.assertEqual(payload["stats"]["results"], 0)
        self.assertEqual(payload["stats"]["fee_balance"], 0.0)


class PortalAnnouncementTests(PortalTestCase):
    def setUp(self):
        self.data = self._make_school()
        self.teacher_user, _ = self._make_teacher_user(self.data["school"])
        self.student_user, _ = self._make_student_user(self.data["school"])
        self.parent_user, self.parent_guardian = self._make_parent_user(self.data["school"])

    def test_teacher_only_announcement_reaches_teacher_not_student(self):
        Announcement.objects.create(
            institution=self.data["school"],
            title="Staff meeting",
            message="Mandatory staff meeting on Monday.",
            audience_roles=["teacher"],
            status="published",
        )

        teacher_resp = self._authed_client(self.teacher_user).get(
            reverse("portal-teacher")
        )
        self.assertEqual(teacher_resp.status_code, 200)
        announcements = teacher_resp.json()["announcements"]
        self.assertEqual(len(announcements), 1)
        self.assertEqual(announcements[0]["title"], "Staff meeting")

        student_resp = self._authed_client(self.student_user).get(
            reverse("portal-student")
        )
        self.assertEqual(student_resp.status_code, 200)
        self.assertEqual(student_resp.json()["announcements"], [])

    def test_draft_announcement_not_visible(self):
        Announcement.objects.create(
            institution=self.data["school"],
            title="Draft note",
            message="Not yet published.",
            audience_roles=["teacher"],
            status="draft",
        )
        resp = self._authed_client(self.teacher_user).get(reverse("portal-teacher"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["announcements"], [])

    def test_class_targeted_parent_announcement_reaches_guardian(self):
        child = Student.objects.create(
            institution=self.data["school"],
            admission_number=f"ADM-PA-{next(_student_seq)}",
            first_name="Sana",
            last_name="Child",
            gender="female",
            guardian=self.parent_guardian,
        )
        Enrollment.objects.create(
            student=child,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
        )
        Announcement.objects.create(
            institution=self.data["school"],
            title="PTM scheduled",
            message="Parent teacher meeting on Saturday.",
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            audience_roles=["parent"],
            status="published",
        )
        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        self.assertEqual(resp.status_code, 200)
        announcements = resp.json()["announcements"]
        self.assertEqual(len(announcements), 1)
        self.assertEqual(announcements[0]["title"], "PTM scheduled")

    def test_org_wide_parent_announcement_reaches_parent_only(self):
        Announcement.objects.create(
            institution=self.data["school"],
            title="School closed",
            message="School is closed on Monday.",
            audience_roles=["parent"],
            status="published",
        )
        parent_resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        self.assertEqual(parent_resp.status_code, 200)
        self.assertEqual(len(parent_resp.json()["announcements"]), 1)
        self.assertEqual(
            parent_resp.json()["announcements"][0]["title"],
            "School closed",
        )
        student_resp = self._authed_client(self.student_user).get(
            reverse("portal-student")
        )
        self.assertEqual(student_resp.status_code, 200)
        self.assertEqual(student_resp.json()["announcements"], [])


class ParentPortalTests(PortalTestCase):
    def setUp(self):
        self.data = self._make_school()
        self.parent_user, self.guardian = self._make_parent_user(self.data["school"])
        self.child_a = self._make_child(self.data["school"], self.guardian, "Maryam")
        self.child_b = self._make_child(self.data["school"], self.guardian, "Omar")
        self.enr_a = Enrollment.objects.create(
            student=self.child_a,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
        )
        self.enr_b = Enrollment.objects.create(
            student=self.child_b,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
        )

    def _child_payload(self, resp_json, child):
        return next(
            c for c in resp_json["children"] if c["id"] == child.id
        )

    def test_requires_guardian_profile(self):
        admin, _ = self._make_user(Role.ADMIN, self.data["school"], "adminportal3")
        resp = self._authed_client(admin).get(reverse("portal-parent"))
        self.assertEqual(resp.status_code, 403)
        self.assertIn("guardian", resp.json().get("detail", "").lower())

    def test_returns_only_own_children(self):
        other_guardian = Guardian.objects.create(
            name="Other Guardian",
            relationship="Parent",
            phone="0713333333",
        )
        self._make_child(self.data["school"], other_guardian, "Ayesha")

        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        self.assertEqual(resp.status_code, 200)

        payload = resp.json()
        self.assertEqual(payload["portal"], "parent")
        self.assertEqual(payload["profile"]["children_count"], 2)
        self.assertEqual(payload["profile"]["name"], "Guardian Parent")
        names = {child["full_name"] for child in payload["children"]}
        self.assertEqual(names, {"Maryam Child", "Omar Child"})
        self.assertNotIn("Ayesha Child", names)

    def test_child_enrollment_attendance_and_leave(self):
        Attendance.objects.create(
            student=self.child_a,
            enrollment=self.enr_a,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            date=date(2026, 9, 1),
            status="present",
        )
        Attendance.objects.create(
            student=self.child_a,
            enrollment=self.enr_a,
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            date=date(2026, 9, 2),
            status="absent",
        )
        StudentLeaveRequest.objects.create(
            student=self.child_a,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
            reason="Family travel",
            requested_by=self.parent_user,
        )

        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        child = self._child_payload(resp.json(), self.child_a)
        self.assertEqual(child["enrollment"]["class_name"], "Grade 7")
        self.assertEqual(child["enrollment"]["section_name"], "A")
        self.assertEqual(child["recorded_days"], 2)
        self.assertEqual(child["attendance_rate"], 50)
        self.assertEqual(child["present"], 1)
        self.assertEqual(child["absent"], 1)
        self.assertEqual(len(child["attendance_records"]), 2)
        self.assertEqual(len(child["leave"]), 1)
        self.assertEqual(child["leave"][0]["reason"], "Family travel")

    def test_child_homework_scoped_per_student_submission(self):
        teacher = Teacher.objects.create(
            employee_number="T-PARENT-HW",
            first_name="Nadia",
            last_name="Butt",
            gender="female",
            institution=self.data["school"],
        )
        hw = Homework.objects.create(
            teacher=teacher,
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            subject=self.data["subject"],
            title="Essay on trees",
            description="Write 300 words.",
            assigned_date=date(2026, 9, 1),
            due_date=date(2026, 9, 8),
            created_by=self.parent_user,
        )
        Submission.objects.create(
            homework=hw,
            student=self.child_a,
            content="Trees are important.",
            status="submitted",
        )

        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        child_a = self._child_payload(resp.json(), self.child_a)
        self.assertEqual(len(child_a["homework"]), 1)
        self.assertEqual(child_a["homework"][0]["title"], "Essay on trees")
        self.assertEqual(child_a["homework"][0]["subject_name"], "English")
        self.assertEqual(child_a["homework"][0]["submission_status"], "submitted")
        self.assertEqual(child_a["due_homework"], 0)

        child_b = self._child_payload(resp.json(), self.child_b)
        self.assertEqual(len(child_b["homework"]), 1)
        self.assertIsNone(child_b["homework"][0]["submission_status"])
        self.assertEqual(child_b["due_homework"], 1)

    def test_child_results_aggregated_per_exam(self):
        self.data["subject"].institution = self.data["school"]
        self.data["subject"].save(update_fields=["institution"])
        SubjectOffering.objects.create(
            academic_year=self.data["year"],
            class_obj=self.data["class_obj"],
            subject=self.data["subject"],
        )
        exam = Exam.objects.create(
            name="Mid-Term 2026",
            exam_type="midterm",
            academic_year=self.data["year"],
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
            status="completed",
        )
        exam_subject = ExamSubject.objects.create(
            exam=exam,
            subject=self.data["subject"],
            maximum_marks=100,
            passing_marks=40,
        )
        StudentResult.objects.create(
            exam=exam,
            student=self.child_a,
            exam_subject=exam_subject,
            obtained_marks=85,
        )

        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        child_a = self._child_payload(resp.json(), self.child_a)
        self.assertEqual(child_a["marks_count"], 1)
        self.assertEqual(len(child_a["marks"]), 1)
        self.assertEqual(child_a["marks"][0]["name"], "Mid-Term 2026")
        entry = child_a["marks"][0]["subjects"][0]
        self.assertEqual(entry["subject"], "English")
        self.assertEqual(entry["obtained"], 85.0)
        self.assertEqual(child_a["marks"][0]["percentage"], 85.0)

        child_b = self._child_payload(resp.json(), self.child_b)
        self.assertEqual(child_b["marks_count"], 0)
        self.assertEqual(child_b["marks"], [])

    def test_child_invoices_receipts_and_transport(self):
        fee = FeeCategory.objects.create(
            institution=self.data["school"],
            name="Tuition",
        )
        invoice = Invoice.objects.create(
            institution=self.data["school"],
            invoice_number="INV-P-1001",
            student=self.child_a,
            enrollment=self.enr_a,
            academic_year=self.data["year"],
            issue_date=date(2026, 9, 1),
            due_date=date(2026, 10, 1),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            category=fee,
            description="Term fee",
            amount=5000,
        )
        Payment.objects.create(
            institution=self.data["school"],
            receipt_number="RCT-P-1001",
            invoice=invoice,
            amount=5000,
            payment_date=date(2026, 9, 5),
            payment_method="cash",
        )
        route = Route.objects.create(
            institution=self.data["school"],
            name="Route 7",
        )
        stop = RouteStop.objects.create(route=route, name="Main Gate", order=1)
        TransportAssignment.objects.create(
            student=self.child_a,
            route=route,
            stop=stop,
        )

        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        child_a = self._child_payload(resp.json(), self.child_a)
        self.assertEqual(len(child_a["invoices"]), 1)
        self.assertEqual(child_a["invoices"][0]["invoice_number"], "INV-P-1001")
        self.assertEqual(child_a["invoices"][0]["status"], "paid")
        self.assertEqual(child_a["fee_balance"], 0.0)
        self.assertEqual(len(child_a["receipts"]), 1)
        self.assertEqual(child_a["receipts"][0]["receipt_number"], "RCT-P-1001")
        self.assertEqual(child_a["receipts"][0]["payment_method"], "cash")
        self.assertEqual(len(child_a["transport"]), 1)
        self.assertEqual(child_a["transport"][0]["route"], "Route 7")
        self.assertEqual(child_a["transport"][0]["stop"], "Main Gate")

        child_b = self._child_payload(resp.json(), self.child_b)
        self.assertEqual(child_b["invoices"], [])
        self.assertEqual(child_b["receipts"], [])
        self.assertEqual(child_b["transport"], [])
        self.assertEqual(child_b["fee_balance"], 0.0)

    def test_child_teacher_list_for_communication(self):
        teacher = Teacher.objects.create(
            employee_number="T-PARENT-1",
            first_name="Nadia",
            last_name="Butt",
            gender="female",
            institution=self.data["school"],
            primary_campus=self.data["campus"],
            phone="0300-1112222",
            email="nadia@test.edu",
            designation="Class Teacher",
        )
        TeacherAssignment.objects.create(
            teacher=teacher,
            campus=self.data["campus"],
            class_obj=self.data["class_obj"],
            section=self.data["section"],
            subject=self.data["subject"],
            academic_year=self.data["year"],
            role="class_teacher",
            status="active",
        )

        resp = self._authed_client(self.parent_user).get(reverse("portal-parent"))
        child_a = self._child_payload(resp.json(), self.child_a)
        self.assertEqual(len(child_a["teachers"]), 1)
        entry = child_a["teachers"][0]
        self.assertEqual(entry["role"], "class_teacher")
        self.assertEqual(entry["teacher_name"], "Nadia Butt")
        self.assertEqual(entry["phone"], "0300-1112222")
        self.assertEqual(entry["email"], "nadia@test.edu")