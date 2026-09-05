import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Building2,
  Plus,
  Power,
  Pencil,
  Eye,
  X,
  LogIn,
  Check,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";
import { useSchool } from "../schoolContext";

const BASE = "/api/schools/tenants/";

const STATUS_CHOICES = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
];

const EMPTY_FORM = {
  name: "",
  code: "",
  city: "",
  first_campus: "",
};

function labelFor(status) {
  const found = STATUS_CHOICES.find((s) => s.value === status);
  return found ? found.label : status;
}

function SchoolModal({
  title,
  subtitle,
  saving,
  error,
  onClose,
  onSubmit,
  children,
}) {
  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !saving) onClose();
      }}
    >
      <div className="teacher-modal">
        <div className="modal-header">
          <div>
            <h3>{title}</h3>
            {subtitle && (
              <p className="hint" style={{ margin: "2px 0 0" }}>
                {subtitle}
              </p>
            )}
          </div>
          <button
            className="modal-close"
            onClick={onClose}
            disabled={saving}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>
        <form onSubmit={onSubmit}>
          <div className="modal-body">
            {error && (
              <div className="state-card error" style={{ marginBottom: 12 }}>
                <strong>Unable to save school.</strong>
                <span>{error}</span>
              </div>
            )}
            <div className="form-grid" style={{ gridTemplateColumns: "1fr" }}>
              {children}
            </div>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SchoolDetail({ tenant, onClose, onEdit, onModules, onAccess, canAccess }) {
  return (
    <div className="modal-overlay" onMouseDown={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}>
      <div className="teacher-modal large">
        <div className="modal-header">
          <div>
            <h3>{tenant.name}</h3>
            {tenant.city && (
              <p className="hint" style={{ margin: "2px 0 0" }}>
                {tenant.city}
              </p>
            )}
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <X size={16} />
          </button>
        </div>
        <div className="modal-body">
          <div className="detail-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 16 }}>
            <div className="form-group">
              <div className="detail-label" style={{ fontSize: 12, color: "var(--text-muted)" }}>School code</div>
              <div className="detail-value" style={{ fontWeight: 600 }}>{tenant.code || "—"}</div>
            </div>
            <div className="form-group">
              <div className="detail-label" style={{ fontSize: 12, color: "var(--text-muted)" }}>Status</div>
              <div className="detail-value" style={{ fontWeight: 600 }}>{labelFor(tenant.status)}</div>
            </div>
            <div className="form-group">
              <div className="detail-label" style={{ fontSize: 12, color: "var(--text-muted)" }}>Campuses</div>
              <div className="detail-value" style={{ fontWeight: 600 }}>{tenant.stats?.campuses ?? 0}</div>
            </div>
            <div className="form-group">
              <div className="detail-label" style={{ fontSize: 12, color: "var(--text-muted)" }}>Students</div>
              <div className="detail-value" style={{ fontWeight: 600 }}>{tenant.stats?.students ?? 0}</div>
            </div>
            <div className="form-group">
              <div className="detail-label" style={{ fontSize: 12, color: "var(--text-muted)" }}>Created</div>
              <div className="detail-value" style={{ fontWeight: 600 }}>
                {tenant.created_at ? new Date(tenant.created_at).toLocaleDateString() : "—"}
              </div>
            </div>
            <div className="form-group">
              <div className="detail-label" style={{ fontSize: 12, color: "var(--text-muted)" }}>School ID</div>
              <div className="detail-value" style={{ fontWeight: 600 }}>{tenant.id}</div>
            </div>
          </div>

          <div className="form-section">
            <h4>Modules</h4>
            {tenant.enabled_modules?.length ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {tenant.enabled_modules.map((mod) => (
                  <span key={mod} className="status-badge info">{mod}</span>
                ))}
              </div>
            ) : (
              <p className="hint">All modules enabled.</p>
            )}
          </div>
        </div>
        <div className="modal-footer">
          <button type="button" className="secondary-button" onClick={() => onModules(tenant)}>
            Modules
          </button>
          <button type="button" className="secondary-button" onClick={() => onEdit(tenant)}>
            <Pencil size={13} /> Edit
          </button>
          {canAccess && (
            <button type="button" className="primary-button" onClick={() => onAccess(tenant)}>
              <LogIn size={13} /> Access dashboard
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState([]);
  const [allModules, setAllModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState(EMPTY_FORM);
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState("");
  const [created, setCreated] = useState(null);

  const [editForm, setEditForm] = useState(null);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  const [detail, setDetail] = useState(null);

  const [editingModules, setEditingModules] = useState(null);
  const [draftModules, setDraftModules] = useState([]);

  const { switchSchool } = useSchool();
  const navigate = useNavigate();

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    apiFetch(BASE)
      .then((data) => {
        setTenants(data.tenants || []);
        setAllModules(data.all_modules || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const extractError = (err) => {
    if (err && err.message && err.message !== "Request failed.") {
      return err.message;
    }
    return "Something went wrong. Please try again.";
  };

  const createTenant = (event) => {
    event.preventDefault();
    setCreateSaving(true);
    setCreateError("");

    apiFetch(BASE, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        name: createForm.name,
        code: createForm.code,
        city: createForm.city,
        first_campus: createForm.first_campus,
      }),
    })
      .then((data) => {
        setShowCreate(false);
        setCreateForm(EMPTY_FORM);
        setCreated(data);
        setNotice(`School "${data.name}" created.`);
        load();
      })
      .catch((err) => setCreateError(extractError(err)))
      .finally(() => setCreateSaving(false));
  };

  const updateSchool = (event) => {
    event.preventDefault();
    if (!editForm) return;
    setEditSaving(true);
    setEditError("");

    const payload = {
      name: editForm.name,
      code: editForm.code,
      city: editForm.city,
      status: editForm.status,
    };

    apiFetch(`${BASE}${editForm.id}/`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    })
      .then(() => {
        setEditForm(null);
        setEditError("");
        setDetail(null);
        setNotice(`"${payload.name}" updated.`);
        load();
      })
      .catch((err) => setEditError(extractError(err)))
      .finally(() => setEditSaving(false));
  };

  const toggleStatus = (tenant) => {
    const next = tenant.status === "active" ? "inactive" : "active";

    apiFetch(`${BASE}${tenant.id}/`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ status: next }),
    })
      .then(() => {
        setNotice(`${tenant.name} is now ${next}.`);
        load();
      })
      .catch((err) => setError(err.message));
  };

  const saveModules = (tenant) => {
    apiFetch(`${BASE}${tenant.id}/`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ enabled_modules: draftModules }),
    })
      .then(() => {
        setEditingModules(null);
        setDetail(null);
        setNotice(`Modules updated for ${tenant.name}.`);
        load();
      })
      .catch((err) => setError(err.message));
  };

  const openModules = (tenant) => {
    setDetail(null);
    setEditingModules(tenant.id);
    setDraftModules(tenant.enabled_modules?.length ? [...tenant.enabled_modules] : [...allModules]);
  };

  const openEdit = (tenant) => {
    setDetail(null);
    setEditingModules(null);
    setEditForm({
      id: tenant.id,
      name: tenant.name,
      code: tenant.code || "",
      city: tenant.city || "",
      status: tenant.status,
    });
    setEditError("");
  };

  const accessSchool = (tenant) => {
    switchSchool(tenant.id)
      .then(() => {
        setDetail(null);
        setNotice(`Switched context to "${tenant.name}".`);
        navigate("/");
      })
      .catch((err) => setError(extractError(err)));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Schools"
        title="Platform · Schools"
        subtitle="Create schools, activate or deactivate tenants, and control which modules each school gets."
        action={
          <button
            type="button"
            className="primary-button"
            onClick={() => {
              setShowCreate((v) => !v);
              setCreated(null);
              setCreateError("");
            }}
          >
            <Plus size={15} />
            New School
          </button>
        }
      />

      {showCreate && (
        <SchoolModal
          title="Onboard a new school"
          subtitle="Creates an isolated tenant. Modules can be adjusted after creation."
          saving={createSaving}
          error={createError}
          onClose={() => setShowCreate(false)}
          onSubmit={createTenant}
        >
          <label>
            School name *
            <input
              required
              placeholder="e.g. Springfield Academy"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            />
          </label>
          <label>
            Short code
            <input
              placeholder="Optional (auto-generated if blank)"
              value={createForm.code}
              onChange={(e) => setCreateForm({ ...createForm, code: e.target.value })}
            />
          </label>
          <label>
            City
            <input
              placeholder="e.g. Lahore"
              value={createForm.city}
              onChange={(e) => setCreateForm({ ...createForm, city: e.target.value })}
            />
          </label>
          <label>
            First campus name
            <input
              placeholder="Optional — creates an initial campus"
              value={createForm.first_campus}
              onChange={(e) => setCreateForm({ ...createForm, first_campus: e.target.value })}
            />
          </label>
        </SchoolModal>
      )}

      {editForm && (
        <SchoolModal
          title={`Edit school — ${editForm.name}`}
          subtitle="Update school details. Changes apply to this tenant only."
          saving={editSaving}
          error={editError}
          onClose={() => setEditForm(null)}
          onSubmit={updateSchool}
        >
          <label>
            School name *
            <input
              required
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            />
          </label>
          <label>
            Short code
            <input
              value={editForm.code}
              onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
            />
          </label>
          <label>
            City
            <input
              value={editForm.city}
              onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
            />
          </label>
          <label>
            Status
            <select
              value={editForm.status}
              onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
            >
              {STATUS_CHOICES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </SchoolModal>
      )}

      {detail && !editForm && (
        <SchoolDetail
          tenant={detail}
          onClose={() => setDetail(null)}
          onEdit={openEdit}
          onModules={openModules}
          onAccess={accessSchool}
          canAccess
        />
      )}

      <div className="panel">
        <PanelHeader
          title="Tenants"
          subtitle={notice || `${tenants.length} schools on this platform`}
        />

        {created && (
          <div className="state-card success" style={{ marginBottom: 12 }}>
            <strong>School created successfully.</strong>
            <span>
              {created.name} (code: {created.code || "auto-generated"}) is ready.
              Credentials are not auto-generated — create the school administrator
              from the school's staff area.
            </span>
            <button type="button" className="secondary-button" onClick={() => setCreated(null)}>
              Dismiss
            </button>
          </div>
        )}

        <StateArea loading={loading} error={error} onRetry={load}>
          {tenants.length === 0 ? (
            <div className="empty-state">
              <Building2 size={42} />
              <h3>No schools yet</h3>
              <p>Create your first tenant using the "New School" button.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>School</th>
                    <th>Code</th>
                    <th>Status</th>
                    <th>Campuses</th>
                    <th>Students</th>
                    <th>Modules</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tenants.map((tenant) => (
                    <tr key={tenant.id}>
                      <td>
                        <strong>{tenant.name}</strong>
                        <small style={{ display: "block" }}>
                          {tenant.city || "—"}
                        </small>
                      </td>
                      <td>{tenant.code || "—"}</td>
                      <td>
                        <span className={`status-badge ${tenant.status === "active" ? "active" : tenant.status === "inactive" ? "inactive" : "warn"}`}>
                          {labelFor(tenant.status)}
                        </span>
                      </td>
                      <td>{tenant.stats?.campuses ?? 0}</td>
                      <td>{tenant.stats?.students ?? 0}</td>
                      <td>
                        {(tenant.enabled_modules?.length
                          ? tenant.enabled_modules.length + " enabled"
                          : "All")}
                        {editingModules === tenant.id && (
                          <div
                            style={{
                              marginTop: 8,
                              maxWidth: 320,
                              display: "grid",
                              gridTemplateColumns: "1fr 1fr",
                              gap: 4,
                            }}
                          >
                            {allModules.map((mod) => (
                              <label key={mod} style={{ fontSize: 12 }}>
                                <input
                                  type="checkbox"
                                  checked={draftModules.includes(mod)}
                                  onChange={(e) =>
                                    setDraftModules(
                                      e.target.checked
                                        ? [...draftModules, mod]
                                        : draftModules.filter((m) => m !== mod)
                                    )
                                  }
                                />{" "}
                                {mod}
                              </label>
                            ))}
                            <button
                              type="button"
                              className="primary-button"
                              onClick={() => saveModules(tenant)}
                            >
                              Save
                            </button>
                          </div>
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="table-action"
                          title="View details"
                          onClick={() => {
                            setEditingModules(null);
                            setEditForm(null);
                            setDetail(editingModules === tenant.id ? null : tenant);
                          }}
                        >
                          <Eye size={13} />
                          View
                        </button>{" "}
                        <button
                          type="button"
                          className="table-action"
                          title="Edit school"
                          onClick={() => openEdit(tenant)}
                        >
                          <Pencil size={13} />
                          Edit
                        </button>{" "}
                        <button
                          type="button"
                          className="table-action"
                          title="Toggle modules"
                          onClick={() => {
                            setDetail(null);
                            if (editingModules !== tenant.id) {
                              setEditingModules(tenant.id);
                              setDraftModules(
                                tenant.enabled_modules?.length
                                  ? [...tenant.enabled_modules]
                                  : [...allModules]
                              );
                            } else {
                              setEditingModules(null);
                            }
                          }}
                        >
                          {editingModules === tenant.id ? (
                            <Check size={13} />
                          ) : (
                            <span>Modules</span>
                          )}
                        </button>{" "}
                        <button
                          type="button"
                          className="table-action"
                          onClick={() => toggleStatus(tenant)}
                        >
                          <Power size={13} />
                          {tenant.status === "active" ? "Deactivate" : "Activate"}
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
