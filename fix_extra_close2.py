with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 765 (0-indexed: 764) - remove the extra )} after the records table
# Line 765 (0-indexed 764) currently has "                  )}"
# It should be removed because the records table already closed with ))}

if "                  )}" in lines[764]:
    lines[764] = ""

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed")