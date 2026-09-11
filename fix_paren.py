with open("frontend/src/pages/PayrollPage.jsx", "r") as f:
    lines = f.readlines()

# Fix line 784 (0-indexed: 783) - change ))} to )))}
lines[783] = lines[783].replace(")}", ")))}")

with open("frontend/src/pages/PayrollPage.jsx", "w") as f:
    f.writelines(lines)

print("Fixed")