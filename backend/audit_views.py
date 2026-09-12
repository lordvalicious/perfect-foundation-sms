import django, os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
sys.path.insert(0, '.')
django.setup()

# Check pagination settings across apps
print("=== Pagination Configuration Audit ===\n")

# Check INSTALLED_APPS for DRF pagination
import django.apps
for app_config in django.apps.apps.get_app_configs():
    app_name = app_config.name
    if app_name in ['library', 'exams', 'students', 'dashboard', 'api']:
        print(f"--- {app_name} ---")
        # Check if there's a pagination setting
        try:
            # Look at views.py for pagination classes
            with open(f'apps/{app_name}/views.py') as f:
                content = f.read()
                if 'Paginator' in content or 'PageNumber' in content or 'LimitOffset' in content:
                    # Find pagination lines
                    import re
                    paginator_lines = re.findall(r'^\s*(.{0,80}Paginator.{0,80})', content, re.MULTILINE)
                    paginator_lines += re.findall(r'^\s*(.{0,80}PageNumberPagination.{0,80})', content, re.MULTILINE)
                    paginator_lines += re.findall(r'^\s*(.{0,80}LimitOffsetPagination.{0,80})', content, re.MULTILINE)
                    if paginator_lines:
                        print(f"  Pagination classes found:")
                        for pl in paginator_lines[:5]:
                            print(f"    - {pl.strip()}")
                    else:
                        print(f"  No DRF pagination classes found in views.py")
                else:
                    print(f"  No DRF pagination classes detected")
        except FileNotFoundError:
            print(f"  views.py not found")
        except Exception as e:
            print(f"  Error: {e}")

print("\n=== Caching Configuration Audit ===\n")
# Check for caching settings
from django.conf import settings
print("CACHE_BACKEND:", getattr(settings, 'CACHE_BACKEND', 'Not set'))
print("CACHES:", getattr(settings, 'CACHES', {}))
print("DEFAULT_CACHE_ALIAS:", getattr(settings, 'DEFAULT_CACHE_ALIAS', 'default'))

# Check if cache_page or cache_to_middleware is used
print("\nChecking views for cache decorators...")
import re
for app_name in ['library', 'exams', 'students']:
    try:
        with open(f'apps/{app_name}/views.py') as f:
            content = f.read()
            # Look for cache_page
            cache_matches = re.findall(r'@.*cache_page.*', content)
            if cache_matches:
                print(f"{app_name}: @cache_page found {len(cache_matches)} times")
                for cm in cache_matches[:3]:
                    print(f"  {cm[:100]}")
            else:
                print(f"{app_name}: No @cache_page decorator found")
            
            # Look for cache_control
            control_matches = re.findall(r'@.*cache_control.*', content)
            if control_matches:
                print(f"  @cache_control found {len(control_matches)} times")
    except FileNotFoundError:
        pass

print("\n=== Background Jobs Audit ===\n")
# Check for celery/background job usage
for app_name in ['students', 'exams', 'finance', 'payroll']:
    try:
        with open(f'apps/{app_name}/models.py') as f:
            content = f.read()
            # Look for signals, post_save, post_delete
            signal_matches = re.findall(r'@.*post_save|@.*post_delete|@.*pre_save', content)
            if signal_matches:
                print(f"{app_name}: {len(signal_matches)} signal handlers")
                for sm in signal_matches[:3]:
                    print(f"  {sm[:80]}")
            else:
                print(f"{app_name}: No Django signals detected in models.py")
    except FileNotFoundError:
        pass

print("\n=== Error Handling Audit ===\n")
# Check for consistent error handling patterns
for app_name in ['students', 'exams', 'library']:
    try:
        with open(f'apps/{app_name}/views.py') as f:
            content = f.read()
            # Look for PermissionDenied, Http404, ValidationError
            error_patterns = [
                ('PermissionDenied', 'PermissionDenied'),
                ('Http404', 'Http404'),
                ('ValidationError', 'ValidationError'),
                ('NotFound', 'NotFound'),
            ]
            for pattern_name, pattern in error_patterns:
                count = content.count(pattern)
                if count > 0:
                    print(f"{app_name}: {pattern} used {count} times")
    except FileNotFoundError:
        pass

print("\n=== Database Connection Handling Audit ===\n")
# Check for connection management
from django.conf import settings
print(f"ATOMIC_REQUESTS in default DB: {settings.DATABASES['default'].get('ATOMIC_REQUESTS', 'Not set')}")
print(f"CONN_MAX_AGE in default DB: {settings.DATABASES['default'].get('CONN_MAX_AGE', 'Not set')}")

# Check for using context managers for DB connections
print("\nChecking views for 'with connection' patterns...")
for app_name in ['students', 'exams']:
    try:
        with open(f'apps/{app_name}/views.py') as f:
            content = f.read()
            with_conn = content.count('with connection')
            if with_conn > 0:
                print(f"{app_name}: 'with connection' used {with_conn} times")
            else:
                print(f"{app_name}: No 'with connection' context managers")
    except FileNotFoundError:
        pass

print("\n=== Done ===")