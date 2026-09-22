import urllib.request, json, time

sid = 'tvm37pvvjrb5tfk3e6mfryhhset1cth4'

# First get CSRF token
print('Getting CSRF token...')
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/auth/csrf/', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    body = resp.read()
    csrf_data = json.loads(body)
    csrf_token = csrf_data.get('csrfToken')
    print('CSRF token:', csrf_token)
except Exception as e:
    print('Failed to get CSRF:', e)
    exit(1)

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

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={
    'Cookie': 'sessionid=' + sid,
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token,
    'Referer': 'https://perfect-foundation-sms.vercel.app/'
}, method='POST')

t0 = time.time()
try:
    resp = urllib.request.urlopen(req, timeout=30)
    dt = time.time() - t0
    body = resp.read()
    print('HTTP {} ({:.1f}s): {}'.format(resp.status, dt, resp.read().decode()))
except urllib.error.HTTPError as e:
    dt = time.time() - t0
    body = e.read()
    print('HTTP {} ({:.1f}s): {}'.format(e.code, time.time()-t0, body.decode()))
except Exception as e:
    dt = time.time() - t0
    print('ERROR {} ({:.1f}s): {}'.format(type(e).__name__, time.time()-t0, e))