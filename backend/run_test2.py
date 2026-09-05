#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'

import django
django.setup()

from django.test.runner import DiscoverRunner

runner = DiscoverRunner(verbosity=2)
suite = runner.test_loader.loadTestsFromName('apps.accounts.tests.SchoolSwitchingTests')
result = runner.run_suite(suite)
if not result.wasSuccessful():
    exit(1)