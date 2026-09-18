"""Tests for the ``cleanup_csp_violations`` management command."""

from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditLog, CSPViolation
from apps.schools.models import School

FROZEN_NOW = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.UTC)


def create_violation(delta=None, *, institution=None, ip_address=None, user_agent=""):
    """Create a CSPViolation, optionally back-dating its authoritative timestamp."""
    violation = CSPViolation.objects.create(
        document_uri="https://example.com/page",
        violated_directive="script-src",
        institution=institution,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if delta is not None:
        CSPViolation.objects.filter(pk=violation.pk).update(
            timestamp=FROZEN_NOW - delta
        )
    return CSPViolation.objects.get(pk=violation.pk)


def run_cleanup(*args):
    out = StringIO()
    call_command("cleanup_csp_violations", *args, stdout=out)
    return out.getvalue()


class CleanupCSPViolationsTests(TestCase):
    def _cleanup(self, *args):
        with patch("django.utils.timezone.now", return_value=FROZEN_NOW):
            return run_cleanup(*args)

    def test_deletes_records_older_than_default_90_days(self):
        old = create_violation(timedelta(days=91))
        recent = create_violation(timedelta(days=10))

        output = self._cleanup()

        self.assertFalse(CSPViolation.objects.filter(pk=old.pk).exists())
        self.assertTrue(CSPViolation.objects.filter(pk=recent.pk).exists())
        self.assertIn("CSP violation(s) older than 90 day(s)", output)

    def test_preserves_recent_records(self):
        recent = create_violation(timedelta(days=89))

        self._cleanup()

        self.assertTrue(CSPViolation.objects.filter(pk=recent.pk).exists())

    def test_boundary_record_at_exact_cutoff_is_preserved(self):
        at_cutoff = create_violation(timedelta(days=90))
        just_below_cutoff = create_violation(timedelta(days=90, seconds=1))

        self._cleanup()

        self.assertTrue(CSPViolation.objects.filter(pk=at_cutoff.pk).exists())
        self.assertFalse(
            CSPViolation.objects.filter(pk=just_below_cutoff.pk).exists()
        )

    def test_custom_retention_days(self):
        older = create_violation(timedelta(days=31))
        recent = create_violation(timedelta(days=29))

        self._cleanup("--days=30")

        self.assertFalse(CSPViolation.objects.filter(pk=older.pk).exists())
        self.assertTrue(CSPViolation.objects.filter(pk=recent.pk).exists())

    def test_days_must_be_positive(self):
        violation = create_violation(timedelta(days=1))

        with self.assertRaises(CommandError):
            self._cleanup("--days=0")
        with self.assertRaises(CommandError):
            self._cleanup("--days=-5")

        self.assertTrue(CSPViolation.objects.filter(pk=violation.pk).exists())

    def test_zero_matching_records_succeeds_and_leaves_unrelated_rows(self):
        recent = create_violation(timedelta(days=1))
        unrelated = AuditLog.objects.create(action="login")

        output = self._cleanup()

        self.assertIn("Deleted 0", output)
        self.assertTrue(CSPViolation.objects.filter(pk=recent.pk).exists())
        self.assertTrue(AuditLog.objects.filter(pk=unrelated.pk).exists())

    def test_cleans_expired_records_across_all_institutions(self):
        school_a = School.objects.create(name="Northfield Academy")
        school_b = School.objects.create(name="Southfield Academy")
        old_a = create_violation(timedelta(days=120), institution=school_a)
        old_b = create_violation(timedelta(days=200), institution=school_b)
        old_unattributed = create_violation(timedelta(days=150))
        recent_a = create_violation(timedelta(days=5), institution=school_a)
        recent_b = create_violation(timedelta(days=3), institution=school_b)

        self._cleanup()

        for record in (old_a, old_b, old_unattributed):
            self.assertFalse(CSPViolation.objects.filter(pk=record.pk).exists())
        self.assertTrue(CSPViolation.objects.filter(pk=recent_a.pk).exists())
        self.assertTrue(CSPViolation.objects.filter(pk=recent_b.pk).exists())

    def test_idempotent_second_run_reports_zero(self):
        old = create_violation(timedelta(days=95))
        recent = create_violation(timedelta(days=2))

        first = self._cleanup()
        second = self._cleanup()

        self.assertFalse(CSPViolation.objects.filter(pk=old.pk).exists())
        self.assertIn("Deleted 0", second)
        self.assertTrue(CSPViolation.objects.filter(pk=recent.pk).exists())

    def test_output_does_not_leak_report_details(self):
        recent = create_violation(
            timedelta(days=1),
            ip_address="203.0.113.77",
            user_agent="Mozilla/5.0 agent-example-1234",
        )

        output = self._cleanup()

        self.assertNotIn("203.0.113.77", output)
        self.assertNotIn("agent-example-1234", output)
        self.assertNotIn("Mozilla", output)