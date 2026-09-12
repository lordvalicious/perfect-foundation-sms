"""P5 AI insight correctness tests.

Verifies the deterministic headline numbers (attendance rate, exam pass
rate, AR outstanding) computed by the AI services.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.exams.models import ExamSubject, StudentResult

from .helpers import (
    ensure_subject_offering,
    make_attendance,
    make_exam,
    make_invoice,
    make_member_user,
    make_school,
    make_staff_profile,
    make_structure,
    make_student,
)


class AiAttendanceInsightsTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Att", "atc")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-AT1")
        self.low = make_student(self.school, self.structure, admission="ADM-AT2")
        self.admin = make_member_user(self.school, "atc-admin", Role.ADMIN)

        today = timezone.localdate()
        make_attendance(self.student, self.structure, today)
        make_attendance(self.student, self.structure, today - timedelta(days=1))
        make_attendance(self.student, self.structure, today - timedelta(days=2), "late")
        make_attendance(self.student, self.structure, today - timedelta(days=3), "absent")
        make_attendance(self.low, self.structure, today - timedelta(days=1), "absent")

    def _client(self):
        client = APIClient()
        self.assertTrue(client.login(username="atc-admin", password="TestPass123!"))
        return client

    def test_attendance_rate_math(self):
        response = self._client().get("/api/ai/insights/attendance/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["records"], 5)
        self.assertEqual(data["present"], 3)
        self.assertEqual(data["overall_rate"], 60.0)
        self.assertEqual(data["status_breakdown"]["absent"], 2)

    def test_low_attendance_flagged_below_75(self):
        response = self._client().get("/api/ai/insights/attendance/")
        flagged = response.json()["students_below_75"]
        rates = {entry["student_id"]: entry["rate"] for entry in flagged}
        self.assertEqual(rates[self.low.pk], 0.0)
        self.assertNotIn(self.student.pk, rates)


class AiAcademicInsightsTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Acad", "aca")
        self.structure = make_structure(self.school)
        ensure_subject_offering(self.school, self.structure)
        self.passing = make_student(self.school, self.structure, admission="ADM-P1")
        self.failing = make_student(self.school, self.structure, admission="ADM-F1")
        self.admin = make_member_user(self.school, "aca-admin", Role.ADMIN)
        self.exam = make_exam(self.school, self.structure, name="Term One")
        self.exam_subject = ExamSubject.objects.create(
            exam=self.exam,
            subject=self.structure["subject"],
            maximum_marks=100,
            passing_marks=50,
        )
        StudentResult.objects.create(
            exam=self.exam,
            student=self.passing,
            exam_subject=self.exam_subject,
            obtained_marks=Decimal("80.00"),
            is_absent=False,
            grade="A",
            is_pass=True,
        )
        StudentResult.objects.create(
            exam=self.exam,
            student=self.failing,
            exam_subject=self.exam_subject,
            obtained_marks=Decimal("30.00"),
            is_absent=False,
            grade="F",
            is_pass=False,
        )

    def test_academic_pass_rate_and_average(self):
        client = APIClient()
        self.assertTrue(client.login(username="aca-admin", password="TestPass123!"))
        response = client.get("/api/ai/insights/academic/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["exam"], "Term One")
        self.assertEqual(data["overall_pass_rate"], 50.0)
        self.assertEqual(len(data["subjects"]), 1)
        self.assertEqual(data["subjects"][0]["pass_rate"], 50.0)
        self.assertEqual(data["subjects"][0]["average_percent"], 55.0)


class AiFinanceInsightsTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Fin", "fni")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-FN1")
        self.accountant = make_member_user(self.school, "fni-acct", Role.ACCOUNTANT)
        membership = self.accountant.memberships.get(institution=self.school)
        make_staff_profile(self.accountant, membership, self.school, self.structure["campus"])
        make_invoice(self.school, self.student, self.structure, "INV-FN-1", "1000.00", 5)
        make_invoice(
            self.school, self.student, self.structure, "INV-FN-2", "500.00", -10
        )

    def test_outstanding_and_overdue_totals(self):
        client = APIClient()
        self.assertTrue(client.login(username="fni-acct", password="TestPass123!"))
        response = client.get("/api/ai/insights/finance/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["invoice_count"], 2)
        self.assertEqual(data["total_outstanding"], "1500.00")
        self.assertEqual(data["overdue_count"], 1)
        self.assertEqual(data["overdue_amount"], "1000.00")


class AiAnomalyTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Anom", "ano")
        self.structure = make_structure(self.school)
        ensure_subject_offering(self.school, self.structure)
        self.student = make_student(self.school, self.structure, admission="ADM-AN1")
        self.admin = make_member_user(self.school, "ano-admin", Role.ADMIN)
        today = timezone.localdate()
        make_attendance(self.student, self.structure, today, "absent")
        exam = make_exam(self.school, self.structure, name="Final")
        exam_subject = ExamSubject.objects.create(
            exam=exam,
            subject=self.structure["subject"],
            maximum_marks=100,
            passing_marks=50,
        )
        StudentResult.objects.create(
            exam=exam,
            student=self.student,
            exam_subject=exam_subject,
            obtained_marks=Decimal("20.00"),
            is_absent=False,
            grade="F",
            is_pass=False,
        )
        make_invoice(self.school, self.student, self.structure, "INV-AN-1", "800.00", 40)

    def test_anomalies_reported_by_category(self):
        client = APIClient()
        self.assertTrue(client.login(username="ano-admin", password="TestPass123!"))
        response = client.get("/api/ai/anomalies/")
        self.assertEqual(response.status_code, 200)
        categories = {
            entry["category"] for entry in response.json()["anomalies"]
        }
        self.assertIn("attendance", categories)
        self.assertIn("academic", categories)
        self.assertIn("finance", categories)


class AiCommunicationDraftTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Draft", "drf")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-DR1")
        self.admin = make_member_user(self.school, "drf-admin", Role.ADMIN)

    def _client(self):
        client = APIClient()
        self.assertTrue(client.login(username="drf-admin", password="TestPass123!"))
        return client

    def test_fee_reminder_draft_uses_real_balance(self):
        make_invoice(self.school, self.student, self.structure, "INV-DR-1", "1200.00", 3)
        response = self._client().post(
            "/api/ai/communication/draft/",
            {"type": "fee_reminder", "student_ids": [self.student.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        draft = response.json()
        self.assertTrue(draft["draft_only"])
        self.assertIn("1200.00", draft["body"])
        self.assertIn("Student One", draft["body"])
        self.assertEqual(draft["recipient_count"], 1)

    def test_draft_rejects_student_outside_scope(self):
        other_school = make_school("Other", "oth")
        other_structure = make_structure(other_school)
        other_student = make_student(other_school, other_structure, admission="ADM-X1")
        response = self._client().post(
            "/api/ai/communication/draft/",
            {"type": "welcome", "student_ids": [other_student.pk, self.student.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class AiOverviewTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Overview", "ovw")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-OV1")
        self.admin = make_member_user(self.school, "ovw-admin", Role.ADMIN)

    def test_overview_role_and_capabilities(self):
        client = APIClient()
        self.assertTrue(client.login(username="ovw-admin", password="TestPass123!"))
        response = client.get("/api/ai/overview/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "manager")
        self.assertEqual(data["institution"], self.school.pk)
        self.assertEqual(data["students_in_scope"], 1)
        self.assertIn("finance_insights", data["capabilities"])