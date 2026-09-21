"""F14 remediation: secure, throttled migration endpoint.

The migration endpoint (core.views.run_migrations_view) is unauthenticated
but bearer-protected and mutates the schema, so it is double-hardened:

1. Endpoint-specific DRF scoped throttle (scope "run_migrations" is applied
   before ANY auth/schema work, so failed-auth attempts are throttled too
   and the bearer cannot be brute-forced -- brute-force origin stays uniform).
2. Constant-time bearer verification (hmac.compare_digest) against
   MIGRATION_SECRET, so the token cannot be recovered via timing.

These tests assert the 429 gating (mirroring the transfer-certificate
sibling: override ScopedRateThrottle.THROTTLE_RATES + a dedicated locmem
cache so the asserted rate is stable), plus the auth-failure uniformity:
missing/mismatched bearer and missing secret stay generic.
"""

from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.test import APIClient


MIGRATION_URL = "/api/admin/run-migrations/"


class RunMigrationsAuthorizationTests(TestCase):
    """Deny access unless DEBUG is off and a valid bearer is presented."""

    def _client_with_bearer(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    @override_settings(DEBUG=False)
    def test_missing_bearer_returns_401(self):
        # F14: pin a non-empty secret so the 503 "not configured" guard is
        # skipped and the missing-bearer path deterministically reaches the
        # constant-time 401 check (env-independent, mirrors siblings).
        with mock.patch("apps.core.views.MIGRATION_SECRET", "the-real-secret"):
            response = APIClient().post(MIGRATION_URL)

        self.assertEqual(response.status_code, 401)

    @override_settings(DEBUG=False)
    def test_mismatched_bearer_returns_401(self):
        with mock.patch("apps.core.views.MIGRATION_SECRET", "the-real-secret"):
            client = self._client_with_bearer("not-the-secret")
            response = client.post(MIGRATION_URL)

        self.assertEqual(response.status_code, 401)

    @override_settings(DEBUG=False)
    def test_missing_secret_returns_503(self):
        with mock.patch("apps.core.views.MIGRATION_SECRET", ""):
            client = self._client_with_bearer("anything")
            response = client.post(MIGRATION_URL)

        self.assertEqual(response.status_code, 503)

    @override_settings(DEBUG=True)
    def test_debug_mode_is_not_allowed(self):
        with mock.patch("apps.core.views.MIGRATION_SECRET", "the-real-secret"):
            client = self._client_with_bearer("the-real-secret")
            response = client.post(MIGRATION_URL)

        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_valid_bearer_runs_migrations(self):
        with mock.patch("apps.core.views.MIGRATION_SECRET", "the-real-secret"):
            client = self._client_with_bearer("the-real-secret")
            with mock.patch("apps.core.views.call_command") as cmd:
                response = client.post(MIGRATION_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        cmd.assert_called_once_with("migrate", "--noinput")


class RunMigrationsThrottleTests(TestCase):
    """The migration endpoint is scoped-rate-throttled before any work."""

    def test_migration_endpoint_is_throttled(self):
        original_rates = ScopedRateThrottle.THROTTLE_RATES
        ScopedRateThrottle.THROTTLE_RATES = {
            "run_migrations": "2/min",
        }
        try:
            with override_settings(
                DEBUG=False,
                CACHES={
                    "default": {
                        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                        "LOCATION": "run-migrations-throttle-test",
                    }
                },
            ), mock.patch("apps.core.views.MIGRATION_SECRET", "the-real-secret"):
                client = self._client_with_bearer("the-real-secret")
                with mock.patch("apps.core.views.call_command") as cmd:
                    self.assertEqual(client.post(MIGRATION_URL).status_code, 200)
                # Second within the min window is still allowed.
                with mock.patch("apps.core.views.call_command"):
                    self.assertEqual(client.post(MIGRATION_URL).status_code, 200)
                # Third is throttled: 429 is asserted via the scoped rate.
                self.assertEqual(client.post(MIGRATION_URL).status_code, 429)
        finally:
            ScopedRateThrottle.THROTTLE_RATES = original_rates

    def _client_with_bearer(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client
