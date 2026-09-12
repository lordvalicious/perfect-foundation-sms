"""P5 AI audit-log tests.

Every AI interaction must write an audit entry tied to the active school.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.audit.models import AuditLog

from .helpers import (
    make_member_user,
    make_school,
    make_structure,
    make_student,
)


class AiAuditTests(TestCase):
    def setUp(self):
        self.school = make_school("AI Audit", "aud")
        self.structure = make_structure(self.school)
        self.student = make_student(self.school, self.structure, admission="ADM-AU1")
        self.admin = make_member_user(self.school, "aud-admin", Role.ADMIN)
        self.client = APIClient()
        self.assertTrue(self.client.login(username="aud-admin", password="TestPass123!"))

    def assert_audited(self, action):
        return AuditLog.objects.filter(
            action=action,
            institution=self.school,
            user=self.admin,
            model_name="ai",
        ).exists()

    def test_ask_is_audited(self):
        self.client.post("/api/ai/ask/", {"query": "how many students"}, format="json")
        self.assertTrue(self.assert_audited("ai_ask"))

    def test_search_is_audited(self):
        self.client.get("/api/ai/search/", {"q": "Student"})
        self.assertTrue(self.assert_audited("ai_search"))

    def test_insights_are_audited(self):
        self.client.get("/api/ai/insights/students/")
        self.assertTrue(self.assert_audited("ai_insight"))

    def test_anomaly_scan_is_audited(self):
        self.client.get("/api/ai/anomalies/")
        self.assertTrue(self.assert_audited("ai_anomaly"))

    def test_draft_is_audited(self):
        self.client.post(
            "/api/ai/communication/draft/",
            {"type": "welcome"},
            format="json",
        )
        self.assertTrue(self.assert_audited("ai_draft"))