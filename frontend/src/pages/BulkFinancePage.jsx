import { useCallback, useEffect, useState } from "react";
import { Layers, X } from "lucide-react";
import { useAuth } from "../auth";
import { PageHeader, StateArea } from "./ui";
import { formatCurrency } from "./format";
import { apiFetch, jsonHeaders } from "../api";

const BULK_INVOICES_URL = "/api/finance/invoices/bulk/";
const BULK_PAYMENTS_URL = "/api/finance/payments/bulk/";
const CAMPUSES_URL = "/api/schools/campuses/";
const ACADEMIC_YEARS_URL = "/api/schools/academic-years/";
const CLASSES_URL = "/api/schools/classes/";
const CATEGORIES_URL = "/api/finance/categories/";
const FEE_STRUCTURES_URL = "/api/finance/fee-structures/";
const INVOICES_URL = "/api/finance/invoices/";

const PAYMENT_METHODS = [
  ["cash", "Cash"],
  ["bank", "Bank Transfer"],
  ["jazzcash", "JazzCash"],
  ["easypaisa", "EasyPaisa"],
  ["card", "Card"],
  ["other", "Other"],
];

const EMPTY_INVOICE_FORM = {
  campus: "",
  academic_year: "",
  class_obj: "",
  category: "",
  due_date: "",
  notes: "",
  skip_existing: true,
};

const EMPTY_PAYMENT_FORM = {
  payment_date: "",
  payment_method: "cash",
  reference: "",
  notes: "",
};

function BulkInvoiceModal({ onClose, onDone }) {
  const [form, setForm] = useState(EMPTY_INVOICE_FORM);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const [campuses, setCampuses] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [classes, setClasses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [, setStructures] = useState([]);

  useEffect(() => {
    const opts = { credentials: "include" };
    Promise.all([
      fetch(CAMPUSES_URL, opts).then((r) => (r.ok ? r.json() : [])),
      fetch(ACADEMIC_YEARS_URL, opts).then((r) => (r.ok ? r.json() : [])),
      fetch(CATEGORIES_URL, opts).then((r) => (r.ok ? r.json() : [])),
    ]).then(([c, y, cat]) => {
      setCampuses(Array.isArray(c) ? c : c.results || []);
      setAcademicYears(Array.isArray(y) ? y : y.results || []);
      setCategories(Array.isArray(cat) ? cat : cat.results || []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!form.campus) { setClasses([]); return; }
    fetch(`${CLASSES_URL}?campus=${form.campus}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setClasses(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
    setForm((p) => ({ ...p, class_obj: "", category: "" }));
  }, [form.campus]);

  useEffect(() => {
    if (!form.academic_year || !form.campus || !form.class_obj) { setStructures([]); return; }
    fetch(`${FEE_STRUCTURES_URL}?academic_year=${form.academic_year}&campus=${form.campus}&class_obj=${form.class_obj}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setStructures(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
  }, [form.academic_year, form.campus, form.class_obj]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((p) => ({ ...p, [name]: type === "checkbox" ? checked : value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setResult(null);

    const body = {
      academic_year: Number(form.academic_year),
      campus: Number(form.campus),
      class_obj: Number(form.class_obj),
      category: Number(form.category),
      due_date: form.due_date || undefined,
      notes: form.notes || undefined,
      skip_existing: form.skip_existing,
    };

    try {
      const data = await apiFetch(BULK_INVOICES_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(body),
      }, "Could not create bulk invoices.");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="teacher-modal event-modal">
        <div className="modal-header">
          <div>
            <h3>Bulk Invoice Creation</h3>
            <p>Generate invoices for all active enrollments in a class.</p>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}><X size={18} /></button>
        </div>

        {result ? (
          <div className="form-section">
            <div className="state-card success">
              <strong>{result.created} invoice(s) created successfully.</strong>
            </div>
            {result.skipped > 0 && (
              <div className="state-card">
                <strong>{result.skipped} enrollment(s) skipped.</strong>
                <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                  {result.skipped_details.map((s, i) => (
                    <li key={i}>{s.student}: {s.reason}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="modal-footer">
              <button className="primary-button" onClick={() => { onDone(); onClose(); }}>Done</button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-section">
              <h4>Select Target</h4>
              <div className="form-grid">
                <label>
                  Campus *
                  <select name="campus" value={form.campus} onChange={handleChange} required>
                    <option value="">Select campus</option>
                    {campuses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </label>

                <label>
                  Academic Year *
                  <select name="academic_year" value={form.academic_year} onChange={handleChange} required>
                    <option value="">Select year</option>
                    {academicYears.map((y) => <option key={y.id} value={y.id}>{y.name}</option>)}
                  </select>
                </label>

                <label>
                  Class *
                  <select name="class_obj" value={form.class_obj} onChange={handleChange} required disabled={!form.campus}>
                    <option value="">Select class</option>
                    {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </label>

                <label>
                  Fee Category *
                  <select name="category" value={form.category} onChange={handleChange} required>
                    <option value="">Select category</option>
                    {categories.filter((c) => c.status === "active").map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </label>

                <label>
                  Due Date
                  <input type="date" name="due_date" value={form.due_date} onChange={handleChange} />
                </label>

                <label>
                  Notes
                  <input name="notes" value={form.notes} onChange={handleChange} placeholder="Optional notes" />
                </label>

                <label className="checkbox-inline" style={{ alignSelf: "end" }}>
                  <input type="checkbox" name="skip_existing" checked={form.skip_existing} onChange={handleChange} />
                  Skip enrollments with existing invoices for this category
                </label>
              </div>
            </div>

            {error && <div className="state-card error"><strong>{error}</strong></div>}

            <div className="modal-footer">
              <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>Cancel</button>
              <button type="submit" className="primary-button" disabled={saving}>
                <Layers size={15} />
                {saving ? "Creating..." : "Create Bulk Invoices"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function BulkPaymentModal({ onClose, onDone }) {
  const [form, setForm] = useState(EMPTY_PAYMENT_FORM);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const [invoices, setInvoices] = useState([]);
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(true);

  const [campus, setCampus] = useState("");
  const [classObj, setClassObj] = useState("");
  const [campuses, setCampuses] = useState([]);
  const [classes, setClasses] = useState([]);

  useEffect(() => {
    fetch(CAMPUSES_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setCampuses(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!campus) { setClasses([]); return; }
    fetch(`${CLASSES_URL}?campus=${campus}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setClasses(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
    setClassObj("");
  }, [campus]);

  const loadInvoices = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams({ status: "issued", page: "1", page_size: "100" });
    if (campus) params.set("campus", campus);
    if (classObj) params.set("class", classObj);
    fetch(`${INVOICES_URL}?${params}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { results: [] }))
      .then((d) => {
        const rows = (d.results || []).filter((inv) => inv.balance > 0);
        setInvoices(rows);
        setSelected({});
      })
      .catch(() => setInvoices([]))
      .finally(() => setLoading(false));
  }, [campus, classObj]);

  useEffect(() => {
    loadInvoices();
  }, [loadInvoices]);

  const toggleSelect = (invoiceId) => {
    setSelected((p) => ({ ...p, [invoiceId]: !p[invoiceId] }));
  };

  const selectAll = () => {
    const all = {};
    invoices.forEach((inv) => { all[inv.id] = true; });
    setSelected(all);
  };

  const deselectAll = () => setSelected({});

  const selectedInvoices = invoices.filter((inv) => selected[inv.id]);
  const totalAmount = selectedInvoices.reduce((sum, inv) => sum + Number(inv.balance), 0);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (selectedInvoices.length === 0) return;

    setSaving(true);
    setError("");
    setResult(null);

    const payments = selectedInvoices.map((inv) => ({
      invoice: inv.id,
      amount: inv.balance,
      payment_method: form.payment_method,
      reference: form.reference,
      notes: form.notes,
    }));

    const body = {
      payments,
      payment_date: form.payment_date || undefined,
    };

    try {
      const data = await apiFetch(BULK_PAYMENTS_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(body),
      }, "Could not process bulk payments.");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="teacher-modal event-modal" style={{ maxWidth: 800 }}>
        <div className="modal-header">
          <div>
            <h3>Bulk Payment Collection</h3>
            <p>Record payments for multiple unpaid invoices at once.</p>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}><X size={18} /></button>
        </div>

        {result ? (
          <div className="form-section">
            <div className="state-card success">
              <strong>{result.created} payment(s) recorded successfully.</strong>
            </div>
            {result.errors > 0 && (
              <div className="state-card error">
                <strong>{result.errors} error(s) occurred.</strong>
                <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                  {result.error_details.map((e, i) => (
                    <li key={i}>#{e.index}: {e.reason}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="modal-footer">
              <button className="primary-button" onClick={() => { onDone(); onClose(); }}>Done</button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-section">
              <h4>Filter Invoices</h4>
              <div className="form-grid">
                <label>
                  Campus
                  <select value={campus} onChange={(e) => setCampus(e.target.value)}>
                    <option value="">All campuses</option>
                    {campuses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </label>
                <label>
                  Class
                  <select value={classObj} onChange={(e) => setClassObj(e.target.value)} disabled={!campus}>
                    <option value="">All classes</option>
                    {classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </label>
              </div>
            </div>

            <div className="form-section">
              <h4>Select Invoices to Pay</h4>
              <div className="filter-row" style={{ marginBottom: 8 }}>
                <button type="button" className="secondary-button" onClick={selectAll}>Select All</button>
                <button type="button" className="secondary-button" onClick={deselectAll}>Deselect All</button>
                <span style={{ marginLeft: "auto", fontWeight: 600 }}>
                  {selectedInvoices.length} selected &middot; {formatCurrency(totalAmount)}
                </span>
              </div>

              <StateArea loading={loading} error="">
                {invoices.length === 0 ? (
                  <div className="state-card">No unpaid invoices found.</div>
                ) : (
                  <div className="table-wrapper" style={{ maxHeight: 250, overflow: "auto" }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th style={{ width: 40 }}></th>
                          <th>INVOICE</th>
                          <th>STUDENT</th>
                          <th>AMOUNT</th>
                          <th>PAID</th>
                          <th>BALANCE</th>
                        </tr>
                      </thead>
                      <tbody>
                        {invoices.map((inv) => (
                          <tr key={inv.id}>
                            <td>
                              <input
                                type="checkbox"
                                checked={!!selected[inv.id]}
                                onChange={() => toggleSelect(inv.id)}
                              />
                            </td>
                            <td><strong>{inv.invoice_number}</strong></td>
                            <td>{inv.student_name || "-"}</td>
                            <td>{formatCurrency(inv.total_amount)}</td>
                            <td>{formatCurrency(inv.paid_amount)}</td>
                            <td><strong>{formatCurrency(inv.balance)}</strong></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </StateArea>
            </div>

            <div className="form-section">
              <h4>Payment Details</h4>
              <div className="form-grid">
                <label>
                  Payment Date
                  <input type="date" name="payment_date" value={form.payment_date} onChange={handleChange} />
                </label>
                <label>
                  Payment Method *
                  <select name="payment_method" value={form.payment_method} onChange={handleChange} required>
                    {PAYMENT_METHODS.map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Reference
                  <input name="reference" value={form.reference} onChange={handleChange} placeholder="Transaction reference" />
                </label>
                <label>
                  Notes
                  <input name="notes" value={form.notes} onChange={handleChange} placeholder="Optional notes" />
                </label>
              </div>
            </div>

            {error && <div className="state-card error"><strong>{error}</strong></div>}

            <div className="modal-footer">
              <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>Cancel</button>
              <button
                type="submit"
                className="primary-button"
                disabled={saving || selectedInvoices.length === 0}
              >
                <Layers size={15} />
                {saving ? "Processing..." : `Pay ${selectedInvoices.length} Invoice(s)`}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default function BulkFinancePage() {
  const { hasRole } = useAuth();
  const [showBulkInvoice, setShowBulkInvoice] = useState(false);
  const [showBulkPayment, setShowBulkPayment] = useState(false);
  const [, setRefreshKey] = useState(0);
  const canManage = hasRole(["super_admin", "admin", "accountant"]);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Finance / Bulk Operations"
        title="Bulk Operations"
        subtitle="Generate invoices and record payments for multiple students at once."
      />

      <div className="stats-grid">
        <div
          className="stat-card"
          style={{ cursor: canManage ? "pointer" : "default", opacity: canManage ? 1 : 0.5 }}
          onClick={() => canManage && setShowBulkInvoice(true)}
        >
          <div className="stat-icon"><Layers size={21} /></div>
          <div>
            <h3>Bulk Invoice Creation</h3>
            <p>Generate invoices for all students in a class based on fee structures.</p>
          </div>
        </div>

        <div
          className="stat-card"
          style={{ cursor: canManage ? "pointer" : "default", opacity: canManage ? 1 : 0.5 }}
          onClick={() => canManage && setShowBulkPayment(true)}
        >
          <div className="stat-icon"><Layers size={21} /></div>
          <div>
            <h3>Bulk Payment Collection</h3>
            <p>Record payments for multiple unpaid invoices at once.</p>
          </div>
        </div>
      </div>

      {showBulkInvoice && (
        <BulkInvoiceModal
          onClose={() => setShowBulkInvoice(false)}
          onDone={() => setRefreshKey((k) => k + 1)}
        />
      )}

      {showBulkPayment && (
        <BulkPaymentModal
          onClose={() => setShowBulkPayment(false)}
          onDone={() => setRefreshKey((k) => k + 1)}
        />
      )}
    </section>
  );
}
