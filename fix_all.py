with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Remove any "                  )}" lines that appear immediately after "                    ))}" lines
new_lines = []
i = 0
while i < len(lines):
    line = lines[i].rstrip('\n')
    # Check if current line is "                    ))}" and next line is "                  )}"
    if i + 1 < len(lines) and lines[i].rstrip() == "                    ))}" and lines[i+1].rstrip() == "                  )}":
        # Skip the next line (the extra )})
        i += 1
        continue
    new_lines.append(lines[i])
    i += 1

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.write('\n'.join(new_lines) + '\n')

print("Fixed")