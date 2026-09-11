with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix the payslips conditional - remove extra ( after &&
for i, line in enumerate(lines):
    if '{tab === "payslips" && (' in line:
        lines[i] = line.replace('{tab === "payslips" && (', '{tab === "payslips" && ')
        print(f'Fixed line {i+1}')

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done")