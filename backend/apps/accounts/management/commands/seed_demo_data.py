from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.demo_seed import (
    audit_reports,
    base,
    part1_foundation,
    part2_academics,
    part2_people,
    part3_operations,
    part4_assets,
    part5_integration,
)

PARTS = {
    1: [
        ("part1_foundation", part1_foundation.run),
    ],
    2: [
        ("part2_academics", part2_academics.run),
        ("part2_people", part2_people.run),
    ],
    3: [
        ("part3_operations", part3_operations.run),
    ],
    4: [
        ("part4_assets", part4_assets.run),
    ],
    5: [
        ("part5_integration", part5_integration.run),
        ("audit_reports", audit_reports.run),
    ],
}

PART_DESCRIPTIONS = {
    1: "school, campuses, sessions, roles, permissions, base users",
    2: "classes, subjects, teachers, support staff, students, parents, timetable",
    3: "attendance, leaves, exams, results, fee structures, invoices, payments, accounting",
    4: "HR records, payroll, library, transport, inventory, fixed assets",
    5: "portals, LMS, discipline, events, communications, helpdesk, admissions, alumni, audit & isolation tests",
}


class Command(BaseCommand):
    help = (
        "Seed repeatable demo data for the 'Demo Education Group' school "
        "(code DEMO-EDU). Idempotent: safe to re-run. Never touches any "
        "pre-existing school."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--part",
            type=int,
            choices=sorted(PARTS),
            help="Seed only one part (1-5).",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Seed every part in order (1-5).",
        )
        parser.add_argument(
            "--allow-prod",
            action="store_true",
            help=(
                "Explicitly allow seeding when DEBUG is off (e.g. the live "
                "database). Refused by default."
            ),
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_prod"]:
            raise CommandError(
                "Refusing to seed demo data: DEBUG is off and --allow-prod "
                "was not passed. This command is designed for development "
                "databases only."
            )

        if options["all"]:
            selected = sorted(PARTS)
        elif options["part"] is not None:
            selected = [options["part"]]
        else:
            raise CommandError("Specify either --part 1..5 or --all.")

        with transaction.atomic():
            ctx = base.build_context(
                stdout=self.stdout, style=self.style
            )
        # Each part commits independently so a failure in a later part does
        # not discard data already seeded by earlier parts. This makes the
        # seed resumable/incremental as well as idempotent.
        for part_no in selected:
            with transaction.atomic():
                self._run_part(ctx, part_no)
        self._print_summary(ctx, selected)

    def _run_part(self, ctx, part_no):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"===== DEMO DATA PART {part_no}: "
            f"{PART_DESCRIPTIONS[part_no]} ====="
        ))
        for label, fn in PARTS[part_no]:
            fn(ctx)

    def _print_summary(self, ctx, selected):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("===== SEED SUMMARY ====="))
        for key in sorted(ctx.counts):
            self.stdout.write(f"  {key:32} {ctx.counts[key]}")
        if ctx.notes:
            self.stdout.write(self.style.WARNING("Notes:"))
            for note in ctx.notes:
                self.stdout.write(f"  - {note}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done. Seeded parts: {', '.join(str(p) for p in selected)}"
        ))
        self.stdout.write(
            "Documentation lives in demo_data/ at the repository root."
        )