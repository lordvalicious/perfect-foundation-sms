with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    if lines[i].rstrip() == "                    ))":
        # Look ahead for the next non-empty line
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and lines[j].rstrip() == "                  )}":
            # Replace from i to j with a single )} line
            new_lines.append("                  )}" + "\n")
            i = j + 1
            print("Fixed payslips tbody closing")
            continue
    new_lines.append(lines[i])
    i += 1

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done")