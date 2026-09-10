"""Flush buffered usage counters into ``DailyUsageSnapshot`` rows.

Run daily (e.g. cron / scheduler) to build the usage history the platform
analytics dashboards read. Safe to run as often as needed; it is idempotent
(upserts per school/date).
"""

from django.core.management.base import BaseCommand

from apps.saas.services import flush_usage


class Command(BaseCommand):
    help = "Persist buffered usage counters into DailyUsageSnapshot."

    def handle(self, *args, **options):
        from django.utils import timezone

        flushed = flush_usage()
        self.stdout.write(
            self.style.SUCCESS(
                f"Usage flushed for {timezone.localdate().isoformat()} "
                f"({flushed} counter increments persisted)."
            )
        )