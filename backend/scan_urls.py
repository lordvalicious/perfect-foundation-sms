import os
import re

url_data = {}

for root, dirs, files in os.walk('apps'):
    for f in files:
        if f == 'urls.py':
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                # Find path() calls with name
                paths = re.findall(r'path\([\'"]([^\'"]+)[\'"].*?name=[\'"]([^\'"]+)[\'"]', content)
                # Find path() calls without name
                paths2 = re.findall(r'path\([\'"]([^\'"]+)[\'"]', content)
                # Filter out ones that already have names
                unnamed = [p for p in paths2 if not any(p == p[0] for p in paths)]
                
                if paths or unnamed:
                    app_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.join(root, f))))
                    if app_name not in url_data:
                        url_data[app_name] = []
                    for p in paths:
                        url_data[app_name].append((p[0], p[1]))
                    for p in unnamed:
                        url_data[app_name].append((p, 'unnamed'))

for app, urls in sorted(url_data.items()):
    print(f'\n=== {app} ===')
    for u in urls:
        print(f'  {u[0]} -> name: {u[1]}')