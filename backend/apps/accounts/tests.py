from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    InstitutionMembership,
    Role,
    RoleAssignment,
)
from apps.schools.models import School


class AuthBaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(
            name="Test School",
            city="Test City",
        )

        self.user = get_user_model().objects.create_user(
            username="teacher",
            email="teacher@test.edu",
            password="TestPass123!",
        )

        membership = InstitutionMembership.objects.create(
            user=self.user,
            institution=self.school,
        )

        RoleAssignment.objects.create(
            membership=membership,
            role=Role.TEACHER,
        )

    def login(self, username="teacher", password="TestPass123!"):
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        return self.client.post(
            "/api/auth/login/",
            {
                "username": username,
                "password": password,
            },
            format="json",
        )


class LoginTests(AuthBaseTestCase):
    def test_login_success(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["username"],
            "teacher",
        )
        self.assertEqual(
            response.json()["primary_role"],
            Role.TEACHER,
        )

    def test_login_failure_rejected(self):
        response = self.login(password="wrong-password")

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_login_with_email(self):
        response = self.login("teacher@test.edu")

        self.assertEqual(response.status_code, 200)


class CurrentUserTests(AuthBaseTestCase):
    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 403)

    def test_me_returns_memberships_and_roles(self):
        self.login()

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["primary_role"], Role.TEACHER)
        self.assertEqual(data["primary_institution"], "Test School")
        self.assertEqual(len(data["memberships"]), 1)

        membership = data["memberships"][0]

        self.assertEqual(
            membership["institution_name"],
            "Test School",
        )
        self.assertEqual(
            membership["roles"][0]["role"],
            Role.TEACHER,
        )

    def test_logout(self):
        self.login()

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, 200)

        me = self.client.get("/api/auth/me/")

        self.assertEqual(me.status_code, 403)


class PermissionTests(AuthBaseTestCase):
    def test_unauthenticated_access_blocked(self):
        response = self.client.get("/api/students/")

        self.assertEqual(response.status_code, 403)

    def test_teacher_can_read_students(self):
        self.login()

        response = self.client.get("/api/students/")

        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_create_students(self):
        self.login()

        response = self.client.post(
            "/api/students/",
            {
                "admission_number": "PF-999",
                "first_name": "New",
                "last_name": "Student",
                "gender": "male",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_access_finance(self):
        self.login()

        response = self.client.get("/api/finance/invoices/")

        self.assertEqual(response.status_code, 403)

    def test_accountant_can_access_finance(self):
        accountant = get_user_model().objects.create_user(
            username="accountant",
            email="accountant@test.edu",
            password="TestPass123!",
        )

        membership = InstitutionMembership.objects.create(
            user=accountant,
            institution=self.school,
        )

        RoleAssignment.objects.create(
            membership=membership,
            role=Role.ACCOUNTANT,
        )

        self.client.post(
            "/api/auth/login/",
            {
                "username": "accountant",
                "password": "TestPass123!",
            },
            format="json",
        )

        response = self.client.get("/api/finance/invoices/")

        self.assertEqual(response.status_code, 200)


class AuditTests(AuthBaseTestCase):
    def test_failed_login_is_audited(self):
        from apps.audit.models import AuditLog

        self.login(password="bad-password")

        failed_logs = AuditLog.objects.filter(
            action="login_failed"
        )

        self.assertEqual(failed_logs.count(), 1)
        self.assertEqual(
            failed_logs.first().details["username"],
            "teacher",
        )
