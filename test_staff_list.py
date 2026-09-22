import urllib.request, json, time

sid = 'tvm37pvvjrb5tfk3e6mfryhhset1cth4'
print('=== Staff List ===')
t0 = time.time()
req = urllib.request.Request('https://perfect-foundation-api.vercel.app/api/staff/', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    print('HTTP {} ({:.1f}s) count={} results={}'.format(resp.status, dt, data.get('count'), len(data.get('results', []))))
    for s in data.get('results', [])[:5]:
        print('  ID={} name={} campus={} emp_no={}'.format(s.get('id'), s.get('full_name'), s.get('primary_campus'), s.get('employee_number')))
except Exception as e:
    dt = time.time() - t0
    print('ERROR {} ({:.1f}s): {}'.format(type(e).__name__, time.time()-t0, e))