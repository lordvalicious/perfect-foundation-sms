import os, sys
sys.path.insert(0, ".")
os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ["DB_NAME"] = r"C:\Users\Ryuk\AppData\Local\Temp\opencode\sms_test.db"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost"

import django
django.setup()

from django.core.management import call_command
call_command("makemigrations", "schools", interactive=False)
call_command("migrate", interactive=False)
print("DONE")
