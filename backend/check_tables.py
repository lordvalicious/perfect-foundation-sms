import os
import sys

# Use the correct DATABASE_URL from .env.local
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-muddy-bar-az3etcoa-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'

# Set the settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from django.conf import settings
from django.db import connection

print("Connection verified!")
print(f"ENGINE: {settings.DATABASES['default']['ENGINE']}")
print(f"NAME: {settings.DATABASES['default']['NAME']}")
print()

# Now let's check what tables exist and what data is available
with connection.cursor() as cursor:
    # List tables
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = cursor.fetchall()
    print("Tables in public schema:")
    for t in tables[:30]:
        print(f"  {t[0]}")
    print(f"... total: {len(tables)} tables")
print()