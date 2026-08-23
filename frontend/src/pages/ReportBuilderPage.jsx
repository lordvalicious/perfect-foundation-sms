import { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  Copy,
  FileText,
  Play,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";
import { apiFetch, jsonHeaders } from "../api";
import { PageHeader, PanelHeader, StateArea, StatusBadge, EmptyState } from "./ui";
import { formatCurrency } from "./format";

const TEMPLATES_URL = "/api/reports/templates/";
const GENERATE_URL = "/api/reports/generate/";

const REPORT_TYPES = [
  { value: "enrollment", label: "Enrollment Report", description: "Students grouped by campus and class." },
  { value: "attendance", label: "Attendance Report", description: "Attendance rates by campus and class." },
  { value: "results", label: "Results Report", description: "Exam results with pass/fail stats." },
  { value: "fees", label: "Fees Report", description: "Fee collection and outstanding amounts." },
  { value: "staff", label: "Staff Report", description: "Staff distribution by campus and designation." },
  { value: "subjects", label: "Subject Performance", description: "Per-subject stats for an exam." },
  { value: "payments", label: "Payment Methods", description: "Payments grouped by method and campus." },
  { value: "student_status", label: "Student Status", description: "Students by status across campuses." },
  { value: "fee_categories", label: "Fee Categories", description: "Invoiced amounts per fee category." },
];

const FILTER_OPTIONS = {
  enrollment: [
    { key: "academic_year", label: "Academic Year", type: "number" },
  ],
  attendance: [
    { key: "month", label: "Month", type: "number", placeholder: "1-12" },
    { key: "year", label: "Year", type: "number", placeholder: "2026" },
    { key: "class_obj", label: "Class ID", type: "number" },
  ],
  results: [
    { key: "exam", label: "Exam ID", type: "number", required: true },
  ],
  fees: [
    { key: "start_date", label: "Start Date", type: "date" },
    { key: "end_date", label: "End Date", type: "date" },
    { key: "payment_method", label: "Payment Method", type: "text" },
  ],
  staff: [],
  subjects: [
    { key: "exam", label: "Exam ID", type: "number", required: true },
  ],
  payments: [
    { key: "start_date", label: "Start Date", type: "date" },
    { key: "end_date", label: "End Date", type: "date" },
  ],
  student_status: [],
  fee_categories: [],
};

function TemplateFormModal({ template, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: template?.name || "",
    description: template?.description || "",
    report_type: template?.report_type || "enrollment",
    filters: template?.filters || {},
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const handleFilterChange = (key, value) => {
    setForm((p) => ({
      ...p,
      filters: { ...p.filters, [key]: value },
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    const body = {
      name: form.name,
      description: form.description,
      report_type: form.report_type,
      filters: form.filters,
    };

    try {
      const url = template ? `${TEMPLATES_URL}${template.id}/` : TEMPLATES_URL;
      const method = template ? "PUT" : "POST";

      await apiFetch(url, {
        method,
        headers: jsonHeaders(),
        body: JSON.stringify(body),
      }, "Failed to save template.");

      onSaved();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const currentFilters = FILTER_OPTIONS[form.report_type] || [];

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="teacher-modal">
        <div className="modal-header">
          <div>
            <h3>{template ? "Edit Template" : "Create Report Template"}</h3>
            <p>Configure a reusable report with filters.</p>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h4>Basic Info</h4>
            <div className="form-grid">
              <label>
                Template Name *
                <input name="name" value={form.name} onChange={handleChange} required placeholder="My report template" />
              </label>
              <label>
                Report Type *
                <select name="report_type" value={form.report_type} onChange={handleChange} required>
                  {REPORT_TYPES.map((rt) => (
                    <option key={rt.value} value={rt.value}>{rt.label}</option>
                  ))}
                </select>
              </label>
              <label style={{ gridColumn: "1 / -1" }}>
                Description
                <input name="description" value={form.description} onChange={handleChange} placeholder="Optional description" />
              </label>
            </div>
          </div>

          {currentFilters.length > 0 && (
            <div className="form-section">
              <h4>Default Filters</h4>
              <div className="form-grid">
                {currentFilters.map((f) => (
                  <label key={f.key}>
                    {f.label} {f.required && "*"}
                    <input
                      type={f.type}
                      value={form.filters[f.key] || ""}
                      onChange={(e) => handleFilterChange(f.key, e.target.value)}
                      placeholder={f.placeholder || ""}
                      required={f.required}
                    />
                  </label>
                ))}
              </div>
            </div>
          )}

          {error && <div className="state-card error"><strong>{error}</strong></div>}

          <div className="modal-footer">
            <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>Cancel</button>
            <button type="submit" className="primary-button" disabled={saving}>
              <Save size={15} />
              {saving ? "Saving..." : "Save Template"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ReportPreviewModal({ reportType, filters, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    apiFetch(GENERATE_URL, {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ report_type: reportType, filters }),
    }, "Failed to generate report.")
      .then((d) => { if (!cancelled) setData(d); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [reportType, filters]);

  const handleExportCSV = () => {
    const params = new URLSearchParams(filters);
    window.open(`/api/reports/${reportType}/?${params}&format=csv`, "_blank");
  };

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="teacher-modal event-modal" style={{ maxWidth: 900, maxHeight: "80vh", overflow: "auto" }}>
        <div className="modal-header">
          <div>
            <h3>Report: {REPORT_TYPES.find((r) => r.value === reportType)?.label || reportType}</h3>
          </div>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <StateArea loading={loading} error={error}>
          {data && (
            <div className="form-section">
              <div className="filter-row" style={{ marginBottom: 12 }}>
                <button className="secondary-button" onClick={handleExportCSV}>
                  <FileText size={14} /> Export CSV
                </button>
              </div>

              {reportType === "enrollment" && (
                <>
                  <div className="stats-grid" style={{ marginBottom: 16 }}>
                    <div className="stat-card"><h3>{data.total_students}</h3><p>Total Students</p></div>
                    <div className="stat-card"><h3>{data.total_classes}</h3><p>Total Classes</p></div>
                    <div className="stat-card"><h3>{data.average_class_size}</h3><p>Avg Class Size</p></div>
                  </div>
                  {data.classes?.length > 0 && (
                    <div className="table-wrapper">
                      <table className="data-table">
                        <thead><tr><th>Campus</th><th>Class</th><th>Total</th><th>Male</th><th>Female</th></tr></thead>
                        <tbody>
                          {data.classes.map((row, i) => (
                            <tr key={i}><td>{row.campus}</td><td>{row.class}</td><td>{row.total}</td><td>{row.male}</td><td>{row.female}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {reportType === "attendance" && (
                <>
                  <div className="stats-grid" style={{ marginBottom: 16 }}>
                    <div className="stat-card"><h3>{data.overall_attendance_rate}%</h3><p>Overall Attendance Rate</p></div>
                  </div>
                  {data.classes?.length > 0 && (
                    <div className="table-wrapper">
                      <table className="data-table">
                        <thead><tr><th>Campus</th><th>Class</th><th>Present</th><th>Absent</th><th>Late</th><th>Leave</th><th>Rate</th></tr></thead>
                        <tbody>
                          {data.classes.map((row, i) => (
                            <tr key={i}><td>{row.campus}</td><td>{row.class}</td><td>{row.present}</td><td>{row.absent}</td><td>{row.late}</td><td>{row.leave}</td><td>{row.attendance_rate}%</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {reportType === "fees" && data.summary && (
                <>
                  <div className="stats-grid" style={{ marginBottom: 16 }}>
                    <div className="stat-card"><h3>{formatCurrency(data.summary.total_invoiced)}</h3><p>Total Invoiced</p></div>
                    <div className="stat-card"><h3>{formatCurrency(data.summary.total_collected)}</h3><p>Collected</p></div>
                    <div className="stat-card"><h3>{formatCurrency(data.summary.total_outstanding)}</h3><p>Outstanding</p></div>
                    <div className="stat-card"><h3>{data.summary.collection_rate}%</h3><p>Collection Rate</p></div>
                  </div>
                </>
              )}

              {reportType === "staff" && (
                <>
                  <div className="stats-grid" style={{ marginBottom: 16 }}>
                    <div className="stat-card"><h3>{data.total_staff}</h3><p>Total Staff</p></div>
                  </div>
                  {data.groups?.length > 0 && (
                    <div className="table-wrapper">
                      <table className="data-table">
                        <thead><tr><th>Campus</th><th>Designation</th><th>Count</th></tr></thead>
                        <tbody>
                          {data.groups.map((row, i) => (
                            <tr key={i}><td>{row.campus}</td><td>{row.designation}</td><td>{row.count}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {reportType === "results" && data.summary && (
                <>
                  <div className="stats-grid" style={{ marginBottom: 16 }}>
                    <div className="stat-card"><h3>{data.summary.total_students}</h3><p>Total Students</p></div>
                    <div className="stat-card"><h3>{data.summary.pass_rate}%</h3><p>Pass Rate</p></div>
                    <div className="stat-card"><h3>{data.summary.average_percentage}%</h3><p>Average</p></div>
                  </div>
                  {data.students?.length > 0 && (
                    <div className="table-wrapper" style={{ maxHeight: 300, overflow: "auto" }}>
                      <table className="data-table">
                        <thead><tr><th>Student</th><th>Adm#</th><th>%</th><th>Grade</th><th>Result</th></tr></thead>
                        <tbody>
                          {data.students.map((row, i) => (
                            <tr key={i}><td>{row.student}</td><td>{row.admission_number}</td><td>{row.percentage}%</td><td>{row.grade}</td><td><StatusBadge status={row.result === "Pass" ? "active" : "inactive"} /></td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {reportType === "student_status" && (
                <>
                  {data.statuses?.length > 0 && (
                    <div className="table-wrapper">
                      <table className="data-table">
                        <thead><tr><th>Status</th><th>Count</th></tr></thead>
                        <tbody>
                          {data.statuses.map((row, i) => (
                            <tr key={i}><td><StatusBadge status={row.status === "Active" ? "active" : row.status === "Inactive" ? "inactive" : "other"} /></td><td>{row.count}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {reportType === "fee_categories" && data.summary && (
                <>
                  <div className="stats-grid" style={{ marginBottom: 16 }}>
                    <div className="stat-card"><h3>{formatCurrency(data.summary.total_invoiced)}</h3><p>Total Invoiced</p></div>
                  </div>
                  {data.by_category?.length > 0 && (
                    <div className="table-wrapper">
                      <table className="data-table">
                        <thead><tr><th>Category</th><th>Amount</th><th>Items</th></tr></thead>
                        <tbody>
                          {data.by_category.map((row, i) => (
                            <tr key={i}><td>{row.category}</td><td>{formatCurrency(row.total_invoiced)}</td><td>{row.item_count}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}

              {reportType === "payments" && data.by_method?.length > 0 && (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead><tr><th>Method</th><th>Amount</th><th>Count</th></tr></thead>
                    <tbody>
                      {data.by_method.map((row, i) => (
                        <tr key={i}><td>{row.method}</td><td>{formatCurrency(row.total)}</td><td>{row.count}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {reportType === "subjects" && data.subjects?.length > 0 && (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead><tr><th>Subject</th><th>Students</th><th>Avg %</th><th>Pass Rate</th></tr></thead>
                    <tbody>
                      {data.subjects.map((row, i) => (
                        <tr key={i}><td>{row.subject}</td><td>{row.students}</td><td>{row.average_percentage}%</td><td>{row.pass_rate}%</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {!data && <p>No data returned.</p>}
            </div>
          )}
        </StateArea>
      </div>
    </div>
  );
}

export default function ReportBuilderPage() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [previewTemplate, setPreviewTemplate] = useState(null);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch(TEMPLATES_URL, {}, "Failed to load templates.");
      setTemplates(Array.isArray(data) ? data : []);
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleDelete = async (template) => {
    if (!window.confirm(`Delete template "${template.name}"?`)) return;
    try {
      await apiFetch(`${TEMPLATES_URL}${template.id}/`, { method: "DELETE" }, "Failed to delete.");
      fetchTemplates();
    } catch {
      // ignore
    }
  };

  const handleDuplicate = async (template) => {
    try {
      await apiFetch(TEMPLATES_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify({
          name: `${template.name} (Copy)`,
          description: template.description,
          report_type: template.report_type,
          filters: template.filters,
        }),
      }, "Failed to duplicate.");
      fetchTemplates();
    } catch {
      // ignore
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Reports / Builder"
        title="Report Builder"
        subtitle="Create, save and generate custom report configurations."
        action={
          <button className="primary-button" onClick={() => { setEditingTemplate(null); setShowForm(true); }}>
            <Plus size={15} /> New Template
          </button>
        }
      />

      <div className="panel">
        <PanelHeader
          title="Saved Templates"
          subtitle="report templates"
          count={templates.length}
        />

        <StateArea loading={loading}>
          {templates.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="No templates yet"
              message="Create your first report template to get started."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>NAME</th>
                    <th>REPORT TYPE</th>
                    <th>FILTERS</th>
                    <th>CREATED</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <strong>{t.name}</strong>
                        {t.description && <><br /><small style={{ opacity: 0.6 }}>{t.description}</small></>}
                      </td>
                      <td><StatusBadge status={t.report_type} /></td>
                      <td>
                        {Object.keys(t.filters || {}).length > 0
                          ? Object.entries(t.filters).map(([k, v]) => v ? <div key={k}><small><strong>{k}:</strong> {v}</small></div> : null)
                          : <small style={{ opacity: 0.5 }}>No filters</small>
                        }
                      </td>
                      <td><small>{new Date(t.created_at).toLocaleDateString()}</small></td>
                      <td>
                        <div className="action-group">
                          <button className="table-action" onClick={() => setPreviewTemplate(t)}>
                            <Play size={14} /> Run
                          </button>
                          <button className="table-action" onClick={() => { setEditingTemplate(t); setShowForm(true); }}>
                            Edit
                          </button>
                          <button className="table-action" onClick={() => handleDuplicate(t)}>
                            <Copy size={14} /> Copy
                          </button>
                          <button className="table-action danger" onClick={() => handleDelete(t)}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>

      {showForm && (
        <TemplateFormModal
          template={editingTemplate}
          onClose={() => { setShowForm(false); setEditingTemplate(null); }}
          onSaved={fetchTemplates}
        />
      )}

      {previewTemplate && (
        <ReportPreviewModal
          reportType={previewTemplate.report_type}
          filters={previewTemplate.filters || {}}
          onClose={() => setPreviewTemplate(null)}
        />
      )}
    </section>
  );
}
