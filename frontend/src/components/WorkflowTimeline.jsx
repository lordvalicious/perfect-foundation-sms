import { ArrowRight } from "lucide-react";

/**
 * Displays the workflow transition history as a timeline.
 */
export function WorkflowTimeline({ transitions }) {
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  const formatState = (state) => {
    if (!state) return "(start)";
    return state.replace(/_/g, " ").toUpperCase();
  };

  const actionTone = (action) => {
    if (action === "approve") return "active";
    if (action === "reject") return "inactive";
    if (action === "submit") return "info";
    return "warn";
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3 className="panel-title">Workflow History</h3>
          <p className="stat-label">Transition timeline</p>
        </div>
      </div>

      <div className="panel-body">
        {transitions.length === 0 ? (
          <div className="state-card">No transitions yet</div>
        ) : (
          <div className="overview-list">
            {transitions
              .slice()
              .reverse()
              .map((transition) => (
                <div key={transition.id} style={{ alignItems: "flex-start" }}>
                  <span style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <strong>
                      {formatState(transition.from_state)}{" "}
                      <ArrowRight size={13} style={{ verticalAlign: "-2px" }} />{" "}
                      {formatState(transition.to_state)}
                    </strong>
                    <span>
                      By {transition.actor_name || "System"} at{" "}
                      {formatDate(transition.created_at)}
                    </span>
                    {transition.comment && (
                      <span style={{ fontStyle: "italic" }}>
                        "{transition.comment}"
                      </span>
                    )}
                  </span>
                  <span className={`status-badge ${actionTone(transition.action)}`}>
                    {String(transition.action || "").toUpperCase()}
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
