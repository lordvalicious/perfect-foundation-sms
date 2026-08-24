"""Apply late fees to overdue invoices.

Run periodically (cron / CI job):

    python manage.py apply_late_fees --percent 2 --grace-days 7
    python manage.py apply_late_fees --flat 200 --grace-days 10
"""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.finance.late_fee_service import apply_late_fees


class Command(BaseCommand):
    help = (
        "Add a one-time late-fee line to invoices that are past their "
        "due date. Each invoice is only charged once."
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--percent",
            type=Decimal,
            help="Fee as a percentage of the outstanding balance.",
        )
        group.add_argument(
            "--flat",
            type=Decimal,
            help="Flat fee amount per invoice.",
        )

        parser.add_argument(
            "--grace-days",
            type=int,
            default=5,
            help="Days past due_date before a fee applies (default 5).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be charged without saving.",
        )

    def handle(self, *args, **options):
        try:
            summary = apply_late_fees(
                percent=options["percent"],
                flat=options["flat"],
                grace_days=options["grace_days"],
                dry_run=options["dry_run"],
            )
        except ValueError as exc:
            raise CommandError(str(exc))

        for row in summary["rows"][:20]:
            self.stdout.write(
                f"  {row['invoice']} ({row['student']}): {row['fee']}"
            )

        label = "DRY RUN:" if summary["dry_run"] else "Late fees applied:"

        message = (
            f"{label} {summary['charged']} invoices, "
            f"total {summary['total']}."
        )

        if summary["dry_run"]:
            self.stdout.write(self.style.WARNING(message + " Nothing saved."))
        else:
            self.stdout.write(self.style.SUCCESS(message))
