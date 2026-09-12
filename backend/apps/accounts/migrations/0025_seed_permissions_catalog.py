"""Seed the granular permission catalog so fresh installs are usable
without running the demo-data seeder.

The permission catalog is pure reference data; seeding it as a migration
guarantees every environment starts from the same set of system
permissions. Idempotent via update_or_create so re-runs and the existing
demo seeder coexist safely.
"""

from django.db import migrations


def seed_permissions(apps, schema_editor):
    # Runtime import keeps the catalog defined in one place (models.py)
    # instead of duplicating ~200 entries inside the migration.
    from apps.accounts.models import Permission as ModelPermission

    Permission = apps.get_model("accounts", "Permission")

    for codename, name, category, action in ModelPermission.get_default_permissions():
        Permission.objects.update_or_create(
            codename=codename,
            defaults={
                "name": name,
                "description": "",
                "category": category,
                "action": action,
                "is_system": True,
            },
        )


def unseed_permissions(apps, schema_editor):
    # Keep rows on reverse; role assignments may reference them.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0024_alter_staffattendancecorrection_staff_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]