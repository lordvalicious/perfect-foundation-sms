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

# Check SUPER_ADMIN role assignments
print("=== SUPER_ADMIN role assignments ===")
cj = load_sess("SUPER_ADMIN")
code, data = call(cj, "/api/role/list/")
print(f"/api/role/list/: HTTP {code}")
if code == 200:
    print(f"  Roles: {json.dumps(data)[:300]}")

# Check institution switch
print("\n=== Check institution switch ===")
code, data = call(cj, "/api/auth/active-institution/", method="POST", payload={"institution_id": 1})
print(f"active-institution: HTTP {code}")

# Check finance routes with SUPER_ADMIN
print("\n=== Finance routes with SUPER_ADMIN ===")
for route in ["/api/finance/reports/trial-balance/", "/api/dashboard/finance/", "/api/finance/reports/income-expense/"]:
    code, data = call(cj, route)
    print(f"  {route}: HTTP {code}")

# Check STAFF finance access
print("\n=== Finance routes with STAFF ===")
cj2 = load_sess("STAFF")
for route in ["/api/finance/reports/trial-balance/", "/api/dashboard/finance/"]:
    code, data = call(cj2, route)
    print(f"  {route}: HTTP {code}")

# Check ADMIN finance access
print("\n=== Finance routes with ADMIN ===")
cj3 = load_sess("ADMIN")
for route in ["/api/finance/reports/trial-balance/", "/api/dashboard/finance/"]:
    code, data = call(cj3, route)
    print(f"  {route}: HTTP {code}")