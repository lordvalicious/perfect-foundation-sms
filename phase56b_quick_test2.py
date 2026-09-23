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
endpoints = [
    "/api/library/books/",
    "/api/library/issues/",
    "/api/reports/",
    "/api/library/reports/",
    "/api/library/members/",
    "/api/library/settings/",
    "/api/library/",
    "/api/reports/library/inventory/",
    "/api/reports/library/available/",
    "/api/reports/library/issued/",
    "/api/reports/library/returned/",
    "/api/reports/library/overdue/",
    "/api/reports/library/fines/",
    "/api/reports/library/activity/",
    "/api/reports/library/most-borrowed/",
]

print("Testing Library API endpoints...")
for ep in endpoints:
    code, ok = call(cj, ep)
    status = "OK" if ok else "FAIL (%d)" % code
    print("%s: %s" % (ep, status))