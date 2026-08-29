#!/usr/bin/env python
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.conf import settings
from django.test.utils import get_runner

def run_tests(app_labels):
    """Run Django tests for given app labels."""
    TestRunner = get_runner(django.settings)
    runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
    failures = []
    
    for app_label in app_labels:
        print(f"\n{'='*60}")
        print(f"TESTING: {app_label}")
        print(f"{'='*60}")
        app_failures = runner.test_labels([app_label], failfast=False)
        failures.extend(app_failures)
        print(f"Failures for {app_label}: {len(app_failures)}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL FAILURES: {len(failures)}")
    print(f"{'='*60}")
    return len(failures)

if __name__ == '__main__':
    # Run tests for key security-related apps
    apps = [
        'accounts',      # Phase 3: Auth, RBAC, Campus isolation
        'students',      # Phase 4: Student lifecycle
        'finance',       # Phase 8: Fees & finance
        'hr',            # Phase 9: HR & Payroll
        'exams',         # Phase 7: Exams & Results
        'attendance',    # Phase 6: Attendance
        'communication', # Phase 13: Notifications
        'workflow',      # Phase 14: Workflow engine
    ]
    
    total = run_tests(apps)
    sys.exit(total)