"""Audit the access-control invariants enforced across the platform.

Checks:
  * At most one ``super_admin`` RoleAssignment (DB constraint backstop).
  * Every Django superuser holds the ``super_admin`` role (or is otherwise
    expected) - flags accounts with gaping privileges no role UI can manage.
  * No non-Super-Admin user holds more than one *active* membership.
  * No ``super_admin`` role exists on a non-superuser account.

Exits 1 when problems remain (after ``--fix`` if requested); 0 otherwise.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import (
    Role,
    RoleAssignment,
    demote_extra_active_memberships,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Audit single-Super-Admin and single-school membership invariants. "
        "Optionally fix membership drift with --fix."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help=(
                "Demote duplicate active memberships for non-Super-Admin "
                "users to enforce the one-school rule."
            ),
        )

    def handle(self, *args, **options):
        problems = []
        fix = options["fix"]

        super_admin_roles = list(
            RoleAssignment.objects.filter(role=Role.SUPER_ADMIN).select_related(
                "membership__user"
            )
        )

        # 1. Exactly one Super Admin role.
        if len(super_admin_roles) == 0:
            problems.append(
                "ERROR: no super_admin RoleAssignment exists - bootstrap it "
                "with `python manage.py ensure_superuser`."
            )
        elif len(super_admin_roles) > 1:
            problems.append(
                "ERROR: multiple super_admin RoleAssignments found - this "
                "violates the unique_super_admin_role constraint."
            )

        holders = {
            ra.membership.user_id
            for ra in super_admin_roles
        }

        # 2. Superuser flags must coincide with the role.
        for user in (
            User.objects.filter(is_superuser=True).order_by("id")
        ):
            if user.pk not in holders:
                problems.append(
                    f"ERROR: '{user.username}' is a Django superuser (full "
                    "system access) but holds no super_admin role."
                )

        for ra in super_admin_roles:
            if ra.membership.user.is_superuser:
                continue
            problems.append(
                f"ERROR: '{ra.membership.user.username}' holds the "
                "super_admin role but is not a Django superuser."
            )

        # 3. Single active school per normal user.
        normal_users = (
            User.objects.exclude(
                id__in=User.objects.filter(is_superuser=True).values("id")
            )
            .exclude(
                id__in=RoleAssignment.objects.filter(
                    role=Role.SUPER_ADMIN
                ).values("membership__user_id")
            )
        )
        drifted = 0
        for user in normal_users.iterator():
            extra = demote_extra_active_memberships(user) if fix else []
            if fix:
                drifted += len(extra)
                continue
            active_count = user.memberships.filter(status="active").count()
            if active_count > 1:
                problems.append(
                    f"WARNING: '{user.username}' holds {active_count} active "
                    "memberships (single-school rule). Run with --fix to "
                    "demote extras."
                )

        if fix:
            self.stdout.write(
                self.style.WARNING(f"Demoted {drifted} duplicate active membership(s).")
            )

        for problem in problems:
            if problem.startswith("ERROR"):
                self.stdout.write(self.style.ERROR(problem))
            else:
                self.stdout.write(self.style.WARNING(problem))

        if problems:
            self.stdout.write(
                self.style.ERROR(
                    f"{len(problems)} invariant violation(s) found."
                )
            )
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(
                "Access-control invariants hold (single Super Admin, "
                "single active school per normal user)."
            )
        )