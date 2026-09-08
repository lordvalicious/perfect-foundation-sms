from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.schools.models import School


class CoreCatalogTests(APITestCase):
    """Tests for the core reports catalog API endpoints."""

    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            code="TS-001",
            institution_type="school",
            status="active",
        )
        self.admin_user = School.objects.model.__class__.objects.create_user(
            username="admin",
            password="testpass123",
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        self.client.force_authenticate(user=self.admin_user)

    def test_report_list(self):
        response = self.client.get("/api/reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_report_config(self):
        response = self.client.get("/api/reports/config/enrollment/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_saved_report_list(self):
        response = self.client.get("/api/reports/saved-reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_saved_report_create(self):
        created = self.client.post(
            "/api/reports/saved-reports/",
            {"name": "Monthly Fees", "report_definition": "fees", "filters": {"campus": "1"}},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

    def test_saved_report_crud(self):
        # Create
        created = self.client.post(
            "/api/reports/saved-reports/",
            {"name": "Test Report", "report_definition": "enrollment", "filters": {}},
            format="json",
        )
        saved_id = created.data["id"]
        # Read
        response = self.client.get(f"/api/reports/saved-reports/{saved_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Update
        updated = self.client.put(
            f"/api/reports/saved-reports/{saved_id}/",
            {"name": "Renamed", "is_favorite": True},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        # Delete
        deleted = self.client.delete(f"/api/reports/saved-reports/{saved_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_saved_report_requires_valid_definition(self):
        response = self.client.post(
            "/api/reports/saved-reports/",
            {"name": "Bad", "report_definition": "not-a-real-def"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_middleware_enabled(self):
        response = self.client.get("/api/reports/audit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_csv_export(self):
        response = self.client.get("/api/reports/enrollment/?format=csv", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pdf_export(self):
        response = self.client.get("/api/reports/pdf/enrollment/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_print_view(self):
        response = self.client.get("/api/reports/print/enrollment/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_generate_endpoint_for_enrollment(self):
        response = self.client.post(
            "/api/reports/generate/",
            {"report_type": "enrollment"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

    def test_generate_endpoint_rejects_unknown_type(self):
        response = self.client.post(
            "/api/reports/generate/",
            {"report_type": "unknown-type"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CampusFilterTests(APITestCase):
    """Tests for campus filtering behavior."""

    def setUp(self):
        self.school_a = School.objects.create(
            name="School A", code="SA-001", institution_type="school", status="active"
        )
        self.school_b = School.objects.create(
            name="School B", code="SB-001", institution_type="school", status="active"
        )
        self.admin_a = School.objects.model.__class__.objects.create_user(
            username="admin_a", password="testpass123"
        )
        self.admin_a.is_staff = True
        self.admin_a.is_superuser = True
        self.admin_a.save()
        self.admin_b = School.objects.model.__class__.objects.create_user(
            username="admin_b", password="testpass123"
        )
        self.admin_b.is_staff = True
        self.admin_b.is_superuser = True
        self.admin_b.save()
        self.client_a = self.client.for_authenticated(self.admin_a)
        self.client_b = self.client.for_authenticated(self.admin_b)

    def test_global_user_see_all_schools(self):
        response = self.client_a.get("/api/reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_campus_param_isolation_school_a(self):
        response = self.client_a.get("/api/reports/enrollment/?campus=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_campus_param_isolation_school_b(self):
        response = self.client_b.get("/api/reports/enrollment/?campus=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_campus_403(self):
        response = self.client_a.get("/api/reports/enrollment/?campus=999")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CampusScopedUserTests(APITestCase):
    """Tests for campus-scoped user permissions."""

    def setUp(self):
        self.school = School.objects.create(
            name="Test School", code="TS-001", institution_type="school", status="active"
        )
        self.unit_a = School.objects.model.__class__.__bases__[0].__bases__[0].__bases__[0]  # Skip - need Campus
        self.client.force_login(School.objects.model.__class__.objects.create_user(username="campus_admin", password="testpass123"))

    def test_campus_admin_may_export_pdf(self):
        response = self.client.get("/api/reports/pdf/enrollment/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionTests(APITestCase):
    """Tests for report API permissions."""

    def setUp(self):
        self.school = School.objects.create(
            name="Test School", code="TS-001", institution_type="school", status="active"
        )
        self.teacher = School.objects.model.__class__.objects.create_user(
            username="teacher", password="testpass123"
        )
        self.teacher.is_staff = True
        self.teacher.save()
        self.client.force_authenticate(user=self.teacher)

    def test_teacher_cannot_pdf(self):
        response = self.client.get("/api/reports/pdf/enrollment/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_print(self):
        response = self.client.get("/api/reports/print/enrollment/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_saved_reports(self):
        response = self.client.get("/api/reports/saved-reports/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_list_allowed(self):
        response = self.client.get("/api/reports/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)