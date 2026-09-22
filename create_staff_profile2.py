import urllib.request, json, time, http.cookiejar

sid = 'tvm37pvvjrb5tfk3e6mfryhhset1cth4'
csrf_token = '7ZUZiSGT0scJZs7X01C405qn9I1AafKd'

url = 'https://perfect-foundation-api.vercel.app/api/staff/'
data = {
    "user": 1157,
    "employee_number": "DI-EMP-0001",
    "first_name": "But",
    "last_name": "Ali",
    "gender": "male",
    "phone": "03001234567",
    "email": "staff@gmail.com",
    "primary_campus": 9,
    "designation": "Staff",
    "department": "Administration",
    "joining_date": "2026-01-01",
    "status": "active",
    "create_account": True,
    "username": "DI-EMP-0001",
    "password": "temp123456"
}

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [
    ('Cookie', 'sessionid=' + sid),
    ('Content-Type', 'application/json'),
    ('X-CSRFToken', csrf_token),
    ('Referer', 'https://perfect-foundation-sms.vercel.app/')
]

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), method='POST')

t0 = time.time()
try:
    resp = opener.open(req, timeout=30)
    dt = time.time() - t0
    body = resp.read()
    print('HTTP {} ({:.1f}s): {}'.format(resp.status, dt, body.decode()))
except urllib.error.HTTPError as e:
    dt = time.time() - t0
    body = e.read()
    print('HTTP {} ({:.1f}s): {}'.format(e.code, time.time()-t0, body.decode()))
except Exception as e:
    dt = time.time() - t0
    print('ERROR {} ({:.1f}s): {}'.format(type(e).__name__, time.time()-t0, e))