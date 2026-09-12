import { CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react";

/**
 * Displays the current state of a workflow instance with visual indicator.
 */
export function WorkflowStateCard({ instance }) {
  const state = instance.current_state || "";

  const Icon =
    state === "approved"
      ? CheckCircle
      : state === "rejected"
        ? XCircle
        : state === "pending_approval"
          ? Clock
          : AlertCircle;

  const tone =
    state === "approved"
      ? "active"
      : state === "rejected"
        ? "inactive"
        : state === "pending_approval"
          ? "warn"
          : "info";

  const formatState = (value) =>
    (value || "unknown").replace(/_/g, " ").toUpperCase();

  const iconColor =
    state === "approved"
      ? "var(--success, #16a34a)"
      : state === "rejected"
        ? "var(--danger, #dc2626)"
        : state === "pending_approval"
          ? "var(--warning, #d97706)"
          : "var(--sky, #0ea5e9)";

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3 className="panel-title">Current State</h3>
          <p className="stat-label">Workflow instance status</p>
        </div>
        <Icon size={20} style={{ color: iconColor }} />
      </div>

      <div className="panel-body">
        <span className={`status-badge ${tone}`}>
          {formatState(state)}
        </span>
        {instance.is_terminal && (
          <p className="muted" style={{ marginTop: 8 }}>
            This workflow is terminal (complete)
          </p>
        )}
      </div>
    </div>
  );
}
