import json
import http.cookiejar
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
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

def call(cj, path):
    cookies = "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None))
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0", "Cookie": "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None)), "Referer": "https://perfect-foundation-sms.vercel.app/"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return 0

sessions = {
    "SUPER_ADMIN": "sa_frostfire.txt",
    "ADMIN": "sa_flora.txt",
    "TEACHER": "sa_SA-EMP-0001.txt",
    "STAFF": "sa_DI-staff.txt",
    "STUDENT": "sa_SA-ST-0001.txt",
}

print("Role-based access to /api/library/books/:")
for role, sess_file in sessions.items():
    cj = load_sess(role)
    code = call(cj, "/api/library/books/")
    print("%s: %d" % (role, code))

print("\nTesting /api/library/issues/:")
for role, sess_file in sessions.items():
    cj = load_sess(role)
    code = call(cj, "/api/library/issues/")
    print("%s: %d" % (role, code))

print("\nTesting /api/library/issues/1/return/ (POST):")
cj = load_sess("SUPER_ADMIN")
code = call(cj, "/api/library/issues/1/return/")
print("SUPER_ADMIN POST /return/: %d" % code)