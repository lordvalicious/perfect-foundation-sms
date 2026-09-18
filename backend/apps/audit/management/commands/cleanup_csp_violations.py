"""`python manage.py cleanup_csp_violations` — enforce CSP violation retention.

Deletes ``CSPViolation`` records older than the configured retention period
(default 90 days) using a single database-side queryset delete. Safe to run
repeatedly; reports how many records were deleted.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.audit.models import CSPViolation


class Command(BaseCommand):
    help = "Delete CSP violation records older than the retention period."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help=(
                "Retention period in days; records older than this are deleted. "
                "Must be at least 1 (default: %(default)s)."
            ),
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError(
                f"--days must be a positive number of days (got {days!r}); "
                "a minimum of 1 day prevents accidental full-table deletion."
            )

        cutoff = timezone.now() - timedelta(days=days)
        queryset = CSPViolation.objects.filter(timestamp__lt=cutoff)
        deleted_count, _ = queryset.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} CSP violation(s) older than {days} day(s)."
            )
        )