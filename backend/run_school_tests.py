#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'

import django
django.setup()

from django.test.runner import DiscoverRunner

runner = DiscoverRunner(verbosity=2)
suite = runner.test_loader.loadTestsFromName('apps.accounts.tests.SchoolSwitchingTests')
result = runner.run_suite(suite)
print(f'\nTests finished: {result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors')
exit(0 if result.wasSuccessful() else 1)