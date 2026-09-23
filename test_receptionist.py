import requests

with open('sa_receptionist.txt', 'r') as f:
    lines = f.read().strip().split('\n')
    sessionid = lines[0].split('=')[1]
    csrftoken = lines[1].split('=')[1]

cookies = {'sessionid': sessionid, 'csrftoken': csrftoken}
headers = {'X-CSRFToken': csrftoken, 'Referer': 'https://perfect-foundation-api.vercel.app'}

base_url = 'https://perfect-foundation-api.vercel.app'

endpoints = [
    '/api/visitors/',
    '/api/auth/me/',
]

for ep in endpoints:
    r = requests.get(f'{base_url}{ep}', cookies=cookies, headers=headers, timeout=10)
    print(f'{r.status_code:3d} {ep}')
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, dict) and 'count' in data:
            print(f'  count: {data["count"]}')
        elif isinstance(data, list):
            print(f'  items: {len(data)}')
        else:
            print(f'  keys: {list(data.keys()) if isinstance(data, dict) else type(data)}')
    elif r.status_code != 404:
        print(f'  {r.text[:100]}')