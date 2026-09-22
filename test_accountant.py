import json, http.cookiejar, urllib.request, urllib.error

BASE = "https://perfect-foundation-sms.vercel.app"
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
    cj.load(f"{SESS_DIR}\{fname}")
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
        req = urllib.request.Request(
            BASE + path,
            data=data,
            headers=headers,
            method="POST",
        )
    else:
        req = urllib.request.Request(
            BASE + path,
            headers=headers,
            method="GET",
        )
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

# SUPER_ADMIN session
cj = load_sess("SUPER_ADMIN")

# First get CSRF token
print("=== Getting CSRF token ===")
req = urllib.request.Request(BASE + "/api/csrf-token/", headers={"User-Agent": "Mozilla/5.0", "Cookie": "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None))})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
        print(f"CSRF response: HTTP {r.status}, body: {body[:200]}")
except Exception as e:
    print(f"CSRF error: {e}")

# Try with CSRF
print("\n=== Step 1: Creating staff profile with CSRF ===")
# Get fresh csrf
csrf_cj = load_sess("SUPER_ADMIN")
req = urllib.request.Request(BASE + "/api/csrf-token/", headers={"User-Agent": "Mozilla/5.0", "Cookie": "; ".join(f"{c.name}={c.value}" for c in csrf_cj if not c.is_expired(now=None))})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        csrf_body = r.read().decode("utf-8", "replace")
        print(f"Got csrf: {csrf_body[:200]}")
except Exception as e:
    print(f"CSRF fetch error: {e}")

# Actually, let me use the session cookie approach - the session should have the CSRF cookie set
# The SUPER_ADMIN session from sa_frostfire.txt should already have CSRF

# Let me try creating with the payload, maybe it will work with the session
payload = {
    "employee_number": "FIN-EMP-0001",
    "first_name": "Finance",
    "last_name": "Certification",
    "designation": "Accountant",
    "create_account": True,
    "username": "finance-certification-accountant",
}
code, data = call(cj, "/api/staff/", method="POST", payload=payload)
print(f"Staff create: HTTP {code}")
if code in [200, 201]:
    print(f"Response: {json.dumps(data)[:300]}")
else:
    print(f"Response: {json.dumps(data)[:300] if isinstance(data, dict) else str(data)[:300]}")

# Check if the user was created
print("\n=== Check if user exists ===")
code, data = call(cj, "/api/auth/me/")
print(f"Auth me after: HTTP {code}, data: {json.dumps(data)[:200] if isinstance(data, dict) else str(data)[:200]}")