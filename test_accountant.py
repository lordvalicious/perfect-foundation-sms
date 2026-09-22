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

# Check what institution 1 is
print("=== Checking SUPER_ADMIN institution info ===")
cj = load_sess("SUPER_ADMIN")
code, data = call(cj, "/api/auth/me/")
print(f"SUPER_AUTH_ME: {json.dumps(data)[:200]}")

# Try to find institutions or schools
print("\n=== Checking available endpoints ===")
# Look at what the SUPER_ADMIN can do
test_ends = [
    "/api/schools/",
    "/api/schools/1/",
    "/api/institutions/",
    "/api/institutions/1/",
    "/api/dashboard/overview/",
    "/api/finance/reports/trial-balance/",
]

for ep in test_ends:
    code, data = call(cj, ep)
    result = json.dumps(data)[:150] if isinstance(data, dict) else str(data)[:150]
    print(f"{ep}: HTTP {code} -> {result}")