import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.test.utils import get_runner

def run_tests():
    runner = get_runner(django.conf.settings)
    test_runner = runner(verbosity=2)
    failures = test_runner.run_tests(['apps.accounts.tests.SchoolSwitchingTests'])
    return failures

if __name__ == '__main__':
    failures = run_tests()
    print(f'\nTests finished with {failures} failures')
    exit(failures)