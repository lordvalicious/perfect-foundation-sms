from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import (
    FailedLoginAttempt,
    InstitutionMembership,
    PasswordHistory,
    Role,
    RoleAssignment,
    TwoFABackupCode,
)
from apps.schools.models import Campus, School


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

    def login(self, username="teacher", password="TestPass123!", client_ip=None):
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        kwargs = {"format": "json"}
        if client_ip:
            kwargs["HTTP_X_FORWARDED_FOR"] = client_ip
        return self.client.post(
            "/api/auth/login/",
            {
                "username": username,
                "password": password,
            },
            **kwargs,
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


class InstitutionIsolationTests(AuthBaseTestCase):
    def setUp(self):
        super().setUp()
        self.other_school = School.objects.create(
            name="Other School",
            city="Other City",
        )
        Campus.objects.create(school=self.school, name="Main Campus")
        Campus.objects.create(
            school=self.other_school,
            name="Other Campus",
        )

        self.other_user = get_user_model().objects.create_user(
            username="other-user",
            email="other-user@test.edu",
            password="TestPass123!",
        )
        membership = InstitutionMembership.objects.create(
            user=self.other_user,
            institution=self.other_school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=Role.TEACHER,
        )

    def test_school_endpoints_only_return_active_institution_data(self):
        self.login()

        response = self.client.get("/api/schools/campuses/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["name"] for item in response.json()],
            ["Main Campus"],
        )

    def test_user_cannot_view_profile_from_another_institution(self):
        self.login()

        response = self.client.get(
            f"/api/auth/users/{self.other_user.pk}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_user_can_switch_only_to_an_active_membership(self):
        # Normal users belong to exactly one school; only the Super Admin may
        # hold (and switch between) memberships in multiple schools.
        super_admin = get_user_model().objects.create_superuser(
            username="sa-switch",
            email="sa-switch@test.edu",
            password="TestPass123!",
        )
        InstitutionMembership.objects.create(
            user=super_admin,
            institution=self.school,
            status="active",
        )
        InstitutionMembership.objects.create(
            user=super_admin,
            institution=self.other_school,
            status="active",
        )
        self.client.post("/api/auth/csrf/", {}, format="json")
        self.client.post(
            "/api/auth/login/",
            {"username": "sa-switch", "password": "TestPass123!"},
            format="json",
        )

        response = self.client.post(
            "/api/auth/active-institution/",
            {"institution_id": self.other_school.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["institution"]["id"], self.other_school.pk)

        campuses = self.client.get("/api/schools/campuses/")
        self.assertEqual(
            [item["name"] for item in campuses.json()],
            ["Other Campus"],
        )

    def test_user_cannot_switch_to_an_unassigned_institution(self):
        self.login()

        response = self.client.post(
            "/api/auth/active-institution/",
            {"institution_id": self.other_school.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

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


class AccountLockoutTests(AuthBaseTestCase):
    def _attempt_failed_logins(self, count):
        for i in range(count):
            # Distinct client IPs so the 15-second failed-login de-duplication
            # window (record_failed_login) does not collapse the attempts.
            response = self.login(
                password="wrong-password",
                client_ip=f"10.0.0.{i + 1}",
            )
            self.assertEqual(response.status_code, 400)

    def test_failed_login_increments_counter(self):
        self._attempt_failed_logins(3)

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 3)
        self.assertIsNone(self.user.locked_until)

    def test_account_locked_after_max_attempts(self):
        self._attempt_failed_logins(5)

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 5)
        self.assertIsNotNone(self.user.locked_until)

    def test_locked_account_cannot_login(self):
        self._attempt_failed_logins(5)

        # Now try with correct password
        response = self.login()
        self.assertEqual(response.status_code, 403)
        self.assertIn("locked", response.json()["detail"].lower())

    def test_successful_login_clears_failed_attempts(self):
        for i in range(3):
            self.login(password="wrong-password")

        response = self.login()
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.locked_until)

    def test_failed_login_recorded(self):
        self.login(password="wrong-password")

        attempts = FailedLoginAttempt.objects.filter(user=self.user)
        self.assertEqual(attempts.count(), 1)
        self.assertEqual(attempts.first().username_or_email, "teacher")

    def test_login_failed_view_records_attempt(self):
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        response = self.client.post(
            "/api/auth/login/failed/",
            {"username": "teacher"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

        attempts = FailedLoginAttempt.objects.filter(user=self.user)
        self.assertEqual(attempts.count(), 1)


class PasswordResetTests(AuthBaseTestCase):
    def test_password_reset_request_sends_email(self):
        from django.core import mail

        self.client.post(
            "/api/auth/password-reset/",
            {"email": "teacher@test.edu"},
            format="json",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password reset", mail.outbox[0].subject)

    def test_password_reset_request_no_user_enumeration(self):
        from django.core import mail

        # Request reset for non-existent email
        self.client.post(
            "/api/auth/password-reset/",
            {"email": "nonexistent@test.edu"},
            format="json",
        )

        # Should return same generic response
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_changes_password(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Verify new password works
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        response = self.client.post(
            "/api/auth/login/",
            {"username": "teacher", "password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_password_reset_stores_history(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        old_hash = self.user.password

        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Check password history
        history = PasswordHistory.objects.filter(user=self.user)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().password_hash, old_hash)

    def test_password_reset_invalidates_sessions(self):
        from django.contrib.sessions.models import Session

        self.login()
        # Login updates `last_login`; refresh so the reset token matches the
        # user state the confirm view will validate against.
        self.user.refresh_from_db()
        session_key = self.client.session.session_key

        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Session should be deleted
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())


class PasswordChangeTests(AuthBaseTestCase):
    def test_password_change_requires_current_password(self):
        self.login()

        response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": "WrongPass123!",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", response.json())

    def test_password_change_prevents_reuse(self):
        self.login()

        response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": "TestPass123!",
                "new_password": "TestPass123!",  # Same as current
                "confirm_password": "TestPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.json())

    def test_password_change_success(self):
        self.login()

        response = self.client.post(
            "/api/auth/password-change/",
            {
                "current_password": "TestPass123!",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Verify new password works
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        response = self.client.post(
            "/api/auth/login/",
            {"username": "teacher", "password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)


class SessionManagementTests(AuthBaseTestCase):
    def test_session_created_on_login(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)

        # Check session list endpoint
        response = self.client.get("/api/auth/sessions/")
        self.assertEqual(response.status_code, 200)
        sessions = response.json()
        self.assertEqual(len(sessions), 1)
        self.assertTrue(sessions[0]["is_current"])

    def test_revoke_other_sessions(self):
        self.login()
        session_key_1 = self.client.session.session_key

        # Simulate another session by creating one directly
        from apps.accounts.models import UserSession
        session_2 = UserSession.objects.create(
            user=self.user,
            session_key="test-session-key-2",
            ip_address="192.168.1.2",
            user_agent="Test Agent 2",
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )

        response = self.client.get("/api/auth/sessions/")
        self.assertEqual(len(response.json()), 2)

        response = self.client.post("/api/auth/sessions/revoke-all/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/auth/sessions/")
        self.assertEqual(len(response.json()), 1)
        self.assertTrue(response.json()[0]["is_current"])

    def test_revoke_specific_session(self):
        self.login()

        from apps.accounts.models import UserSession
        session_2 = UserSession.objects.create(
            user=self.user,
            session_key="test-session-key-3",
            ip_address="192.168.1.3",
            user_agent="Test Agent 3",
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )

        response = self.client.get("/api/auth/sessions/")
        self.assertEqual(len(response.json()), 2)

        response = self.client.delete(f"/api/auth/sessions/{session_2.id}/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/auth/sessions/")
        self.assertEqual(len(response.json()), 1)

    def test_cannot_revoke_current_session(self):
        self.login()

        response = self.client.get("/api/auth/sessions/")
        current_session_id = response.json()[0]["id"]

        response = self.client.delete(f"/api/auth/sessions/{current_session_id}/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("current session", response.json()["detail"].lower())


class TwoFABackupCodeTests(AuthBaseTestCase):
    def test_backup_codes_generated_on_activate(self):
        self.login()

        # Setup 2FA
        response = self.client.post("/api/auth/2fa/setup/")
        self.assertEqual(response.status_code, 200)

        # Activate with a code (we can't easily test TOTP, so we'll test backup code generation separately)
        user = get_user_model().objects.get(pk=self.user.pk)
        user.twofa_secret = "JBSWY3DPEHPK3PXP"  # Known secret for testing
        user.save()

        import pyotp
        totp = pyotp.TOTP(user.twofa_secret)
        code = totp.now()

        response = self.client.post(
            "/api/auth/2fa/activate/",
            {"code": code},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Check backup codes were generated
        backup_codes = TwoFABackupCode.objects.filter(user=user, used_at__isnull=True)
        self.assertEqual(backup_codes.count(), 10)

    def test_backup_codes_can_be_regenerated(self):
        self.login()

        user = get_user_model().objects.get(pk=self.user.pk)
        user.twofa_enabled = True
        user.twofa_secret = "JBSWY3DPEHPK3PXP"
        user.save()

        # Create some old backup codes
        for _ in range(5):
            TwoFABackupCode.objects.create(user=user, code_hash="oldhash")

        response = self.client.post("/api/auth/2fa/backup-codes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["backup_codes"]), 10)

        # Old codes should be invalidated
        old_unused = TwoFABackupCode.objects.filter(user=user, used_at__isnull=True, code_hash="oldhash")
        self.assertEqual(old_unused.count(), 0)


class LockoutStatusTests(AuthBaseTestCase):
    def test_lockout_status_endpoint(self):
        self.login()

        response = self.client.get("/api/auth/lockout/status/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["locked"])
        self.assertEqual(data["failed_attempts"], 0)

    def test_lockout_status_when_locked(self):
        # Establish a valid session first (the status endpoint is authenticated),
        # then lock the account with distinct-IP attempts to defeat de-dup.
        self.login()
        for i in range(5):
            self.login(password="wrong-password", client_ip=f"10.0.1.{i + 1}")

        response = self.client.get("/api/auth/lockout/status/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["locked"])
        self.assertIsNotNone(data["locked_until"])
        self.assertGreater(data["remaining_minutes"], 0)


class AdminUnlockTests(AuthBaseTestCase):
    def setUp(self):
        super().setUp()
        # Create admin user
        self.admin_user = get_user_model().objects.create_user(
            username="admin",
            email="admin@test.edu",
            password="Admin123!",
        )
        membership = InstitutionMembership.objects.create(
            user=self.admin_user,
            institution=self.school,
        )
        RoleAssignment.objects.create(
            membership=membership,
            role=Role.ADMIN,
        )

    def test_admin_can_unlock_account(self):
        # Lock the teacher account
        for i in range(5):
            self.login(password="wrong-password")

        # Login as admin
        self.client.post(
            "/api/auth/csrf/",
            {},
            format="json",
        )
        self.client.post(
            "/api/auth/login/",
            {"username": "admin", "password": "Admin123!"},
            format="json",
        )

        response = self.client.post(f"/api/auth/admin/unlock/{self.user.pk}/")
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.locked_until)

    def test_teacher_cannot_unlock_account(self):
        for i in range(5):
            self.login(password="wrong-password")

        # Login as teacher (already logged in)
        response = self.client.post(f"/api/auth/admin/unlock/{self.user.pk}/")
        self.assertEqual(response.status_code, 403)
