"""P5 AI authorization tests.

Covers role gating, the active-institution requirement, and the explicit
deny overlay (UserPermission effect="deny") on AI capabilities.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Permission, Role, UserPermission

from .helpers import (
    make_member_user,
    make_school,
    make_structure,
    make_student,
    make_superuser,
)


class AiRoleGateTests(TestCase):
    """Each AI insight family is gated by the platform role classes."""

    def setUp(self):
        self.school = make_school("AI Auth", "aia")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-A1")

        self.admin = make_member_user(self.school, "aia-admin", Role.ADMIN)
        self.teacher = make_member_user(self.school, "aia-teacher", Role.TEACHER)
        self.accountant = make_member_user(self.school, "aia-acct", Role.ACCOUNTANT)
        self.parent = make_member_user(self.school, "aia-parent", Role.PARENT)
        self.student_user = make_member_user(self.school, "aia-student", Role.STUDENT)

    def _client(self, username):
        client = APIClient()
        self.assertTrue(client.login(username=username, password="TestPass123!"))
        return client

    def test_finance_insights_blocked_for_teacher(self):
        self.assertEqual(
            self._client("aia-teacher").get("/api/ai/insights/finance/").status_code,
            403,
        )

    def test_finance_insights_allowed_for_accountant(self):
        self.assertEqual(
            self._client("aia-acct").get("/api/ai/insights/finance/").status_code,
            200,
        )

    def test_student_insights_blocked_for_parent_and_student(self):
        for username in ("aia-parent", "aia-student"):
            self.assertEqual(
                self._client(username).get("/api/ai/insights/students/").status_code,
                403,
                username,
            )

    def test_student_insights_allowed_for_teacher_and_admin(self):
        for username in ("aia-teacher", "aia-admin"):
            response = self._client(username).get("/api/ai/insights/students/")
            self.assertEqual(response.status_code, 200, username)
            self.assertIn("insights", response.json())

    def test_draft_blocked_for_teacher(self):
        client = self._client("aia-teacher")
        response = client.post(
            "/api/ai/communication/draft/", {"type": "welcome"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_draft_allowed_for_admin(self):
        client = self._client("aia-admin")
        response = client.post(
            "/api/ai/communication/draft/", {"type": "welcome"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["draft_only"])

    def test_ask_allowed_for_all_roles(self):
        for username in ("aia-parent", "aia-student"):
            client = self._client(username)
            response = client.post(
                "/api/ai/ask/", {"query": "hello"}, format="json"
            )
            self.assertEqual(response.status_code, 200, username)


class AiInstitutionRequiredTests(TestCase):
    """AI endpoints refuse to serve without an active institution."""

    def test_ask_requires_institution(self):
        self.school = make_school("AI NoInst", "ain")
        self.superuser = make_superuser("ain-super")
        client = APIClient()
        self.assertTrue(client.login(username="ain-super", password="TestPass123!"))
        response = client.post("/api/ai/ask/", {"query": "hi"}, format="json")
        self.assertEqual(response.status_code, 403)


class AiDenyOverlayTests(TestCase):
    """Explicit UserPermission denies override role-based AI access."""

    def setUp(self):
        self.school = make_school("AI Deny", "aid")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-D1")
        self.admin = make_member_user(self.school, "aid-admin", Role.ADMIN)
        self.permission = Permission.objects.get(codename="insight.student.view")

    def _client(self):
        client = APIClient()
        self.assertTrue(client.login(username="aid-admin", password="TestPass123!"))
        return client

    def test_deny_blocks_admin(self):
        UserPermission.objects.create(
            user=self.admin,
            permission=self.permission,
            institution=self.school,
            effect="deny",
            reason="test deny",
        )
        self.assertEqual(
            self._client().get("/api/ai/insights/students/").status_code,
            403,
        )

    def test_without_deny_admin_can_access(self):
        self.assertEqual(
            self._client().get("/api/ai/insights/students/").status_code,
            200,
        )

    def test_expired_deny_is_ignored(self):
        UserPermission.objects.create(
            user=self.admin,
            permission=self.permission,
            institution=self.school,
            effect="deny",
            reason="expired",
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertEqual(
            self._client().get("/api/ai/insights/students/").status_code,
            200,
        )

    def test_superuser_bypasses_deny(self):
        superuser = make_superuser("aid-super")
        # Add membership so middleware can find the institution
        from apps.accounts.models import InstitutionMembership
        InstitutionMembership.objects.create(user=superuser, institution=self.school)
        UserPermission.objects.create(
            user=superuser,
            permission=self.permission,
            institution=self.school,
            effect="deny",
            reason="test deny",
        )
        client = APIClient()
        self.assertTrue(client.login(username="aid-super", password="TestPass123!"))
        self.assertEqual(
            client.get("/api/ai/insights/students/").status_code,
            200,
        )