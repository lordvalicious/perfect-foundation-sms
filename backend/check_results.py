import re

with open('full_baseline.txt') as f:
    content = f.read()

# Find "Ran" pattern
match = re.search(r'Ran (\d+) tests', content)
if match:
    count = match.group(1)
    print(f"Tests run: {count}")
    
    # Check for OK or FAILED
    if 'OK' in content:
        print("Status: OK")
    if 'FAILED' in content:
        print("Status: FAILED")
    if 'ERROR' in content:
        print("Status: ERROR")

# Also check for the "Destroying test database" marker which implies completion
print("File size:", len(content), "bytes")