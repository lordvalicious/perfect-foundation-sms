with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 1225 (0-indexed: 1224) - change )} to }
if lines[1224].rstrip() == "                  )}":
    lines[1224] = "                  }" + "\n"
    print("Fixed line 1225")

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done")