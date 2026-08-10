from django.db import migrations


def seed_default_scale(apps, schema_editor):
    GradeScale = apps.get_model("reportcards", "GradeScale")
    GradeBand = apps.get_model("reportcards", "GradeBand")

    scale, _ = GradeScale.objects.get_or_create(
        name="Default (A-F)",
        defaults={"is_default": True},
    )

    bands = [
        # (letter, grade_point, min_percentage, max_percentage)
        ("A+", "4.00", 80, 100),
        ("A", "3.70", 75, 80),
        ("B+", "3.30", 70, 75),
        ("B", "3.00", 65, 70),
        ("C+", "2.70", 60, 65),
        ("C", "2.30", 55, 60),
        ("D", "1.70", 50, 55),
        ("F", "0.00", 0, 50),
    ]

    for letter, grade_point, minimum, maximum in bands:
        GradeBand.objects.get_or_create(
            scale=scale,
            letter_grade=letter,
            defaults={
                "grade_point": grade_point,
                "minimum_percentage": minimum,
                "maximum_percentage": maximum,
            },
        )

    if scale.is_default is False:
        GradeScale.objects.filter(
            is_default=True,
        ).exclude(pk=scale.pk).update(is_default=False)
        scale.is_default = True
        scale.save(update_fields=["is_default", "updated_at"])


def unseed_default_scale(apps, schema_editor):
    GradeScale = apps.get_model("reportcards", "GradeScale")

    GradeScale.objects.filter(name="Default (A-F)").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("reportcards", "0002_gradescale_reportcard_published_at_reportcard_status_and_more"),
    ]

    operations = [
        migrations.RunPython(
            seed_default_scale,
            reverse_code=unseed_default_scale,
        ),
    ]
