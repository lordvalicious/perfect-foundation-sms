import { useEffect, useState } from "react";
import { MessageSquare, Send, Settings2, AlertCircle, CheckCircle, XCircle } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";

const API_BASE = "/api/communication";

const ROLES = [
  { value: "parent", label: "Parents" },
  { value: "teacher", label: "Teachers" },
  { value: "student", label: "Students" },
  { value: "staff", label: "Staff" },
];

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return null;
}

function authHeaders(extra = {}) {
  return {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken") || "",
    ...extra,
  };
}

function StatusIcon({ status }) {
  if (status === "sent") return <CheckCircle size={14} className="text-green-500" />;
  if (status === "failed") return <XCircle size={14} className="text-red-500" />;
  return <AlertCircle size={14} className="text-yellow-500" />;
}

export default function SMSPage() {
  const [tab, setTab] = useState("send");
  const [message, setMessage] = useState("");
  const [role, setRole] = useState("");
  const [campusId, setCampusId] = useState("");
  const [campuses, setCampuses] = useState([]);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logFilter, setLogFilter] = useState("");
  const [prefs, setPrefs] = useState(null);
  const [prefsLoading, setPrefsLoading] = useState(true);
  const [prefsSaving, setPrefsSaving] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/sms/logs/?${logFilter ? `status=${logFilter}` : ""}`, {
      credentials: "include",
    })
      .then((r) => r.json())
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLogsLoading(false));
  }, [logFilter]);

  useEffect(() => {
    fetch(`${API_BASE}/notification-preferences/`, {
      credentials: "include",
    })
      .then((r) => r.json())
      .then(setPrefs)
      .catch(() => {})
      .finally(() => setPrefsLoading(false));
  }, []);

  useEffect(() => {
    fetch("/api/schools/campuses/", { credentials: "include" })
      .then((r) => r.json())
      .then((data) => setCampuses(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setSending(true);
    setSendResult(null);

    try {
      const body = { message: message.trim() };
      if (campusId) body.campus_id = Number(campusId);
      if (role) body.role = role;

      const res = await fetch(`${API_BASE}/sms/send/`, {
        method: "POST",
        credentials: "include",
        headers: authHeaders(),
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        setSendResult({ ok: false, text: data.detail || "Failed to send." });
      } else {
        setSendResult({
          ok: true,
          text: `Sent: ${data.sent} | Failed: ${data.failed} | Total: ${data.total_recipients}`,
        });
        setMessage("");
      }
    } catch (err) {
      setSendResult({ ok: false, text: err.message });
    } finally {
      setSending(false);
    }
  };

  const handlePrefChange = async (field, value) => {
    const updated = { ...prefs, [field]: value };
    setPrefs(updated);
    setPrefsSaving(true);
    try {
      await fetch(`${API_BASE}/notification-preferences/`, {
        method: "PUT",
        credentials: "include",
        headers: authHeaders(),
        body: JSON.stringify({ [field]: value }),
      });
    } catch {
      setPrefs({ ...prefs });
    } finally {
      setPrefsSaving(false);
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / SMS Notifications"
        title="SMS Notifications"
        subtitle="Send SMS messages and manage notification preferences."
      />

      <div className="tabs" style={{ marginBottom: 16 }}>
        <button
          className={`tab ${tab === "send" ? "active" : ""}`}
          onClick={() => setTab("send")}
        >
          <Send size={14} /> Send SMS
        </button>
        <button
          className={`tab ${tab === "logs" ? "active" : ""}`}
          onClick={() => setTab("logs")}
        >
          <MessageSquare size={14} /> SMS Logs
        </button>
        <button
          className={`tab ${tab === "prefs" ? "active" : ""}`}
          onClick={() => setTab("prefs")}
        >
          <Settings2 size={14} /> Preferences
        </button>
      </div>

      {tab === "send" && (
        <div className="panel" style={{ padding: 24, maxWidth: 640 }}>
          <PanelHeader title="Send SMS Broadcast" />

          {sendResult && (
            <div
              className={`alert ${sendResult.ok ? "alert-success" : "alert-error"}`}
              style={{ marginBottom: 16 }}
            >
              {sendResult.text}
            </div>
          )}

          <form onSubmit={handleSend}>
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label">Recipient Group</label>
              <select
                className="form-input"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="">All users with phone numbers</option>
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label">Filter by Campus</label>
              <select
                className="form-input"
                value={campusId}
                onChange={(e) => setCampusId(e.target.value)}
              >
                <option value="">All campuses</option>
                {campuses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label">Message</label>
              <textarea
                className="form-input"
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your SMS message here..."
                required
              />
              <small style={{ color: "var(--text-muted)" }}>
                {message.length}/160 characters
                {message.length > 160 && " (will be sent as multiple SMS)"}
              </small>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={sending || !message.trim()}
            >
              {sending ? "Sending..." : "Send SMS"}
            </button>
          </form>
        </div>
      )}

      {tab === "logs" && (
        <div className="panel" style={{ padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <PanelHeader title="SMS Logs" />
            <select
              className="form-input"
              style={{ width: "auto", marginLeft: "auto" }}
              value={logFilter}
              onChange={(e) => setLogFilter(e.target.value)}
            >
              <option value="">All statuses</option>
              <option value="sent">Sent</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <StateArea loading={logsLoading} error="" rows={logs.results || []}>
            <table className="table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Phone</th>
                  <th>Message</th>
                  <th>Sent By</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {(logs.results || []).map((log) => (
                  <tr key={log.id}>
                    <td>
                      <StatusIcon status={log.status} />
                      <span style={{ marginLeft: 4, textTransform: "capitalize" }}>
                        {log.status}
                      </span>
                    </td>
                    <td>{log.phone_number}</td>
                    <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {log.message}
                    </td>
                    <td>{log.sent_by_name || "System"}</td>
                    <td>{new Date(log.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </StateArea>
        </div>
      )}

      {tab === "prefs" && (
        <div className="panel" style={{ padding: 24, maxWidth: 500 }}>
          <PanelHeader title="Notification Preferences" />

          {prefsLoading ? (
            <p>Loading...</p>
          ) : prefs ? (
            <div>
              <PrefToggle
                label="SMS Notifications"
                desc="Enable SMS delivery for notifications"
                value={prefs.sms_enabled}
                onChange={(v) => handlePrefChange("sms_enabled", v)}
              />
              <PrefToggle
                label="Email Notifications"
                desc="Enable email delivery"
                value={prefs.email_enabled}
                onChange={(v) => handlePrefChange("email_enabled", v)}
              />
              <PrefToggle
                label="In-App Notifications"
                desc="Show notifications in the bell dropdown"
                value={prefs.push_enabled}
                onChange={(v) => handlePrefChange("push_enabled", v)}
              />
              <hr style={{ margin: "16px 0", borderColor: "var(--border)" }} />
              <PrefToggle
                label="Attendance Alerts"
                desc="SMS when your child is absent"
                value={prefs.attendance_alerts}
                onChange={(v) => handlePrefChange("attendance_alerts", v)}
              />
              <PrefToggle
                label="Payment Reminders"
                desc="SMS for fee payment due dates"
                value={prefs.payment_reminders}
                onChange={(v) => handlePrefChange("payment_reminders", v)}
              />
              <PrefToggle
                label="Result Notifications"
                desc="SMS when exam results are published"
                value={prefs.result_notifications}
                onChange={(v) => handlePrefChange("result_notifications", v)}
              />
              <PrefToggle
                label="Announcement SMS"
                desc="SMS for important announcements"
                value={prefs.announcement_sms}
                onChange={(v) => handlePrefChange("announcement_sms", v)}
              />
              {prefsSaving && (
                <small style={{ color: "var(--text-muted)" }}>Saving...</small>
              )}
            </div>
          ) : (
            <p>Could not load preferences.</p>
          )}
        </div>
      )}
    </section>
  );
}

function PrefToggle({ label, desc, value, onChange }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "12px 0",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div>
        <div style={{ fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{desc}</div>
      </div>
      <label className="toggle">
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="toggle-slider" />
      </label>
    </div>
  );
}
