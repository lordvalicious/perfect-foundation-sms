with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix the payslips tbody closing - combine the two lines into one )} line
new_lines = []
i = 0
while i < len(lines):
    if lines[i].rstrip() == "                    ))" and i + 1 < len(lines) and lines[i+1].rstrip() == "                  )}":
        # Replace both lines with a single )} line
        new_lines.append("                  )}" + "\n")
        i += 2
        print("Fixed payslips tbody closing")
    else:
        new_lines.append(lines[i])
        i += 1

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done")