# Generated manually to add tenant settings without renaming the existing School table.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schools", "0005_subjectoffering"),
    ]

    operations = [
        migrations.AddField(
            model_name="school",
            name="currency",
            field=models.CharField(default="PKR", max_length=3),
        ),
        migrations.AddField(
            model_name="school",
            name="institution_type",
            field=models.CharField(
                choices=[
                    ("school", "School"),
                    ("college", "College"),
                    ("university", "University"),
                ],
                default="school",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="school",
            name="timezone",
            field=models.CharField(default="UTC", max_length=64),
        ),
    ]
