import json
import http.cookiejar
import urllib.request
import urllib.error
import time

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"

def call_login(username, password):
    """Login and return session cookies"""
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/api/auth/login/",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Referer": FRONTEND + "/",
        },
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
    """Make authenticated call with session cookies"""
    req = urllib.request.Request(
        BASE + path,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Cookie": cookies,
            "Referer": FRONTEND + "/",
            "Content-Type": "application/json",
        },
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

# Test accounts from user
accounts = [
    ("LIBRARIAN", "SA-EMP-00011", "uz9Z931kl0Khfi"),
    ("ACCOUNTANT", "DEG-EMP-00031", "3ykbRgXrltSV9Q"),
    ("TEACHER", "SA-EMP-0001", "SpwdH7s4NrHWgf"),
    ("TEACHER2", "SA-EMP-0003", "TgaHg38Kilcwsr"),
    ("TEACHER3", "SA-EMP-0004", "qpm6xdgsSDXSRM"),
    ("STUDENT", "SA-ST-0001", "oLa5tnj4PTPQFV"),
    ("STUDENT2", "SA-ST-0002", "KSJcs4Y7Uf82lh"),
    ("STUDENT3", "SA-ST-0003", "35cgP0rwpQNCBb"),
    ("STAFF", "DI-EMP-0001", "DxAVwyPy4OREGK"),
    ("ADMIN", "Flora", "ra2a1s345"),
    ("GUARD", "SA-EMP-00031", "LRhphWLmWx0TKu"),
    ("ADMIN_OFFICER", "SA-EMP-00041", "986kMMsspRKNXp"),
    ("NURSE", "SA-EMP-0002", "OZMvlIJ3Tq0wGL"),
]

# Test modules/endpoints per role
module_endpoints = {
    "Library": [
        "/api/library/books/",
        "/api/library/issues/",
        "/api/library/members/",
        "/api/library/reports/",
    ],
    "Finance": [
        "/api/dashboard/finance/",
        "/api/finance/reports/trial-balance/",
        "/api/finance/reports/income-expense/",
        "/api/finance/reports/receivables/",
        "/api/finance/categories/",
        "/api/finance/fee-structures/",
    ],
    "Students": [
        "/api/students/",
        "/api/students/me/",
    ],
    "Teachers": [
        "/api/teachers/",
        "/api/teachers/me/",
    ],
    "Staff": [
        "/api/staff/",
        "/api/staff/me/",
    ],
    "Attendance": [
        "/api/attendance/",
    ],
    "Exams": [
        "/api/exams/",
    ],
    "Timetable": [
        "/api/timetable/",
    ],
    "HR": [
        "/api/hr/",
    ],
    "Transport": [
        "/api/transport/",
    ],
    "Inventory": [
        "/api/inventory/",
    ],
    "Hostel": [
        "/api/hostel/",
    ],
    "Admissions": [
        "/api/admissions/",
    ],
    "Visitors": [
        "/api/visitors/",
    ],
    "Health": [
        "/api/health/",
    ],
    "Discipline": [
        "/api/discipline/",
    ],
    "Reports": [
        "/api/reports/",
    ],
    "AI": [
        "/api/ai/",
    ],
    "Dashboard": [
        "/api/dashboard/overview/",
    ],
    "Settings": [
        "/api/settings/",
    ],
}

results = []

for role_name, username, password in accounts:
    print(f"\n=== Testing {role_name}: {username} ===")
    status, data, cookies = call_login(username, password)
    
    if status != 200:
        print(f"  LOGIN FAILED: {status} - {data}")
        results.append({
            "role": role_name,
            "username": username,
            "login": "FAIL",
            "auth_me": "N/A",
            "role": "N/A",
            "institution": "N/A",
            "error": data
        })
        continue
    
    print(f"  LOGIN SUCCESS")
    
    # Get /api/auth/me/
    me_status, me_data = call_with_cookies("/api/auth/me/", cookies)
    print(f"  /api/auth/me/: {me_status}")
    
    role = me_data.get("primary_role", "unknown") if isinstance(me_data, dict) else "error"
    institution = me_data.get("primary_institution", "unknown") if isinstance(me_data, dict) else "error"
    campus = me_data.get("active_campus", "unknown") if isinstance(me_data, dict) else "error"
    
    results.append({
        "type": "auth",
        "role": role_name,
        "username": username,
        "login": "PASS",
        "auth_me": me_status,
        "role": role,
        "institution": institution,
        "campus": campus,
        "me_data": me_data
    })
    
    # Test module endpoints
    for module_name, endpoints in module_endpoints.items():
        for endpoint in endpoints:
            ep_status, ep_data = call_with_cookies(endpoint, cookies)
            result = {
                "type": "endpoint",
                "role": role_name,
                "username": username,
                "module": module_name,
                "endpoint": endpoint,
                "status": ep_status,
                "data_preview": str(ep_data)[:200] if ep_data else "none"
            }
            results.append(result)
            print(f"    {endpoint}: {ep_status}")
            time.sleep(0.1)  # Rate limiting

# Save results
with open("phase55_test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n=== SUMMARY ===")
for r in results:
    if r["type"] == "endpoint":
        print(f"  {r['role']} / {r['module']} / {r['endpoint']}: {r['status']}")
    else:
        print(f"  {r['role']} login: {r['login']}, role: {r.get('role', 'N/A')}, auth_me: {r.get('auth_me', 'N/A')}")