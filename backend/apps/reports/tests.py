"""Tests for the Reports module.

Covers the centrally-seeded catalog, config/list endpoints, saved reports
CRUD, audit logging, CSV/PDF/print exports, campus isolation and role-based
permission gating.
"""

from datetime import date
import json

from django.test import TestCase

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
    StaffProfile,
    User,
)
from apps.reports.models import ReportAuditLog
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
)
from apps.students.models import Enrollment, Guardian, Student


def make_school(name="Test School", code="ts"):
    school = School.objects.create(name=name, code=code, status="active")
    campus = Campus.objects.create(school=school, name="Main Campus", status="active")
    unit = AcademicUnit.objects.create(campus=campus, name="Primary", status="active")
    class_obj = Class.objects.create(unit=unit, name="Grade 1", status="active")
    section = Section.objects.create(class_obj=class_obj, name="A", status="active")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 7, 31),
        status="active",
    )
    return school, campus, unit, class_obj, section, year


class CoreCatalogTests(TestCase):
    def setUp(self):
        self.school, self.campus, *_ = make_school()
        self.user = User.objects.create_superuser(
            username="reports-admin",
            email="reports-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_list_endpoint_returns_seeded_core_reports(self):
        response = self.client.get("/api/reports/list/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIsInstance(payload, list)

        core = next(
            (cat for cat in payload if cat.get("slug") == "core-reports"),
            None,
        )
        self.assertIsNotNone(core, "core-reports category is missing")

        keys = {report["key"] for report in core["reports"]}
        for key in ("enrollment", "fees", "at-risk", "student-status", "chronic-absentee"):
            self.assertIn(key, keys)

        enrollment = next(r for r in core["reports"] if r["key"] == "enrollment")
        self.assertTrue(enrollment["supports_pdf"])
        self.assertTrue(enrollment["supports_print"])
        self.assertTrue(enrollment["supports_csv"])
        self.assertEqual(enrollment["endpoint_url"], "/api/reports/enrollment/")

    def test_config_endpoint_returns_definition(self):
        response = self.client.get("/api/reports/config/enrollment/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["key"], "enrollment")
        self.assertEqual(payload["endpoint_url"], "/api/reports/enrollment/")
        self.assertTrue(payload["supports_pdf"])
        self.assertTrue(payload["supports_print"])

    def test_config_unknown_key_returns_404(self):
        response = self.client.get("/api/reports/config/not-a-report/")
        self.assertEqual(response.status_code, 404)

    def test_saved_report_crud(self):
        created = self.client.post(
            "/api/reports/saved-reports/",
            data=json.dumps(
                {
                    "name": "Monthly Fees",
                    "report_definition": "fees",
                    "filters": {"campus": "1"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        saved_id = created.json()["id"]

        listing = self.client.get("/api/reports/saved-reports/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()[0]["name"], "Monthly Fees")

        detail = self.client.get(f"/api/reports/saved-reports/{saved_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["report_definition"]["key"], "fees")

        updated = self.client.put(
            f"/api/reports/saved-reports/{saved_id}/",
            data=json.dumps({"name": "Renamed", "is_favorite": True}),
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200)

        deleted = self.client.delete(f"/api/reports/saved-reports/{saved_id}/")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/reports/saved-reports/").json(), [])

    def test_saved_report_requires_valid_definition(self):
        response = self.client.post(
            "/api/reports/saved-reports/",
            data=json.dumps({"name": "Bad", "report_definition": "not-a-real-def"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_audit_endpoint_returns_logs_for_user(self):
        ReportAuditLog.objects.create(
            user=self.user,
            action="view",
            record_count=3,
        )
        response = self.client.get("/api/reports/audit/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertGreaterEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["action"], "view")
        self.assertEqual(payload["results"][0]["record_count"], 3)

    def test_middleware_audits_report_views(self):
        self.client.get("/api/reports/enrollment/")
        self.assertTrue(
            ReportAuditLog.objects
            .filter(user=self.user, action="view")
            .exists()
        )

    def test_csv_export_for_enrollment(self):
        response = self.client.get("/api/reports/enrollment/?format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Campus", response.content.decode("utf-8"))

    def test_at_risk_csv_export(self):
        response = self.client.get("/api/reports/at-risk/?format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Student", response.content.decode("utf-8"))

    def test_pdf_export_for_known_report(self):
        response = self.client.get("/api/reports/pdf/enrollment/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_pdf_export_unknown_key_returns_404(self):
        response = self.client.get("/api/reports/pdf/not-a-report/")
        self.assertEqual(response.status_code, 404)

    def test_print_view_for_known_report(self):
        response = self.client.get("/api/reports/print/enrollment/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        self.assertIn("Enrollment Report", response.content.decode("utf-8"))

    def test_generate_endpoint_for_enrollment(self):
        response = self.client.post(
            "/api/reports/generate/",
            data=json.dumps({"report_type": "enrollment"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_generate_endpoint_rejects_unknown_type(self):
        response = self.client.post(
            "/api/reports/generate/",
            data=json.dumps({"report_type": "unknown-type"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class CampusFilterTests(TestCase):
    """Global users can target a single campus; everyone else is locked."""

    def setUp(self):
        self.school = School.objects.create(
            name="ISO School", code="iso", status="active"
        )
        self.campus_a = Campus.objects.create(
            school=self.school, name="Campus A", status="active"
        )
        self.campus_b = Campus.objects.create(
            school=self.school, name="Campus B", status="active"
        )
        self.unit_a = AcademicUnit.objects.create(
            campus=self.campus_a, name="Unit A", status="active"
        )
        self.unit_b = AcademicUnit.objects.create(
            campus=self.campus_b, name="Unit B", status="active"
        )
        self.class_a = Class.objects.create(
            unit=self.unit_a, name="Grade A", status="active"
        )
        self.class_b = Class.objects.create(
            unit=self.unit_b, name="Grade B", status="active"
        )
        Section.objects.create(class_obj=self.class_a, name="A", status="active")
        Section.objects.create(class_obj=self.class_b, name="B", status="active")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
            status="active",
        )

        self._make_student("ADM-A-1", self.class_a, self.campus_a, "male")
        self._make_student("ADM-B-1", self.class_b, self.campus_b, "female")

        self.global_user = User.objects.create_superuser(
            username="iso-super",
            email="iso-super@example.com",
            password="test-password",
        )
        self.client.force_login(self.global_user)

    def _make_student(self, admission_number, class_obj, campus, gender):
        guardian = Guardian.objects.create(
            name=f"Parent {admission_number}",
            relationship="Father",
            phone=f"0300{admission_number.replace('-', '')}",
        )
        student = Student.objects.create(
            admission_number=admission_number,
            first_name=admission_number,
            gender=gender,
            guardian=guardian,
            status="active",
        )
        Enrollment.objects.create(
            student=student,
            academic_year=self.year,
            campus=campus,
            class_obj=class_obj,
            section=class_obj.sections.first(),
            status="active",
        )

    def test_global_user_filters_by_requested_campus(self):
        response = self.client.get(f"/api/reports/enrollment/?campus={self.campus_a.id}")
        self.assertEqual(response.status_code, 200)

        rows = response.json()["classes"]
        self.assertTrue(rows)
        self.assertTrue(all(row["campus"] == "Campus A" for row in rows))

    def test_global_user_sees_all_campuses_without_filter(self):
        response = self.client.get("/api/reports/enrollment/")
        self.assertEqual(response.status_code, 200)

        campuses = {row["campus"] for row in response.json()["classes"]}
        self.assertEqual(campuses, {"Campus A", "Campus B"})

    def test_global_user_invalid_campus_rejected(self):
        response = self.client.get("/api/reports/enrollment/?campus=999999")
        self.assertEqual(response.status_code, 403)


class CampusScopedUserTests(TestCase):
    """Non-global users are limited to their own campuses."""

    def setUp(self):
        self.school = School.objects.create(
            name="Scoped School", code="scoped", status="active"
        )
        self.campus_a = Campus.objects.create(
            school=self.school, name="Campus A", status="active"
        )
        self.campus_b = Campus.objects.create(
            school=self.school, name="Campus B", status="active"
        )
        self.unit_a = AcademicUnit.objects.create(
            campus=self.campus_a, name="Unit A", status="active"
        )
        self.unit_b = AcademicUnit.objects.create(
            campus=self.campus_b, name="Unit B", status="active"
        )
        self.class_a = Class.objects.create(
            unit=self.unit_a, name="Grade A", status="active"
        )
        self.class_b = Class.objects.create(
            unit=self.unit_b, name="Grade B", status="active"
        )
        Section.objects.create(class_obj=self.class_a, name="A", status="active")
        Section.objects.create(class_obj=self.class_b, name="B", status="active")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
            status="active",
        )

        self._make_student("SC-A-1", self.class_a, self.campus_a)
        self._make_student("SC-B-1", self.class_b, self.campus_b)

        self.user = User.objects.create_user(
            username="campus-a-admin",
            email="campus-a@example.com",
            password="test-password",
            first_name="Campus",
            last_name="Admin",
        )
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.school, status="active"
        )
        RoleAssignment.objects.create(
            membership=self.membership, role=Role.CAMPUS_ADMIN
        )
        StaffProfile.objects.create(
            user=self.user,
            membership=self.membership,
            institution=self.school,
            employee_number="EMP-A-1",
            first_name="Campus",
            last_name="Admin",
            gender="male",
            primary_campus=self.campus_a,
        )
        self.client.force_login(self.user)

    def _make_student(self, admission_number, class_obj, campus):
        guardian = Guardian.objects.create(
            name=f"Parent {admission_number}",
            relationship="Father",
            phone=f"0311{admission_number.replace('-', '')}",
        )
        student = Student.objects.create(
            admission_number=admission_number,
            first_name=admission_number,
            gender="male",
            guardian=guardian,
            status="active",
        )
        Enrollment.objects.create(
            student=student,
            academic_year=self.year,
            campus=campus,
            class_obj=class_obj,
            section=class_obj.sections.first(),
            status="active",
        )

    def test_campus_admin_only_sees_own_campus(self):
        response = self.client.get("/api/reports/enrollment/")
        self.assertEqual(response.status_code, 200)

        campuses = {row["campus"] for row in response.json()["classes"]}
        self.assertEqual(campuses, {"Campus A"})

    def test_campus_admin_cannot_request_other_campus(self):
        response = self.client.get(f"/api/reports/enrollment/?campus={self.campus_b.id}")
        self.assertEqual(response.status_code, 403)

    def test_campus_admin_may_export_pdf(self):
        response = self.client.get("/api/reports/pdf/enrollment/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))


class PermissionTests(TestCase):
    """Accountant-only endpoints must reject teachers."""

    def setUp(self):
        school, _campus, *_ = make_school()
        self.teacher = User.objects.create_user(
            username="teacher-1",
            email="teacher-1@example.com",
            password="test-password",
        )
        membership = InstitutionMembership.objects.create(
            user=self.teacher, institution=school, status="active"
        )
        RoleAssignment.objects.create(membership=membership, role=Role.TEACHER)
        self.client.force_login(self.teacher)

    def test_teacher_denied_accountant_only_endpoints(self):
        paths = (
            "/api/reports/pdf/enrollment/",
            "/api/reports/print/enrollment/",
            "/api/reports/audit/",
            "/api/reports/config/enrollment/",
            "/api/reports/saved-reports/",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_teacher_can_list_reports(self):
        response = self.client.get("/api/reports/list/")
        self.assertEqual(response.status_code, 200)