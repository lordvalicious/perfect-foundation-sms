"""Auth / MFA hardening tests (PART 2).

Covers the behaviours added during the auth hardening pass:
  - failed-login de-duplication window (record_failed_login)
  - account lockout once the threshold is crossed
  - password reuse rejection (_check_new_password)
  - HMAC-SHA256 + salt backup codes, including legacy SHA-256 fallback
"""

import hashlib

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework import serializers
from rest_framework.test import APIClient

from apps.accounts.models import (
    FailedLoginAttempt,
    PasswordHistory,
    TwoFABackupCode,
)
from apps.accounts.views import _check_new_password, record_failed_login
from apps.accounts.twofa_views import (
    _backup_code_row,
    _generate_backup_code,
    _hash_backup_code,
)

User = get_user_model()


# =============================================================================
# FAILED LOGIN RECORDING
# =============================================================================

class FailedLoginRecordingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            email="tester@test.edu",
            password="TestPass123!",
        )

    def _request(self, ip="10.0.0.1"):
        request = RequestFactory().get("/api/auth/login/")
        request.META["REMOTE_ADDR"] = ip
        return request

    def test_duplicate_attempt_within_15s_is_collapsed(self):
        req = self._request()
        record_failed_login(req, self.user, "tester")
        record_failed_login(req, self.user, "tester")

        self.assertEqual(
            FailedLoginAttempt.objects.filter(user=self.user).count(), 1
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_distinct_ip_records_separate_attempt(self):
        record_failed_login(self._request("10.0.0.1"), self.user, "tester")
        record_failed_login(self._request("10.0.0.2"), self.user, "tester")

        self.assertEqual(
            FailedLoginAttempt.objects.filter(user=self.user).count(), 2
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 2)

    def test_distinct_identifier_records_separate_attempt(self):
        req = self._request()
        record_failed_login(req, self.user, "tester")
        record_failed_login(req, self.user, "tester@test.edu")

        self.assertEqual(
            FailedLoginAttempt.objects.filter(user=self.user).count(), 2
        )

    def test_lockout_applied_at_threshold(self):
        self.user.failed_login_attempts = 4
        self.user.save()

        record_failed_login(self._request(), self.user, "tester")

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 5)
        self.assertIsNotNone(self.user.locked_until)
        self.assertGreater(self.user.locked_until, timezone.now())


# =============================================================================
# PASSWORD REUSE POLICY
# =============================================================================

class PasswordReusePolicyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="puser",
            email="puser@test.edu",
            password="OldStr0ng!Pass1",
        )
        # Simulate a completed password change: the previous hash is archived
        # in history and the account now uses a different password.
        PasswordHistory.objects.create(
            user=self.user, password_hash=self.user.password
        )
        self.user.set_password("NewCurrent#Pass123!")
        self.user.save()

    def test_reusing_a_recorded_old_password_is_rejected(self):
        with self.assertRaises(serializers.ValidationError):
            _check_new_password(self.user, "OldStr0ng!Pass1")

    def test_reusing_current_password_is_rejected(self):
        with self.assertRaises(serializers.ValidationError):
            _check_new_password(self.user, "NewCurrent#Pass123!")

    def test_fresh_password_passes_policy(self):
        # No stored/current match -> must NOT raise.
        _check_new_password(self.user, "Totally-New#Pass456!")

    def test_weak_password_rejected_by_validators(self):
        with self.assertRaises(serializers.ValidationError):
            _check_new_password(self.user, "abc")


# =============================================================================
# BACKUP CODES
# =============================================================================

class BackupCodeHardeningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mfa_user",
            email="mfa@test.edu",
            password="TestPass123!",
        )
        self.user.twofa_enabled = True
        self.user.twofa_secret = "JBSWY3DPEHPK3PXP"
        self.user.save()

        self.client = APIClient()

    def test_generated_code_shape_and_alphabet(self):
        for _ in range(25):
            code = _generate_backup_code()
            self.assertRegex(code, r"^[A-Z2-9]{4}-[A-Z2-9]{4}$")

    def test_row_hash_is_hmac_keyed_and_salted(self):
        row = _backup_code_row()
        self.assertTrue(row["salt"])
        self.assertEqual(
            row["hash"], _hash_backup_code(row["code"], row["salt"])
        )

    def test_hmac_hash_differs_from_bare_sha256(self):
        code = "ABCD-EFGH"
        self.assertNotEqual(
            _hash_backup_code(code, "somesalt"),
            hashlib.sha256(code.encode()).hexdigest(),
        )

    def test_verify_endpoint_accepts_salted_code(self):
        row = _backup_code_row()
        TwoFABackupCode.objects.create(
            user=self.user, code_hash=row["hash"], salt=row["salt"]
        )

        response = self.client.post(
            "/api/auth/2fa/verify-backup/",
            {
                "username": self.user.username,
                "backup_code": row["code"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])

        code = TwoFABackupCode.objects.get(user=self.user)
        self.assertIsNotNone(code.used_at)

    def test_verify_endpoint_accepts_legacy_bare_sha(self):
        legacy_code = "WXYZ-2345"
        TwoFABackupCode.objects.create(
            user=self.user,
            code_hash=hashlib.sha256(legacy_code.encode()).hexdigest(),
            salt="",
        )

        response = self.client.post(
            "/api/auth/2fa/verify-backup/",
            {
                "username": self.user.username,
                "backup_code": legacy_code,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])

    def test_salted_row_never_falls_back_to_bare_sha(self):
        # Stored SHA-256 hash but WITH a non-empty salt: the salted code would
        # only match if the HMAC path were bypassed, which it must never be.
        code = "WXYZ-2345"
        TwoFABackupCode.objects.create(
            user=self.user,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            salt="present",
        )

        response = self.client.post(
            "/api/auth/2fa/verify-backup/",
            {
                "username": self.user.username,
                "backup_code": code,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_verify_rejects_wrong_code(self):
        row = _backup_code_row()
        TwoFABackupCode.objects.create(
            user=self.user, code_hash=row["hash"], salt=row["salt"]
        )

        response = self.client.post(
            "/api/auth/2fa/verify-backup/",
            {
                "username": self.user.username,
                "backup_code": "XXXX-XXXX",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)