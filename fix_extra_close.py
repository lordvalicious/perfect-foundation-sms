with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 662 (0-indexed: 661) - remove the extra )} after the structure table
# Line 662 (0-indexed 661) currently has "                  )}"
# It should be removed because the structure table already closed with ))}

if "                  )}" in lines[661]:
    lines[661] = ""

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed")