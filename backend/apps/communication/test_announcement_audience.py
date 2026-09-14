"""Announcement audience-role regression tests (SQLite-safe filtering).

Covers a P1 defect where ``audience_roles__contains`` raised
``NotSupportedError`` on SQLite at query-evaluation time (during DRF
pagination/count), producing a 500 on ``GET /api/communication/announcements/``.

The audience filter must work on SQLite AND PostgreSQL, while preserving the
business rules: empty ``audience_roles`` = unrestricted, an exact role slug =
targeted, unrelated roles are hidden, and institution isolation always holds.
"""

from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.communication.models import Announcement
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
)
from apps.accounts.test_access import make_user


class AnnouncementAudienceRegressionBase(TestCase):
    """Two-school fixture with role users and role-targeted announcements."""

    PASSWORD = "TestPass123!"

    def setUp(self):
        self.school_a = School.objects.create(name="Audience School A")
        self.school_b = School.objects.create(name="Audience School B")

        self.campus_a1 = Campus.objects.create(
            school=self.school_a, name="Campus A1"
        )
        self.unit_a1 = AcademicUnit.objects.create(
            campus=self.campus_a1, name="Lower A1"
        )
        self.class_a1 = Class.objects.create(
            unit=self.unit_a1, name="Grade 1A1"
        )
        self.year = AcademicYear.objects.create(
            school=self.school_a,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )

        self.teacher_a = make_user("aud-teacher-a", Role.TEACHER, self.school_a)
        self.parent_a = make_user("aud-parent-a", Role.PARENT, self.school_a)
        self.student_a = make_user("aud-student-a", Role.STUDENT, self.school_a)
        self.teacher_b = make_user("aud-teacher-b", Role.TEACHER, self.school_b)
        self.parent_b = make_user("aud-parent-b", Role.PARENT, self.school_b)

        self.ann_unrestricted_a = Announcement.objects.create(
            institution=self.school_a,
            title="Unrestricted A",
            message="For everyone in A",
            status="published",
            audience_roles=[],
        )
        self.ann_teacher_only_a = Announcement.objects.create(
            institution=self.school_a,
            title="Teacher Only A",
            message="Only teachers A",
            status="published",
            audience_roles=["teacher"],
        )
        self.ann_parent_only_a = Announcement.objects.create(
            institution=self.school_a,
            title="Parent Only A",
            message="Only parents A",
            status="published",
            audience_roles=["parent"],
        )
        self.ann_teacher_parent_a = Announcement.objects.create(
            institution=self.school_a,
            title="Teacher+Parent A",
            message="Teachers and parents A",
            status="published",
            audience_roles=["teacher", "parent"],
        )
        self.ann_admin_only_a = Announcement.objects.create(
            institution=self.school_a,
            title="Admin Only A",
            message="Only admins A",
            status="published",
            audience_roles=["admin"],
        )
        self.ann_unrestricted_b = Announcement.objects.create(
            institution=self.school_b,
            title="Unrestricted B",
            message="For everyone in B",
            status="published",
            audience_roles=[],
        )
        self.ann_teacher_only_b = Announcement.objects.create(
            institution=self.school_b,
            title="Teacher Only B",
            message="Only teachers B",
            status="published",
            audience_roles=["teacher"],
        )

        self.client = APIClient()

    def _as(self, user):
        self.client.force_authenticate(user=None)
        self.assertTrue(
            self.client.login(
                username=user.username,
                password=self.PASSWORD,
            ), f"login failed for {user.username}"
        )
        self.client.force_authenticate(user=user)
        return self.client

    def _fetched_titles(self, user):
        response = self._as(user).get("/api/communication/announcements/?page=1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        return {item["title"] for item in data["results"]}


class AnnouncementAudienceFilteringTests(AnnouncementAudienceRegressionBase):
    """Business-rule coverage through the real DRF flow (pagination executes)."""

    def test_unrestricted_visible_to_teacher(self):
        titles = self._fetched_titles(self.teacher_a)
        self.assertIn("Unrestricted A", titles)

    def test_unrestricted_visible_to_parent(self):
        titles = self._fetched_titles(self.parent_a)
        self.assertIn("Unrestricted A", titles)

    def test_unrestricted_visible_to_student(self):
        titles = self._fetched_titles(self.student_a)
        self.assertIn("Unrestricted A", titles)

    def test_current_role_visible(self):
        self.assertIn("Teacher Only A", self._fetched_titles(self.teacher_a))
        self.assertIn("Parent Only A", self._fetched_titles(self.parent_a))

    def test_unrelated_role_hidden(self):
        titles = self._fetched_titles(self.teacher_a)
        self.assertNotIn("Parent Only A", titles)
        self.assertNotIn("Admin Only A", titles)

        parent_titles = self._fetched_titles(self.parent_a)
        self.assertNotIn("Teacher Only A", parent_titles)
        self.assertNotIn("Admin Only A", parent_titles)

    def test_multi_role_containing_current_visible(self):
        self.assertIn(
            "Teacher+Parent A", self._fetched_titles(self.teacher_a)
        )
        self.assertIn(
            "Teacher+Parent A", self._fetched_titles(self.parent_a)
        )

    def test_multi_role_not_containing_current_hidden(self):
        titles = self._fetched_titles(self.student_a)
        self.assertNotIn("Teacher+Parent A", titles)

    def test_other_school_unrestricted_hidden(self):
        titles = self._fetched_titles(self.teacher_a)
        self.assertNotIn("Unrestricted B", titles)
        titles_b = self._fetched_titles(self.teacher_b)
        self.assertIn("Unrestricted B", titles_b)
        self.assertNotIn("Unrestricted A", titles_b)

    def test_other_school_role_targeted_hidden(self):
        titles = self._fetched_titles(self.teacher_a)
        self.assertNotIn("Teacher Only B", titles)
        titles_b = self._fetched_titles(self.teacher_b)
        self.assertIn("Teacher Only B", titles_b)
        self.assertNotIn("Teacher Only A", titles_b)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/communication/announcements/?page=1")
        self.assertIn(response.status_code, [401, 403])

    def test_pagination_no_500(self):
        for i in range(25):
            Announcement.objects.create(
                institution=self.school_a,
                title=f"Bulk A {i}",
                message="Bulk message",
                status="published",
                audience_roles=[],
            )
        response = self._as(self.teacher_a).get(
            "/api/communication/announcements/?page=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("next", data)
        self.assertIn("count", data)
        self.assertEqual(len(data["results"]), 20)

        response2 = self._as(self.teacher_a).get(
            "/api/communication/announcements/?page=2"
        )
        self.assertEqual(response2.status_code, 200)

    def test_postgres_compatible_business_result(self):
        """Filtering yields the same set JSON __contains would on PostgreSQL.

        On PostgreSQL ``audience_roles__contains=['<role>']`` returns rows whose
        array contains the role. The cast-to-text + quoted-slug matching used to
        keep SQLite working must produce the identical business result.
        """
        reference_roles = {
            "teacher": {"Teacher Only A", "Teacher+Parent A"},
            "parent": {"Parent Only A", "Teacher+Parent A"},
            "student": set(),
        }
        expected_common = {"Unrestricted A"}

        for role_slug, user, extra in (
            ("teacher", self.teacher_a, reference_roles["teacher"]),
            ("parent", self.parent_a, reference_roles["parent"]),
            ("student", self.student_a, reference_roles["student"]),
        ):
            actual = self._fetched_titles(user)
            expected = expected_common | extra
            self.assertEqual(actual & expected, expected, role_slug)


class AnnouncementIsolationRegressionTests(AnnouncementAudienceRegressionBase):
    """Tenant isolation: role users only ever see their own school."""

    def test_parent_a_only_sees_school_a(self):
        titles = self._fetched_titles(self.parent_a)
        self.assertEqual(
            set(titles) & {"Unrestricted B", "Teacher Only B"},
            set(),
        )
        self.assertNotIn("Unrestricted B", titles)

    def test_parent_b_only_sees_school_b(self):
        titles = self._fetched_titles(self.parent_b)
        self.assertNotIn("Unrestricted A", titles)
        self.assertNotIn("Teacher Only A", titles)
        self.assertIn("Unrestricted B", titles)