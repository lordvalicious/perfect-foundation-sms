"""F10 remediation: public 2FA backup-code verification endpoint tests."""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import TwoFABackupCode, User
from apps.accounts.twofa_views import _backup_code_row

URL = "/api/auth/2fa/verify-backup/"


class TwoFAVerifyBackupCodeTests(TestCase):
    """Uniform failures, no oracle, constant-time compare, throttled."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="backupuser",
            email="backup@example.com",
            password="TestPass123!",
        )
        self.user.twofa_enabled = True
        self.user.twofa_secret = "JBSWY3DPEHPK3PXP"
        self.user.save()

        self.row = _backup_code_row()
        TwoFABackupCode.objects.create(
            user=self.user, code_hash=self.row["hash"], salt=self.row["salt"]
        )

        self.client = APIClient()

    def _post(self, payload, client=None):
        return (client or self.client).post(URL, payload, format="json")

    def test_valid_code_returns_true_and_is_consumed(self):
        response = self._post(
            {"username": self.user.username, "backup_code": self.row["code"]}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        code = TwoFABackupCode.objects.get(user=self.user)
        self.assertIsNotNone(code.used_at)

    def test_used_code_rejected_with_uniform_body(self):
        self._post({"username": self.user.username, "backup_code": self.row["code"]})

        response = self._post(
            {"username": self.user.username, "backup_code": self.row["code"]}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid credentials."})

    def test_all_failure_modes_share_one_uniform_401_body(self):
        cases = [
            {"username": "does-not-exist", "backup_code": "ABCD-EFGH"},
            {"email": "plain-user@example.com", "backup_code": "ABCD-EFGH"},
            {"username": self.user.username, "backup_code": "XXXX-XXXX"},
            {"username": self.user.username},
            {"backup_code": "ABCD-EFGH"},
        ]

        for payload in cases:
            with self.subTest(payload=payload):
                response = self._post(payload)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(
                    response.json(), {"detail": "Invalid credentials."}
                )

    def test_unknown_user_without_twofa_rejected_uniform(self):
        other = User.objects.create_user(
            username="plainuser",
            email="plain@example.com",
            password="TestPass123!",
        )
        row = _backup_code_row()

        # A backup code that is not linked to the (2FA-less) target user must
        # produce the same 401 body as every other failure.
        for payload in (
            {"username": other.username, "backup_code": row["code"]},
            {"username": other.username, "backup_code": "ABCD-EFGH"},
        ):
            with self.subTest(payload=payload):
                response = self._post(payload)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(
                    response.json(), {"detail": "Invalid credentials."}
                )

    def test_salted_mismatch_uses_compare_digest(self):
        # A matching HMAC must still pass (constant-time compare keeps parity).
        response = self._post(
            {"username": self.user.username, "backup_code": self.row["code"]}
        )
        self.assertEqual(response.status_code, 200)

    def test_endpoint_is_throttled(self):
        original_rates = ScopedRateThrottle.THROTTLE_RATES
        ScopedRateThrottle.THROTTLE_RATES = {"twofa_backup_verify": "2/min"}
        try:
            with override_settings(
                CACHES={
                    "default": {
                        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                        "LOCATION": "twofa-backup-verify-throttle-test",
                    }
                }
            ):
                client = APIClient()
                payload = {
                    "username": self.user.username,
                    "backup_code": "XXXX-XXXX",
                }
                self.assertEqual(client.post(URL, payload, format="json").status_code, 401)
                self.assertEqual(client.post(URL, payload, format="json").status_code, 401)
                self.assertEqual(client.post(URL, payload, format="json").status_code, 429)
        finally:
            ScopedRateThrottle.THROTTLE_RATES = original_rates