"""Phase 8 F3 — Exam list/detail institution isolation.

Regression: ExamListView/ExamDetailView called apply_campus_scope with the
default institution_field ("institution_id"), but Exam has no institution FK
(the institution is reached through academic_year.school). The path-resolution
guard silently skipped institution scoping, so a global user in school A could
list and retrieve school B exams whenever no ?campus= filter was present.
"""

from apps.exams.models import Exam
from apps.tests.test_tenant_isolation import TenantIsolationTestBase


class ExamTenantIsolationTest(TenantIsolationTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.exam_a1 = Exam.objects.create(
            academic_year=cls.year_a,
            class_obj=cls.class_a1,
            campus=cls.campus_a1,
            name="Mid-Term A1",
            exam_type="midterm",
            start_date="2024-10-01",
            end_date="2024-10-05",
            status="scheduled",
        )
        cls.exam_b1 = Exam.objects.create(
            academic_year=cls.year_b,
            class_obj=cls.class_b1,
            campus=cls.campus_b1,
            name="Mid-Term B1",
            exam_type="midterm",
            start_date="2024-10-01",
            end_date="2024-10-05",
            status="scheduled",
        )

    def _exam_ids(self, response):
        return [item["id"] for item in response.json().get("results", [])]

    def test_admin_a_cannot_list_school_b_exams(self):
        """A glbobal admin in school A must not see school B exams."""
        self._login(self.admin_a)
        response = self.client.get("/api/exams/")
        self.assertEqual(response.status_code, 200)
        ids = self._exam_ids(response)
        self.assertIn(self.exam_a1.id, ids)
        self.assertNotIn(self.exam_b1.id, ids)

    def test_admin_a_cannot_retrieve_school_b_exam(self):
        """School B exam detail is not reachable by a school A admin."""
        self._login(self.admin_a)

        ok = self.client.get(f"/api/exams/{self.exam_a1.id}/")
        self.assertEqual(ok.status_code, 200)

        denied = self.client.get(f"/api/exams/{self.exam_b1.id}/")
        self.assertEqual(denied.status_code, 404)

    def test_admin_a_cannot_filter_to_school_b_campus(self):
        """A school A admin may not use a school B campus filter."""
        self._login(self.admin_a)
        response = self.client.get(f"/api/exams/?campus={self.campus_b1.id}")
        self.assertEqual(response.status_code, 403)

    def test_admin_a_can_filter_to_own_school_campus(self):
        """Legitimate same-institution campus filter still works."""
        self._login(self.admin_a)
        response = self.client.get(f"/api/exams/?campus={self.campus_a1.id}")
        self.assertEqual(response.status_code, 200)
        ids = self._exam_ids(response)
        self.assertIn(self.exam_a1.id, ids)
        self.assertNotIn(self.exam_b1.id, ids)

    def test_superuser_retains_global_visibility(self):
        """A platform super admin can still see every school's exams."""
        self._login(self.super_admin)
        response = self.client.get("/api/exams/")
        self.assertEqual(response.status_code, 200)
        ids = self._exam_ids(response)
        self.assertIn(self.exam_a1.id, ids)
        self.assertIn(self.exam_b1.id, ids)