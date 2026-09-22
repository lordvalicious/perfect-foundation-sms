import json, http.cookiejar, urllib.request, urllib.error

BASE = "https://perfect-foundation-sms.vercel.app"
SESS_DIR = r"C:\Users\Ryuk\AppData\Local\Temp\opencode"

roles = ["SUPER_ADMIN", "ADMIN", "TEACHER", "STAFF", "STUDENT"]

for role in roles:
    fname = {
        "SUPER_ADMIN": "sa_frostfire.txt",
        "ADMIN": "sa_flora.txt",
        "TEACHER": "sa_SA-EMP-0001.txt",
        "STAFF": "sa_DI-staff.txt",
        "STUDENT": "sa_SA-ST-0001.txt",
    }[role]
    cj = http.cookiejar.MozillaCookieJar()
    try:
        cj.load(f"{SESS_DIR}\{fname}")
        cookies = "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired(now=None))
        req = urllib.request.Request(
            BASE + "/api/auth/me/",
            headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8", "replace")
                data = json.loads(body) if body.strip() else {}
                primary_role = data.get("primary_role", "N/A")
                institution = data.get("primary_institution", "N/A")
                print(f"{role:12s}: primary_role={primary_role:20s}, institution={institution}")
        except Exception as e:
            print(f"{role:12s}: ERROR - {str(e)[:50]}")
    except Exception as e:
        print(f"{role:12s}: Cannot load session - {str(e)[:50]}")