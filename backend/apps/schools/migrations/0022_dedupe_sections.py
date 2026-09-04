from django.db import migrations, models


def dedupe_sections(apps, schema_editor):
    """Remove duplicate (class_obj, name) Section rows before the unique
    constraint is added, keeping the lowest-id row in each group."""
    Section = apps.get_model("schools", "Section")
    rows = (
        Section.objects.values("class_obj_id", "name")
        .annotate(count=models.Count("id"))
        .filter(count__gt=1)
    )
    for row in rows:
        keep_id = (
            Section.objects.filter(
                class_obj_id=row["class_obj_id"],
                name=row["name"],
            )
            .order_by("id")
            .values_list("id", flat=True)
            .first()
        )
        Section.objects.filter(
            class_obj_id=row["class_obj_id"],
            name=row["name"],
        ).exclude(id=keep_id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0021_subjectoffering_institution'),
    ]

    operations = [
        migrations.RunPython(
            dedupe_sections,
            migrations.RunPython.noop,
            atomic=False,
        ),
    ]
