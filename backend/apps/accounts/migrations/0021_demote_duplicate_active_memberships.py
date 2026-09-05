"""Backfill: enforce one active school per normal user.

Historical data may still contain non-Super-Admin users with more than one
*active* membership (created before the single-school guard existed). This
migration demotes the extras to ``inactive``.

``InstitutionMembership.save()`` deliberately goes unused here: the single-school
guard it runs would reject exactly this historical cleanup (the kept membership
is still active). ``bulk_update`` mirrors ``demote_extra_active_memberships()`` in
``apps/accounts/models.py``.
"""
from django.db import migrations


def demote_duplicate_active_memberships(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    InstitutionMembership = apps.get_model("accounts", "InstitutionMembership")
    RoleAssignment = apps.get_model("accounts", "RoleAssignment")

    demoted_count = 0
    for user in User.objects.all().iterator():
        if user.is_superuser:
            continue
        if RoleAssignment.objects.filter(
            membership__user=user,
            role="super_admin",
        ).exists():
            continue

        actives = list(
            InstitutionMembership.objects.filter(
                user=user,
                status="active",
            ).order_by("created_at", "id")
        )
        if len(actives) <= 1:
            continue

        keeper = None
        if user.institution_id is not None:
            keeper = next(
                (
                    m
                    for m in actives
                    if m.institution_id == user.institution_id
                ),
                None,
            )
        if keeper is None:
            keeper = actives[0]

        to_demote = [m for m in actives if m.pk != keeper.pk]
        for membership in to_demote:
            membership.status = "inactive"
        InstitutionMembership.objects.bulk_update(to_demote, ["status"])
        demoted_count += len(to_demote)

    if demoted_count:
        print(
            "Demoted "
            f"{demoted_count} duplicate active membership(s) to inactive."
        )


def noop(apps, schema_editor):
    """Reverse is a no-op: we never re-activate demoted rows."""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0020_roleassignment_unique_super_admin"),
    ]

    operations = [
        migrations.RunPython(
            demote_duplicate_active_memberships,
            noop,
        ),
    ]