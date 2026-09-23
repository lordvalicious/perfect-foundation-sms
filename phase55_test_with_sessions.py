import json
import http.cookiejar
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"
SESS_DIR = r"C:\Users\Ryuk\AppData\Local\Temp\opencode"

def load_session(session_file):
    cj = http.cookiejar.MozillaCookieJar()
    cj.load(os.path.join(SESS_DIR, session_file))
    cookies = "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired())
    return cookies

import os

# Load all working sessions
sessions = {
    "SUPER_ADMIN": load_session("sa_frostfire.txt"),
    "ADMIN": load_session("sa_flora.txt"),
    "TEACHER": load_session("sa_SA-EMP-0001.txt"),
    "STAFF": load_session("sa_DI-staff.txt"),
    "STUDENT": load_session("sa_SA-ST-0001.txt"),
}

# Test modules per role using working sessions
role_endpoints = {
    "SUPER_ADMIN": {
        "Dashboard": ["/api/dashboard/overview/", "/api/auth/me/"],
        "Finance": ["/api/dashboard/finance/", "/api/finance/reports/trial-balance/", "/api/finance/reports/income-expense/", "/api/finance/reports/receivables/"],
        "Students": ["/api/students/", "/api/students/me/"],
        "Teachers": ["/api/teachers/", "/api/teachers/me/"],
        "Staff": ["/api/staff/", "/api/staff/me/"],
        "Library": ["/api/library/books/", "/api/library/issues/"],
        "Attendance": ["/api/attendance/"],
        "Exams": ["/api/exams/"],
        "Reports": ["/api/reports/"],
    },
    "ADMIN": {
        "Dashboard": ["/api/dashboard/overview/", "/api/auth/me/"],
        "Finance": ["/api/dashboard/finance/", "/api/finance/reports/trial-balance/"],
        "Students": ["/api/students/", "/api/students/me/"],
        "Teachers": ["/api/teachers/"],
        "Staff": ["/api/staff/"],
        "Library": ["/api/library/books/"],
    },
    "TEACHER": {
        "Dashboard": ["/api/dashboard/overview/", "/api/auth/me/"],
        "Teachers": ["/api/teachers/me/"],
        "Students": ["/api/students/"],
        "Attendance": ["/api/attendance/"],
        "Exams": ["/api/exams/"],
        "Finance": ["/api/dashboard/finance/"],
        "Library": ["/api/library/books/"],
    },
    "STAFF": {
        "Dashboard": ["/api/dashboard/overview/", "/api/auth/me/"],
        "Staff": ["/api/staff/me/"],
        "Students": ["/api/students/"],
        "Finance": ["/api/dashboard/finance/"],
    },
    "STUDENT": {
        "Dashboard": ["/api/dashboard/overview/", "/api/auth/me/"],
        "Students": ["/api/students/me/"],
        "Finance": ["/api/dashboard/finance/"],
        "Attendance": ["/api/attendance/"],
        "Exams": ["/api/exams/"],
    },
}

def call_with_cookies(cookies, path):
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies, "Referer": "https://perfect-foundation-sms.vercel.app/", "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(body) if body else {}
            except:
                return r.status, {"raw": body[:200]}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body) if body else {}
        except:
            return e.code, {"raw": body[:200]}
    except Exception as e:
        return 0, {"error": str(e)}

results = {}

for role, cookies in sessions.items():
    print(f"\n=== Testing {role} ===")
    endpoints = role_endpoints.get(role, {})
    role_results = {"auth_me": {}, "modules": {}}
    
    # Test auth/me first
    status, data = call_with_cookies(cookies, "/api/auth/me/")
    role_results["auth_me"] = {"status": status, "data": data}
    print(f"  auth/me: {status} - role: {data.get('primary_role', 'N/A') if isinstance(data, dict) else 'N/A'}")
    
    for module, eps in endpoints.items():
        module_results = {}
        for ep in eps:
            status, data = call_with_cookies(cookies, ep)
            module_results[ep] = {"status": status, "data_preview": str(data)[:150] if isinstance(data, dict) else str(data)[:150]}
            status_str = "PASS" if status == 200 else ("EXPECTED_FORBIDDEN" if status == 403 else ("NOT_FOUND" if status == 404 else f"ERROR_{status}"))
            print(f"    {module}/{ep}: {status} ({status_str})")
    
    results[role] = role_results

# Save
with open("phase55_existing_sessions_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n=== SUMMARY ===")
for role, data in results.items():
    auth_status = data["auth_me"]["status"]
    role_name = data["auth_me"]["data"].get("primary_role", "N/A") if isinstance(data["auth_me"]["data"], dict) else "N/A"
    print(f"{role:12s} | auth/me: {auth_status} | role: {role_name}")
    for module, eps in data["modules"].items():
        for ep, result in eps.items():
            status = result["status"]
            status_str = "PASS" if status == 200 else ("403" if status == 403 else ("404" if status == 404 else f"ERR_{status}"))
            print(f"  {module:15s} | {ep:45s} | {status_str}")