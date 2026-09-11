import re

# Read the current file
with open("frontend/src/pages/PayrollPage.jsx", "r") as f:
    content = f.read()

# Find the end of loadReferenceData useEffect and add state/handlers after it
# Find the end of loadReferenceData useEffect
old_useeffect = """  useEffect(() => {
    loadReferenceData();
  }, [loadReferenceData]);

  const load = useCallback("""

new_useeffect = """  useEffect(() => {
    loadReferenceData();
  }, [loadReferenceData]);

  // Reference data for forms
  const [employees, setEmployees] = useState([]);
  const [payrollPeriods, setPayrollPeriods] = useState([]);
  const [salaryStructures, setSalaryStructures] = useState([]);

  // Modals
  const [modal, setModal] = useState(null); // null | { type: 'structure'|'record', mode: 'create'|'edit', item }
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  // Structure form state
  const [structureForm, setStructureForm] = useState({
    employee: "",
    name: "",
    code: "",
    basic_salary: "",
    effective_date: "",
    status: "active",
    components: [],
  });

  // Record form state
  const [recordForm, setRecordForm] = useState({
    employee: "",
    campus: "",
    salary_structure: "",
    payroll_period: "",
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    working_days: "",
    paid_days: "",
    leave_days: "0",
    overtime_hours: "0",
    overtime_amount: "0",
    status: "draft",
  });

  // Load reference data
  const loadReferenceData = useCallback(async () => {
    try {
      const [empRes, periodRes, structRes] = await Promise.all([
        fetch("/api/hr/employees/", { credentials: "include" }),
        fetch("/api/hr/payroll-periods/", { credentials: "include" }),
        fetch("/api/payroll/salary-structures/", { credentials: "include" }),
      ]);

      if (empRes.ok) {
        const empData = await empRes.json();
        setEmployees(Array.isArray(empData) ? empData : (empData.results || []));
      }
      if (periodRes.ok) {
        const periodData = await periodRes.json();
        setPayrollPeriods(Array.isArray(periodData) ? periodData : (periodData.results || []));
      }
      if (structRes.ok) {
        const structData = await structRes.json();
        setSalaryStructures(Array.isArray(structData) ? structData : (structData.results || []));
      }
    } catch (err) {
      console.warn("Failed to load reference data:", err);
    }
  }, []);

  useEffect(() => {
    loadReferenceData();
  }, [loadReferenceData]);

  const load = useCallback("""

content = content.replace(
    "  useEffect(() => {\n    loadReferenceData();\n  }, [loadReferenceData]);\n\n  const load = useCallback(",
    new_useeffect
)

# Write the modified content back
with open("frontend/src/pages/PayrollPage.jsx", "w") as f:
    f.write(content)

print("Step 2 done - state and reference data added")