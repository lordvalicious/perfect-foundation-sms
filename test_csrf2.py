import urllib.request, json, time, http.cookiejar

sid = 'tvm37pvvjrb5tfk3e6mfryhhset1cth4'

# Get CSRF cookie
print('Getting CSRF cookie...')
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/auth/csrf/', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = opener.open(req, timeout=15)
    print('Response:', resp.read().decode())
    print('Cookies:')
    for cookie in cj:
        print('  {}={}'.format(cookie.name, cookie.value))
except Exception as e:
    print('Failed:', e)