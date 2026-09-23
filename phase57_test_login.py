import json
import http.cookiejar
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"

def test_login(username, password):
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/api/auth/login/",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Referer": "https://perfect-foundation-sms.vercel.app/",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            cookies = r.headers.get("Set-Cookie", "")
            print(f"Status: {r.status}")
            print(f"Set-Cookie: {cookies[:200]}")
            print(f"Body: {body[:500]}")
            return r.status, json.loads(body), cookies
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"Status: {e.code}")
        print(f"Body: {body[:500]}")
        return e.code, json.loads(body) if body else {}, ""
    except Exception as e:
        print(f"Error: {e}")
        return 0, {}, ""

print("Testing Librarian login (SA-EMP-00011)...")
# Need password - let's check if there's a known password or if we need to use the temporary one
# The account has must_change_password=True, so it likely has a temporary password
# Let's try with a common temporary password or see if we can trigger the password change flow