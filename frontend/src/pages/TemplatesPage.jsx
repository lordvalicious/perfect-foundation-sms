import { useCallback, useEffect, useState } from "react";
import { FileText, Plus, Send, Trash2, X } from "lucide-react";
import { apiFetch, jsonHeaders } from "../api";
import { useAuth } from "../auth";
import { PageHeader, PanelHeader, StateArea, StatusBadge, EmptyState } from "./ui";

const TEMPLATES_URL = "/api/communication/templates/";
const SMS_SEND_URL = "/api/communication/sms/send/";

const PLACEHOLDER_HELP = [
  { key: "{student_name}", description: "Student's full name" },
  { key: "{admission_number}", description: "Student admission number" },
  { key: "{class_name}", description: "Class name" },
  { key: "{amount}", description: "Fee amount" },
  { key: "{due_date}", description: "Fee due date" },
  { key: "{school_name}", description: "School name" },
  { key: "{parent_name}", description: "Parent/guardian name" },
  { key: "{date}", description: "Current date" },
];

function TemplateFormModal({ template, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: template?.name || "",
    channel: template?.channel || "sms",
    subject: template?.subject || "",
    body: template?.body || "",
    variables: template?.variables || [],
  });
  const [variableInput, setVariableInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const addVariable = () => {
    const v = variableInput.trim().replace(/[{}]/g, "");
    if (v && !form.variables.includes(v)) {
      setForm((p) => ({ ...p, variables: [...p.variables, v] }));
      setVariableInput("");
    }
  };

  const removeVariable = (v) => {
    setForm((p) => ({ ...p, variables: p.variables.filter((x) => x !== v) }));
  };

  const insertPlaceholder = (key) => {
    const clean = key.replace(/[{}]/g, "");
    setForm((p) => ({ ...p, body: p.body + ` {${clean}} ` }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const url = template ? `${TEMPLATES_URL}${template.id}/` : TEMPLATES_URL;
      const method = template ? "PUT" : "POST";

      await apiFetch(url, {
        method,
        headers: jsonHeaders(),
        body: JSON.stringify(form),
      }, "Failed to save template.");

      onSaved();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="teacher-modal">
        <div className="modal-header">
          <div>
            <h3>{template ? "Edit Template" : "Create Template"}</h3>
            <p>Create reusable message templates with placeholders.</p>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h4>Template Info</h4>
            <div className="form-grid">
              <label>
                Template Name *
                <input name="name" value={form.name} onChange={handleChange} required placeholder="Payment Reminder" />
              </label>
              <label>
                Channel *
                <select name="channel" value={form.channel} onChange={handleChange} required>
                  <option value="sms">SMS</option>
                  <option value="email">Email</option>
                  <option value="both">Both</option>
                </select>
              </label>
              {(form.channel === "email" || form.channel === "both") && (
                <label style={{ gridColumn: "1 / -1" }}>
                  Subject
                  <input name="subject" value={form.subject} onChange={handleChange} placeholder="Email subject line" />
                </label>
              )}
            </div>
          </div>

          <div className="form-section">
            <h4>Message Body</h4>
            <textarea
              name="body"
              value={form.body}
              onChange={handleChange}
              required
              rows={6}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="Type your message here. Use {placeholder} for dynamic content."
            />

            <div style={{ marginTop: 8 }}>
              <small style={{ opacity: 0.6 }}>Click to insert a placeholder:</small>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                {PLACEHOLDER_HELP.map((p) => (
                  <button
                    key={p.key}
                    type="button"
                    className="secondary-button"
                    style={{ fontSize: 11, padding: "2px 8px" }}
                    onClick={() => insertPlaceholder(p.key)}
                    title={p.description}
                  >
                    {p.key}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginTop: 8 }}>
              <small style={{ opacity: 0.6 }}>Custom variables:</small>
              <div style={{ display: "flex", gap: 4, marginTop: 4 }}>
                <input
                  value={variableInput}
                  onChange={(e) => setVariableInput(e.target.value)}
                  placeholder="Add variable name"
                  style={{ flex: 1 }}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addVariable(); } }}
                />
                <button type="button" className="secondary-button" onClick={addVariable}>Add</button>
              </div>
              {form.variables.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                  {form.variables.map((v) => (
                    <span key={v} className="status-badge active" style={{ cursor: "pointer" }} onClick={() => removeVariable(v)}>
                      {v} &times;
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {error && <div className="state-card error"><strong>{error}</strong></div>}

          <div className="modal-footer">
            <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>Cancel</button>
            <button type="submit" className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save Template"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SendFromTemplateModal({ template, onClose, onSent }) {
  const [recipients, setRecipients] = useState("all");
  const [campus, setCampus] = useState("");
  const [campuses, setCampuses] = useState([]);
  const [variables, setVariables] = useState({});
  const [preview, setPreview] = useState("");
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/schools/campuses/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setCampuses(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const ctx = {};
    template.variables.forEach((v) => { ctx[v] = variables[v] || `[${v}]`; });
        ctx.school_name = ctx.school_name || "School";
    ctx.date = ctx.date || new Date().toLocaleDateString();
    let text = template.body;
    for (const [key, value] of Object.entries(ctx)) {
      text = text.replace(new RegExp(`\\{${key}\\}`, "g"), value);
    }
    setPreview(text);
  }, [template.body, template.variables, variables]);

  const handleSend = async () => {
    setSaving(true);
    setError("");

    const body = {
      message: preview,
      role: recipients,
    };
    if (campus) body.campus_id = campus;

    try {
      const data = await apiFetch(SMS_SEND_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(body),
      }, "Failed to send SMS.");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="teacher-modal event-modal">
        <div className="modal-header">
          <div>
            <h3>Send: {template.name}</h3>
            <p>Configure recipients and variables before sending.</p>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}><X size={18} /></button>
        </div>

        {result ? (
          <div className="form-section">
            <div className="state-card success">
              <strong>{result.sent} SMS sent successfully.</strong>
              {result.failed > 0 && <span> {result.failed} failed.</span>}
            </div>
            <div className="modal-footer">
              <button className="primary-button" onClick={() => { onSent(); onClose(); }}>Done</button>
            </div>
          </div>
        ) : (
          <div className="form-section">
            <div className="form-grid">
              <label>
                Recipients *
                <select value={recipients} onChange={(e) => setRecipients(e.target.value)}>
                  <option value="all">All Users</option>
                  <option value="parent">Parents</option>
                  <option value="teacher">Teachers</option>
                  <option value="student">Students</option>
                  <option value="staff">Staff</option>
                </select>
              </label>
              <label>
                Campus
                <select value={campus} onChange={(e) => setCampus(e.target.value)}>
                  <option value="">All Campuses</option>
                  {campuses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </label>
            </div>

            {template.variables.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>Variables</h4>
                <div className="form-grid">
                  {template.variables.map((v) => (
                    <label key={v}>
                      {v}
                      <input
                        value={variables[v] || ""}
                        onChange={(e) => setVariables((p) => ({ ...p, [v]: e.target.value }))}
                        placeholder={`Value for {${v}}`}
                      />
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <h4>Message Preview</h4>
              <div className="state-card" style={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 13 }}>
                {preview}
              </div>
              <small style={{ opacity: 0.5 }}>{preview.length} characters</small>
            </div>

            {error && <div className="state-card error"><strong>{error}</strong></div>}

            <div className="modal-footer">
              <button className="secondary-button" onClick={onClose} disabled={saving}>Cancel</button>
              <button className="primary-button" onClick={handleSend} disabled={saving}>
                <Send size={15} />
                {saving ? "Sending..." : "Send SMS"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function TemplatesPage() {
  const { hasRole } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [channelFilter, setChannelFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [sendingTemplate, setSendingTemplate] = useState(null);

  const canManage = hasRole(["super_admin", "admin"]);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const params = channelFilter ? `?channel=${channelFilter}` : "";
      const data = await apiFetch(`${TEMPLATES_URL}${params}`, {}, "Failed to load templates.");
      setTemplates(Array.isArray(data) ? data : []);
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, [channelFilter]);

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

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Communication / Templates"
        title="Message Templates"
        subtitle="Create reusable SMS and email templates with dynamic placeholders."
        action={
          canManage && (
            <button className="primary-button" onClick={() => { setEditingTemplate(null); setShowForm(true); }}>
              <Plus size={15} /> New Template
            </button>
          )
        }
      />

      <div className="panel">
        <PanelHeader
          title="Templates"
          subtitle="message templates"
          count={templates.length}
          action={
            <div className="filter-item">
              <select value={channelFilter} onChange={(e) => setChannelFilter(e.target.value)}>
                <option value="">All Channels</option>
                <option value="sms">SMS</option>
                <option value="email">Email</option>
                <option value="both">Both</option>
              </select>
            </div>
          }
        />

        <StateArea loading={loading}>
          {templates.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No templates"
              message="Create your first message template."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>NAME</th>
                    <th>CHANNEL</th>
                    <th>PREVIEW</th>
                    <th>VARIABLES</th>
                    <th>STATUS</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((t) => (
                    <tr key={t.id}>
                      <td><strong>{t.name}</strong></td>
                      <td><StatusBadge status={t.channel} /></td>
                      <td><small style={{ opacity: 0.7 }}>{t.body.substring(0, 80)}{t.body.length > 80 ? "..." : ""}</small></td>
                      <td>
                        {t.variables.length > 0
                          ? t.variables.map((v) => <span key={v} className="status-badge active" style={{ marginRight: 4 }}>{`{${v}}`}</span>)
                          : <small style={{ opacity: 0.5 }}>None</small>
                        }
                      </td>
                      <td><StatusBadge status={t.is_active ? "active" : "inactive"} /></td>
                      <td>
                        <div className="action-group">
                          {t.channel === "sms" && (
                            <button className="table-action" onClick={() => setSendingTemplate(t)}>
                              <Send size={14} /> Send
                            </button>
                          )}
                          <button className="table-action" onClick={() => { setEditingTemplate(t); setShowForm(true); }}>
                            Edit
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

      {sendingTemplate && (
        <SendFromTemplateModal
          template={sendingTemplate}
          onClose={() => setSendingTemplate(null)}
          onSent={fetchTemplates}
        />
      )}
    </section>
  );
}
