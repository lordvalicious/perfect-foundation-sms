import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schools", "0006_school_institution_settings"),
    ]

    operations = [
        migrations.CreateModel(
            name="SchoolSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("logo", models.ImageField(blank=True, null=True, upload_to="school/branding/")),
                ("favicon", models.ImageField(blank=True, null=True, upload_to="school/branding/")),
                ("primary_color", models.CharField(default="#1a73e8", max_length=7)),
                ("secondary_color", models.CharField(default="#34a853", max_length=7)),
                ("accent_color", models.CharField(default="#fbbc04", max_length=7)),
                ("motto", models.CharField(blank=True, max_length=300)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=20)),
                ("contact_website", models.URLField(blank=True)),
                ("address_line", models.TextField(blank=True)),
                ("footer_text", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="settings", to="schools.school")),
            ],
        ),
    ]
