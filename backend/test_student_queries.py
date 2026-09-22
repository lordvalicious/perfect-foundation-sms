import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.test')
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')
import django
django.setup()

from django.db import connection, reset_queries
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.students.views import StudentListCreateView

User = get_user_model()
admin = User.objects.filter(username='Flora').first()
if not admin:
    admin = User.objects.filter(username='admin').first()

factory = RequestFactory()
request = factory.get('/api/students/')
request.user = admin
from apps.accounts.managers import get_current_institution
inst = get_current_institution()
print('Institution:', inst)
request.institution = inst

reset_queries()
view = StudentListCreateView()
view.request = request
queryset = view.get_queryset()
list(queryset)

print('Queries:', len(connection.queries))
for q in connection.queries:
    t = float(q['time'])
    sql = q['sql'][:200]
    print('  {:.4f}s: {}...'.format(t, sql))
total = sum(float(q['time']) for q in connection.queries)
print('Total time: {:.4f}s'.format(total))