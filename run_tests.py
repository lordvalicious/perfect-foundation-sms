import subprocess
import sys

tests = [
    'apps.accounts.test_campus_isolation.StudentIsolationTests',
    'apps.accounts.test_campus_isolation.DashboardIsolationTests', 
    'apps.accounts.test_campus_isolation.DocumentIsolationTests',
    'apps.accounts.test_campus_isolation.SearchIsolationTests',
    'apps.accounts.test_campus_isolation.FinanceIsolationTests',
    'apps.accounts.test_campus_isolation.ExamResultIsolationTests',
]

for test in tests:
    result = subprocess.run(
        [sys.executable, 'manage.py', 'test', test, '--settings=config.settings.production'],
        capture_output=True, text=True,
        cwd=r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend'
    )
    output = result.stdout + result.stderr
    if 'OK' in output and 'FAIL' not in output and 'ERROR' not in output:
        print(f'{test}: PASS')
    else:
        print(f'{test}: FAIL')
        lines = output.split('\n')
        for line in lines[-30:]:
            print(line)
PYEOF