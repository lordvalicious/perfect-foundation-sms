import os
import re

pattern = re.compile(r'ArrayField|HStoreField|JSONField|UUIDField')
matches = []
for root, dirs, files in os.walk('apps'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                content = open(path, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            if pattern.search(content):
                matches.append(path)
if matches:
    print('\n'.join(matches))
else:
    print('No Postgres-specific fields found')
