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
        "Referer": FRONTEND + "/",
        "Content-Type": "application/json",
    }
    if method == "POST" and data is not None:
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(BASE + path, data=data, headers=headers, method="POST")
    else:
        req = urllib.request.Request(BASE + path, headers=headers, method=method)
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

# Get SUPER_ADMIN session
cj = load_sess("SUPER_ADMIN")

# Check current Librarian account
print("=== Checking Librarian account ===")
code, data = call(cj, "/api/staff/")
print(f"Staff list: {code}")
if code == 200 and isinstance(data, list):
    for staff in data:
        if staff.get("employee_number") == "SA-EMP-00011" or staff.get("user", {}).get("username") == "SA-EMP-00011":
            print(f"Found Librarian: {json.dumps(staff, indent=2)[:500]}")

# Try to get the specific staff member
code, data = call(cj, "/api/staff/?search=SA-EMP-00011")
print(f"Search SA-EMP-00011: {code}")
if code == 200:
    print(f"Results: {json.dumps(data, indent=2)[:500]}")

# Check if there's an endpoint to update staff
print("\n=== Checking staff endpoints ===")
code, data = call(cj, "/api/staff/1/")
print(f"Staff 1: {code} - {json.dumps(data)[:200] if isinstance(data, dict) else data[:200]}")