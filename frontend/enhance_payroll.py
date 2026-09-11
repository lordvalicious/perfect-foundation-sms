import re

# Read the original file
with open("frontend/src/pages/PayrollPage.jsx", "r") as f:
    content = f.read()

# Replace imports
content = content.replace(
    'import { Banknote, BadgePoundSterling, ReceiptText } from "lucide-react";',
    'import { Banknote, BadgePoundSterling, ReceiptText, Plus, Edit, Trash2, Loader2 } from "lucide-react";'
)

content = content.replace(
    'import { apiFetch, apiDownload, jsonHeaders } from "../api";',
    'import { apiFetch, apiDownload, jsonHeaders, buildErrorMessage } from "../api";'
)

# Add constants after MONTHS
content = content.replace(
    '''const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];''',
'''const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const STRUCTURE_STATUS_CHOICES = [
  { value: "active", label: "Active" },
  { value: "archived", label: "Archived" },
];

const COMPONENT_TYPES = [
  { value: "allowance", label: "Allowance" },
  { value: "deduction", label: "Deduction" },
];

const CALCULATION_TYPES = [
  { value: "fixed", label: "Fixed Amount" },
  { value: "percent_basic", label: "% of Basic" },
  { value: "percent_gross", label: "% of Gross" },
  { value: "percent_net", label: "% of Net" },
  { value: "per_day", label: "Per Day" },
  { value: "per_hour", label: "Per Hour" },
];

const RECORD_STATUS_CHOICES = [
  { value: "draft", label: "Draft" },
  { value: "processed", label: "Processed" },
  { value: "approved", label: "Approved" },
  { value: "paid", label: "Paid" },
  { value: "cancelled", label: "Cancelled" },
];''')

# Write the modified content back
with open("frontend/src/pages/PayrollPage.jsx", "w") as f:
    f.write(content)

print("Step 1 done - imports and constants added")