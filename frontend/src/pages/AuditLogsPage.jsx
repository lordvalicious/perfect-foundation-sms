import { useCallback, useEffect, useState } from "react";
import { ScrollText } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";

function formatTime(value) {
  if (!value) return "—";

  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  const loadLogs = useCallback(() => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();

    if (actionFilter) {
      params.append("action", actionFilter);
    }

    return fetch(`/api/audit/?${params.toString()}`, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load audit logs.");
        }

        return response.json();
      })
      .then((data) => {
        setLogs(Array.isArray(data) ? data : []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [actionFilter]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Audit Logs"
        title="Audit Logs"
        subtitle="A record of important actions across the system."
      />

      <div className="teacher-filter-panel">
        <select
          value={actionFilter}
          onChange={(event) =>
            setActionFilter(event.target.value)
          }
        >
          <option value="">All actions</option>
          <option value="login">Login</option>
          <option value="login_failed">Login Failed</option>
          <option value="logout">Logout</option>
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="delete">Delete</option>
        </select>

        <button
          className="primary-button"
          onClick={loadLogs}
        >
          Filter
        </button>
      </div>

      <div className="panel">
        <PanelHeader
          title="Audit Trail"
          subtitle="entries"
          count={logs.length}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={loadLogs}
        >
          {logs.length === 0 ? (
            <div className="empty-state">
              <ScrollText size={42} />
              <h3>No log entries</h3>
              <p>No audit entries match the current filter.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>TIMESTAMP</th>
                    <th>USER</th>
                    <th>ACTION</th>
                    <th>RECORD</th>
                    <th>IP ADDRESS</th>
                  </tr>
                </thead>

                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td>{formatTime(log.timestamp)}</td>

                      <td>
                        <strong>{log.user_name || "Anonymous"}</strong>
                      </td>

                      <td>
                        <span className="status-badge info">
                          {log.action_label || log.action}
                        </span>
                      </td>

                      <td>
                        {log.object_repr || log.model_name || "—"}
                      </td>

                      <td>{log.ip_address || "—"}</td>
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
