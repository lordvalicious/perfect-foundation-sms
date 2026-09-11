with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the title attribute placement
old = ''').catch(() => alert("Could not download payslip."))
                              title="Download Payslip"
                            >
                              Payslip PDF
                            </button>'''

new = ''').catch(() => alert("Could not download payslip."))
                              title="Download Payslip"
                            >
                              Payslip PDF
                            </button>'''

content = content.replace(old, new)

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed")