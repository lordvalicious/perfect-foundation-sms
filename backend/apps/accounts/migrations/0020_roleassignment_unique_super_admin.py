from django.db import migrations, models


def dedupe_super_admin(apps, schema_editor):
    """Reconcile pre-existing duplicate ``super_admin`` role assignments.

    The platform allows exactly ONE Super Admin. Priority is:
      1. A user that is also a Django superuser (platform-provisioned).
      2. Otherwise the earliest-created assignment.
    Every other ``super_admin`` assignment is downgraded to ``admin``.
    """
    RoleAssignment = apps.get_model("accounts", "RoleAssignment")

    rows = list(
        RoleAssignment.objects.filter(role="super_admin")
        .select_related("membership__user")
        .order_by("id")
    )
    if len(rows) <= 1:
        return

    keep = None
    for row in rows:
        if row.membership.user.is_superuser:
            keep = row
            break
    if keep is None:
        keep = rows[0]

    duplicates = [r.pk for r in rows if r.pk != keep.pk]
    if duplicates:
        RoleAssignment.objects.filter(pk__in=duplicates).update(role="admin")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0019_alter_user_options_user_institution_and_more"),
    ]

    operations = [
        migrations.RunPython(dedupe_super_admin, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="roleassignment",
            constraint=models.UniqueConstraint(
                condition=models.Q(("role", "super_admin")),
                fields=("role",),
                name="unique_super_admin_role",
            ),
        ),
    ]