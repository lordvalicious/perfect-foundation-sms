import { useEffect, useState, createElement } from "react";
import { X, Plus, Trash2, Edit, AlertTriangle } from "lucide-react";
import { apiFetch } from "../api";
import { useApiList } from "./useApiList";
import { PanelHeader, StateArea, EmptyState } from "./ui";
import { formatDate } from "./format";

const API_URL = "/api/discipline/";

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

  const severityClass = (sev) => {
    const s = (sev || "").toLowerCase();
    if (s === "major") return "danger";
    if (s === "moderate") return "warning";
    return "success";
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

    const toListOrEmpty = (response) => response.ok ? response.json() : [];

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

  // Build table rows using createElement to avoidrolldown JSX parsing issues
  const buildTableRows = () => {
    const rows = [];
    for (let i = 0; i < incidents.length; i++) {
      const incident = incidents[i];
      const sev = (incident.severity || "").toLowerCase();
      const sevClass = sev === "major" ? "row-danger" : sev === "moderate" ? "row-warning" : "";
      const severityStyle = {
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
      };

      rows.push(
        createElement(
          "tr",
          { key: incident.id, className: sevClass },
          createElement("td", null,
            createElement("strong", null, incident.title || "—")
          ),
          createElement("td", null,
            createElement("span", { style: severityStyle }, incident.severity || "—")
          ),
          createElement("td", null, incident.category || "—"),
          createElement("td", null, formatDate(incident.created_at)),
          createElement("td", { style: { whiteSpace: "nowrap" } },
            createElement("button", {
              className: "table-action",
              title: "Edit incident",
              onClick: () => openEdit(incident),
            }, createElement(Edit, { size: 14 })),
            createElement("button", {
              className: "table-action danger",
              title: "Delete incident",
              onClick: () => handleDelete(incident),
            }, createElement(Trash2, { size: 14 }))
          )
        )
      );
    }
    return rows;
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
                <tbody>{buildTableRows()}</tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
