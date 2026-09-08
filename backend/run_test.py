#!/usr/bin/env python
import os
import sys

os.chdir('C:\\Users\\Ryuk\\Documents\\perfect-foundation-sms\\backend')

# Configure Django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'apps.accounts',
        'apps.schools',
        'apps.teachers',
        'apps.students',
    ],
    MIDDLEWARE=[
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ],
    ROOT_URLCONF='config.urls',
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
    }],
    AUTH_PASSWORD_VALIDATORS=[],
)

import django
django.setup()

print('Django setup complete')

# Now try running the test
from apps.teachers.tests import TeacherAPIRegressionTests
from django.test.utils import get_runner

runner = get_runner(settings)
test_runner = runner(verbosity=2)
suite = test_runner.test_loader.loadTestsFromTestCase(TeacherAPIRegressionTests)
result = test_runner.run_suite(suite)

print()
print('='*60)
print(f'Tests run: {result.testsRun}')
print(f'Failures: {len(result.failures)}')
print(f'Errors: {len(result.errors)}')
for f in result.failures:
    print(f'FAILURE: {f[0]}: {f[1]}')
for e in result.errors:
    print(f'ERROR: {e[0]}: {e[1]}')