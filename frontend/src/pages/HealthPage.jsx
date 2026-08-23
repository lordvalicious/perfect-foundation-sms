import { useCallback, useEffect, useState } from "react";
import { Activity, Database, RefreshCw, Server, Users } from "lucide-react";
import { apiFetch } from "../api";
import { PageHeader, StateArea } from "./ui";
import { formatDate } from "./format";

const HEALTH_URL = "/api/reports/health/";

function StatusIndicator({ status }) {
  const colors = {
    healthy: "#27ae60",
    degraded: "#f39c12",
    error: "#e74c3c",
  };
  const labels = {
    healthy: "Healthy",
    degraded: "Degraded",
    error: "Error",
  };

  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      fontSize: 13,
      fontWeight: 600,
      color: colors[status] || "#999",
    }}>
      <span style={{
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: colors[status] || "#999",
      }} />
      {labels[status] || status}
    </span>
  );
}

export default function HealthPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      const data = await apiFetch(HEALTH_URL, {}, "Failed to load health data.");
      setHealth(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / System / Health"
        title="System Health Monitor"
        subtitle="Monitor database, API, users, and system status in real-time."
        action={
          <button
            className="secondary-button"
            onClick={() => fetchHealth(true)}
            disabled={refreshing}
          >
            <RefreshCw size={14} className={refreshing ? "spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        }
      />

      <StateArea loading={loading} error={error} onRetry={() => fetchHealth()}>
        {health && (
          <>
            {/* Overall Status */}
            <div className="stats-grid" style={{ marginBottom: 24 }}>
              <div className="stat-card">
                <div className="stat-icon" style={{ color: health.overall_status === "healthy" ? "#27ae60" : "#f39c12" }}>
                  <Activity size={21} />
                </div>
                <div>
                  <h3><StatusIndicator status={health.overall_status} /></h3>
                  <p>Overall System Status</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon"><Database size={21} /></div>
                <div>
                  <h3>
                    <StatusIndicator status={health.database?.status} />
                    <span style={{ fontSize: 12, marginLeft: 4, opacity: 0.6 }}>
                      {health.database?.response_ms}ms
                    </span>
                  </h3>
                  <p>Database</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon"><Users size={21} /></div>
                <div>
                  <h3>{health.users?.active_today || 0}</h3>
                  <p>Active Users Today</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon"><Server size={21} /></div>
                <div>
                  <h3>{health.users?.total || 0}</h3>
                  <p>Total Users</p>
                </div>
              </div>
            </div>

            {/* Database */}
            <div className="panel">
              <div className="teacher-list-header">
                <h3><Database size={16} /> Database</h3>
              </div>
              <div className="form-section">
                <div className="form-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Status</div>
                    <StatusIndicator status={health.database?.status} />
                  </div>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Response Time</div>
                    <strong>{health.database?.response_ms || 0}ms</strong>
                  </div>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Engine</div>
                    <strong>{health.database?.engine?.split(".")?.pop() || "N/A"}</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* Record Counts */}
            <div className="panel">
              <div className="teacher-list-header">
                <h3>Record Counts</h3>
              </div>
              <div className="form-section">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 12 }}>
                  {Object.entries(health.records || {}).map(([key, count]) => (
                    <div key={key} style={{ background: "#f5f5f5", padding: 12, borderRadius: 8, textAlign: "center" }}>
                      <div style={{ fontSize: 20, fontWeight: 700 }}>{count.toLocaleString()}</div>
                      <div style={{ fontSize: 12, color: "#666", textTransform: "capitalize" }}>
                        {key.replace(/_/g, " ")}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* System Info */}
            <div className="panel">
              <div className="teacher-list-header">
                <h3>System Information</h3>
              </div>
              <div className="form-section">
                <div className="form-grid" style={{ gridTemplateColumns: "repeat(2, 1fr)" }}>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Python Version</div>
                    <strong>{health.system?.python_version || "N/A"}</strong>
                  </div>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Platform</div>
                    <strong style={{ fontSize: 13 }}>{health.system?.platform || "N/A"}</strong>
                  </div>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Debug Mode</div>
                    <strong style={{ color: health.system?.debug_mode ? "#e74c3c" : "#27ae60" }}>
                      {health.system?.debug_mode ? "ON" : "OFF"}
                    </strong>
                  </div>
                  <div style={{ background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#666" }}>Hostname</div>
                    <strong style={{ fontSize: 13 }}>{health.system?.hostname || "N/A"}</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            {health.recent_activity?.length > 0 && (
              <div className="panel">
                <div className="teacher-list-header">
                  <h3>Recent Activity</h3>
                </div>
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ACTION</th>
                        <th>USER</th>
                        <th>TIMESTAMP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {health.recent_activity.map((log, i) => (
                        <tr key={i}>
                          <td><strong>{log.action}</strong></td>
                          <td>{log.user}</td>
                          <td>{formatDate(log.timestamp)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </StateArea>
    </section>
  );
}
