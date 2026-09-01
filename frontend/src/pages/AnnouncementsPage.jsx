import { useState } from "react";
import { Megaphone, Pencil, Plus, Send, Trash2, X } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, EmptyState } from "./ui";
import { formatDate } from "./format";
import { apiFetch, jsonHeaders } from "../api";

const ANNOUNCEMENTS_URL = "/api/communication/announcements/";

const ROLES = [
  ["parent", "Parents"],
  ["teacher", "Teachers"],
  ["student", "Students"],
];

export default function AnnouncementsPage() {
  const [rows, setRows] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    title: "",
    message: "",
    category: "announcement",
    status: "draft",
    audience_roles: [],
  });

  const [editing, setEditing] = useState(null);

  const load = () => {
    setLoading(true);
    setError("");

    fetch(ANNOUNCEMENTS_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => {
        setRows(json.results || json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const openCreate = () => {
    setEditing(null);
    setCreating(true);
    setMessage("");
    setForm({
      title: "",
      message: "",
      category: "announcement",
      status: "draft",
      audience_roles: [],
    });
  };

  const openEdit = (announcement) => {
    setEditing(announcement);
    setCreating(true);
    setMessage("");
    setForm({
      title: announcement.title || "",
      message: announcement.message || "",
      category: announcement.category || "announcement",
      status: announcement.status || "draft",
      audience_roles: announcement.audience_roles || [],
    });
  };

  const toggleRole = (role) => {
    setForm((previous) => {
      const current = previous.audience_roles.includes(role)
        ? previous.audience_roles.filter((item) => item !== role)
        : [...previous.audience_roles, role];

      return { ...previous, audience_roles: current };
    });
  };

  const handleCreate = async (event) => {
    event.preventDefault();

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const isEditing = Boolean(editing);

      await apiFetch(
        isEditing
          ? `${ANNOUNCEMENTS_URL}${editing.id}/`
          : ANNOUNCEMENTS_URL,
        {
          method: isEditing ? "PATCH" : "POST",
          headers: jsonHeaders(),
          body: JSON.stringify(form),
        },
        isEditing
          ? "Could not update the announcement."
          : "Could not create the announcement."
      );

      setCreating(false);
      setEditing(null);
      setMessage(
        form.status === "published"
          ? "Announcement published and sent to recipients."
          : "Announcement saved as draft."
      );
      setRows(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (announcement) => {
    if (
      !window.confirm(
        `Delete announcement "${announcement.title}"? This cannot be undone.`
      )
    ) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiFetch(
        `${ANNOUNCEMENTS_URL}${announcement.id}/`,
        { method: "DELETE" },
        "Could not delete the announcement."
      );

      setMessage("Announcement deleted.");
      setRows(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (rows === null && !loading) {
    load();
  }

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Announcements"
        title="Announcements"
        subtitle="Create announcements and notify parents, teachers, and students."
      />

      {message && (
        <div className="state-card success">
          <strong>{message}</strong>
        </div>
      )}

      {!creating && (
        <div className="filter-row">
          <button type="button" className="primary-button" onClick={openCreate}>
            <Plus size={15} />
            New Announcement
          </button>
        </div>
      )}

      {creating && (
        <div className="panel">
          <PanelHeader
            title={editing ? "Edit Announcement" : "New Announcement"}
            subtitle={editing ? "update the details below" : "fill in the details below"}
          />

          <form onSubmit={handleCreate}>
            <div className="form-section">
              <div className="form-grid">
                <label>
                  Title
                  <input
                    type="text"
                    required
                    value={form.title}
                    onChange={(event) =>
                      setForm({ ...form, title: event.target.value })
                    }
                    placeholder="e.g. Winter Break Notice"
                  />
                </label>

                <label>
                  Category
                  <select
                    value={form.category}
                    onChange={(event) =>
                      setForm({ ...form, category: event.target.value })
                    }
                  >
                    <option value="announcement">Announcement</option>
                    <option value="notice">Notice</option>
                  </select>
                </label>
              </div>

              <label>
                Message
                <textarea
                  required
                  rows={4}
                  value={form.message}
                  onChange={(event) =>
                    setForm({ ...form, message: event.target.value })
                  }
                  placeholder="Write the announcement message..."
                />
              </label>

              <div className="form-grid">
                <label>
                  Status
                  <select
                    value={form.status}
                    onChange={(event) =>
                      setForm({ ...form, status: event.target.value })
                    }
                  >
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                  </select>
                </label>

                <div>
                  <span className="field-label">Audience</span>

                  <div className="checkbox-group">
                    {ROLES.map(([value, label]) => (
                      <label key={value} className="checkbox-inline">
                        <input
                          type="checkbox"
                          checked={form.audience_roles.includes(value)}
                          onChange={() => toggleRole(value)}
                        />
                        {label}
                      </label>
                    ))}
                  </div>

                  <span className="field-hint">
                    Leave all unchecked to notify every active member.
                  </span>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  setCreating(false);
                  setEditing(null);
                }}
              >
                <X size={15} />
                Cancel
              </button>

              <button type="submit" className="primary-button" disabled={saving}>
                <Send size={15} />
                {saving
                  ? "Saving..."
                  : editing
                    ? "Save Changes"
                    : form.status === "published"
                      ? "Publish"
                      : "Save Draft"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Announcement List"
          subtitle="announcements found"
          count={rows ? rows.length : null}
        />

        <StateArea loading={loading} error={error} onRetry={load}>
          {!rows || rows.length === 0 ? (
            <EmptyState
              icon={Megaphone}
              title="No announcements yet"
              message="Create your first announcement to get started."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>TITLE</th>
                    <th>CATEGORY</th>
                    <th>AUDIENCE</th>
                    <th>STATUS</th>
                    <th>PUBLISHED AT</th>
                    <th style={{ width: 130 }}>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {rows.map((announcement) => (
                    <tr key={announcement.id}>
                      <td>
                        <strong>{announcement.title}</strong>

                        <div className="cell-sub">{announcement.message}</div>
                      </td>

                      <td>{announcement.category_display || "—"}</td>

                      <td>
                        {announcement.audience_roles?.length
                          ? announcement.audience_roles
                              .map((role) => role.charAt(0).toUpperCase() + role.slice(1))
                              .join(", ")
                          : "Everyone"}
                      </td>

                      <td>
                        <span className={`status-badge ${announcement.status === "published" ? "active" : "warn"}`}>
                          {announcement.status_display}
                        </span>
                      </td>

                      <td>{formatDate(announcement.published_at)}</td>

                      <td style={{ whiteSpace: "nowrap" }}>
                        <button
                          type="button"
                          className="table-action"
                          onClick={() => openEdit(announcement)}
                        >
                          <Pencil size={13} />
                          Edit
                        </button>

                        <button
                          type="button"
                          className="table-action danger"
                          onClick={() => handleDelete(announcement)}
                        >
                          <Trash2 size={13} />
                          Delete
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
