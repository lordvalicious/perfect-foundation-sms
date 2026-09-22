import urllib.request, json, time

def test_student(sid, label):
    print('\n=== {} ==='.format(label))
    for ep in ['/api/attendance/', '/api/exams/', '/api/report-cards/']:
        t0 = time.time()
        req = urllib.request.Request('https://perfect-foundation-api.vercel.app' + ep, headers={'Cookie': 'sessionid=' + sid})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            dt = time.time() - t0
            body = resp.read()
            data = json.loads(body)
            count = data.get('count', len(data.get('results', [])))
            print('  {}: {} ({:.1f}s) count={}'.format(ep, resp.status, dt, count))
        except Exception as e:
            dt = time.time() - t0
            print('  {}: ERROR {} ({:.1f}s)'.format(ep, type(e).__name__, dt))

# Test all students
test_student('k3li9nxl34wjy43iyg58fnb1wc7ac1td', 'STUDENT_01 (SA-ST-0001)')
test_student('yjux3tqn1c5oken9nuiar9mng00t8cp3', 'STUDENT_02 (SA-ST-0002)')
test_student('7c3g87pfca1gqq37eu56azjdxy9t2j7s', 'STUDENT_03 (SA-ST-0003)')
test_student('srvi7t8uptqp6vpakn0ykaxbgptnt4a0', 'STUDENT_BONUS (PF-20262027-0121)')