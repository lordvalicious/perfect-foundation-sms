with open('backend/apps/students/test_student_transfer_f12.py', 'rb') as f:
    content = f.read()
# Replace CRLF with LF
content = content.replace(b'\r\n', b'\n')
# Split into lines
lines = content.split(b'\n')
# Strip trailing whitespace from each line (including any remaining \r)
lines = [line.rstrip() for line in lines]
# Rejoin with LF
content = b'\n'.join(lines) + b'\n'
with open('backend/apps/students/test_student_transfer_f12.py', 'wb') as f:
    f.write(content)
print('Fixed')