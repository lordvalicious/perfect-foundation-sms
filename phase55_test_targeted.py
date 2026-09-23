import json
import urllib.request
import urllib.error
import time

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"

def call_login(username, password):
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/api/auth/login/",
        data=data,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Referer": FRONTEND + "/"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            cookies = r.headers.get("Set-Cookie", "")
            return r.status, json.loads(body) if body else {}, cookies
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, json.loads(body) if body else {}, ""
    except Exception as e:
        return 0, {"error": str(e)}, ""

def call_with_cookies(path, cookies):
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies, "Referer": FRONTEND + "/", "Content-Type": "application/json"},
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

# Key accounts to test
accounts = [
    ("LIBRARIAN", "SA-EMP-00011", "uz9Z931kl0Khfi"),
    ("ACCOUNTANT", "DEG-EMP-00031", "3ykbRgXrltSV9Q"),
    ("TEACHER", "SA-EMP-0001", "SpwdH7s4NrHWgf"),
    ("STUDENT", "SA-ST-0001", "oLa5tnj4PTPQFV"),
    ("STAFF", "DI-EMP-0001", "DxAVwyPy4OREGK"),
    ("ADMIN", "Flora", "ra2a1s345"),
    ("GUARD", "SA-EMP-00031", "LRhphWLmWx0TKu"),
    ("ADMIN_OFFICER", "SA-EMP-00041", "986kMMsspRKNXp"),
    ("NURSE", "SA-EMP-0002", "OZMvlIJ3Tq0wGL"),
]

# Critical endpoints per role
role_endpoints = {
    "LIBRARIAN": {
        "Library": ["/api/library/books/", "/api/library/issues/", "/api/library/members/"],
        "Dashboard": ["/api/dashboard/overview/"],
        "Auth": ["/api/auth/me/"],
    },
    "ACCOUNTANT": {
        "Finance": ["/api/dashboard/finance/", "/api/finance/reports/trial-balance/", "/api/finance/reports/income-expense/"],
        "Auth": ["/api/auth/me/"],
    },
    "TEACHER": {
        "Teachers": ["/api/teachers/me/"],
        "Students": ["/api/students/"],
        "Attendance": ["/api/attendance/"],
        "Exams": ["/api/exams/"],
        "Auth": ["/api/auth/me/"],
    },
    "STUDENT": {
        "Students": ["/api/students/me/"],
        "Finance": ["/api/dashboard/finance/"],
        "Auth": ["/api/auth/me/"],
    },
    "STAFF": {
        "Staff": ["/api/staff/me/"],
        "Dashboard": ["/api/dashboard/overview/"],
        "Auth": ["/api/auth/me/"],
    },
    "ADMIN": {
        "Dashboard": ["/api/dashboard/overview/"],
        "Finance": ["/api/dashboard/finance/", "/api/finance/reports/trial-balance/"],
        "Students": ["/api/students/"],
        "Auth": ["/api/auth/me/"],
    },
    "GUARD": {
        "Auth": ["/api/auth/me/"],
    },
    "ADMIN_OFFICER": {
        "Auth": ["/api/auth/me/"],
    },
    "NURSE": {
        "Health": ["/api/health/"],
        "Auth": ["/api/auth/me/"],
    },
}

def test_account(role_name, username, password, endpoints):
    print(f"\n=== {role_name}: {username} ===")
    status, data, cookies = call_login(username, password)
    if status != 200:
        print(f"  LOGIN FAILED: {status} - {data}")
        return {"role": role_name, "username": username, "login": "FAIL", "error": data}
    
    print(f"  LOGIN OK")
    
    # Test /api/auth/me/
    me_status, me_data = call_with_cookies("/api/auth/me/", cookies)
    primary_role = me_data.get("primary_role", "unknown") if isinstance(me_data, dict) else "error"
    institution = me_data.get("primary_institution", "unknown") if isinstance(me_data, dict) else "error"
    campus = me_data.get("active_campus", "unknown") if isinstance(me_data, dict) else "error"
    print(f"  auth/me: {me_status} | role: {primary_role} | inst: {institution} | campus: {campus}")
    
    # Test role-specific endpoints
    for module, eps in endpoints.items():
        for ep in eps:
            ep_status, ep_data = call_with_cookies(ep, cookies)
            preview = str(ep_data)[:100] if isinstance(ep_data, dict) else str(ep_data)[:100]
            print(f"    {module}/{ep}: {ep_status}")
            time.sleep(0.05)
    
    return {"role": role_name, "username": username, "login": "PASS", "primary_role": primary_role, "institution": institution, "campus": campus}

results = []
for role_name, username, password in accounts:
    endpoints = role_endpoints.get(role_name, {})
    result = test_account(role_name, username, password, endpoints)
    results.append(result)

# Save
with open("phase55_targeted_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n=== FINAL SUMMARY ===")
for r in results:
    print(f"{r['role']:15s} | login: {r.get('login', 'N/A'):4s} | role: {r.get('primary_role', 'N/A'):15s} | inst: {r.get('institution', 'N/A')}")