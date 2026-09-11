with open("frontend/src/pages/PayrollPage.jsx", "r") as f:
    content = f.read()

# Fix the payslips table header
old = '''{tab === "payslips" && (
                      rows.map((payslip) => (
                    <tr>
                      <th>TEACHER</th>
                      <th>PERIOD</th>
                      <th>ISSUED AT</th>
                    </tr>
                  )}'''

new = '''{tab === "payslips" && (
                    <tr>
                      <th>TEACHER</th>
                      <th>PERIOD</th>
                      <th>ISSUED AT</th>
                    </tr>
                  )}'''

content = content.replace(old, new)

with open("frontend/src/pages/PayrollPage.jsx", "w") as f:
    f.write(content)

print('Fixed')