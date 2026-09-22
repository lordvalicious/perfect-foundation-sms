import os, sys, django, time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.production')
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')

import django
django.setup()

from django.db import connection, reset_queries
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.dashboard.views import _institution_overview_counts
from apps.accounts.access import campus_access, get_institution

# Find the admin user
User = get_user_model()
admin_user = User.objects.filter(username='Flora').first()
if not admin_user:
    print("Admin user not found")
    sys.exit(1)

print(f"Found admin user: {admin_user.username} (id={admin_user.id})")

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/dashboard/overview/')
request.user = admin_user

# Check institution
institution = get_institution(request)
print(f"Institution: {institution}")

# Check campus access
ca = campus_access(request)
print(f"Campus access: {ca}")

# Reset queries
reset_queries()

# Time the query
t0 = time.time()
result = _institution_overview_counts(request)
dt = time.time() - t0

print(f"Result: {result}")
print(f"Time: {dt:.3f}s")
print(f"Queries executed: {len(connection.queries)}")

for i, q in enumerate(connection.queries):
    print(f"\nQuery {i+1} ({float(q['time']):.3f}s):")
    print(q['sql'][:500])
    print("...")

print(f"\nTotal query time: {sum(float(q['time']) for q in connection.queries):.3f}s")
print(f"Total queries: {len(connection.queries)}")