"""Seed the AI & Insights permission catalog entries.

Idempotent via update_or_create; mirrors 0025 so fresh installs and
existing environments converge on the same system permission set.
"""

from django.db import migrations


def seed_ai_permissions(apps, schema_editor):
    from apps.accounts.models import Permission as ModelPermission

    Permission = apps.get_model("accounts", "Permission")

    for codename, name, category, action in ModelPermission.get_default_permissions():
        if not codename.startswith("insight."):
            continue
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


def unseed_ai_permissions(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0026_alter_permission_action_alter_permission_category"),
    ]

    operations = [
        migrations.RunPython(seed_ai_permissions, unseed_ai_permissions),
    ]