import json
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"

# Test with a known working account from previous phases
# Let's try the super admin account if we can, or check the previous session files

# First, let's check what the login response actually contains for cookies
import http.cookiejar

# Check the existing session files from Phase 53/54
SESS_DIR = r"C:\Users\Ryuk\AppData\Local\Temp\opencode"

import os
for f in os.listdir(SESS_DIR):
    if f.endswith('.txt'):
        print(f"Session file: {f}")
        cj = http.cookiejar.MozillaCookieJar()
        try:
            cj.load(os.path.join(SESS_DIR, f))
            for cookie in cj:
                print(f"  {f}: {cookie.name}={cookie.value[:20]}... domain={cookie.domain} path={cookie.path}")
        except Exception as e:
            print(f"  {f}: Error loading - {e}")

# Now let's test if we can use an existing valid session
print("\n=== Testing with existing SUPER_ADMIN session ===")
cj = http.cookiejar.MozillaCookieJar()
cj.load(os.path.join(SESS_DIR, "sa_frostfire.txt"))
cookies = "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired())

import urllib.request
BASE = "https://perfect-foundation-api.vercel.app"
req = urllib.request.Request(
    BASE + "/api/auth/me/",
    headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies, "Referer": "https://perfect-foundation-sms.vercel.app/"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"SUPER_ADMIN session works: {r.status}")
        body = r.read().decode("utf-8", "replace")
        print(f"Response: {body[:200]}")
except urllib.error.HTTPError as e:
    print(f"SUPER_ADMIN session failed: {e.code}")