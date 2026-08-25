import { useCallback, useEffect, useState } from "react";
import { GraduationCap, Plus } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/alumni/";

export default function AlumniPage() {
  const [rows, setRows] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [batchYear, setBatchYear] = useState("");
  const [campusFilter, setCampusFilter] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState({
    full_name: "",
    batch_year: new Date().getFullYear(),
    campus: "",
    email: "",
    phone: "",
    occupation: "",
    organization: "",
    city: "",
    notes: "",
  });

  useEffect(() => {
    fetch("/api/schools/campuses/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setCampuses(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (batchYear) params.append("batch_year", batchYear);
    if (campusFilter) params.append("campus", campusFilter);

    apiFetch(`${BASE}?${params.toString()}`)
      .then((data) => setRows(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, batchYear, campusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");

    apiFetch(BASE, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setShowForm(false);
        load();
      })
      .catch((err) => setFormError(err.message))
      .finally(() => setSaving(false));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Alumni"
        title="Alumni Network"
        subtitle="Stay connected with former students."
        action={
          <button
            type="button"
            className="primary-button"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus size={15} />
            Add Alumni
          </button>
        }
      />

      {showForm && (
        <div className="panel">
          <PanelHeader title="Add alumni record" />
          <form onSubmit={submit} className="filter-row">
            <input
              required
              placeholder="Full name *"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />

            <input
              required
              type="number"
              placeholder="Batch year *"
              value={form.batch_year}
              onChange={(e) => setForm({ ...form, batch_year: e.target.value })}
            />

            <select
              value={form.campus}
              onChange={(e) => setForm({ ...form, campus: e.target.value })}
            >
              <option value="">Campus (optional)</option>
              {campuses.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            <input
              placeholder="Occupation"
              value={form.occupation}
              onChange={(e) => setForm({ ...form, occupation: e.target.value })}
            />

            <input
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />

            <input
              placeholder="Phone"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />

            <input
              placeholder="City"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
            />

            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
          </form>
          {formError && <div className="state-card error">{formError}</div>}
        </div>
      )}

      <div className="panel">
        <PanelHeader title="Alumni" subtitle={`${rows.length} records`} />

        <StateArea loading={loading} error={error} onRetry={load}>
          <div className="filter-row">
            <input
              className="filter-search"
              placeholder="Search by name, organization or city..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <input
              type="number"
              placeholder="Batch year"
              value={batchYear}
              onChange={(e) => setBatchYear(e.target.value)}
            />

            <select
              value={campusFilter}
              onChange={(e) => setCampusFilter(e.target.value)}
            >
              <option value="">All campuses</option>
              {campuses.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          {rows.length === 0 ? (
            <div className="empty-state">
              <GraduationCap size={42} />
              <h3>No alumni records</h3>
              <p>Add former students to build the network.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Batch</th>
                    <th>Campus</th>
                    <th>Occupation</th>
                    <th>Organization</th>
                    <th>City</th>
                    <th>Contact</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td><strong>{row.full_name}</strong></td>
                      <td>{row.batch_year}</td>
                      <td>{row.campus_name || "—"}</td>
                      <td>{row.occupation || "—"}</td>
                      <td>{row.organization || "—"}</td>
                      <td>{row.city || "—"}</td>
                      <td>
                        {row.email && <small style={{ display: "block" }}>{row.email}</small>}
                        {row.phone && <small>{row.phone}</small>}
                        {!row.email && !row.phone && "—"}
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
