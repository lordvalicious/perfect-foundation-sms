"""Scan codebase for ALL environment variables the app reads.
Cross-reference with .env.example to find missing documentation."""
import os
import re
import glob
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.chdir(r"C:\Users\Ryuk\Documents\perfect-foundation-sms\backend")

# 1. Scan all Python files for os.environ.get / os.environ[ patterns
env_vars = {}

for fpath in glob.glob("config/**/*.py", recursive=True) + \
             glob.glob("apps/**/*.py", recursive=True):
    with open(fpath, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # os.environ.get("VAR_NAME", default)
    for m in re.finditer(r'os\.environ\.get\(\s*["\'](\w+)["\']\s*(?:,\s*([^)]+))?\)', content):
        var = m.group(1)
        default = m.group(2)
        if var not in env_vars:
            env_vars[var] = {"files": set(), "defaults": set()}
        env_vars[var]["files"].add(fpath)
        if default:
            env_vars[var]["defaults"].add(default.strip()[:40])

    # os.environ["VAR_NAME"]
    for m in re.finditer(r'os\.environ\[["\'](\w+)["\']\]', content):
        var = m.group(1)
        if var not in env_vars:
            env_vars[var] = {"files": set(), "defaults": set()}
        env_vars[var]["files"].add(fpath)

# 2. Scan .env.example for documented vars
documented = set()
env_example = ".env.example"
if os.path.exists(env_example):
    with open(env_example) as f:
        for line in f:
            m = re.match(r'#?\s*([A-Z_]+)\s*=', line)
            if m:
                documented.add(m.group(1))

# 3. Also check LAUNCH.md for documented vars
launch = r"..\LAUNCH.md"
if os.path.exists(launch):
    with open(launch) as f:
        for m in re.finditer(r'`([A-Z][A-Z_]+)`', f.read()):
            documented.add(m.group(1))

# 4. Report
print("=" * 70)
print("ENVIRONMENT VARIABLES USED BY THE APPLICATION")
print("=" * 70)

categories = {
    "REQUIRED (app won't start)": [],
    "RECOMMENDED (features break)": [],
    "OPTIONAL (features disabled)": [],
}

for var in sorted(env_vars.keys()):
    files = ", ".join(sorted(env_vars[var]["files"]))
    defaults = env_vars[var]["defaults"]
    default_str = f" (default: {'; '.join(defaults)})" if defaults else ""
    documented_str = "[DOCS OK]" if var in documented else "[NOT DOCS]"

    if var in ("DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "DATABASE_URL",
               "DJANGO_SETTINGS_MODULE"):
        categories["REQUIRED (app won't start)"].append((var, files, default_str, documented_str))
    elif var in ("DJANGO_EMAIL_HOST", "DJANGO_EMAIL_PORT", "DJANGO_EMAIL_USER",
                 "DJANGO_EMAIL_PASSWORD", "DJANGO_EMAIL_USE_TLS", "CRON_SECRET",
                 "DEFAULT_FROM_EMAIL"):
        categories["RECOMMENDED (features break)"].append((var, files, default_str, documented_str))
    else:
        categories["OPTIONAL (features disabled)"].append((var, files, default_str, documented_str))

for cat, vars_list in categories.items():
    print(f"\n--- {cat} ---")
    for var, files, default_str, doc in sorted(vars_list):
        print(f"  {var:<30} {doc:<12} {default_str}")
        print(f"    {'':30} used in: {files}")

print(f"\n{'=' * 70}")
print(f"TOTAL: {len(env_vars)} env vars read by the application")
print(f"Documented in .env.example: {len(documented)}")

# Missing from docs
undoc = set(env_vars.keys()) - documented
if undoc:
    print(f"\n⚠️  NOT DOCUMENTED ANYWHERE:")
    for v in sorted(undoc):
        print(f"   {v}")
else:
    print("\n✓ All env vars are documented")
