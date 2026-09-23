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
        with urllib.request.urlopen(req, timeout=30) as r:
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
    except Exception as e:
        return 0, str(e)

cj = load_sess("SUPER_ADMIN")
print("Testing /api/library/books/...")
code, data = call(cj, "/api/library/books/")
print("Status:", code)
if code == 200:
    print("Results count:", len(data.get('results', data)) if isinstance(data, dict) else len(data) if isinstance(data, list) else 'N/A')

print("Testing /api/library/issues/...")
code, data = call(cj, "/api/library/issues/")
print("Status:", code)

print("Testing /api/reports/library/inventory/...")
code, data = call(cj, "/api/reports/library/inventory/")
print("Status:", code)

print("Testing /api/reports/...")
code, data = call(cj, "/api/reports/")
print("Status:", code)

print("Testing /api/library/reports/...")
code, data = call(cj, "/api/library/reports/")
print("Status:", code)

print("Testing /api/library/members/...")
code, data = call(cj, "/api/library/members/")
print("Status:", code)

print("Testing /api/library/settings/...")
code, data = call(cj, "/api/library/settings/")
print("Status:", code)

print("Testing /api/library/...")
code, data = call(cj, "/api/library/")
print("Status:", code)

# Test role-based access
sessions = {
    "SUPER_ADMIN": "sa_frostfire.txt",
    "ADMIN": "sa_flora.txt",
    "TEACHER": "sa_SA-EMP-0001.txt",
    "STAFF": "sa_DI-staff.txt",
    "STUDENT": "sa_SA-ST-0001.txt",
}

print("\nRole-based access:")
for role, sess_file in sessions.items():
    cj = load_sess(role)
    code, data = call(cj, "/api/library/books/")
    print(f"{role}: {code}")