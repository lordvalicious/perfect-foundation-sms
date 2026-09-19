"""Phase 8 F2 — Google SSO must not bypass 2FA.

Regression: before the fix, GoogleLoginView called ``django_login`` for any
verified Google account even when the user had 2FA enabled, bypassing the
same inline TOTP gate the password LoginView applies.
"""

import pyotp
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.google_sso import GoogleLoginView

GOOGLE_LOGIN_URL = "/api/auth/google/login/"
TWOFA_STATUS_URL = "/api/auth/2fa/status/"
GOOGLE_CLIENT_ID = "test-client.apps.googleusercontent.com"
GOOGLE_SECRET = "JBSWY3DPEHPK3PXP"


def google_payload(email):
    return {
        "iss": "https://accounts.google.com",
        "aud": GOOGLE_CLIENT_ID,
        "sub": "123456789012345678901",
        "email": email,
        "email_verified": True,
    }


class GoogleSsoTwoFaTestBase(TestCase):
    def setUp(self):
        self.env_patcher = mock.patch.dict(
            os.environ,
            {"GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID},
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        self.client = APIClient()

    def _make_user(self, email="sso.user@test.edu", twofa=False):
        user = get_user_model().objects.create_user(
            username="ssouser",
            email=email,
            password="TestPass123!",
        )
        if twofa:
            user.twofa_enabled = True
            user.twofa_secret = GOOGLE_SECRET
            user.save(update_fields=["twofa_enabled", "twofa_secret"])
        return user

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


class GoogleSso2FaRequiredTest(GoogleSsoTwoFaTestBase):
    def test_sso_without_otp_is_rejected_and_session_stays_anonymous(self):
        user = self._make_user(twofa=True)

        response = self._sso_login(user.email)

        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertIn("otp_required", body)
        self.assertTrue(body["otp_required"])

        status = self.client.get(TWOFA_STATUS_URL)
        self.assertEqual(status.status_code, 403)

    def test_sso_with_wrong_otp_is_rejected_and_session_stays_anonymous(self):
        user = self._make_user(twofa=True)

        response = self._sso_login(user.email, otp="000000")

        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertIn("otp_required", body)
        self.assertTrue(body["otp_required"])

        status = self.client.get(TWOFA_STATUS_URL)
        self.assertEqual(status.status_code, 403)

    def test_sso_with_valid_otp_logs_in(self):
        user = self._make_user(twofa=True)
        otp = pyotp.TOTP(user.twofa_secret).now()

        response = self._sso_login(user.email, otp=otp)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], user.pk)

        status = self.client.get(TWOFA_STATUS_URL)
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["enabled"])

    def test_sso_without_2fa_logs_in_directly(self):
        user = self._make_user(twofa=False)

        response = self._sso_login(user.email)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], user.pk)

        status = self.client.get(TWOFA_STATUS_URL)
        self.assertEqual(status.status_code, 200)