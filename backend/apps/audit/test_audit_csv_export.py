"""Regression tests: audit log CSV export (F-2).

Verifies that ``GET /api/audit/?format=csv`` 200s with a valid ``text/csv``
response, mirrors the JSON listing's tenant/campus scope and authorization,
and keeps the JSON API intact.
"""

import csv
import io
import json

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role
from apps.accounts.test_access import make_user
from apps.audit.models import AuditLog
from apps.schools.models import Campus, School
from apps.teachers.models import Teacher


class AuditCsvExportTests(TestCase):
    """Real HTTP/DRF regression tests for the audit log CSV endpoint."""

    def setUp(self):
        self.school_a = School.objects.create(name="Northfield Academy")
        self.school_b = School.objects.create(name="Southfield Academy")
        self.campus_a = Campus.objects.create(school=self.school_a, name="Campus A")
        self.campus_b = Campus.objects.create(school=self.school_b, name="Campus B")

        self.admin_a = make_user("admin-a", Role.ADMIN, self.school_a)
        self.admin_b = make_user("admin-b", Role.ADMIN, self.school_b)
        self.teacher = make_user("teacher", Role.TEACHER, self.school_a)

        self.client = APIClient()
        self.PASSWORD = "TestPass123!"

    def _as(self, user):
        self.client.force_authenticate(user=None)
        self.assertTrue(
            self.client.login(username=user.username, password=self.PASSWORD)
        )
        self.client.force_authenticate(user=user)
        return self.client

    def _log(self, school, *, user=None, action="create", **kwargs):
        return AuditLog.objects.create(
            institution=school,
            user=user,
            action=action,
            **kwargs,
        )

    def _body(self, response):
        return response.content.decode("utf-8-sig")

    def _rows(self, response):
        body = self._body(response)
        return list(csv.reader(io.StringIO(body)))

    # ------------------------------------------------------------------
    # A. 200 for authorized admin
    # ------------------------------------------------------------------

    def test_a_csv_export_returns_200(self):
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # B. Content type
    # ------------------------------------------------------------------

    def test_b_csv_content_type_is_text_csv(self):
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith("text/csv"),
            response["Content-Type"],
        )

    # ------------------------------------------------------------------
    # C. Header row
    # ------------------------------------------------------------------

    def test_c_csv_header_columns(self):
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)
        rows = self._rows(response)
        self.assertEqual(
            rows[0],
            [
                "Timestamp", "User", "Action", "Model",
                "Object", "Object ID", "IP Address", "Details",
            ],
        )

    # ------------------------------------------------------------------
    # D. Known record appears
    # ------------------------------------------------------------------

    def test_d_csv_contains_known_record(self):
        self._log(
            self.school_a,
            user=self.admin_a,
            model_name="Student",
            object_id="S-100",
            object_repr="CSV Known Student",
            details={"field": "value"},
            ip_address="10.1.2.3",
        )
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)
        body = self._body(response)
        self.assertIn("CSV Known Student", body)
        self.assertIn("S-100", body)

    # ------------------------------------------------------------------
    # E. Filters preserved (action + user)
    # ------------------------------------------------------------------

    def test_e_csv_respects_action_filter(self):
        self._log(
            self.school_a,
            user=self.admin_a,
            action="create",
            model_name="Student",
            object_repr="Created Thing",
        )
        self._log(
            self.school_a,
            user=self.admin_a,
            action="delete",
            model_name="Student",
            object_repr="Deleted Thing",
        )
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv&action=create")
        self.assertEqual(response.status_code, 200)
        body = self._body(response)
        self.assertIn("Created Thing", body)
        self.assertNotIn("Deleted Thing", body)

    def test_e_csv_respects_user_filter(self):
        self._log(
            self.school_a,
            user=self.admin_a,
            model_name="Student",
            object_repr="Admin Log",
        )
        self._log(
            self.school_a,
            user=None,
            model_name="Student",
            object_repr="Anonymous Log",
        )
        self._as(self.admin_a)
        response = self.client.get(
            f"/api/audit/?format=csv&user={self.admin_a.pk}"
        )
        self.assertEqual(response.status_code, 200)
        body = self._body(response)
        self.assertIn("Admin Log", body)
        self.assertNotIn("Anonymous Log", body)

    # ------------------------------------------------------------------
    # F/G. Tenant isolation
    # ------------------------------------------------------------------

    def test_f_school_a_csv_excludes_school_b(self):
        self._log(self.school_a, model_name="Student", object_repr="School A Log")
        self._log(self.school_b, model_name="Student", object_repr="School B Log")
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)
        body = self._body(response)
        self.assertIn("School A Log", body)
        self.assertNotIn("School B Log", body)

    def test_g_school_b_csv_excludes_school_a(self):
        self._log(self.school_a, model_name="Student", object_repr="School A Log")
        self._log(self.school_b, model_name="Student", object_repr="School B Log")
        self._as(self.admin_b)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)
        body = self._body(response)
        self.assertIn("School B Log", body)
        self.assertNotIn("School A Log", body)

    # ------------------------------------------------------------------
    # H. Unauthorized user cannot export
    # ------------------------------------------------------------------

    def test_h_unauthorized_teacher_cannot_export(self):
        self._log(self.school_a, model_name="Student", object_repr="Secret A Log")
        self._as(self.teacher)
        response = self.client.get("/api/audit/?format=csv")
        self.assertIn(response.status_code, [401, 403])

    # ------------------------------------------------------------------
    # I. JSON API still works
    # ------------------------------------------------------------------

    def test_i_json_audit_list_still_200(self):
        self._log(self.school_a, model_name="Student", object_repr="JSON Log")
        self._as(self.admin_a)
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)

    # ------------------------------------------------------------------
    # J. JSON pagination / filters unchanged
    # ------------------------------------------------------------------

    def test_j_json_pagination_and_filter_unchanged(self):
        for i in range(65):
            self._log(
                self.school_a,
                action="create" if i % 2 == 0 else "delete",
                model_name="Student",
                object_repr=f"Payload {i}",
            )
        self._as(self.admin_a)

        page1 = self.client.get("/api/audit/?page=1&page_size=50")
        self.assertEqual(page1.status_code, 200)
        data1 = page1.json()
        self.assertEqual(len(data1["results"]), 50)
        self.assertEqual(data1["count"], 65)

        page2 = self.client.get("/api/audit/?page=2&page_size=50")
        self.assertEqual(page2.status_code, 200)
        self.assertEqual(len(page2.json()["results"]), 15)

        filtered = self.client.get("/api/audit/?action=delete")
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["count"], 32)

        explicit_json = self.client.get("/api/audit/?format=json")
        self.assertEqual(explicit_json.status_code, 200)

    # ------------------------------------------------------------------
    # K. CSV escaping (commas / quotes / newlines in Details)
    # ------------------------------------------------------------------

    def test_k_csv_special_characters_stay_well_formed(self):
        details = {
            "note": "contains, a comma", "quote": 'say "hi"',
            "line": "line one\nline two",
        }
        self._log(
            self.school_a,
            model_name="Student",
            object_repr="Escaped Row",
            details=details,
        )
        self._as(self.admin_a)
        response = self.client.get("/api/audit/?format=csv")
        self.assertEqual(response.status_code, 200)
        rows = self._rows(response)
        self.assertEqual(len(rows), 2)  # header + one record
        row = rows[1]
        self.assertEqual(len(row), 8)
        self.assertEqual(json.loads(row[7]), details)

    # ------------------------------------------------------------------
    # L. No active institution -> fail closed (same as JSON listing)
    # ------------------------------------------------------------------

    def test_l_no_active_institution_fails_closed(self):
        self._log(self.school_a, model_name="Student", object_repr="School A Log")
        self._log(self.school_b, model_name="Student", object_repr="School B Log")

        # A user whose only membership is NOT active has no active
        # institution; the existing audit list denies them (fail closed).
        inactive = make_user("inactive-admin", Role.ADMIN, self.school_a)
        InstitutionMembership.objects.filter(user=inactive).update(
            status="inactive"
        )

        self._as(inactive)
        json_response = self.client.get("/api/audit/")
        csv_response = self.client.get("/api/audit/?format=csv")

        # CSV must behave exactly like the existing JSON listing: denied.
        self.assertIn(json_response.status_code, [401, 403])
        self.assertEqual(csv_response.status_code, json_response.status_code)
        self.assertNotIn(
            "School B Log".encode("utf-8"), csv_response.content
        )