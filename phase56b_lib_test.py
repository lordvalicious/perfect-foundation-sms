import json
import http.cookiejar
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"
SESS_DIR = r"C:\Users\Ryuk\AppData\Local\Temp\opencode"

def load_sess(role):
    fname = {
        "SUPER_ADMIN": "sa_frostfire.txt",
        "ADMIN": "sa_flora.txt",
        "TEACHER": "sa_SA-EMP-0001.txt",
        "STAFF": "sa_DI-staff.txt",
        "STUDENT": "sa_SA-ST-0001.txt",
    }[role]
    cj = http.cookiejar.MozillaCookieJar()
    cj.load(f"{SESS_DIR}\\{fname}")
    return cj

def call(cj, path, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    cookies = "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None))
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": cookies,
        "Referer": "https://perfect-foundation-sms.vercel.app/",
        "Content-Type": "application/json",
    }
    if method == "POST" and payload is not None:
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    else:
        req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0", "Cookie": "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None)), "Referer": "https://perfect-foundation-sms.vercel.app/", "Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(body)
            except Exception:
                return r.status, body[:300]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:300]

def safe_print(text):
    print(text.encode('ascii', 'replace').decode('ascii'))

# Test with SUPER_ADMIN
cj = load_sess("SUPER_ADMIN")

safe_print("=== Testing Library API with SUPER_ADMIN ===")
endpoints = [
    ("/api/library/books/", "Books List"),
    ("/api/library/issues/", "Issues List"),
    ("/api/library/books/?search=test", "Books Search"),
    ("/api/library/books/?category=fiction", "Books Filter"),
    ("/api/schools/campuses/", "Campuses (for Library form)"),
]

for ep, desc in endpoints:
    code, data = call(cj, ep)
    status_str = "PASS" if code == 200 else "FAIL (%d)" % code
    count = len(data.get('results', data)) if isinstance(data, dict) and 'results' in data else (len(data) if isinstance(data, list) else 'N/A')
    safe_print("  %s: %s - Count: %s" % (desc, status_str, count))

# Check if Library reports are accessible
safe_print("\n=== Testing Library Reports (IsAccountantRole) ===")
lib_reports = [
    "/api/reports/library/inventory/",
    "/api/reports/library/available/",
    "/api/reports/library/issued/",
    "/api/reports/library/returned/",
    "/api/reports/library/overdue/",
    "/api/reports/library/fines/",
    "/api/reports/library/activity/",
    "/api/reports/library/most-borrowed/",
]

for ep in lib_reports:
    code, data = call(cj, ep)
    status_str = "PASS" if code == 200 else "FAIL (%d)" % code
    safe_print("  %s: %s" % (ep, status_str))

# Check missing endpoints
safe_print("\n=== Testing Missing Library Endpoints ===")
missing = [
    "/api/library/reports/",
    "/api/library/members/",
    "/api/library/settings/",
    "/api/library/",
    "/api/reports/library/",
]
for ep in missing:
    code, data = call(cj, ep)
    status_str = "PASS" if code == 200 else "404" if code == 404 else "FAIL (%d)" % code
    safe_print("  %s: %s" % (ep, status_str))

# Check Reports base
safe_print("\n=== Reports Base ===")
code, data = call(cj, "/api/reports/")
safe_print("  /api/reports/: %d" % code)

# Check Library route access for different roles
safe_print("\n=== Role-based Access Test ===")
sessions = {
    "SUPER_ADMIN": "sa_frostfire.txt",
    "ADMIN": "sa_flora.txt",
    "TEACHER": "sa_SA-EMP-0001.txt",
    "STAFF": "sa_DI-staff.txt",
    "STUDENT": "sa_SA-ST-0001.txt",
}

for role, sess_file in sessions.items():
    cj = load_sess(role)
    code, data = call(cj, "/api/library/books/")
    status_str = "PASS" if code == 200 else "FAIL (%d)" % code
    safe_print("  %s: %s" % (role, status_str))