import { useCallback, useEffect, useState } from "react";
import { Building2, Plus, Power } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/schools/tenants/";

export default function TenantsPage() {
  const [tenants, setTenants] = useState([]);
  const [allModules, setAllModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "",
    code: "",
    city: "",
    first_campus: "",
  });
  const [saving, setSaving] = useState(false);

  const [editingModules, setEditingModules] = useState(null);
  const [draftModules, setDraftModules] = useState([]);

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

  const createTenant = (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice("");

    apiFetch(BASE, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setShowCreate(false);
        setForm({ name: "", code: "", city: "", first_campus: "" });
        setNotice("School created.");
        load();
      })
      .catch((err) => setError(err.message))
      .finally(() => setSaving(false));
  };

  const toggleStatus = (tenant) => {
    const next =
      tenant.status === "active" ? "inactive" : "active";

    apiFetch(`${BASE}${tenant.id}/`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ status: next }),
    })
      .then(() => {
        setNotice(
          `${tenant.name} is now ${next}.`
        );
        load();
      })
      .catch((err) => setError(err.message));
  };

  const saveModules = (tenant) => {
    apiFetch(`${BASE}${tenant.id}/`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        enabled_modules: draftModules,
      }),
    })
      .then(() => {
        setEditingModules(null);
        setNotice(`Modules updated for ${tenant.name}.`);
        load();
      })
      .catch((err) => setError(err.message));
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
            onClick={() => setShowCreate((v) => !v)}
          >
            <Plus size={15} />
            New School
          </button>
        }
      />

      {showCreate && (
        <div className="panel">
          <PanelHeader
            title="Onboard a new school"
            subtitle="Creates an isolated tenant. Modules can be adjusted after creation."
          />
          <form onSubmit={createTenant} className="filter-row">
            <input
              required
              placeholder="School name *"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              placeholder="Short code (e.g. ca-main)"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
            />
            <input
              placeholder="City"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
            />
            <input
              placeholder="First campus name"
              value={form.first_campus}
              onChange={(e) =>
                setForm({ ...form, first_campus: e.target.value })
              }
            />
            <button className="primary-button" disabled={saving}>
              {saving ? "Creating..." : "Create school"}
            </button>
          </form>
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Tenants"
          subtitle={notice || `${tenants.length} schools on this platform`}
        />

        <StateArea loading={loading} error={error} onRetry={load}>
          {tenants.length === 0 ? (
            <div className="empty-state">
              <Building2 size={42} />
              <h3>No schools yet</h3>
              <p>Create your first tenant above.</p>
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
                      <td>{tenant.status}</td>
                      <td>{tenant.stats?.campuses ?? 0}</td>
                      <td>{tenant.stats?.students ?? 0}</td>
                      <td>
                        {(tenant.enabled_modules?.length
                          ? tenant.enabled_modules.length +
                            " enabled"
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
                              <label
                                key={mod}
                                style={{ fontSize: 12 }}
                              >
                                <input
                                  type="checkbox"
                                  checked={draftModules.includes(mod)}
                                  onChange={(e) =>
                                    setDraftModules(
                                      e.target.checked
                                        ? [...draftModules, mod]
                                        : draftModules.filter(
                                            (m) => m !== mod
                                          )
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
                          className="primary-button"
                          onClick={() => {
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
                          {editingModules === tenant.id ? "Cancel" : "Modules"}
                        </button>{" "}
                        <button
                          type="button"
                          className="table-action"
                          onClick={() => toggleStatus(tenant)}
                        >
                          <Power size={13} />
                          {tenant.status === "active"
                            ? "Deactivate"
                            : "Activate"}
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
