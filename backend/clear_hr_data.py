import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Get all HR-related tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hr_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Disable foreign key constraints
    cursor.execute('PRAGMA foreign_keys=OFF')
    
    for table in tables:
        try:
            cursor.execute(f'DELETE FROM {table}')
            print(f'Cleared {table}')
        except Exception as e:
            print(f'Error clearing {table}: {e}')
    
    cursor.execute('PRAGMA foreign_keys=ON')
    print('All HR tables cleared')