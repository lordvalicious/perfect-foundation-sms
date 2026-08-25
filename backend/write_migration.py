import os, sys
sys.path.insert(0, ".")
os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ["DB_NAME"] = r"C:\Users\Ryuk\AppData\Local\Temp\opencode\sms_test.db"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost"

import django
django.setup()

from django.db import migrations, models
from django.utils import timezone
from django.core.management import call_command

# Write the migration file manually
migration_content = '''from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("schools", "0015_school_enabled_modules"),
    ]

    operations = [
        migrations.AddField(
            model_name="academicunit",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="academicunit",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="academicyear",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="academicyear",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="term",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="term",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="subject",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="subject",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="subjectoffering",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="subjectoffering",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
'''

migration_path = os.path.join("apps", "schools", "migrations", "0016_add_missing_timestamps.py")
with open(migration_path, "w") as f:
    f.write(migration_content)

print(f"Written: {migration_path}")

# Apply it
call_command("migrate", "schools", interactive=False)
print("Migration applied!")

call_command("check")
print("Check passed!")
