import { useCallback, useEffect, useState } from "react";
import { HeartPulse, Pencil, Plus, Trash2, Users, ClipboardList } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/health-records/records/";

const TYPES = [
  ["checkup", "General Checkup"],
  ["illness", "Illness"],
  ["injury", "Injury / First Aid"],
  ["allergy", "Allergy Note"],
  ["vaccination", "Vaccination"],
  ["screening", "Screening"],
  ["other", "Other"],
];

export default function HealthRecordsPage() {
  const [rows, setRows] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [studentFilter, setStudentFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState({
    student: "",
    campus: "",
    record_type: "checkup",
    record_date: new Date().toISOString().slice(0, 10),
    notes: "",
    height_cm: "",
    weight_kg: "",
    temperature_c: "",
    treated_by: "",
  });

  useEffect(() => {
    fetch("/api/students/?page_size=1000", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { results: [] }))
      .then((json) => setStudents(json.results || []))
      .catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();
    if (studentFilter) params.append("student", studentFilter);
    if (typeFilter) params.append("type", typeFilter);

    apiFetch(`${BASE}?${params.toString()}`)
      .then((data) => setRows(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [studentFilter, typeFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const openEdit = (row) => {
    setEditing(row);
    setShowForm(true);
    setForm({
      student: row.student ?? "",
      campus: row.campus ?? "",
      record_type: row.record_type ?? "checkup",
      record_date: row.record_date ?? new Date().toISOString().slice(0, 10),
      notes: row.notes ?? "",
      height_cm: row.height_cm ?? "",
      weight_kg: row.weight_kg ?? "",
      temperature_c: row.temperature_c ?? "",
      treated_by: row.treated_by ?? "",
    });
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete this health record? This cannot be undone.`)) return;

    setSaving(true);
    setFormError("");

    try {
      await apiFetch(
        `${BASE}${row.id}/`,
        { method: "DELETE" },
        "Could not delete the health record."
      );
      load();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const submitRecord = (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");

    const isEditing = Boolean(editing);

    apiFetch(isEditing ? `${BASE}${editing.id}/` : BASE, {
      method: isEditing ? "PATCH" : "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setEditing(null);
        setShowForm(false);
        load();
      })
      .catch((err) => setFormError(err.message))
      .finally(() => setSaving(false));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Health Records"
        title="Health Records"
        subtitle="Clinic visits, allergies, vaccinations and screenings."
        hero
        stats={[
          {
            label: "Health records",
            value: rows.length,
            icon: <HeartPulse size={18} />,
            sub: "total records",
          },
          {
            label: "Students",
            value: students.length,
            icon: <Users size={18} />,
            sub: "with clinic profiles",
          },
          {
            label: "Record types",
            value: TYPES.length,
            icon: <ClipboardList size={18} />,
            sub: "categories tracked",
          },
        ]}
        action={
          <button
            type="button"
            className="primary-button"
            onClick={() => {
              setEditing(null);
              setShowForm((v) => !v);
            }}
          >
            <Plus size={15} />
            New Record
          </button>
        }
      />

      {showForm && (
        <div className="panel">
          <PanelHeader title={editing ? "Edit health record" : "Add health record"} subtitle="Campus follows the student's active enrollment" />
          <form onSubmit={submitRecord} className="filter-row">
            <select
              required
              value={form.student}
              onChange={(e) => setForm({ ...form, student: e.target.value })}
            >
              <option value="">Student...</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.full_name} ({s.admission_number})
                </option>
              ))}
            </select>

            <select
              value={form.record_type}
              onChange={(e) => setForm({ ...form, record_type: e.target.value })}
            >
              {TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>

            <input
              type="date"
              required
              value={form.record_date}
              onChange={(e) => setForm({ ...form, record_date: e.target.value })}
            />

            <input
              placeholder="Height (cm)"
              type="number"
              step="0.1"
              value={form.height_cm}
              onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
            />

            <input
              placeholder="Weight (kg)"
              type="number"
              step="0.1"
              value={form.weight_kg}
              onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
            />

            <input
              placeholder="Temp (°C)"
              type="number"
              step="0.1"
              value={form.temperature_c}
              onChange={(e) =>
                setForm({ ...form, temperature_c: e.target.value })
              }
            />

            <input
              placeholder="Treated by"
              value={form.treated_by}
              onChange={(e) => setForm({ ...form, treated_by: e.target.value })}
            />

            <textarea
              placeholder="Notes"
              rows={2}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />

            <button
              type="button"
              className="secondary-button"
              onClick={() => { setEditing(null); setShowForm(false); }}
            >
              Cancel
            </button>
            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : editing ? "Save Changes" : "Save"}
            </button>
          </form>
          {formError && <div className="state-card error">{formError}</div>}
        </div>
      )}

      <div className="panel">
        <PanelHeader title="Records" subtitle={`${rows.length} entries`} />

        <StateArea loading={loading} error={error} onRetry={load}>
          <div className="filter-row">
            <select
              value={studentFilter}
              onChange={(e) => setStudentFilter(e.target.value)}
            >
              <option value="">All students</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.full_name} ({s.admission_number})
                </option>
              ))}
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All types</option>
              {TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {rows.length === 0 ? (
            <div className="empty-state">
              <HeartPulse size={42} />
              <h3>No health records</h3>
              <p>Nothing recorded yet for this filter.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Student</th>
                    <th>Type</th>
                    <th>Height</th>
                    <th>Weight</th>
                    <th>BMI</th>
                    <th>Temp</th>
                    <th>Treated By</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td>{row.record_date}</td>
                      <td>
                        <strong>{row.student_name}</strong>
                        <small style={{ display: "block" }}>
                          {row.admission_number} · {row.campus_name}
                        </small>
                      </td>
                      <td>{row.record_type_display}</td>
                      <td>{row.height_cm ? `${row.height_cm} cm` : "—"}</td>
                      <td>{row.weight_kg ? `${row.weight_kg} kg` : "—"}</td>
                      <td>{row.bmi ?? "—"}</td>
                      <td>{row.temperature_c ? `${row.temperature_c}°` : "—"}</td>
                      <td>{row.treated_by || "—"}</td>
                      <td style={{ whiteSpace: "nowrap" }}>
                        <button
                          type="button"
                          className="table-action"
                          onClick={() => openEdit(row)}
                        >
                          <Pencil size={13} /> Edit
                        </button>
                        <button
                          type="button"
                          className="table-action danger"
                          onClick={() => handleDelete(row)}
                        >
                          <Trash2 size={13} /> Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
