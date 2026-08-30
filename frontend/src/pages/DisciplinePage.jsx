import { useEffect, useState } from "react";
import { X, Plus, Trash2, Edit, AlertTriangle } from "lucide-react";
import { apiFetch } from "../api";
import { useApiList } from "./useApiList";
import { PanelHeader, StateArea, EmptyState } from "./ui";
import { formatDate } from "./format";

const API_URL = "/api/discipline/";

// Build status options array without destructuring in map
const STATUS_OPTIONS = [
  { value: "minor", label: "Minor" },
  { value: "moderate", label: "Moderate" },
  { value: "major", label: "Major" },
];

// Helper to get status tag HTML
const getStatusTag = (status) =>
  status
    ? `<span style={{ padding: "2px 6px", borderRadius: "10px", fontSize: "11px", color: "var(--text-muted)" }}>{status}</span>`
    : "—";

export default function DisciplinePage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    status: "minor",
    category: "",
    severity: "minor",
  });
  const [actionError, setActionError] = useState("");

  const {
    rows,
    count,
    loading: listLoading,
    error: listError,
    page,
    next,
    previous,
    refresh,
  } = useApiList(API_URL, { page_size: 50 });

  const applyFilters = (pageNumber = 1) => {
    refresh(buildParams(pageNumber));
  };

  const buildParams = (pageNumber = 1) => {
    const params = new URLSearchParams();
    params.append("page", pageNumber);
    return params;
  };

  const openCreate = () => {
    setEditing(null);
    setForm({
      title: "",
      description: "",
      status: "minor",
      category: "",
      severity: "minor",
    });
    setActionError("");
    setShowForm(true);
  };

  const openEdit = (incident) => {
    setEditing(incident);
    setForm({
      title: incident.title,
      description: incident.description || "",
      status: incident.status || "minor",
      category: incident.category || "",
      severity: incident.severity || "minor",
    });
    setActionError("");
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
    setForm({
      title: "",
      description: "",
      status: "minor",
      category: "",
      severity: "minor",
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (editing) {
        await apiFetch(
          `/api/discipline/incidents/${editing.id}/`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(form),
          },
          "Failed to update the incident."
        );
      } else {
        await apiFetch(
          "/api/discipline/",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(form),
          },
          "Failed to create the incident."
        );
      }

      closeForm();
      applyFilters(page);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (incident) => {
    if (!window.confirm(`Delete incident "${incident.title}"?`)) {
      return;
    }

    try {
      await apiFetch(
        `/api/discipline/incidents/${incident.id}/`,
        { method: "DELETE" },
        "Failed to delete the incident."
      );
      applyFilters(page);
    } catch (err) {
      setError(err.message || String(err));
    }
  };

  const load = () => {
    setLoading(true);
    setError("");

    const toListOrEmpty = (response) =>
      response.ok ? response.json() : [];

    fetch(API_URL, { credentials: "include" })
      .then(toListOrEmpty)
      .then((json) => {
        setIncidents(json.results || json);
        setLoading(false);
      })
      .catch(() => setError("Failed to load incidents."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Helper: render severity badge class
  const severityClass = (sev) => {
    const s = (sev || "").toLowerCase();
    if (s === "major") return "danger";
    if (s === "moderate") return "warning";
    return "success";
  };

  // Helper: render row CSS class
  const rowClasses = (incident) => {
    const s = (incident.severity || "").toLowerCase();
    if (s === "major") return "row-danger";
    if (s === "moderate") return "row-warning";
    return "";
  };

  // Render status options <option> elements
  const renderSeverityOptions = () => {
    const options = [];
    for (let i = 0; i < STATUS_OPTIONS.length; i++) {
      const opt = STATUS_OPTIONS[i];
      options.push(
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      );
    }
    return options;
  };

  return (
    <section className="content">
      <h1 className="page-heading">
        Discipline Management
        <small>Incident reports and actions</small>
      </h1>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="panel">
        <PanelHeader title="Incident List" subtitle="incidents" count={count} />

        <StateArea loading={loading} error={error} onRetry={load}>
          {incidents.length === 0 ? (
            <EmptyState
              icon={AlertTriangle}
              title="No incidents found"
              message="Add an incident to track discipline records."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>TITLE</th>
                    <th>SEVERITY</th>
                    <th>CATEGORY</th>
                    <th>STATUS</th>
                    <th>CREATED</th>
                    <th style={{ width: 140 }}>Actions</th>
                  </tr>
                </thead>

                <tbody>
{incidents.map((incident) => {
                    const sev = (incident.severity || "").toLowerCase();
                    const sevClass = sev === "major" ? "row-danger" : sev === "moderate" ? "row-warning" : "";
                    return (
                      <div>
                        <tr key={incident.id} className={sevClass}>
                          <td>
                            <strong>{incident.title || "—"}</strong>
                          </td>

                          <td>
                            <span
                              style={{
                                padding: "2px 6px",
                                borderRadius: "10px",
                                fontSize: "11px",
                                fontWeight: 600,
                                color:
                                  severityClass(incident.severity) === "danger"
                                    ? "var(--danger)"
                                    : severityClass(incident.severity) === "warning"
                                      ? "var(--warning)"
                                      : "var(--success)",
                          }}
                        >
                          {incident.severity || "—"}
                        </span>
                      </td>

                      <td>{incident.category || "—"}</td>

                      <td>{getStatusTag(incident.status)}</td>

                      <td>{formatDate(incident.created_at)}</td>

                      <td style={{ whiteSpace: "nowrap" }}>
                        <button
                          className="table-action"
                          title="Edit incident"
                          onClick={() => openEdit(incident)}
                        >
                          <Edit size={14} />
                        </button>
                        <button
                          className="table-action danger"
                          title="Delete incident"
                          onClick={() => handleDelete(incident)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                        </tr>
                      </div>
                    })}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>

        {showForm && (
          <div
            className="modal-overlay"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) closeForm();
            }}
          >
            <div className="modal">
              <div className="modal-header">
                <div>
                  <h3>{editing ? "Edit Incident" : "Add Incident"}</h3>
                  <p>
                    {editing ? "Update the incident details." : "Record a new discipline incident."}
                  </p>
                </div>
                <button className="modal-close" onClick={closeForm}>
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="modal-body">
                  <div className="form-section">
                    <h4>Incident details</h4>

                    <div className="form-grid">
                      <div>
                        <strong>Title</strong>
                        <input
                          type="text"
                          required
                          value={form.title}
                          onChange={(event) =>
                            setForm((current) => ({
                              ...current,
                              title: event.target.value,
                            }))
                          }
                        />
                      </div>

                      <div>
                        <strong>Category</strong>
                        <input
                          type="text"
                          value={form.category}
                          onChange={(event) =>
                            setForm((current) => ({
                              ...current,
                              category: event.target.value,
                            }))
                          }
                        />
                      </div>

                      <div>
                        <strong>Severity</strong>
                        <select
                          value={form.severity}
                          onChange={(event) =>
                            setForm((current) => ({
                              ...current,
                              severity: event.target.value,
                            }))
                        >
                          {renderSeverityOptions()}
                        </select>
                      </div>
                  </div>

                  <div className="form-section">
                    <h4>Description</h4>

                    <textarea
                      value={form.description}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          description: event.target.value,
                        }))
                      />
                    </textarea>
                  </div>
                </div>

                {actionError && <div className="alert alert-error">{actionError}</div>}

                <div className="modal-footer">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={closeForm}
                    disabled={loading}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                    disabled={loading}
                  >
                    {loading ? "Saving..." : editing ? "Save changes" : "Create incident"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}