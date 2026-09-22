import urllib.request, json, time

sid = 'tvm37pvvjrb5tfk3e6mfryhhset1cth4'

# First get CSRF token
print('Getting CSRF token...')
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/auth/csrf/', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    body = resp.read()
    print('Response:', body)
    csrf_data = json.loads(body)
    csrf_token = csrf_data.get('csrfToken') or csrf_data.get('detail') or 'NO_TOKEN'
    print('CSRF token:', csrf_token)
except Exception as e:
    print('Failed to get CSRF:', e)
    exit(1)