with open('backend/apps/exams/models.py', 'r') as f:
    lines = f.readlines()

# Find the line number of is_pass
for i, line in enumerate(lines):
    if 'is_pass = models.BooleanField(default=False)' in line and i > 210 and i < 230:
        print(f'Found is_pass at line {i+1}')
        # Insert is_locked after this line (i+1) and before the next line
        # Insert after line i
        new_lines = lines[:i+1] + [
            '\n',
            '    is_locked = models.BooleanField(\n',
            '        default=False,\n',
            "        help_text='Prevents editing of this result record.',\n",
            '    )\n',
        ] + lines[i+1:]
        break

with open('backend/apps/exams/models.py', 'w') as f:
    f.writelines(new_lines)
print('Added is_locked field')