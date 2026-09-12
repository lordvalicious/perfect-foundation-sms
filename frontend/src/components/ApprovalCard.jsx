import { Clock, CheckCircle, XCircle, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * Card displaying a single pending approval for the approvals list.
 */
export function ApprovalCard({ approval, instance, onDecide, loading = false }) {
  const tone =
    approval.status === "approved"
      ? "active"
      : approval.status === "rejected"
        ? "inactive"
        : approval.status === "pending"
          ? "warn"
          : "info";

  const getStatusIcon = (status) => {
    const color =
      status === "approved"
        ? "var(--success, #16a34a)"
        : status === "rejected"
          ? "var(--danger, #dc2626)"
          : "var(--warning, #d97706)";
    if (status === "approved") return <CheckCircle size={18} style={{ color }} />;
    if (status === "rejected") return <XCircle size={18} style={{ color }} />;
    return <Clock size={18} style={{ color }} />;
  };

  const formatRole = (role) => {
    return role.replace(/_/g, " ").toUpperCase();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString();
  };

  const canViewInstance = Boolean(approval.instance && Object.keys(instance).length > 0);

  return (
    <div className="panel">
      <div className="panel-body">
        <div
          className="overview-list"
          style={{ marginBottom: 12 }}
        >
          <div>
            <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {getStatusIcon(approval.status)}
              <strong>
                {instance.definition_name || instance.name || "Workflow"}
              </strong>
            </span>
            <span className={`status-badge ${tone}`}>
              {approval.status}
            </span>
          </div>

          <div>
            <span>
              Step {(approval.sequence || 0) + 1}: {formatRole(approval.role)}
            </span>
          </div>

          <div>
            <span>Submitted by: {instance.created_by_name || "—"}</span>
            <span>Submitted at: {formatDate(instance.created_at)}</span>
          </div>

          {approval.decided_at && (
            <div>
              <span>Decided at: {formatDate(approval.decided_at)}</span>
            </div>
          )}
        </div>

        {approval.comment && (
          <div className="state-card" style={{ padding: "10px 14px" }}>
            <span style={{ fontStyle: "italic" }}>"{approval.comment}"</span>
          </div>
        )}

        <div className="filter-row" style={{ justifyContent: "flex-end" }}>
          {canViewInstance && (
            <Link
              to={`/workflow/instances/${approval.instance}/`}
              className="secondary-button"
            >
              View details <ArrowRight size={14} />
            </Link>
          )}

          {approval.status === "pending" && (
            <button
              type="button"
              className="primary-button"
              onClick={() => onDecide(approval)}
              disabled={loading}
            >
              {loading ? "Processing..." : "Review & Decide"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
