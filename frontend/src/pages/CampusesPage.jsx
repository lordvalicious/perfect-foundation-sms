import { useEffect, useState } from "react";
import {
  Building2,
  BookOpen,
  Users,
  LayoutGrid,
  Plus,
  Eye,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  StatusBadge,
} from "./ui";
import { apiFetch, authHeaders } from "../api";
import { formatDate } from "./format";

const API_URL = "/api/schools/campuses/";
const TENANTS_URL = "/api/schools/tenants/";
const SCHOOLS_URL = "/api/schools/";

const emptyForm = { name: "", city: "", address: "", school: "" };

export default function CampusesPage() {
  const { rows, count, loading, error, refresh } = useApiList(API_URL);

  const [schools, setSchools] = useState([]);
  const [selectedSchool, setSelectedSchool] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState(emptyForm);

  const [viewing, setViewing] = useState(null);

  const currentParams = () =>
    new URLSearchParams(
      selectedSchool ? { school: selectedSchool } : {}
    );

  const buildForm = (firstSchoolId) => ({
    ...emptyForm,
    school: firstSchoolId ? String(firstSchoolId) : "",
  });

  useEffect(() => {
    apiFetch(TENANTS_URL)
      .then((data) => {
        const list = (data.tenants || []).map((t) => ({
          id: t.id,
          name: t.name,
        }));
        setSchools(list);
        if (list.length === 1) {
          setForm((f) => (f.school ? f : { ...f, school: String(list[0].id) }));
        }
      })
      .catch(() => {
        apiFetch(SCHOOLS_URL)
          .then((rowsData) => {
            if (Array.isArray(rowsData) && rowsData.length) {
              const list = rowsData.map((s) => ({ id: s.id, name: s.name }));
              setSchools(list);
              setForm((f) => (f.school ? f : { ...f, school: String(list[0].id) }));
            }
          })
          .catch(() => {});
      });
  }, []);

  const toggleForm = () => {
    const opening = !showForm;
    setShowForm(opening);

    if (opening) {
      setEditing(null);
      setFormError("");
      setForm(buildForm(schools.length === 1 ? schools[0].id : ""));
    }
  };

  const startEdit = (campus) => {
    setEditing(campus);
    setFormError("");
    setForm({
      name: campus.name,
      city: campus.city || "",
      address: campus.address || "",
      school: campus.school ? String(campus.school) : buildForm(schools.length === 1 ? schools[0].id : "").school,
    });
    setShowForm(true);
  };

  const submit = (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");

    const isEdit = Boolean(editing);

    apiFetch(isEdit ? `${API_URL}${editing.id}/` : API_URL, {
      method: isEdit ? "PATCH" : "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setShowForm(false);
        setEditing(null);
        setForm(emptyForm);
        refresh(currentParams());
      })
      .catch((err) => setFormError(err.message))
      .finally(() => setSaving(false));
  };

  const removeCampus = (campus) => {
    const confirmed = window.confirm(
      `Delete campus "${campus.name}"?\n\n` +
        "This permanently removes the campus and all linked academic units, classes, sections and enrollments."
    );

    if (!confirmed) return;

    apiFetch(`${API_URL}${campus.id}/`, {
      method: "DELETE",
      headers: authHeaders(),
    })
      .then(() => refresh(currentParams()))
      .catch((err) => setFormError(err.message));
  };

  const onSchoolFilter = (event) => {
    const id = event.target.value;
    setSelectedSchool(id);
    refresh(new URLSearchParams(id ? { school: id } : {}));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Campuses"
        title="Campuses"
        subtitle="Manage campuses across schools and their statistics."
        action={
          <button type="button" className="primary-button" onClick={toggleForm}>
            <Plus size={15} />
            Add Campus
          </button>
        }
      />

      {showForm && (
        <div className="panel">
          <PanelHeader
            title={editing ? `Edit ${editing.name}` : "Add a new campus"}
            subtitle={
              editing
                ? "Update this campus' details."
                : "Choose which school this campus belongs to."
            }
          />
          <form onSubmit={submit} className="filter-row">
            <select
              required
              value={form.school}
              onChange={(e) => setForm({ ...form, school: e.target.value })}
              disabled={schools.length === 1}
            >
              <option value="">
                {schools.length ? "Select school *" : "Loading schools..."}
              </option>
              {schools.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <input
              required
              placeholder="Campus name *"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              placeholder="City"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
            />
            <input
              placeholder="Address"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : editing ? "Update Campus" : "Save Campus"}
            </button>
          </form>
          {formError && (
            <div className="state-card error" style={{ marginTop: 10 }}>
              {formError}
            </div>
          )}
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Campus List"
          subtitle="campuses found"
          count={count}
          action={
            schools.length > 1 ? (
              <select
                value={selectedSchool}
                onChange={onSchoolFilter}
                style={{ maxWidth: 260 }}
              >
                <option value="">
                  All schools (current scope)
                </option>
                {schools.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            ) : null
          }
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => refresh(currentParams())}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={Building2}
              title="No campuses found"
              message="Click 'Add Campus' to create your first campus."
            />
          ) : (
            <div className="campuses-grid">
              {rows.map((campus) => (
                <div className="campus-card" key={campus.id}>
                  <div className="campus-card-head">
                    <div className="campus-card-icon">
                      <Building2 size={22} />
                    </div>

                    <div>
                      <strong>{campus.name}</strong>

                      <span>
                        {[
                          campus.school_name,
                          campus.city,
                          campus.address,
                        ]
                          .filter(Boolean)
                          .join(" · ") || "—"}
                      </span>
                    </div>

                    <StatusBadge status={campus.status} />
                  </div>

                  <div className="campus-stats">
                    <div>
                      <Users size={17} />
                      <strong>
                        {campus.student_count ?? 0}
                      </strong>
                      <span>Students</span>
                    </div>

                    <div>
                      <BookOpen size={17} />
                      <strong>
                        {campus.class_count ?? 0}
                      </strong>
                      <span>Classes</span>
                    </div>

                    <div>
                      <LayoutGrid size={17} />
                      <strong>
                        {campus.section_count ?? 0}
                      </strong>
                      <span>Sections</span>
                    </div>
                  </div>

                  <div className="campus-card-actions">
                    <button
                      type="button"
                      className="table-action"
                      onClick={() => setViewing(campus)}
                    >
                      <Eye size={13} />
                      View
                    </button>
                    <button
                      type="button"
                      className="table-action"
                      onClick={() => startEdit(campus)}
                    >
                      <Pencil size={13} />
                      Edit
                    </button>
                    <button
                      type="button"
                      className="table-action danger"
                      onClick={() => removeCampus(campus)}
                    >
                      <Trash2 size={13} />
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </StateArea>
      </div>

      {viewing && (
        <div
          className="modal-overlay"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setViewing(null);
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <h3>Campus details</h3>
              <button
                className="modal-close"
                onClick={() => setViewing(null)}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <div className="campus-view-row">
                <span>Name</span>
                <strong>{viewing.name}</strong>
              </div>
              <div className="campus-view-row">
                <span>School</span>
                <strong>{viewing.school_name || "—"}</strong>
              </div>
              <div className="campus-view-row">
                <span>Status</span>
                <StatusBadge status={viewing.status} />
              </div>
              <div className="campus-view-row">
                <span>City</span>
                <strong>{viewing.city || "—"}</strong>
              </div>
              <div className="campus-view-row">
                <span>Address</span>
                <strong>{viewing.address || "—"}</strong>
              </div>
              <div className="campus-view-row">
                <span>Students</span>
                <strong>{viewing.student_count ?? 0}</strong>
              </div>
              <div className="campus-view-row">
                <span>Classes</span>
                <strong>{viewing.class_count ?? 0}</strong>
              </div>
              <div className="campus-view-row">
                <span>Sections</span>
                <strong>{viewing.section_count ?? 0}</strong>
              </div>
              <div className="campus-view-row">
                <span>Created</span>
                <strong>{formatDate(viewing.created_at)}</strong>
              </div>
              <div className="campus-view-row">
                <span>Updated</span>
                <strong>{formatDate(viewing.updated_at)}</strong>
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="table-action"
                onClick={() => {
                  const campus = viewing;
                  setViewing(null);
                  startEdit(campus);
                }}
              >
                <Pencil size={13} />
                Edit
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => setViewing(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}