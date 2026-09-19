"""F6 remediation: lockout consistency — backend order + SSO enforcement + clear on success."""

import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.authentication import EmailOrUsernameBackend
from apps.accounts.models import FailedLoginAttempt, User
from apps.accounts.views import clear_failed_logins, record_failed_login

GOOGLE_LOGIN_URL = "/api/auth/google/login/"
GOOGLE_CLIENT_ID = "test-client.apps.googleusercontent.com"


def google_payload(email):
    return {
        "iss": "https://accounts.google.com",
        "aud": GOOGLE_CLIENT_ID,
        "sub": "123456789012345678901",
        "email": email,
        "email_verified": True,
    }


class LockoutBackendTests(TestCase):
    """EmailOrUsernameBackend must check lockout BEFORE password hashing."""

    def setUp(self):
        self.backend = EmailOrUsernameBackend()
        self.user = User.objects.create_user(
            username="lockuser",
            email="lock@example.com",
            password="TestPass123!",
        )

    def _mock_request(self, institution=None):
        request = mock.MagicMock()
        request.institution = institution
        return request

    def test_locked_account_skips_password_hashing(self):
        self.user.locked_until = timezone.now() + timezone.timedelta(minutes=5)
        self.user.save(update_fields=["locked_until"])

        request = self._mock_request()
        with mock.patch.object(self.user, "check_password") as mock_check:
            user = self.backend.authenticate(
                request, username=self.user.username, password="TestPass123!"
            )
            self.assertIsNone(user)
            mock_check.assert_not_called()

    def test_locked_account_rejects_even_with_correct_password_via_view(self):
        # The view-level pre-check already covers this, but ensure backend path too
        self.user.locked_until = timezone.now() + timezone.timedelta(minutes=5)
        self.user.save(update_fields=["locked_until"])

        request = self._mock_request()
        user = self.backend.authenticate(
            request, username=self.user.username, password="TestPass123!"
        )
        self.assertIsNone(user)

    def test_expired_lock_allows_password_check(self):
        self.user.locked_until = timezone.now() - timezone.timedelta(minutes=1)
        self.user.failed_login_attempts = 5
        self.user.save(update_fields=["locked_until", "failed_login_attempts"])

        request = self._mock_request()
        user = self.backend.authenticate(
            request, username=self.user.username, password="TestPass123!"
        )
        # If check_password were skipped, authenticate would return None.
        # Getting the user back proves the hash was computed and matched.
        self.assertEqual(user, self.user)

    def test_inactive_user_rejected_before_hash(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        request = self._mock_request()
        with mock.patch.object(self.user, "check_password") as mock_check:
            user = self.backend.authenticate(
                request, username=self.user.username, password="TestPass123!"
            )
            self.assertIsNone(user)
            mock_check.assert_not_called()


class GoogleSsoLockoutTests(TestCase):
    """Google SSO must respect lockout and clear failures on success."""

    def setUp(self):
        self.env_patcher = mock.patch.dict(
            os.environ,
            {"GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID, "GOOGLE_ALLOWED_DOMAINS": "test.edu"},
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        self.client = APIClient()

    def _mock_token(self, email):
        return mock.patch(
            "apps.accounts.google_sso.verify_id_token",
            return_value=google_payload(email),
        )

    def _sso_login(self, email, otp=None):
        data = {"credential": "fake-google-token"}
        if otp is not None:
            data["otp"] = otp
        with self._mock_token(email):
            return self.client.post(GOOGLE_LOGIN_URL, data, format="json")

    def _make_user(self, email="sso.user@test.edu", twofa=False, locked=False, failed=0):
        user = get_user_model().objects.create_user(
            username="ssolock" + email.split("@")[0],
            email=email,
            password="TestPass123!",
        )
        if twofa:
            user.twofa_enabled = True
            user.twofa_secret = "JBSWY3DPEHPK3PXP"
        if locked:
            user.locked_until = timezone.now() + timezone.timedelta(minutes=5)
        user.failed_login_attempts = failed
        user.save(update_fields=["twofa_enabled", "twofa_secret", "locked_until", "failed_login_attempts"])
        return user

    def test_google_login_rejects_locked_account_with_403(self):
        user = self._make_user(locked=True, failed=5)

        response = self._sso_login(user.email)

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertIn("locked_until", body)
        self.assertIn("Try again in", body["detail"])
        # No session should be created
        self.assertEqual(self.client.session.get("_auth_user_id"), None)

    def test_google_login_success_clears_failed_logins(self):
        user = self._make_user(twofa=False, failed=3)

        response = self._sso_login(user.email)

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.locked_until)

    def test_google_login_otp_failure_records_attempt(self):
        user = self._make_user(twofa=True, failed=2)

        response = self._sso_login(user.email, otp="000000")

        self.assertEqual(response.status_code, 401)
        user.refresh_from_db()
        # record_failed_login increments failed_login_attempts
        self.assertEqual(user.failed_login_attempts, 3)

    def test_google_login_otp_failure_on_locked_account_is_preempted(self):
        # Locked account gets 403 for lockout BEFORE OTP gate triggers
        user = self._make_user(twofa=True, locked=True, failed=5)

        response = self._sso_login(user.email, otp="000000")

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertIn("locked_until", body)
        user.refresh_from_db()
        self.assertEqual(user.failed_login_attempts, 5)  # unchanged

    def test_google_login_with_valid_otp_logs_in_and_clears(self):
        user = self._make_user(twofa=True, failed=4)
        import pyotp

        otp = pyotp.TOTP(user.twofa_secret).now()

        response = self._sso_login(user.email, otp=otp)

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.locked_until)