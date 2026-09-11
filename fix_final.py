with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 1529 (0-indexed: 1528) - change )))} to )}
if ")))}" in lines[1528]:
    lines[1528] = lines[1528].replace(")))", ")")
    print("Fixed line 1529")

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done")