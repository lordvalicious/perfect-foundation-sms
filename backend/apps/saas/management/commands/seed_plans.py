"""Seed the standard subscription plans.

The ``free`` plan is guaranteed to exist (the code path also auto-creates it
on first access via ``get_default_plan``), so tenants always have a row to
subscribe to.
"""

from django.core.management.base import BaseCommand

from apps.saas.models import Plan

PLANS = [
    {
        "code": "free",
        "name": "Free",
        "description": "Single campus, core modules.",
        "max_students": 500,
        "max_staff": 100,
        "max_storage_mb": 1000,
        "max_api_requests_per_day": 5000,
        "monthly_price_cents": 0,
        "sort_order": 0,
    },
    {
        "code": "startup",
        "name": "Startup",
        "description": "Up to 1,500 students across up to 3 campuses.",
        "max_students": 1500,
        "max_staff": 200,
        "max_storage_mb": 5000,
        "max_api_requests_per_day": 20000,
        "monthly_price_cents": 4900,
        "sort_order": 1,
    },
    {
        "code": "grow",
        "name": "Grow",
        "description": "Up to 5,000 students, multi-campus, all modules.",
        "max_students": 5000,
        "max_staff": 500,
        "max_storage_mb": 20000,
        "max_api_requests_per_day": 100000,
        "monthly_price_cents": 9900,
        "sort_order": 2,
    },
    {
        "code": "scale",
        "name": "Scale",
        "description": "Unlimited students, priority support and SLAs.",
        "max_students": None,
        "max_staff": None,
        "max_storage_mb": None,
        "max_api_requests_per_day": None,
        "monthly_price_cents": 24900,
        "sort_order": 3,
    },
]


class Command(BaseCommand):
    help = "Seed (idempotently) the standard subscription plans."

    def handle(self, *args, **options):
        created = 0
        for spec in PLANS:
            defaults = dict(spec)
            defaults.pop("code")
            _, was_created = Plan.objects.update_or_create(
                code=spec["code"],
                defaults={**defaults, "is_active": True},
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Plans: {created} created, {Plan.objects.filter(is_active=True).count()} active."
            )
        )