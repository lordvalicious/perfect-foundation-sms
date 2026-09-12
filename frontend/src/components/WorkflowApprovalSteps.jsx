import { CheckCircle, Clock, XCircle } from "lucide-react";

/**
 * Displays the approval queue steps in sequence.
 */
export function WorkflowApprovalSteps({ approvals }) {
  const getStatusIcon = (status) => {
    if (status === "approved") return <CheckCircle size={16} style={{ color: "var(--success, #16a34a)" }} />;
    if (status === "rejected") return <XCircle size={16} style={{ color: "var(--danger, #dc2626)" }} />;
    if (status === "pending") return <Clock size={16} style={{ color: "var(--warning, #d97706)" }} />;
    return null; // skipped
  };

  const tone = (status) => {
    if (status === "approved") return "active";
    if (status === "rejected") return "inactive";
    if (status === "pending") return "warn";
    return "info";
  };

  const formatRole = (role) => {
    return role.replace(/_/g, " ").toUpperCase();
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3 className="panel-title">Approval Queue</h3>
          <p className="stat-label">Sequential approval steps</p>
        </div>
      </div>

      <div className="panel-body">
        {approvals.length === 0 ? (
          <div className="state-card">No approvals required</div>
        ) : (
          <div className="overview-list">
            {approvals.map((approval, index) => (
              <div
                key={approval.id}
                style={{ alignItems: "flex-start" }}
              >
                <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  {getStatusIcon(approval.status)}
                  <strong>
                    Step {index + 1}: {formatRole(approval.role)}
                  </strong>
                </span>

                <span style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-end" }}>
                  <span className={`status-badge ${tone(approval.status)}`}>
                    {approval.status}
                  </span>
                  {approval.approver_name && (
                    <span>
                      {approval.status === "pending" ? "Waiting for" : "Approved by"}:{" "}
                      {approval.approver_name}
                    </span>
                  )}
                  {approval.comment && (
                    <span style={{ fontStyle: "italic" }}>
                      "{approval.comment}"
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
