"""Tests for the SaaS / enterprise-infrastructure layer.

Covers:
  - Feature-flag resolution (global, per-institution override, default-off)
  - Feature-flag admin API (create, delete, permission gating)
  - Subscription defaulting, read/write, plan/status validation, audit trail
  - Usage buffering, flush, and analytics endpoint
  - Platform admin permission gating on overview/security/status views
  - Platform health endpoint DB probe
"""

import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role
from apps.accounts.test_access import make_user
from apps.audit.models import AuditLog
from apps.schools.models import Campus, School, SchoolSettings
from apps.saas.models import DailyUsageSnapshot, FeatureFlag, Plan, Subscription
from apps.saas.services import (
    DEFAULT_PLAN_CODE,
    _USAGE_REGISTRY_KEY,
    _usage_counter_key,
    coerce_bool,
    feature_enabled,
    flush_usage,
    get_default_plan,
    get_subscription,
    record_usage,
    set_feature_flag,
)

User = get_user_model()

PASSWORD = "TestPass123!"


def _make_superadmin(username, school):
    """Create a super_admin-role user (not Django superuser)."""
    return make_user(username, Role.SUPER_ADMIN, school)


def _make_django_superuser(username, school):
    """Create a Django superuser with membership for institution resolution.

    Django superusers bypass every permission check via ``is_superuser``, and
    the ``super_admin`` role is globally unique — so no RoleAssignment is
    created here.
    """
    user = User.objects.create_superuser(
        username=username,
        email=f"{username}@test.edu",
        password=PASSWORD,
    )
    InstitutionMembership.objects.create(
        user=user, institution=school, status="active",
    )
    return user


class _BaseTestCase(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School", code="TST")
        self.campus = Campus.objects.create(school=self.school, name="Campus A")
        self.admin = _make_superadmin("admin", self.school)
        self.client = APIClient()

    def _auth(self, user=None):
        """Authenticate like the real app: session login (so the middleware
        resolves ``request.institution``) plus DRF auth."""
        u = user or self.admin
        self.client.force_authenticate(user=None)
        if u is not None and u.has_usable_password():
            self.assertTrue(
                self.client.login(username=u.username, password=PASSWORD)
            )
        self.client.force_authenticate(user=u)
        return self.client


# ---------------------------------------------------------------------------
# Feature Flag – service logic
# ---------------------------------------------------------------------------

class FeatureFlagServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="S1", code="S1")

    def test_flag_off_by_default(self):
        self.assertFalse(feature_enabled("nonexistent.flag"))

    def test_global_flag_enabled(self):
        set_feature_flag("grading.v2", enabled=True)
        self.assertTrue(feature_enabled("grading.v2"))

    def test_global_flag_disabled(self):
        set_feature_flag("grading.v2", enabled=False)
        self.assertFalse(feature_enabled("grading.v2"))

    def test_institution_override_wins(self):
        set_feature_flag("grading.v2", enabled=False)
        set_feature_flag("grading.v2", enabled=True, institution=self.school)
        self.assertTrue(feature_enabled("grading.v2", self.school))

    def test_institution_override_off_when_global_on(self):
        set_feature_flag("grading.v2", enabled=True)
        set_feature_flag("grading.v2", enabled=False, institution=self.school)
        self.assertFalse(feature_enabled("grading.v2", self.school))

    def test_no_flag_for_other_institution(self):
        other = School.objects.create(name="S2", code="S2")
        set_feature_flag("grading.v2", enabled=True, institution=self.school)
        self.assertFalse(feature_enabled("grading.v2", other))

    def test_set_feature_flag_update(self):
        flag = set_feature_flag("x", enabled=False)
        self.assertFalse(flag.enabled)
        flag = set_feature_flag("x", enabled=True, label="Label", description="Desc")
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.label, "Label")
        self.assertEqual(flag.description, "Desc")

    def test_string_values_coerce_to_strict_bool(self):
        self.assertFalse(coerce_bool("false"))
        self.assertFalse(coerce_bool("0"))
        self.assertFalse(coerce_bool("off"))
        self.assertTrue(coerce_bool("true"))
        self.assertTrue(coerce_bool("1"))
        self.assertTrue(coerce_bool("on"))
        self.assertFalse(coerce_bool(False))
        self.assertTrue(coerce_bool(True))
        self.assertFalse(coerce_bool(None))

    def test_set_feature_flag_string_false_not_enabled(self):
        # bool("false") is True; the service must never do that.
        flag = set_feature_flag("strict.false", enabled="false")
        self.assertFalse(flag.enabled)
        self.assertFalse(feature_enabled("strict.false"))

    def test_cache_invalidated_on_update(self):
        cache.delete("saas:flag:global:grading.v2")
        set_feature_flag("grading.v2", enabled=True)
        self.assertTrue(feature_enabled("grading.v2"))
        # Update flag and ensure cache is refreshed
        set_feature_flag("grading.v2", enabled=False)
        cache.delete("saas:flag:global:grading.v2")  # simulate cache expiry
        self.assertFalse(feature_enabled("grading.v2"))


# ---------------------------------------------------------------------------
# Feature Flag – admin API
# ---------------------------------------------------------------------------

class FeatureFlagAdminAPITests(_BaseTestCase):
    def test_requires_platform_admin(self):
        school_user = make_user("regular", Role.ADMIN, self.school)
        self._auth(school_user)
        resp = self.client.get("/api/saas/flags/")
        self.assertEqual(resp.status_code, 403)

    def test_list_global_and_override(self):
        set_feature_flag("f1", enabled=True)
        set_feature_flag("f1", enabled=False, institution=self.school)
        self._auth()
        resp = self.client.get("/api/saas/flags/")
        self.assertEqual(resp.status_code, 200)
        names = [f["name"] for f in resp.data]
        self.assertIn("f1", names)

    def test_create_global_flag(self):
        self._auth()
        resp = self.client.post("/api/saas/flags/", {
            "name": "new.flag", "enabled": True, "label": "New",
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(feature_enabled("new.flag"))

    def test_create_flag_requires_name(self):
        self._auth()
        resp = self.client.post("/api/saas/flags/", {"enabled": True}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.data)

    def test_create_flag_unknown_institution(self):
        self._auth()
        resp = self.client.post("/api/saas/flags/", {
            "name": "bad.inst", "institution_id": 99999,
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_create_flag_string_false_stays_false(self):
        self._auth()
        resp = self.client.post("/api/saas/flags/", {
            "name": "safe.flag", "enabled": "false",
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data["enabled"])
        self.assertFalse(feature_enabled("safe.flag"))

    def test_delete_flag(self):
        flag = set_feature_flag("to_delete", enabled=True)
        self._auth()
        resp = self.client.delete(f"/api/saas/flags/{flag.pk}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(FeatureFlag.objects.filter(pk=flag.pk).exists())

    def test_delete_nonexistent_returns_404(self):
        self._auth()
        resp = self.client.delete("/api/saas/flags/99999/")
        self.assertEqual(resp.status_code, 404)


class CurrentFlagsAPITests(_BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create a regular user for flag viewing
        self.user = make_user("viewer", Role.TEACHER, self.school)
        SchoolSettings.objects.get_or_create(school=self.school)

    def test_requires_auth(self):
        resp = APIClient().get("/api/saas/flags/current/")
        self.assertIn(resp.status_code, [401, 403])

    def test_returns_enabled_flags_for_institution(self):
        set_feature_flag("f1", enabled=True)
        self._auth(self.user)
        resp = self.client.get("/api/saas/flags/current/")
        self.assertEqual(resp.status_code, 200)
        names = [f["name"] for f in resp.data["flags"]]
        self.assertIn("f1", names)

    def test_override_reported_as_overridden(self):
        set_feature_flag("f1", enabled=False)
        set_feature_flag("f1", enabled=True, institution=self.school)
        self._auth(self.user)
        resp = self.client.get("/api/saas/flags/current/")
        rows = [f for f in resp.data["flags"] if f["name"] == "f1"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["enabled"])
        self.assertTrue(rows[0]["overridden"])

    def test_disabled_global_not_in_current(self):
        set_feature_flag("f1", enabled=False)
        self._auth(self.user)
        resp = self.client.get("/api/saas/flags/current/")
        names = [f["name"] for f in resp.data["flags"]]
        self.assertNotIn("f1", names)


# ---------------------------------------------------------------------------
# Subscription – service logic
# ---------------------------------------------------------------------------

class SubscriptionServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Sub School", code="SUB")

    def test_default_plan_created(self):
        plan = get_default_plan()
        self.assertEqual(plan.code, DEFAULT_PLAN_CODE)
        self.assertTrue(plan.is_active)

    def test_get_subscription_creates_trial_free(self):
        sub, created = get_subscription(self.school)
        self.assertTrue(created)
        self.assertEqual(sub.status, "trial")
        self.assertEqual(sub.plan.code, DEFAULT_PLAN_CODE)
        self.assertTrue(sub.is_active_subscription)

    def test_get_subscription_returns_existing(self):
        sub1, _ = get_subscription(self.school)
        sub2, created = get_subscription(self.school)
        self.assertFalse(created)
        self.assertEqual(sub1.pk, sub2.pk)

    def test_is_active_subscription_lifecycle(self):
        sub, _ = get_subscription(self.school)
        self.assertTrue(sub.is_active_subscription)
        sub.status = "past_due"
        self.assertFalse(sub.is_active_subscription)
        sub.status = "canceled"
        self.assertFalse(sub.is_active_subscription)

    def test_subscription_str(self):
        sub, _ = get_subscription(self.school)
        s = str(sub)
        self.assertIn(self.school.name, s)
        self.assertIn(sub.plan.code, s)


# ---------------------------------------------------------------------------
# Subscription – admin API
# ---------------------------------------------------------------------------

class SubscriptionAPITests(_BaseTestCase):
    def test_requires_platform_admin(self):
        school_user = make_user("regular", Role.ADMIN, self.school)
        self._auth(school_user)
        resp = self.client.get(f"/api/saas/tenants/{self.school.pk}/subscription/")
        self.assertEqual(resp.status_code, 403)

    def test_get_creates_subscription(self):
        self._auth()
        resp = self.client.get(f"/api/saas/tenants/{self.school.pk}/subscription/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "trial")

    def test_post_updates_plan_and_status(self):
        Plan.objects.create(code="pro", name="Pro", sort_order=1)
        self._auth()
        resp = self.client.post(f"/api/saas/tenants/{self.school.pk}/subscription/", {
            "plan_code": "pro", "status": "active",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["plan_code"], "pro")
        self.assertEqual(resp.data["status"], "active")
        # Audit record created
        self.assertTrue(
            AuditLog.objects.filter(action="subscription_changed").exists()
        )

    def test_post_rejects_unknown_plan(self):
        self._auth()
        resp = self.client.post(f"/api/saas/tenants/{self.school.pk}/subscription/", {
            "plan_code": "nonexistent",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_rejects_invalid_status(self):
        self._auth()
        resp = self.client.post(f"/api/saas/tenants/{self.school.pk}/subscription/", {
            "status": "INVALID",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_rejects_non_numeric_seats(self):
        self._auth()
        resp = self.client.post(f"/api/saas/tenants/{self.school.pk}/subscription/", {
            "seats_used": "not-a-number",
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.data)

    def test_post_rejects_negative_seats(self):
        self._auth()
        resp = self.client.post(f"/api/saas/tenants/{self.school.pk}/subscription/", {
            "seats_used": -3,
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_accepts_valid_seats(self):
        Plan.objects.create(code="pro", name="Pro", sort_order=1)
        self._auth()
        resp = self.client.post(f"/api/saas/tenants/{self.school.pk}/subscription/", {
            "plan_code": "pro", "status": "active", "seats_used": 12,
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["seats_used"], 12)

    def test_post_nonexistent_school_returns_404(self):
        self._auth()
        resp = self.client.post("/api/saas/tenants/99999/subscription/", {
            "status": "active",
        }, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_user_subscription_summary_no_institution(self):
        """Unaffiliated user gets 404 on user-level summary."""
        loner = User.objects.create_user(
            username="loner",
            email="loner@test.edu",
            password=PASSWORD,
        )
        self._auth(loner)
        resp = self.client.get("/api/saas/subscription/")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("detail", resp.data)


class PlansListAPITests(_BaseTestCase):
    def test_requires_platform_admin(self):
        school_user = make_user("r", Role.ADMIN, self.school)
        self._auth(school_user)
        resp = self.client.get("/api/saas/plans/")
        self.assertEqual(resp.status_code, 403)

    def test_lists_active_plans(self):
        Plan.objects.create(code="a", name="A", is_active=True, sort_order=0)
        Plan.objects.create(code="b", name="B", is_active=False, sort_order=1)
        self._auth()
        resp = self.client.get("/api/saas/plans/")
        self.assertEqual(resp.status_code, 200)
        codes = [p["code"] for p in resp.data]
        self.assertIn("a", codes)
        self.assertNotIn("b", codes)

    def test_empty_plans_list(self):
        self._auth()
        resp = self.client.get("/api/saas/plans/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])


# ---------------------------------------------------------------------------
# Usage Analytics
# ---------------------------------------------------------------------------

class UsageAnalyticsServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="U School", code="U1")
        self.campus = Campus.objects.create(school=self.school, name="Campus U")
        cache.clear()

    def test_record_usage_buffers(self):
        record_usage(self.school.pk, "api_requests")
        from django.utils import timezone

        key = _usage_counter_key("api_requests", self.school.pk, timezone.localdate())
        self.assertEqual(cache.get(key), 1)

    def test_record_usage_ignores_invalid_metric(self):
        record_usage(self.school.pk, "invalid_metric")
        from django.utils import timezone
        key = _usage_counter_key("invalid_metric", self.school.pk, timezone.localdate())
        self.assertIsNone(cache.get(key))

    def test_record_usage_ignores_none_school(self):
        record_usage(None, "api_requests")
        # No exception, no registry entry
        self.assertIsNone(cache.get(_USAGE_REGISTRY_KEY))

    def test_flush_usage_persists(self):
        from django.utils import timezone

        day = timezone.localdate()
        record_usage(self.school.pk, "api_requests")
        record_usage(self.school.pk, "api_requests")
        record_usage(self.school.pk, "logins")
        total = flush_usage(day)
        self.assertEqual(total, 2)

        snap = DailyUsageSnapshot.objects.get(school=self.school, date=day)
        self.assertEqual(snap.api_requests, 2)
        self.assertEqual(snap.logins, 1)

    def test_flush_usage_counts_live_staff(self):
        """Live dimensions (staff) are recomputed from the DB on flush."""
        from django.utils import timezone
        from apps.accounts.models import StaffProfile

        day = timezone.localdate()
        staff_user = make_user("staffmem", Role.TEACHER, self.school)
        StaffProfile.objects.create(
            user=staff_user,
            institution=self.school,
            employee_number="STF-001",
            first_name="Staff",
            last_name="One",
            gender="male",
            primary_campus=self.campus,
            status="active",
        )
        record_usage(self.school.pk, "api_requests")
        flush_usage(day)
        snap = DailyUsageSnapshot.objects.get(school=self.school, date=day)
        self.assertEqual(snap.staff, 1)

    def test_flush_empty_registry_creates_no_snapshots(self):
        from django.utils import timezone

        cache.clear()
        flush_usage(timezone.localdate())
        self.assertFalse(DailyUsageSnapshot.objects.exists())


class UsageAnalyticsAPITests(_BaseTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def test_requires_platform_admin(self):
        school_user = make_user("r", Role.ADMIN, self.school)
        self._auth(school_user)
        resp = self.client.get("/api/saas/analytics/usage/")
        self.assertEqual(resp.status_code, 403)

    def test_returns_empty_when_no_usage(self):
        self._auth()
        resp = self.client.get("/api/saas/analytics/usage/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_requests"], 0)
        self.assertEqual(resp.data["active_schools"], 0)

    def test_custom_days_parameter(self):
        self._auth()
        resp = self.client.get("/api/saas/analytics/usage/?days=7")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["days"], 7)

    def test_days_capped_at_365(self):
        self._auth()
        resp = self.client.get("/api/saas/analytics/usage/?days=999999")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["days"], 365)

    def test_non_numeric_days_defaults_to_30(self):
        self._auth()
        resp = self.client.get("/api/saas/analytics/usage/?days=abc")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["days"], 30)


# ---------------------------------------------------------------------------
# Platform overview / status / security
# ---------------------------------------------------------------------------

class PlatformAdminPermissionTests(_BaseTestCase):
    def _unauthorized_user(self):
        return make_user("regular", Role.ADMIN, self.school)

    def test_overview_requires_platform_admin(self):
        self._auth(self._unauthorized_user())
        resp = self.client.get("/api/saas/platform/overview/")
        self.assertEqual(resp.status_code, 403)

    def test_security_requires_platform_admin(self):
        self._auth(self._unauthorized_user())
        resp = self.client.get("/api/saas/security/")
        self.assertEqual(resp.status_code, 403)

    def test_status_requires_platform_admin(self):
        self._auth(self._unauthorized_user())
        resp = self.client.get("/api/saas/platform/status/")
        self.assertEqual(resp.status_code, 403)

    def test_overview_accepts_superuser(self):
        user = _make_django_superuser("su", self.school)
        self._auth(user)
        resp = self.client.get("/api/saas/platform/overview/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("schools", resp.data)

    def test_status_returns_ok(self):
        self._auth()
        resp = self.client.get("/api/saas/platform/status/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["database"]["ok"], True)
        self.assertEqual(resp.data["cache"]["ok"], True)

    def test_security_returns_expected_keys(self):
        self._auth()
        resp = self.client.get("/api/saas/security/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("failed_logins_24h", resp.data)
        self.assertIn("brute_force_alerts_7d", resp.data)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_liveness(self):
        resp = self.client.get("/api/health/")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["database"]["ok"])

    def test_db_probe(self):
        resp = self.client.get("/api/health/?probe=db")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data["database"]["ok"])
        self.assertIsNone(data["database"]["error"])

    def test_utc_now_present(self):
        resp = self.client.get("/api/health/")
        data = json.loads(resp.content)
        self.assertIn("utc_now", data)


# ---------------------------------------------------------------------------
# Audit middleware – brute-force detection
# ---------------------------------------------------------------------------

class BruteForceAuditTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="BF School", code="BF1")
        self.user = make_user("victim", Role.ADMIN, self.school)
        self.client = APIClient()
        cache.clear()

    def _do_login(self, password=PASSWORD, status=None):
        resp = self.client.post("/api/auth/login/", {
            "username": self.user.username,
            "password": password,
        })
        return resp

    def test_threshold_triggers_brute_force_audit(self):
        for i in range(11):
            self._do_login(password="wrongpass")
        records = AuditLog.objects.filter(action="brute_force_detected")
        self.assertEqual(records.count(), 1)

    def test_one_flag_per_ip_per_day(self):
        for i in range(15):
            self._do_login(password="wrongpass")
        records = AuditLog.objects.filter(action="brute_force_detected")
        self.assertEqual(records.count(), 1)

    def test_success_login_not_brute_force(self):
        self._do_login(password=PASSWORD)
        self.assertFalse(AuditLog.objects.filter(action="brute_force_detected").exists())


# ---------------------------------------------------------------------------
# Tenant provisioning integration
# ---------------------------------------------------------------------------

class TenantProvisioningTests(_BaseTestCase):
    def test_post_with_admin_creates_school_atomically(self):
        self._auth()
        resp = self.client.post("/api/schools/tenants/", {
            "name": "Provisioned School",
            "admin": {
                "username": "admin-prov",
                "email": "admin-prov@test.edu",
                "first_name": "A",
                "last_name": "B",
                "password": "Str0ngP@ssw0rd!",
            },
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        school = School.objects.get(pk=resp.data["id"])
        self.assertEqual(school.name, "Provisioned School")
        self.assertEqual(resp.data["admin"]["username"], "admin-prov")

    def test_post_without_admin(self):
        self._auth()
        resp = self.client.post("/api/schools/tenants/", {
            "name": "No Admin School",
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertNotIn("admin", resp.data)

    def test_patch_string_false_is_paused_does_not_pause(self):
        """``bool("false")`` is True; a string "false" must unpause, not keep
        the school paused."""
        school = School.objects.create(
            name="Pause School", code="PSE", status="active", is_paused=True,
        )
        self._auth()
        resp = self.client.patch(
            f"/api/schools/tenants/{school.pk}/",
            {"is_paused": "false"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        school.refresh_from_db()
        self.assertFalse(school.is_paused)

    def test_patch_failed_admin_does_not_partially_persist(self):
        """Admin failure must roll back EVERY mutation in the patch, including
        a state toggle that previously saved itself immediately."""
        existing = User.objects.create_user(
            username="blocked",
            email="blocked@test.edu",
            password=PASSWORD,
        )
        InstitutionMembership.objects.create(
            user=existing, institution=self.school, status="active",
        )
        school = School.objects.create(
            name="Atomic School", code="ATM", status="active", is_paused=True,
        )
        self._auth()
        resp = self.client.patch(
            f"/api/schools/tenants/{school.pk}/",
            {
                "is_paused": False,
                "admin": {
                    "email": existing.email,
                    "password": "Str0ngP@ssw0rd!",
                },
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        school.refresh_from_db()
        self.assertTrue(school.is_paused)

    def test_post_missing_name_returns_400(self):
        self._auth()
        resp = self.client.post("/api/schools/tenants/", {
            "city": "Test",
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.data)

    def test_post_invalid_modules_returns_400(self):
        self._auth()
        resp = self.client.post("/api/schools/tenants/", {
            "name": "Bad Modules",
            "enabled_modules": ["nonexistent"],
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_admin_email_rolls_back_school(self):
        """A terminal admin-provisioning failure rolls the whole school back.

        ``create_user_with_username`` treats email conflicts as fatal, so the
        nested transaction must undo the School/SchoolSettings as well.
        """
        existing = User.objects.create_user(
            username="other",
            email="taken@test.edu",
            password=PASSWORD,
        )
        InstitutionMembership.objects.create(
            user=existing, institution=self.school, status="active",
        )
        self._auth()
        resp = self.client.post("/api/schools/tenants/", {
            "name": "Rollback School",
            "admin": {
                "username": "adm",
                "email": "taken@test.edu",
                "password": "Str0ngP@ssw0rd!",
            },
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.data)
        # School should NOT exist (atomic rollback)
        self.assertFalse(School.objects.filter(name="Rollback School").exists())


# ---------------------------------------------------------------------------
# DailyUsageSnapshot model
# ---------------------------------------------------------------------------

class DailyUsageSnapshotTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Snap School", code="SNP")

    def test_unique_constraint(self):
        DailyUsageSnapshot.objects.create(school=self.school, date="2026-01-01", logins=1)
        with self.assertRaises(Exception):
            DailyUsageSnapshot.objects.create(school=self.school, date="2026-01-01", logins=2)

    def test_str(self):
        snap = DailyUsageSnapshot.objects.create(
            school=self.school, date="2026-01-01", api_requests=42,
        )
        self.assertIn("42", str(snap))
        self.assertIn(self.school.name, str(snap))


# ---------------------------------------------------------------------------
# Plan model
# ---------------------------------------------------------------------------

class PlanTests(TestCase):
    def test_str(self):
        plan = Plan.objects.create(code="enterprise", name="Enterprise")
        self.assertEqual(str(plan), "Enterprise")

    def test_unique_code(self):
        Plan.objects.create(code="a", name="A")
        with self.assertRaises(Exception):
            Plan.objects.create(code="a", name="A2")


# ---------------------------------------------------------------------------
# FeatureFlag model
# ---------------------------------------------------------------------------

class FeatureFlagModelTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="FF School", code="FF1")

    def test_global_str(self):
        flag = FeatureFlag.objects.create(name="x", enabled=True)
        self.assertIn("global", str(flag))
        self.assertIn("ON", str(flag))

    def test_institution_str(self):
        flag = FeatureFlag.objects.create(name="x", enabled=False, institution=self.school)
        self.assertIn("inst:", str(flag))
        self.assertIn("off", str(flag))
