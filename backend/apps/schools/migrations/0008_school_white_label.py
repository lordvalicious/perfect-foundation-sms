from django.db import migrations, models


def populate_codes(apps, schema_editor):
    School = apps.get_model("schools", "School")
    for school in School.objects.using(schema_editor.connection.alias).order_by("pk"):
        school.code = f"school-{school.pk}"
        school.save(update_fields=["code"])


class Migration(migrations.Migration):
    dependencies = [("schools", "0007_schoolsettings")]

    operations = [
        migrations.AddField(
            model_name="school",
            name="code",
            field=models.SlugField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="schoolsettings",
            name="header_color",
            field=models.CharField(blank=True, max_length=7),
        ),
        migrations.AddField(
            model_name="schoolsettings",
            name="login_background",
            field=models.ImageField(blank=True, null=True, upload_to="school/branding/"),
        ),
        migrations.AddField(
            model_name="schoolsettings",
            name="sidebar_color",
            field=models.CharField(blank=True, max_length=7),
        ),
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
    ]