"""School-aware authentication security tests (PROMPT 5).

Covers:
  * Duplicate usernames across schools (``0001`` in Lahore AND Sialkot)
  * School-scoped login via ``school_code`` (unambiguous)
  * Ambiguous unscoped login refused (no arbitrary account picked)
  * Wrong-school / mismatched school login rejected
  * Duplicate username within the same school blocked by the DB constraint
    while the generator allocates a fresh per-school username
  * Concurrency-safe username generation (IntegrityError retry path; a race
    loser never leaks a broken row)
  * Temporary-password flow: must_change_password forced for auto-generated
    credentials, cleared on password change, interim flag surfaces at login
  * Passwords never exposed in login/me responses, generated credential
    returned exactly once by the approved creation flow
* Post-auth school context is server-controlled (session-bound), not
     client-controllable
   * Failed-login attribution stays in scope: ambiguous shared-username
     attempts never lock out an arbitrary account (no cross-school lockout
     DoS)
"""
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.accounts.models import (
    FailedLoginAttempt,
    InstitutionMembership,
    Role,
    RoleAssignment,
)
from apps.accounts.services import (
    create_user_with_username,
    generate_username,
    login_candidate_count,
    scoped_user_queryset,
)
from apps.schools.models import School

User = get_user_model()

PASSWORD = "SchoolTro#ngPass123"


def _school(name, code):
    return School.objects.create(
        name=name,
        code=code,
        institution_type="school",
        status="active",
    )


def _member(name, school, role=Role.ADMIN, password=PASSWORD, email=None):
    """Create a user with one active membership and the given role."""
    user = User.objects.create_user(
        username=name,
        email=email or f"{name}-{school.code}@test.edu",
        password=password,
        institution=school,
    )
    InstitutionMembership.objects.create(
        user=user,
        institution=school,
        status="active",
    )
    RoleAssignment.objects.create(
        membership=user.memberships.get(),
        role=role,
    )
    return user


class SchoolAuthBase(TestCase):
    """Two schools with a deliberately shared username ``0001``.

    Each school's ``0001`` has a *different* password, proving credentials are
    resolved inside the declared school, not globally.
    """

    def setUp(self):
        self.lahore = _school("Lahore School", "LHR")
        self.sialkot = _school("Sialkot School", "SKT")

        self.lhr_password = "Lhr#Strong1"
        self.skt_password = "Skt#Strong7"

        self.lhr_user = _member(
            "0001", self.lahore, password=self.lhr_password
        )
        self.skt_user = _member(
            "0001", self.sialkot, password=self.skt_password
        )

    def _login(self, payload):
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")
        return client, client.post(
            "/api/auth/login/",
            payload,
            format="json",
        )


# =============================================================================
# DUPLICATE USERNAMES ACROSS SCHOOLS + AMBIGUITY GATE
# =============================================================================

class DuplicateUsernameLoginTests(SchoolAuthBase):
    def test_duplicate_username_logs_in_with_school_code(self):
        for code, expected, password in (
            ("LHR", self.lhr_user, self.lhr_password),
            ("SKT", self.skt_user, self.skt_password),
        ):
            client, response = self._login(
                {"username": "0001", "password": password, "school_code": code}
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["username"], "0001")
            school_names = {
                m["institution_name"]
                for m in response.data["memberships"]
            }
            self.assertEqual(
                school_names,
                {expected.memberships.get().institution.name},
            )
            # Session active institution is bound server-side.
            self.assertEqual(
                client.session["active_institution_id"],
                expected.memberships.get().institution_id,
            )

    def test_duplicate_username_works_for_both_schools(self):
        client_a, response_a = self._login(
            {"username": "0001", "password": self.lhr_password, "school_code": "LHR"}
        )
        client_b, response_b = self._login(
            {"username": "0001", "password": self.skt_password, "school_code": "SKT"}
        )
        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(response_b.status_code, 200)
        # Contexts do not bleed: each session is pinned to its own school.
        self.assertEqual(
            client_a.session["active_institution_id"], self.lahore.id
        )
        self.assertEqual(
            client_b.session["active_institution_id"], self.sialkot.id
        )

    def test_ambiguous_scoped_login_without_school_code_refused(self):
        _, response = self._login(
            {"username": "0001", "password": self.lhr_password}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("school_code", str(response.data).lower())
        self.assertNotIn("sessionid", response.cookies)

    def test_duplicate_username_login_with_wrong_school_rejected(self):
        # Lahore's 0001 password must not authenticate in the Sialkot scope.
        _, response = self._login(
            {
                "username": "0001",
                "password": self.lhr_password,
                "school_code": "SKT",
            }
        )
        self.assertEqual(response.status_code, 400)

        # Sialkot's 0001 password must not authenticate in the Lahore scope.
        _, response = self._login(
            {
                "username": "0001",
                "password": self.skt_password,
                "school_code": "LHR",
            }
        )
        self.assertEqual(response.status_code, 400)

        # Correct school, wrong password.
        _, response = self._login(
            {
                "username": "0001",
                "password": "TotallyWrong!1",
                "school_code": "LHR",
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_username_login_mismatched_membership_rejected(self):
        # "agent" exists in Lahore (member) and as a second user with no
        # membership. Declaring Sialkot must fail: no credential match exists
        # there and no arbitrary account is picked.
        User.objects.create_user(
            username="agent",
            email="agent@test.edu",
            password=PASSWORD,
            institution=self.lahore,
        )
        User.objects.create_user(
            username="agent",
            email="agent2@test.edu",
            password=PASSWORD,
        )
        InstitutionMembership.objects.create(
            user=User.objects.get(email="agent@test.edu"),
            institution=self.lahore,
            status="active",
        )
        _, response = self._login(
            {"username": "agent", "password": PASSWORD, "school_code": "SKT"}
        )
        self.assertEqual(response.status_code, 400)

    def test_single_account_without_school_code_still_logs_in(self):
        solo = _member("solo", self.lahore)
        client, response = self._login(
            {"username": solo.username, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["username"], "solo")

    def test_shared_email_across_schools_is_impossible(self):
        # Email is globally unique at the DB level, so there is no email-based
        # ambiguity path to guard; attempt to duplicate it is an IntegrityError.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="dup-email-user",
                    email=self.lhr_user.email,
                    password=PASSWORD,
                    institution=self.sialkot,
                )


# =============================================================================
# BACKEND + QUERY SCOPING UNITS
# =============================================================================

class ScopedLookupTests(SchoolAuthBase):
    def test_scoped_queryset_isolates_schools(self):
        self.assertEqual(login_candidate_count("0001"), 2)
        self.assertEqual(
            scoped_user_queryset("0001", school_code="LHR").get(),
            self.lhr_user,
        )
        self.assertEqual(
            scoped_user_queryset("0001", school_code="SKT").get(),
            self.skt_user,
        )

    def test_scoped_queryset_is_case_insensitive_on_code(self):
        self.assertEqual(
            scoped_user_queryset("0001", school_code=" lhr ").get(),
            self.lhr_user,
        )

    def test_email_lookup_respects_scope(self):
        self.assertEqual(
            scoped_user_queryset("0001-lhr@test.edu", school_code="LHR").get(),
            self.lhr_user,
        )
        self.assertEqual(login_candidate_count("0001-lhr@test.edu"), 1)

    def test_institution_scope_resolves_membership_only_user(self):
        # A user whose institution FK is NULL but holds an active membership
        # must still resolve inside that institution's scope (host logins and
        # failed-login attribution rely on this).
        user = User.objects.create_user(
            username="member-only",
            email="member-only@test.edu",
            password=PASSWORD,
        )
        InstitutionMembership.objects.create(
            user=user,
            institution=self.lahore,
            status="active",
        )
        self.assertEqual(
            scoped_user_queryset(
                "member-only", institution=self.lahore
            ).get(),
            user,
        )
        self.assertEqual(
            scoped_user_queryset(
                "member-only", institution=self.sialkot
            ).count(),
            0,
        )

    def test_backend_authenticates_scoped_username(self):
        from django.contrib.auth import authenticate

        user = authenticate(
            request=None,
            username="0001",
            password=self.skt_password,
            school_code="SKT",
        )
        self.assertEqual(user, self.skt_user)

        user = authenticate(
            request=None,
            username="0001",
            password=self.lhr_password,
            school_code="LHR",
        )
        self.assertEqual(user, self.lhr_user)


# =============================================================================
# PER-SCHOOL USERNAME UNIQUENESS
# =============================================================================

class PerSchoolUsernameTests(TestCase):
    def test_duplicate_username_in_same_school_blocked_by_db(self):
        school = _school("Lahore School", "LHR")
        _member("0001", school)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="0001",
                    email="another@test.edu",
                    password=PASSWORD,
                    institution=school,
                )

    def test_same_username_allowed_in_different_schools(self):
        a = _school("Lahore School", "LHR")
        b = _school("Sialkot School", "SKT")
        user_a = _member("0001", a, email="u1@test.edu")
        user_b = _member("0001", b, email="u2@test.edu")
        self.assertEqual(
            list(User.objects.filter(username="0001").order_by("id")),
            [user_a, user_b],
        )

    def test_generator_dedupes_within_school(self):
        school = _school("Lahore School", "LHR")
        _member("0001", school, email="e0@test.edu")
        first, first_name, first_pw = create_user_with_username(
            "0001", school, email="e1@test.edu", password="Pw#Test12345"
        )
        second, second_name, second_pw = create_user_with_username(
            "0001", school, email="e2@test.edu", password="Pw#Test12345"
        )
        self.assertEqual(first_name, "00011")
        self.assertEqual(second_name, "00012")
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(first.institution, school)
        self.assertEqual(second.institution, school)
        self.assertEqual(first_pw, "Pw#Test12345")
        self.assertEqual(second_pw, "Pw#Test12345")

    def test_generator_keeps_username_across_schools(self):
        a = _school("Lahore School", "LHR")
        b = _school("Sialkot School", "SKT")
        user_a, name_a, _ = create_user_with_username(
            "0001", a, email="e1@test.edu", password="Pw#Test12345"
        )
        user_b, name_b, _ = create_user_with_username(
            "0001", b, email="e2@test.edu", password="Pw#Test12345"
        )
        self.assertEqual(name_a, "0001")
        self.assertEqual(name_b, "0001")
        self.assertEqual(user_a.institution, a)
        self.assertEqual(user_b.institution, b)

    def test_email_conflict_is_terminal(self):
        school = _school("Lahore School", "LHR")
        create_user_with_username(
            "bob", school, email="bob@test.edu", password="Pw#Test12345"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_user_with_username(
                    "bobby", school, email="bob@test.edu", password="Pw#Test12345"
                )

    def test_placeholder_emails_never_collide_across_schools(self):
        a = _school("Lahore School", "LHR")
        b = _school("Sialkot School", "SKT")
        user_a, _, _ = create_user_with_username(
            "0001", a, email="", password="Pw#Test12345"
        )
        user_b, _, _ = create_user_with_username(
            "0001", b, email="", password="Pw#Test12345"
        )
        self.assertNotEqual(user_a.email, user_b.email)
        self.assertTrue(user_a.email.endswith("@perfectfoundation.local"))
        self.assertTrue(user_b.email.endswith("@perfectfoundation.local"))

    def test_bulk_creation_same_school_allocates_unique_usernames(self):
        school = _school("Lahore School", "LHR")
        n = 12
        results = [
            create_user_with_username(
                "0001",
                school,
                email=f"bulk-{i}@test.edu",
                password="Pw#Test12345",
            )
            for i in range(n)
        ]
        usernames = [username for _, username, _ in results]
        self.assertEqual(len(usernames), n)
        self.assertEqual(len(set(usernames)), n, usernames)
        # Exactly the per-school contract: base, base1, base2, ...
        self.assertEqual(
            sorted(usernames[1:]),
            sorted(f"0001{i}" for i in range(1, n)),
        )
        self.assertEqual(usernames[0], "0001")


# =============================================================================
# CONCURRENCY
# =============================================================================

class IntegrityErrorRetryTests(TransactionTestCase):
    """The generator must survive losing an insert race (IntegrityError).

    SQLite's shared-cache mode cannot run true parallel writers (table locks),
    so the race is simulated deterministically by making ``create_user`` raise
    IntegrityError on the account that needs "losing" to another school/user.
    On PostgreSQL the production data race itself is arbited by the same
    partial unique constraint + retry loop.
    """

    def test_retries_when_a_concurrent_writer_wins_the_username(self):
        school = _school("Lahore School", "LHR")
        # Someone else already took "0001" and "00011" in the same school.
        _member("0001", school, email="taken1@test.edu")
        _member("00011", school, email="taken2@test.edu")

        user, username, password = create_user_with_username(
            "0001", school, email="late@test.edu", password="Pw#Test12345"
        )
        self.assertEqual(username, "00012")
        self.assertEqual(user.username, "00012")
        self.assertTrue(user.check_password("Pw#Test12345"))

    def test_retry_loop_survives_interleaved_integrity_errors(self):
        school = _school("Lahore School", "LHR")
        real_create = User.objects.create_user
        calls = {"count": 0}

        def flaky_create(*args, **kwargs):
            # Lose candidate "0001" (attempt 0) and "00011" (attempt 1) to a
            # simulated concurrent writer, then let the real insert through.
            if calls["count"] < 2:
                calls["count"] += 1
                raise IntegrityError("simulated unique violation")
            return real_create(*args, **kwargs)

        with mock.patch.object(
            User.objects, "create_user", side_effect=flaky_create
        ):
            user, username, _ = create_user_with_username(
                "0001", school, email="racer@test.edu", password="Pw#Test12345"
            )

        self.assertEqual(username, "00012")
        self.assertEqual(user.username, "00012")
        self.assertEqual(
            User.objects.filter(username="00012").count(), 1
        )

    def test_parallel_creation_across_schools_keeps_shared_username(self):
        a = _school("Lahore School", "LHR")
        b = _school("Sialkot School", "SKT")

        def make(school, i):
            user, username, _ = create_user_with_username(
                "0001", school, email=f"x{i}@test.edu", password="Pw#Test12345"
            )
            return user, username

        with ThreadPoolExecutor(max_workers=2) as pool:
            (user_a, name_a), (user_b, name_b) = pool.map(
                make, (a, b), (1, 2)
            )

        self.assertEqual(name_a, "0001")
        self.assertEqual(name_b, "0001")
        self.assertEqual(user_a.institution_id, a.id)
        self.assertEqual(user_b.institution_id, b.id)

    def test_generate_username_never_touches_another_school(self):
        a = _school("Lahore School", "LHR")
        b = _school("Sialkot School", "SKT")
        # Only Sialkot holds "0001".
        _member("0001", b, email="gb@test.edu")
        # Lahore is unaffected by Sialkot's "0001" ...
        self.assertEqual(generate_username("0001", a), "0001")
        # ... while Sialkot correctly sees its own "0001" as taken.
        self.assertEqual(generate_username("0001", b), "00011")


# =============================================================================
# TEMPORARY PASSWORDS / FORCED CHANGE
# =============================================================================

class TemporaryPasswordTests(SchoolAuthBase):
    def _temp_user(self):
        user, username, password = create_user_with_username(
            "tempy",
            self.lahore,
            email="tempy@test.edu",
            # No password -> generated temp password + must_change_password
        )
        InstitutionMembership.objects.create(
            user=user,
            institution=self.lahore,
            status="active",
        )
        return user, username, password

    def test_temp_password_forces_must_change(self):
        temp_user, username, password = self._temp_user()
        self.assertTrue(temp_user.must_change_password)
        self.assertTrue(temp_user.check_password(password))

    def test_temp_password_is_never_the_user_provided_context(self):
        # A generated password must be long and random, not a guessable value.
        _, _, password = self._temp_user()
        self.assertGreaterEqual(len(password), 14)

    def test_explicit_password_does_not_force_change(self):
        user, _, password = create_user_with_username(
            "plain", self.lahore, email="plain@test.edu", password=PASSWORD
        )
        self.assertFalse(user.must_change_password)
        self.assertEqual(password, PASSWORD)

    def test_login_with_temp_password_sets_must_change_flag(self):
        temp_user, username, password = self._temp_user()
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")
        response = client.post(
            "/api/auth/login/",
            {"username": username, "password": password, "school_code": "LHR"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["must_change_password"])
        self.assertNotIn("password", response.data)

        me = client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.data["must_change_password"])
        self.assertNotIn("password", me.data)

    def test_password_change_clears_flag_and_retires_temp_password(self):
        temp_user, username, password = self._temp_user()
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")
        login = client.post(
            "/api/auth/login/",
            {"username": username, "password": password, "school_code": "LHR"},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.data)

        new_password = "NewFresh&Pass456!"
        change = client.post(
            "/api/auth/password-change/",
            {
                "current_password": password,
                "new_password": new_password,
                "confirm_password": new_password,
            },
            format="json",
        )
        self.assertEqual(change.status_code, 200, change.data)

        temp_user.refresh_from_db()
        self.assertFalse(temp_user.must_change_password)
        self.assertFalse(temp_user.check_password(password))
        self.assertTrue(temp_user.check_password(new_password))

        # Old temp password no longer authenticates.
        client2 = APIClient()
        client2.post("/api/auth/csrf/", {}, format="json")
        stale = client2.post(
            "/api/auth/login/",
            {"username": username, "password": password, "school_code": "LHR"},
            format="json",
        )
        self.assertEqual(stale.status_code, 400)


# =============================================================================
# NO PASSWORD LEAKAGE IN NORMAL RESPONSES
# =============================================================================

class PasswordExposureTests(SchoolAuthBase):
    def test_login_and_me_responses_never_expose_password(self):
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")
        response = client.post(
            "/api/auth/login/",
            {
                "username": "0001",
                "password": self.lhr_password,
                "school_code": "LHR",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.data)

        me = client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertNotIn("password", me.data)

    def test_staff_create_returns_generated_credential_once(self):
        from apps.accounts.models import StaffProfile
        from apps.accounts.serializers import StaffProfileCRUDSerializer

        staff = StaffProfile(
            employee_number="68001",
            first_name="Zara",
            last_name="Q",
            institution=self.lahore,
            status="active",
        )
        staff.save()
        serializer = StaffProfileCRUDSerializer(
            staff,
            context={"request": None},
        )
        serializer._generated_password = "Temp!Once123"
        data = serializer.data
        self.assertIn("generated_password", data)
        self.assertEqual(data["generated_password"], "Temp!Once123")

        # A fresh serialization (e.g. the subsequent list GET) must not reveal it.
        fresh = StaffProfileCRUDSerializer(
            staff,
            context={"request": None},
        ).data
        self.assertIsNone(fresh["generated_password"])


# =============================================================================
# POST-AUTH SCHOOL CONTEXT IS SERVER-CONTROLLED
# =============================================================================

class SchoolContextControlTests(SchoolAuthBase):
    def _authed(self, password=None):
        password = password or self.lhr_password
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")
        response = client.post(
            "/api/auth/login/",
            {"username": "0001", "password": password, "school_code": "LHR"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        return client

    def test_active_institution_switch_to_foreign_school_rejected(self):
        client = self._authed()
        response = client.post(
            "/api/auth/active-institution/",
            {"institution_id": self.sialkot.id},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_session_bound_to_membership_school_after_login(self):
        client = self._authed()
        self.assertEqual(
            client.session["active_institution_id"], self.lahore.id
        )

    def test_direct_session_manipulation_to_foreign_school_is_ignored(self):
        # Even if the client rewrites its session cookie, the middleware only
        # honors institutions the user belongs to.
        client = self._authed()
        client.session["active_institution_id"] = self.sialkot.id
        client.session.save()

        me = client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        # Session was re-validated against memberships and pinned back to Lahore.
        self.assertEqual(
            client.session["active_institution_id"], self.lahore.id
        )


# =============================================================================
# FAILED-LOGIN ATTRIBUTION STAYS IN SCOPE (no cross-school lockout DoS)
# =============================================================================

class FailedLoginAttributionTests(SchoolAuthBase):
    def _failed_attempt(self, payload):
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")
        return client.post(
            "/api/auth/login/",
            payload,
            format="json",
        )

    def _assert_counters(self, lhr, skt):
        self.lhr_user.refresh_from_db()
        self.skt_user.refresh_from_db()
        self.assertEqual(self.lhr_user.failed_login_attempts, lhr)
        self.assertEqual(self.skt_user.failed_login_attempts, skt)

    def test_ambiguous_unscoped_failures_never_lock_an_arbitrary_account(self):
        # Five failed unscoped logins for a username shared by two schools
        # must not attribute a single attempt to either account: the ambiguity
        # gate refuses them before any specific account can be blamed.
        for _ in range(5):
            response = self._failed_attempt(
                {"username": "0001", "password": "TotallyWrong!1"}
            )
            self.assertEqual(response.status_code, 400)

        self._assert_counters(0, 0)
        self.assertIsNone(self.lhr_user.locked_until)
        self.assertIsNone(self.skt_user.locked_until)
        self.assertFalse(
            FailedLoginAttempt.objects.filter(
                user__in=(self.lhr_user, self.skt_user),
                username_or_email="0001",
            ).exists()
        )

    def test_scoped_failed_login_attributed_to_declared_school_only(self):
        response = self._failed_attempt(
            {
                "username": "0001",
                "password": "TotallyWrong!1",
                "school_code": "SKT",
            }
        )
        self.assertEqual(response.status_code, 400)
        self._assert_counters(0, 1)

    @mock.patch(
        "apps.accounts.middleware.ActiveInstitutionMiddleware._resolve_by_host"
    )
    def test_white_label_host_failure_attributed_to_host_account(self, resolve):
        resolve.return_value = self.lahore

        response = self._failed_attempt(
            {"username": "0001", "password": "TotallyWrong!1"}
        )
        self.assertEqual(response.status_code, 400)
        self._assert_counters(1, 0)

    def test_login_failed_view_notification_obeys_same_scope(self):
        client = APIClient()
        client.post("/api/auth/csrf/", {}, format="json")

        # Ambiguous unscoped notification is attributed to nobody.
        client.post(
            "/api/auth/login/failed/",
            {"username": "0001"},
            format="json",
        )
        self._assert_counters(0, 0)

        # Declared-school notification is attributed to that school only.
        client.post(
            "/api/auth/login/failed/",
            {"username": "0001", "school_code": "SKT"},
            format="json",
        )
        self._assert_counters(0, 1)