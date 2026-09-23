import json
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"

def call_login(username, password):
    data = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/api/auth/login/",
        data=data,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Referer": FRONTEND + "/"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            print(f"  Response headers:")
            for h in r.headers:
                if "cookie" in h.lower() or "set-cookie" in h.lower():
                    print(f"    {h}: {r.headers[h]}")
            cookies = r.headers.get("Set-Cookie", "")
            return r.status, json.loads(body) if body else {}, cookies, r.headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, json.loads(body) if body else {}, "", e.headers

def call_with_cookies(path, cookies):
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies, "Referer": FRONTEND + "/", "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(body) if body else {}
            except:
                return r.status, {"raw": body[:200]}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body) if body else {}
        except:
            return e.code, {"raw": body[:200]}
    except Exception as e:
        return 0, {"error": str(e)}

# Test Librarian
print("=== Testing Librarian ===")
status, data, cookies, headers = call_login("SA-EMP-00011", "uz9Z931kl0Khfi")
print(f"Login status: {status}")
print(f"Login data: {data}")
print(f"Cookies received: {cookies[:200]}")

# Test with different cookie formats
if cookies:
    # Try just the sessionid
    import re
    sessionid = re.search(r'sessionid=([^;]+)', cookies)
    csrftoken = re.search(r'csrftoken=([^;]+)', cookies)
    
    if sessionid:
        cookie_str = f"sessionid={sessionid.group(1)}"
        if csrftoken:
            cookie_str += f"; csrftoken={csrftoken.group(1)}"
        
        print(f"\nTrying with parsed cookies: {cookie_str}")
        status, data = call_with_cookies("/api/auth/me/", cookie_str)
        print(f"auth/me: {status} - {data}")
        
        status, data = call_with_cookies("/api/library/books/", cookie_str)
        print(f"library/books: {status} - {str(data)[:100]}")
        
        # Also try with Referer
        req = urllib.request.Request(
            "https://perfect-foundation-api.vercel.app/api/auth/me/",
            headers={"User-Agent": "Mozilla/5.0", "Cookie": cookie_str, "Referer": "https://perfect-foundation-sms.vercel.app/", "Content-Type": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"With Referer: {r.status}")
        except urllib.error.HTTPError as e:
            print(f"With Referer: {e.code}")

# Also test with school_code
print("\n=== Testing with school_code ===")
status, data, cookies, headers = call_login("SA-EMP-00011", "uz9Z931kl0Khfi")
if cookies:
    # Try login with school_code
    data2 = json.dumps({"username": "SA-EMP-00011", "password": "uz9Z931kl0Khfi", "school_code": "SA"}).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/api/auth/login/",
        data=data2,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Referer": FRONTEND + "/"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            cookies2 = r.headers.get("Set-Cookie", "")
            print(f"Login with school_code: {r.status}")
            print(f"Cookies: {cookies2[:200]}")
    except urllib.error.HTTPError as e:
        print(f"Login with school_code failed: {e.code}")