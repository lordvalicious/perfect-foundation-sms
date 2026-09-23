import json
import http.cookiejar
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
SESS_DIR = r"C:\Users\Ryuk\AppData\Local\Temp\opencode"

def load_sess(role):
    fname = {"SUPER_ADMIN": "sa_frostfire.txt"}[role]
    cj = http.cookiejar.MozillaCookieJar()
    cj.load(f"{SESS_DIR}\\{fname}")
    return cj

def call(cj, path):
    cookies = "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None))
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0", "Cookie": "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None)), "Referer": "https://perfect-foundation-sms.vercel.app/"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, r.status == 200
    except urllib.error.HTTPError as e:
        return e.code, False
    except Exception as e:
        return 0, False

cj = load_sess("SUPER_ADMIN")
print("Testing /api/library/books/...")
code, ok = call("/api/library/books/")
print("Status:", code, "OK:", ok)

print("Testing /api/library/issues/...")
code, ok = call("/api/library/issues/")
print("Status:", code, "OK:", ok)

print("Testing /api/reports/...")
code, ok = call("/api/reports/")
print("Status:", code)

print("Testing /api/library/reports/...")
code, ok = call("/api/library/reports/")
print("Status:", code)

print("Testing /api/library/members/...")
code, ok = call("/api/library/members/")
print("Status:", code)

print("Testing /api/library/settings/...")
code, ok = call("/api/library/settings/")
print("Status:", code)

print("Testing /api/library/...")
code, ok = call("/api/library/")
print("Status:", code)

print("Testing /api/reports/library/inventory/...")
code, ok = call("/api/reports/library/inventory/")
print("Status:", code)

print("Testing /api/reports/...")
code, ok = call("/api/reports/")
print("Status:", code)