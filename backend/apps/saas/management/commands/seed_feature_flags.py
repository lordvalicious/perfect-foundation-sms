"""Seed the standard feature-flag catalogue.

New flags default to OFF. Operators turn them on via the platform admin API
(POST /api/saas/flags/) or this command with ``--enable``.
"""

from django.core.management.base import BaseCommand

from apps.saas.models import FeatureFlag

DEFAULT_FLAGS = [
    {
        "name": "lms.grading_v2",
        "label": "LMS Grading v2",
        "description": "Opt-in rubric grading workflow in the LMS module.",
    },
    {
        "name": "finance.auto_late_fees",
        "label": "Auto Late Fees",
        "description": "Enable automatic late-fee application on overdue invoices.",
    },
    {
        "name": "communication.sms_delivery",
        "label": "SMS Delivery",
        "description": "Enable SMS delivery for announcements and alerts.",
    },
    {
        "name": "reports.enhanced_exports",
        "label": "Enhanced Report Exports",
        "description": "Enable the extended report export formats.",
    },
]


class Command(BaseCommand):
    help = "Seed (idempotently) the standard feature-flag catalogue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--enable",
            dest="enable",
            nargs="*",
            default=[],
            help="Names of flags to enable during this run.",
        )

    def handle(self, *args, **options):
        created = 0
        for spec in DEFAULT_FLAGS:
            _, was_created = FeatureFlag.objects.update_or_create(
                name=spec["name"],
                institution=None,
                defaults={
                    "label": spec["label"],
                    "description": spec["description"],
                    "enabled": spec["name"] in options["enable"],
                },
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Feature flags: {created} created, "
                f"{FeatureFlag.objects.filter(institution=None).count()} global total."
            )
        )