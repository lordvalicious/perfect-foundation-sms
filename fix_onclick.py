with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the onClick handler - remove braces to avoid confusion with JSX expression boundary
old = '''                              className="table-action"
                  onClick={() =>
                    apiDownload(
                      `${BASE}records/${record.id}/payslip.pdf`,
                      `payslip_${record.teacher_number || record.id}_${record.year}_${String(record.month).padStart(2, "0")}.pdf`
                    ).catch(() => alert("Could not download payslip."))
                            title="Download Payslip"
                          >
                              Payslip PDF
                            </button>'''

new = '''                              className="table-action"
                  onClick={() =>
                    apiDownload(
                      `${BASE}records/${record.id}/payslip.pdf`,
                      `payslip_${record.teacher_number || record.id}_${record.year}_${String(record.month).padStart(2, "0")}.pdf`
                    ).catch(() => alert("Could not download payslip."))
                    title="Download Payslip"
                  >
                    Payslip PDF
                  </button>'''

content = content.replace(old, new)

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed")