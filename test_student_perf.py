import urllib.request, json, time

sid = 'k3li9nxl34wjy43iyg58fnb1wc7ac1td'

print('=== STUDENT_01 Attendance with date filter ===')
t0 = time.time()
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/attendance/?date=2026-09-15', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    count = data.get('count', len(data.get('results', [])))
    print('  /api/attendance/?date=2026-09-15: {} ({:.1f}s) count={}'.format(resp.status, dt, count))
except Exception as e:
    dt = time.time() - t0
    print('  ERROR {} ({:.1f}s)'.format(type(e).__name__, dt))

print('\n=== With student filter ===')
t0 = time.time()
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/attendance/?student=1158', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    count = data.get('count', len(data.get('results', [])))
    print('  /api/attendance/?student=1158: {} ({:.1f}s) count={}'.format(resp.status, dt, count))
except Exception as e:
    dt = time.time() - t0
    print('  ERROR {} ({:.1f}s)'.format(type(e).__name__, dt))

print('\n=== Exams with class filter ===')
t0 = time.time()
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/exams/?class=132', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    count = data.get('count', len(data.get('results', [])))
    print('  /api/exams/?class=132: {} ({:.1f}s) count={}'.format(resp.status, dt, count))
except Exception as e:
    dt = time.time() - t0
    print('  ERROR {} ({:.1f}s)'.format(type(e).__name__, dt))