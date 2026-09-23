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

cj = load_sess("SUPER_ADMIN")

# Get all staff with pagination
print("=== Getting all staff ===")
code, data = call(cj, "/api/staff/")
if code == 200:
    print(f"Total count: {data.get('count', 'N/A')}")
    results = data.get('results', data if isinstance(data, list) else [])
    for staff in results:
        emp_num = staff.get('employee_number', 'N/A')
        user = staff.get('user', {})
        username = user.get('username', 'N/A')
        designation = staff.get('designation', 'N/A')
        department = staff.get('department', 'N/A')
        print(f"  {emp_num} | {username} | {designation} | {department}")

# Check if there's a way to create/update staff
print("\n=== Checking staff create permissions ===")
code, data = call(cj, "/api/staff/", method="POST", payload={"employee_number": "TEST-001", "first_name": "Test", "last_name": "User"})
print(f"Create staff: {code} - {json.dumps(data)[:200] if isinstance(data, dict) else data[:200]}")