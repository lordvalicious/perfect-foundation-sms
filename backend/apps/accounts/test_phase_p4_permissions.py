"""Tests for P4 permission-catalog seeding.

The granular permission catalog is now provided by a data migration so a
fresh install has a usable, consistent set of system permissions without
running the demo-data seeder (which previously was the only source).
"""

from django.test import TestCase

from apps.accounts.models import Permission


class PermissionCatalogSeedingTests(TestCase):
    """A fresh test database (built from migrations) must already contain
    the system permission catalog."""

    def test_default_catalog_exists_without_running_demo_seeder(self):
        perms = Permission.objects.filter(is_system=True)

        # The catalog is large (100+ entries per the model contract).
        self.assertGreaterEqual(perms.count(), 100)

        # Spot-check canonical system codenames across categories.
        expected = {
            "student.view",
            "student.create",
            "teacher.view",
            "finance.invoice.create",
            "attendance.view",
            "exam.result.view",
            "hr.employee.view",
        }
        present = set(perms.values_list("codename", flat=True))
        self.assertTrue(expected.issubset(present))

    def test_catalog_entries_are_well_formed(self):
        for perm in Permission.objects.filter(is_system=True):
            self.assertTrue(perm.codename, "system codenames must be non-empty")
            self.assertEqual(perm.codename.split(".")[-1], perm.action)
            self.assertIn(perm.category, dict(Permission.CATEGORY_CHOICES))

    def test_re_seeding_is_idempotent(self):
        # Calling the seeder again adds nothing (mirrors migration behavior).
        from apps.accounts.test_access import seed_default_permissions

        before = Permission.objects.count()
        seed_default_permissions()
        after = Permission.objects.count()

        self.assertEqual(before, after)