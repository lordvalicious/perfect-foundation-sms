import { useCallback, useEffect, useState } from "react";
import {
  AlertOctagon,
  Plus,
  ShieldAlert,
  Gavel,
  CircleCheck,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const INCIDENTS_URL = "/api/discipline/incidents/";
const SUMMARY_URL = "/api/discipline/summary/";

const SEVERITY_OPTIONS = ["minor", "moderate", "major"];
const STATUS_OPTIONS = ["open", "action_taken", "resolved"];
const ACTION_TYPES = [
  ["verbal_warning", "Verbal Warning"],
  ["written_warning", "Written Warning"],
  ["detention", "Detention"],
  ["suspension", "Suspension"],
  ["parent_meeting", "Parent Meeting"],
  ["counselling", "Counselling Referral"],
  ["other", "Other"],
];

function severityBadge(severity) {
  const map = {
    minor: "badge-green",
    moderate: "badge-amber",
    major: "badge-red",
  };
  return map[severity] || "";
}

export default function DisciplinePage() {
  const [incidents, setIncidents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [students, setStudents] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    student: "",
    campus: "",
    title: "",
    description: "",
    location: "",
    incident_date: new Date().toISOString().slice(0, 10),
    severity: "minor",
  });

  const [selected, setSelected] = useState(null);
  const [actions, setActions] = useState([]);
  const [actionForm, setActionForm] = useState({
    action_type: "verbal_warning",
    details: "",
    action_date: new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    Promise.all([
      fetch("/api/students/?page_size=1000", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : { results: [] })),
      fetch("/api/schools/campuses/", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([studentsJson, campusList]) => {
        const list = Array.isArray(campusList)
          ? campusList
          : campusList.results || [];

        setStudents(studentsJson.results || []);
        setCampuses(list);
        setForm((f) => ({
          ...f,
          campus: list[0]?.id ?? "",
        }));
      })
      .catch(() => {});
  }, []);

  const loadIncidents = useCallback(() => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (severityFilter) params.append("severity", severityFilter);
    if (statusFilter) params.append("status", statusFilter);

    apiFetch(`${INCIDENTS_URL}?${params.toString()}`)
      .then((data) => setIncidents(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, severityFilter, statusFilter]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  useEffect(() => {
    apiFetch(SUMMARY_URL)
      .then(setSummary)
      .catch(() => {});
  }, [incidents]);

  const submitIncident = (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");

    apiFetch(INCIDENTS_URL, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setShowForm(false);
        setForm({ ...form, title: "", description: "", location: "" });
        loadIncidents();
      })
      .catch((err) => setFormError(err.message))
      .finally(() => setSaving(false));
  };

  const openIncident = (incident) => {
    setSelected(incident);

    return apiFetch(`${INCIDENTS_URL}${incident.id}/actions/`)
      .then((data) => setActions(data.results || data))
      .catch(() => setActions([]));
  };

  const addAction = (event) => {
    event.preventDefault();
    if (!selected) return;

    apiFetch(`${INCIDENTS_URL}${selected.id}/actions/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(actionForm),
    })
      .then(() => {
        setActionForm({ ...actionForm, details: "" });
        openIncident(selected);
        loadIncidents();
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Discipline"
        title="Discipline"
        subtitle="Record behaviour incidents and track follow-up actions."
        action={
          <button
            type="button"
            className="primary-button"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus size={15} />
            New Incident
          </button>
        }
      />

      {summary && (
        <div className="dashboard-grid">
          <div className="stat-card">
            <strong>
              <AlertOctagon size={18} /> {summary.total}
            </strong>
            <span>Total Incidents</span>
          </div>

          {(summary.by_status || []).map((item) => (
            <div key={item.status} className="stat-card">
              <strong>{item.count}</strong>
              <span>{item.status}</span>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="panel">
          <PanelHeader
            title="Record a new incident"
            subtitle="The incident starts as Open until an action is recorded."
          />

          <form onSubmit={submitIncident} className="filter-row">
            <select
              required
              value={form.campus}
              onChange={(e) => setForm({ ...form, campus: e.target.value })}
            >
              <option value="">Campus...</option>
              {campuses.map((campus) => (
                <option key={campus.id} value={campus.id}>
                  {campus.name}
                </option>
              ))}
            </select>

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

            <input
              required
              placeholder="Title e.g. Disrupting class"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />

            <select
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s[0].toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>

            <input
              type="date"
              required
              value={form.incident_date}
              onChange={(e) =>
                setForm({ ...form, incident_date: e.target.value })
              }
            />

            <input
              placeholder="Location (optional)"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
            />

            <textarea
              placeholder="Description (optional)"
              rows={2}
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />

            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save Incident"}
            </button>
          </form>

          {formError && (
            <div className="state-card error">{formError}</div>
          )}
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Incident Register"
          subtitle={`${incidents.length} incidents`}
        />

        <StateArea loading={loading} error={error} onRetry={loadIncidents}>
          <div className="filter-row">
            <input
              className="filter-search"
              placeholder="Search by student or title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <option value="">All severities</option>
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s[0].toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")[0].toUpperCase() +
                    s.replace("_", " ").slice(1)}
                </option>
              ))}
            </select>
          </div>

          {incidents.length === 0 ? (
            <div className="empty-state">
              <ShieldAlert size={42} />
              <h3>No incidents found</h3>
              <p>Adjust filters or record a new incident.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Student</th>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Points</th>
                    <th>Campus</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((incident) => (
                    <tr key={incident.id}>
                      <td>{incident.incident_date}</td>
                      <td>
                        <strong>{incident.student_name}</strong>
                        <small style={{ display: "block" }}>
                          {incident.admission_number}
                        </small>
                      </td>
                      <td>{incident.title}</td>
                      <td>
                        <span className={severityBadge(incident.severity)}>
                          {incident.severity}
                        </span>
                      </td>
                      <td>
                        {incident.status.replace("_", " ")}
                      </td>
                      <td>{incident.points}</td>
                      <td>{incident.campus_name}</td>
                      <td>
                        <button
                          type="button"
                          className="primary-button"
                          onClick={() => openIncident(incident)}
                        >
                          <Gavel size={14} />
                          Actions
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

      {selected && (
        <div className="panel">
          <PanelHeader
            title={`Actions — ${selected.title}`}
            subtitle={`${selected.student_name} · ${selected.severity} · ${selected.status.replace("_", " ")}`}
            action={
              <button
                type="button"
                className="primary-button"
                onClick={() => setSelected(null)}
              >
                <CircleCheck size={15} />
                Close
              </button>
            }
          />

          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Action</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {actions.length === 0 && (
                  <tr>
                    <td colSpan={3}>No actions recorded yet.</td>
                  </tr>
                )}

                {actions.map((action) => (
                  <tr key={action.id}>
                    <td>{action.action_date}</td>
                    <td>
                      <strong>{action.action_type_display}</strong>
                    </td>
                    <td>{action.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <form onSubmit={addAction} className="filter-row">
            <select
              value={actionForm.action_type}
              onChange={(e) =>
                setActionForm({ ...actionForm, action_type: e.target.value })
              }
            >
              {ACTION_TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>

            <input
              type="date"
              required
              value={actionForm.action_date}
              onChange={(e) =>
                setActionForm({ ...actionForm, action_date: e.target.value })
              }
            />

            <input
              placeholder="Details (optional)"
              value={actionForm.details}
              onChange={(e) =>
                setActionForm({ ...actionForm, details: e.target.value })
              }
            />

            <button className="primary-button">Add Action</button>
          </form>
        </div>
      )}
    </section>
  );
}
