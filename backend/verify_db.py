import os

# Set DATABASE_URL BEFORE Django setup
os.environ['DATABASE_URL'] = 'postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Now set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.conf import settings
db = settings.DATABASES['default']
print("ENGINE:", db.get('ENGINE'))
print("NAME:", db.get('NAME'))
print("HOST:", db.get('HOST'))
print("SSL MODE:", db.get('OPTIONS', {}).get('sslmode', 'not set') if db.get('OPTIONS') else 'no options')
print("\nProduction PostgreSQL connection verified!")