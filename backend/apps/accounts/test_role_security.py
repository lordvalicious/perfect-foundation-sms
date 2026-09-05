"""Role hierarchy, school membership and Super Admin integrity tests.

Covers the PROMPT-4 security requirements:
  * Role escalation (self-granting, admin->super_admin, upward permission mgmt)
  * Wrong-school membership / invalid school assignment / profile contradictions
  * Duplicate Super Admin creation
  * Unauthorized role changes
  * Normal user attempting multi-school access
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from apps.accounts.access import can_manage_role
from apps.accounts.models import (
    InstitutionMembership,
    Permission,
    Role,
    RoleAssignment,
    assign_role_safely,
)
from apps.accounts.permissions import IsSuperAdmin
from apps.schools.models import School
from apps.students.models import Guardian
from apps.teachers.models import Teacher

User = get_user_model()


class RoleSecurityBase(TestCase):
    """Two schools (Lahore, Sialkot) so membership rules can be exercised."""

    def setUp(self):
        self.school_a = School.objects.create(name="Lahore School", city="Lahore")
        self.school_b = School.objects.create(name="Sialkot School", city="Sialkot")
        self.perm = Permission.objects.create(
            codename="student.create",
            name="Create Students",
            action="create",
            category="student",
        )

    def _user(self, username, role, school, is_superuser=False, role_username=None):
        """Create a user with one active membership and the given role."""
        if is_superuser:
            user = User.objects.create_superuser(
                username=username,
                email=f"{username}@test.edu",
                password="TestPass123!",
            )
        else:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@test.edu",
                password="TestPass123!",
            )
        if school is not None:
            membership = InstitutionMembership.objects.create(
                user=user,
                institution=school,
                status="active",
            )
            RoleAssignment.objects.create(
                membership=membership,
                role=role,
            )
        return user

    def _login(self, client, username, password="TestPass123!"):
        client.post("/api/auth/csrf/", {}, format="json")
        return client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )


class SuperAdminIntegrityTests(RoleSecurityBase):
    def test_duplicate_super_admin_role_rejected_by_db(self):
        admin1 = self._user("sa1", Role.SUPER_ADMIN, self.school_a)
        admin2 = self._user("sa2", Role.ADMIN, self.school_b)

        membership = admin2.memberships.get()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RoleAssignment.objects.create(
                    membership=membership,
                    role=Role.SUPER_ADMIN,
                )

    def test_duplicate_super_admin_clean_rejected(self):
        self._user("sa1", Role.SUPER_ADMIN, self.school_a)
        admin2 = self._user("sa2", Role.ADMIN, self.school_b)

        assignment = RoleAssignment(
            membership=admin2.memberships.get(),
            role=Role.SUPER_ADMIN,
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

    def test_assign_role_safely_downgrades_duplicate_super_admin(self):
        self._user("sa1", Role.SUPER_ADMIN, self.school_a)
        admin2 = self._user("sa2", Role.ADMIN, self.school_b)

        assignment, created, note = assign_role_safely(
            admin2.memberships.get(), Role.SUPER_ADMIN
        )
        self.assertFalse(created)
        self.assertEqual(assignment.role, Role.ADMIN)
        self.assertIsNotNone(note)
        self.assertEqual(
            RoleAssignment.objects.filter(role=Role.SUPER_ADMIN).count(),
            1,
        )

    def test_assign_role_safely_same_user_second_membership_stays_single(self):
        # Re-seeding the holder of the Super Admin role on another school must
        # NOT crash with IntegrityError - it degrades to an admin assignment
        # while keeping exactly one super_admin row.
        sa = self._user("sa-dup", Role.SUPER_ADMIN, self.school_a)

        assignment, created, note = assign_role_safely(
            InstitutionMembership.objects.create(
                user=sa,
                institution=self.school_b,
                status="active",
            ),
            Role.SUPER_ADMIN,
        )
        self.assertTrue(created)
        self.assertEqual(assignment.role, Role.ADMIN)
        self.assertIsNotNone(note)
        self.assertEqual(
            RoleAssignment.objects.filter(role=Role.SUPER_ADMIN).count(),
            1,
        )

    def test_admin_cannot_escalate_to_super_admin(self):
        admin = self._user("lhr-admin", Role.ADMIN, self.school_a)
        sa = self._user("lhr-sa", Role.SUPER_ADMIN, self.school_a)

        # Role security: ADMIN cannot manage the super_admin role.
        self.assertFalse(can_manage_role(admin, Role.SUPER_ADMIN, self.school_a))
        # Uniqueness backstop: once a Super Admin exists, a second
        # super_admin assignment is impossible at the DB level.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RoleAssignment.objects.create(
                    membership=admin.memberships.get(),
                    role=Role.SUPER_ADMIN,
                )
        self.assertTrue(can_manage_role(sa, Role.SUPER_ADMIN, self.school_a))

    def test_admin_not_detected_as_super_admin(self):
        admin = self._user("sa-admin", Role.ADMIN, self.school_a)
        request = APIRequestFactory().get("/")
        request.user = admin
        request.institution = self.school_a
        self.assertFalse(IsSuperAdmin().has_permission(request, None))

    def test_super_admin_detected(self):
        sa = self._user("sa-boss", Role.SUPER_ADMIN, self.school_a)
        request = APIRequestFactory().get("/")
        request.user = sa
        request.institution = self.school_a
        self.assertTrue(IsSuperAdmin().has_permission(request, None))

    def test_unauthenticated_has_no_super_admin_access(self):
        self.assertFalse(
            IsSuperAdmin().has_permission(
                type("R", (), {"user": None, "institution": None})(), None
            )
        )


class RoleEscalationTests(RoleSecurityBase):
    def test_hierarchy_ranks(self):
        admin = self._user("rank-admin", Role.ADMIN, self.school_a)
        teacher = self._user("rank-teacher", Role.TEACHER, self.school_b)

        self.assertTrue(can_manage_role(admin, Role.TEACHER, self.school_a))
        self.assertFalse(can_manage_role(admin, Role.ADMIN, self.school_a))
        self.assertFalse(can_manage_role(teacher, Role.ACCOUNTANT, self.school_b))
        self.assertFalse(
            can_manage_role(teacher, Role.ADMIN, self.school_b)
        )
        self.assertFalse(
            can_manage_role(teacher, Role.SUPER_ADMIN, self.school_b)
        )

    def test_super_admin_manages_everything(self):
        sa = self._user("rank-sa", Role.SUPER_ADMIN, self.school_a)
        for role in (Role.SUPER_ADMIN, Role.ADMIN, Role.ACCOUNTANT, Role.TEACHER):
            self.assertTrue(can_manage_role(sa, role, self.school_a))

    def test_admin_cannot_grant_role_permissions_at_own_level(self):
        admin = self._user("g-admin", Role.ADMIN, self.school_a)
        client = APIClient()
        self._login(client, "g-admin")

        response = client.post(
            "/api/auth/role-permissions/create/",
            {
                "role": Role.ADMIN,
                "permission": self.perm.pk,
                "institution": self.school_a.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_may_grant_role_permissions_below_own_level(self):
        admin = self._user("g-admin2", Role.ADMIN, self.school_a)
        client = APIClient()
        self._login(client, "g-admin2")

        response = client.post(
            "/api/auth/role-permissions/create/",
            {
                "role": Role.TEACHER,
                "permission": self.perm.pk,
                "institution": self.school_a.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_admin_cannot_grant_permission_to_himself(self):
        admin = self._user("g-admin3", Role.ADMIN, self.school_a)
        client = APIClient()
        self._login(client, "g-admin3")

        response = client.post(
            "/api/auth/user-permissions/create/",
            {
                "user": admin.pk,
                "permission": self.perm.pk,
                "institution": self.school_a.pk,
                "effect": "allow",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_grant_permission_to_peer_admin(self):
        admin = self._user("g-admin4", Role.ADMIN, self.school_a)
        peer = self._user("g-admin5", Role.ADMIN, self.school_a)
        client = APIClient()
        self._login(client, "g-admin4")

        response = client.post(
            "/api/auth/user-permissions/create/",
            {
                "user": peer.pk,
                "permission": self.perm.pk,
                "institution": self.school_a.pk,
                "effect": "allow",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_grant_permissions(self):
        student = self._user("g-student", Role.STUDENT, self.school_a)
        client = APIClient()
        self._login(client, "g-student")

        response = client.post(
            "/api/auth/user-permissions/create/",
            {"user": student.pk, "permission": self.perm.pk},
            format="json",
        )
        self.assertIn(response.status_code, (403, 400))

    def test_admin_can_grant_permission_to_lower_role(self):
        admin = self._user("g-admin6", Role.ADMIN, self.school_a)
        staff = self._user("g-staff", Role.STAFF, self.school_a)
        client = APIClient()
        self._login(client, "g-admin6")

        response = client.post(
            "/api/auth/user-permissions/create/",
            {
                "user": staff.pk,
                "permission": self.perm.pk,
                "institution": self.school_a.pk,
                "effect": "allow",
                "reason": "Needs access",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)


class SchoolMembershipTests(RoleSecurityBase):
    def test_normal_user_cannot_join_second_school(self):
        teacher = self._user("m-teacher", Role.TEACHER, self.school_a)

        with self.assertRaises(ValidationError):
            InstitutionMembership.objects.create(
                user=teacher,
                institution=self.school_b,
                status="active",
            )
        # Still exactly one membership.
        self.assertEqual(teacher.memberships.filter(status="active").count(), 1)

    def test_accountant_cannot_join_second_school(self):
        accountant = self._user("m-acct", Role.ACCOUNTANT, self.school_a)

        with self.assertRaises(ValidationError):
            InstitutionMembership.objects.create(
                user=accountant,
                institution=self.school_b,
                status="active",
            )

    def test_second_membership_same_school_allowed_by_membership_only(self):
        # Re-creating the same (user, school) pair is blocked by the unique
        # constraint, not by the single-school rule.
        admin = self._user("m-admin", Role.ADMIN, self.school_a)
        with self.assertRaises(IntegrityError):
            InstitutionMembership.objects.create(
                user=admin,
                institution=self.school_a,
                status="active",
            )

    def test_super_admin_may_hold_multiple_schools(self):
        sa = self._user("m-sa", Role.SUPER_ADMIN, self.school_a, is_superuser=True)
        InstitutionMembership.objects.create(
            user=sa,
            institution=self.school_b,
            status="active",
        )
        self.assertEqual(sa.memberships.filter(status="active").count(), 2)

    def test_profile_institution_must_match_membership(self):
        # "User = Lahore but Profile = Sialkot" is impossible server-side.
        teacher_user = User.objects.create_user(
            username="ct-teacher",
            email="ct-teacher@test.edu",
            password="TestPass123!",
        )
        Teacher.objects.create(
            user=teacher_user,
            employee_number="CT-001",
            first_name="Cross",
            last_name="Tenant",
            gender="female",
            institution=self.school_b,
        )

        with self.assertRaises(ValidationError):
            InstitutionMembership.objects.create(
                user=teacher_user,
                institution=self.school_a,
                status="active",
            )

        # A matching membership is fine.
        InstitutionMembership.objects.create(
            user=teacher_user,
            institution=self.school_b,
            status="active",
        )

    def test_student_profile_institution_must_match_membership(self):
        from apps.students.models import Student

        student_user = User.objects.create_user(
            username="ct-student",
            email="ct-student@test.edu",
            password="TestPass123!",
        )
        guardian = Guardian.objects.create(
            name="Guardian One",
            relationship="Father",
            phone="+92 300 1234567",
            institution=self.school_a,
        )
        Student.objects.create(
            user=student_user,
            admission_number="PF-CT-001",
            first_name="Cross",
            last_name="Student",
            gender="male",
            institution=self.school_a,
            guardian=guardian,
        )

        with self.assertRaises(ValidationError):
            InstitutionMembership.objects.create(
                user=student_user,
                institution=self.school_b,
                status="active",
            )

    def test_normal_user_cannot_switch_to_other_school_via_api(self):
        self._user("sw-teacher", Role.TEACHER, self.school_a)
        client = APIClient()
        self._login(client, "sw-teacher")

        response = client.post(
            "/api/auth/active-institution/",
            {"institution_id": self.school_b.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class WrongSchoolAssignmentTests(RoleSecurityBase):
    def test_invalid_school_assignment_blocked(self):
        # A super admin may NOT be assigned a membership to a school that is
        # not how normal assignment works; normal users simply can't be
        # assigned a second school no matter the data supplied.
        teacher = self._user("ws-teacher", Role.STAFF, self.school_a)
        with self.assertRaises(ValidationError):
            InstitutionMembership.objects.create(
                user=teacher,
                institution=self.school_b,
                status="active",
            )

    def test_admin_user_institution_flag_matches_membership(self):
        # user.institution (denormalized) must agree with a real membership.
        admin = User.objects.create_user(
            username="ws-admin",
            email="ws-admin@test.edu",
            password="TestPass123!",
            institution=self.school_a,
        )
        user = User.objects.get(pk=admin.pk)
        user.institution = self.school_a
        membership = InstitutionMembership.objects.create(
            user=user,
            institution=self.school_a,
            status="active",
        )
        # Sanity: the FK points at the same school as the membership.
        self.assertEqual(user.institution_id, membership.institution_id)


class SuperAdminCouplingTests(RoleSecurityBase):
    """Granting the role must elevate, and a non-superuser may not hold it."""

    def test_granting_super_admin_role_elevates_to_django_superuser(self):
        holder = self._user("cpl-holder", Role.ADMIN, self.school_a)
        self.assertFalse(holder.is_superuser)
        self.assertFalse(holder.is_staff)

        RoleAssignment.objects.create(
            membership=holder.memberships.get(),
            role=Role.SUPER_ADMIN,
        )
        holder.refresh_from_db()
        self.assertTrue(holder.is_superuser)
        self.assertTrue(holder.is_staff)

    def test_admin_role_does_not_elevate(self):
        admin = self._user("cpl-admin", Role.ADMIN, self.school_a)
        admin.refresh_from_db()
        self.assertFalse(admin.is_superuser)
        self.assertFalse(admin.is_staff)

    def test_super_admin_role_rejected_on_non_superuser_by_clean(self):
        teacher = self._user("cpl-teacher", Role.TEACHER, self.school_a)
        assignment = RoleAssignment(
            membership=teacher.memberships.get(),
            role=Role.SUPER_ADMIN,
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

    def test_user_clean_rejects_role_flag_drift(self):
        holder = self._user("cpl-drift", Role.ADMIN, self.school_a)
        RoleAssignment.objects.create(
            membership=holder.memberships.get(),
            role=Role.SUPER_ADMIN,
        )
        holder.refresh_from_db()
        holder.is_superuser = False  # simulated drift / raw DB edit
        with self.assertRaises(ValidationError):
            holder.clean()


class IntegrityCommandTests(RoleSecurityBase):
    """audit_superadmin command: reporting + --fix backfill."""

    def _command_ok(self):
        try:
            call_command("audit_superadmin")
            return True
        except SystemExit as exc:
            return exc.code in (0, None)

    def _exit_code(self, *args, **kwargs):
        try:
            call_command("audit_superadmin", *args, **kwargs)
            return None  # clean exit (code 0)
        except SystemExit as exc:
            return exc.code

    def test_audit_passes_when_invariants_hold(self):
        self._user("audit-sa", Role.SUPER_ADMIN, self.school_a)
        self._user("audit-admin", Role.ADMIN, self.school_a)
        self.assertTrue(self._command_ok())

    def test_audit_flags_missing_super_admin(self):
        self._user("audit-nobody", Role.ADMIN, self.school_a)
        self.assertEqual(self._exit_code(), 1)

    def test_audit_flags_superuser_without_role(self):
        self._user(
            "audit-root",
            Role.ADMIN,
            self.school_a,
            is_superuser=True,
        )
        self.assertEqual(self._exit_code(), 1)

    def test_audit_warns_on_duplicate_memberships_and_fix_demotes(self):
        self._user("audit-sa2", Role.SUPER_ADMIN, self.school_a)
        teacher = self._user("audit-t2", Role.TEACHER, self.school_a)

        # Create historical drift by bypassing the single-school save guard.
        InstitutionMembership.objects.bulk_create(
            [
                InstitutionMembership(
                    user=teacher,
                    institution=self.school_b,
                    status="active",
                    created_at=timezone.now(),
                    joined_at=timezone.now().date(),
                )
            ]
        )
        self.assertEqual(
            teacher.memberships.filter(status="active").count(),
            2,
        )

        # Without --fix the command reports the drift (exit 1)...
        self.assertEqual(self._exit_code(), 1)

        # ...and with --fix it demotes the extra membership (exit 0).
        self.assertIsNone(self._exit_code(fix=True))
        self.assertEqual(
            teacher.memberships.filter(status="active").count(),
            1,
        )