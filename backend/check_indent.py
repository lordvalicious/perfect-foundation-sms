import sys

with open(r'C:\Users\Ryuk\AppData\Local\Temp\opencode\smoke_round6.py', 'rb') as f:
    data = f.read()
lines = data.splitlines()
for i, line in enumerate(lines):
    if i >= 95 and i < 105:
        print(f"Line {i+1}: repr={repr(line)}")
        if i == 98:  # 0-indexed line 99
            print(f"  >> LINE 99: repr={repr(line)}")