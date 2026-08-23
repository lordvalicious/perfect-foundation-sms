import { useCallback, useEffect, useState } from "react";
import { Fragment } from "react";
import { Download, Filter, ScrollText, ChevronDown, ChevronUp } from "lucide-react";
import { apiFetch, apiDownload } from "../api";
import { PageHeader, PanelHeader, StateArea, EmptyState } from "./ui";

const AUDIT_URL = "/api/audit/";
const ACTIONS_URL = "/api/audit/actions/";

function formatTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

function getActionColor(action) {
  const colors = {
    login_failed: "error",
    delete: "error",
    payment_reversal: "error",
    payment_refund: "error",
    password_reset: "error",
    login: "active",
    logout: "info",
    create: "active",
    update: "info",
    payment: "active",
    invoice: "active",
    grade_publish: "active",
    grade_amendment: "warning",
  };
  return colors[action] || "info";
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [actions, setActions] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    apiFetch(ACTIONS_URL, {}, "").then((data) => {
      setActions(Array.isArray(data) ? data : []);
    }).catch(() => {});
  }, []);

  const loadLogs = useCallback(async (pageNum = 1) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      params.append("page", pageNum);
      params.append("page_size", "50");
      if (actionFilter) params.append("action", actionFilter);
      if (search) params.append("search", search);
      if (dateFrom) params.append("date_from", dateFrom);
      if (dateTo) params.append("date_to", dateTo);

      const response = await fetch(`${AUDIT_URL}?${params}`, { credentials: "include" });
      if (!response.ok) throw new Error("Failed to load audit logs.");

      const data = await response.json();
      if (data.results) {
        setLogs(data.results);
        setTotalCount(data.count || 0);
      } else {
        setLogs(Array.isArray(data) ? data : []);
        setTotalCount(Array.isArray(data) ? data.length : 0);
      }
      setPage(pageNum);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [actionFilter, search, dateFrom, dateTo]);

  useEffect(() => {
    loadLogs(1);
  }, [loadLogs]);

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams();
      params.append("format", "csv");
      if (actionFilter) params.append("action", actionFilter);
      if (search) params.append("search", search);
      if (dateFrom) params.append("date_from", dateFrom);
      if (dateTo) params.append("date_to", dateTo);
      await apiDownload(`${AUDIT_URL}?${params}`, "audit_logs.csv");
    } catch {
      // ignore
    } finally {
      setExporting(false);
    }
  };

  const clearFilters = () => {
    setActionFilter("");
    setSearch("");
    setDateFrom("");
    setDateTo("");
  };

  const hasActiveFilters = actionFilter || search || dateFrom || dateTo;
  const totalPages = Math.ceil(totalCount / 50);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Audit Logs"
        title="Audit Logs"
        subtitle="A record of important actions across the system."
        action={
          <button className="secondary-button" onClick={handleExportCSV} disabled={exporting}>
            <Download size={14} />
            {exporting ? "Exporting..." : "Export CSV"}
          </button>
        }
      />

      <div className="panel">
        <div className="teacher-filter-panel" style={{ flexWrap: "wrap", gap: 8, padding: "12px 16px" }}>
          <div className="filter-item" style={{ position: "relative", flex: 2, minWidth: 200 }}>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by user, model, or record..."
            />
          </div>
          <div className="filter-item">
            <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
              <option value="">All Actions</option>
              {actions.map((a) => (
                <option key={a.value} value={a.value}>{a.label}</option>
              ))}
            </select>
          </div>
          <div className="filter-item">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              title="From date"
            />
          </div>
          <div className="filter-item">
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              title="To date"
            />
          </div>
          {hasActiveFilters && (
            <button className="secondary-button" onClick={clearFilters}>
              <Filter size={14} /> Clear
            </button>
          )}
        </div>
      </div>

      <div className="panel">
        <PanelHeader
          title="Audit Trail"
          subtitle="entries"
          count={totalCount}
        />

        <StateArea loading={loading} error={error} onRetry={() => loadLogs(page)}>
          {logs.length === 0 ? (
            <EmptyState
              icon={ScrollText}
              title="No log entries"
              message="No audit entries match the current filters."
            />
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: 30 }}></th>
                      <th>TIMESTAMP</th>
                      <th>USER</th>
                      <th>ACTION</th>
                      <th>MODEL</th>
                      <th>RECORD</th>
                      <th>IP ADDRESS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <Fragment key={log.id}>
                        <tr
                          key={log.id}
                          style={{ cursor: log.details && Object.keys(log.details).length > 0 ? "pointer" : "default" }}
                          onClick={() => {
                            if (log.details && Object.keys(log.details).length > 0) {
                              setExpandedId(expandedId === log.id ? null : log.id);
                            }
                          }}
                        >
                          <td>
                            {log.details && Object.keys(log.details).length > 0 && (
                              expandedId === log.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                            )}
                          </td>
                          <td><small>{formatTime(log.timestamp)}</small></td>
                          <td><strong>{log.user_name || "Anonymous"}</strong></td>
                          <td>
                            <span className={`status-badge ${getActionColor(log.action)}`}>
                              {log.action_label || log.action}
                            </span>
                          </td>
                          <td><small>{log.model_name || "—"}</small></td>
                          <td>{log.object_repr || "—"}</td>
                          <td><small style={{ opacity: 0.6 }}>{log.ip_address || "—"}</small></td>
                        </tr>
                        {expandedId === log.id && log.details && (
                          <tr key={`${log.id}-details`}>
                            <td colSpan={7} style={{ background: "#f8f9fa", padding: 12 }}>
                              <strong style={{ fontSize: 12 }}>Details:</strong>
                              <pre style={{
                                marginTop: 4,
                                padding: 8,
                                background: "#fff",
                                borderRadius: 4,
                                border: "1px solid #e0e0e0",
                                fontSize: 12,
                                overflow: "auto",
                                maxHeight: 200,
                              }}>
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: 16 }}>
                  <button
                    className="secondary-button"
                    onClick={() => loadLogs(page - 1)}
                    disabled={page <= 1}
                  >
                    Previous
                  </button>
                  <span style={{ lineHeight: "32px", fontSize: 13 }}>
                    Page {page} of {totalPages} ({totalCount} entries)
                  </span>
                  <button
                    className="secondary-button"
                    onClick={() => loadLogs(page + 1)}
                    disabled={page >= totalPages}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </StateArea>
      </div>
    </section>
  );
}
