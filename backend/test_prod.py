import os
import sys

# Set DATABASE_URL before anything else
os.environ['DATABASE_URL'] = 'postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Set the settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

# Add the backend directory to path
sys.path.insert(0, '.')

import django
django.setup()

from django.conf import settings
db = settings.DATABASES['default']
print("ENGINE:", db['ENGINE'])
print("NAME:", db['NAME'])
print("HOST:", db['HOST'])

# Now try to access the database
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    print("Database query successful! Result:", cursor.fetchone())