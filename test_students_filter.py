import urllib.request, json, time

sid = 'tvm37pvvjrb5tfk3e6mfryhhset1cth4'
base = 'https://perfect-foundation-api.vercel.app/api/students/'

# Test pagination
print('=== Pagination ===')
for page in [1, 2]:
    t0 = time.time()
    url = base + '?page=' + str(page) + '&page_size=2'
    req = urllib.request.Request(url, headers={'Cookie': 'sessionid=' + sid})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        dt = time.time() - t0
        body = resp.read()
        data = json.loads(body)
        print('Page {}: HTTP {} ({:.1f}s) count={} results={}'.format(page, resp.status, dt, data.get('count'), len(data.get('results', []))))
    except Exception as e:
        dt = time.time() - t0
        print('Page {}: ERROR {} ({:.1f}s)'.format(page, type(e).__name__, dt))

# Test search
print('\n=== Search ===')
t0 = time.time()
req = urllib.request.Request(base + '?search=Aether', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    print('Search: HTTP {} ({:.1f}s) count={} results={}'.format(resp.status, dt, data.get('count'), len(data.get('results', []))))
except Exception as e:
    dt = time.time() - t0
    print('Search: ERROR {} ({:.1f}s)'.format(type(e).__name__, dt))

# Test status filter
print('\n=== Status filter ===')
t0 = time.time()
req = urllib.request.Request(base + '?status=active', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    print('Filter: HTTP {} ({:.1f}s) count={} results={}'.format(resp.status, dt, data.get('count'), len(data.get('results', []))))
except Exception as e:
    dt = time.time() - t0
    print('Filter: ERROR {} ({:.1f}s)'.format(type(e).__name__, dt))

# Test gender filter
print('\n=== Gender filter ===')
t0 = time.time()
req = urllib.request.Request(base + '?gender=male', headers={'Cookie': 'sessionid=' + sid})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    dt = time.time() - t0
    body = resp.read()
    data = json.loads(body)
    print('Gender filter: HTTP {} ({:.1f}s) count={} results={}'.format(resp.status, dt, data.get('count'), len(data.get('results', []))))
except Exception as e:
    dt = time.time() - t0
    print('Gender filter: ERROR {} ({:.1f}s)'.format(type(e).__name__, dt))