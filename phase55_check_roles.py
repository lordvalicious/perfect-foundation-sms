import json
import urllib.request
import urllib.error

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"

# Check what roles exist in the system by looking at role choices
# Let's check the login response for various accounts to understand role mappings

# First, let's check if there's a librarian role defined by looking at the Librarian account
# The login response showed: primary_role: 'staff', memberships[0].roles: [{'role': 'staff', 'role_label': 'Staff Member'}]

# Let's check if there's a way to see all roles
# Try with SUPER_ADMIN session to see if there's a roles endpoint
import http.cookiejar
import os

BASE = "https://perfect-foundation-api.vercel.app"
FRONTEND = "https://perfect-foundation-sms.vercel.app"
SESS_DIR = r"C:\Users\Ryuk\AppData\Local\Temp\opencode"

def load_session(session_file):
    cj = http.cookiejar.MozillaCookieJar()
    cj.load(os.path.join(SESS_DIR, session_file))
    return "; ".join(f"{c.name}={c.value}" for c in cj if not c.is_expired())

super_admin_cookies = load_session("sa_frostfire.txt")

import urllib.request

def call_with_cookies(cookies, path):
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies, "Referer": "https://perfect-foundation-sms.vercel.app/", "Content-Type": "application/json"},
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

# Check roles endpoint
print("=== Checking roles/permissions endpoints ===")
for ep in ["/api/roles/", "/api/role/list/", "/api/auth/roles/", "/api/permissions/"]:
    status, data = call_with_cookies(super_admin_cookies, ep)
    print(f"  {ep}: {status} - {str(data)[:200]}")

# Check if there's a way to see all users and their roles
print("\n=== Checking user management endpoints ===")
for ep in ["/api/users/", "/api/auth/users/", "/api/admin/users/"]:
    status, data = call_with_cookies(super_admin_cookies, ep)
    print(f"  {ep}: {status} - {str(data)[:200]}")

# Check the Librarian account specifically - what role should it have?
# The login showed primary_role: 'staff', but username is SA-EMP-00011 which suggests Librarian
# Let's check if there's a way to see the user's actual role assignments
print("\n=== Checking Librarian account details ===")
# We can't easily query without a session, but we know from login response:
# primary_role: 'staff', memberships[0].roles: [{'role': 'staff', 'role_label': 'Staff Member'}]
# So the account has 'staff' role, not 'librarian'

# Let's check what the role choices are in the system by looking at the model
# The Role model has: SUPER_ADMIN, ADMIN, PRINCIPAL, VICE_PRINCIPAL, CAMPUS_ADMIN, ACADEMIC, ACCOUNTANT, HR, RECEPTIONIST, LIBRARIAN, GUARD, TEACHER, PARENT, STUDENT, STAFF
# So LIBRARIAN role EXISTS in the model but the account SA-EMP-00011 was assigned 'staff' role instead

# Let's check the Library module permissions - what role is required?
print("\n=== Checking Library module access control ===")
# We know SUPER_ADMIN, ADMIN, TEACHER can access /api/library/books/
# Let's see if there's a specific permission for librarian

# Check the existing sessions to see their permissions
# We'll test a few more endpoints
super_admin_cookies = super_admin_cookies

# Check more library endpoints
for ep in ["/api/library/", "/api/library/reports/", "/api/library/members/", "/api/library/settings/"]:
    status, data = call_with_cookies(super_admin_cookies, ep)
    print(f"  {ep}: {status}")

# Check if there's a librarian-specific permission
# The role 'librarian' exists in the model but the account wasn't assigned it