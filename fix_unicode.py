with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 784 (0-indexed: 783) - ensure it's just ")}" with proper encoding
lines[783] = ")}" + "\n"

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed")