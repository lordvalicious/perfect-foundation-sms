import os
import sys

# Set DATABASE_URL before importing Django
os.environ['DATABASE_URL'] = 'postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Set the settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

# Now import and setup Django
sys.path.insert(0, '.')
import django
django.setup()

from django.conf import settings
db = settings.DATABASES['default']
print("ENGINE:", db['ENGINE'])
print("NAME:", db['NAME'])
print("USER:", db['USER'])
print("HOST:", db['HOST'])
print("PORT:", db['PORT'])
print("SSL MODE:", db['OPTIONS'].get('sslmode', 'not set'))
print("\nProduction PostgreSQL connection verified!")