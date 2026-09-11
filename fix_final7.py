with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 1529 (0-indexed: 1528) - change )))} to )}
if lines[1528].rstrip() == "                  )))":
    lines[1528] = "                  )}" + "\n"
    print("Fixed line 1529")

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done")