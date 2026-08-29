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

  const getActionColor = (action) => {
    if (action === "approve") return "bg-green-100 text-green-800";
    if (action === "reject") return "bg-red-100 text-red-800";
    if (action === "submit") return "bg-blue-100 text-blue-800";
    return "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-900">Workflow History</h3>
      <div className="space-y-3">
        {transitions.length === 0 ? (
          <p className="text-sm text-gray-500">No transitions yet</p>
        ) : (
          transitions
            .slice()
            .reverse()
            .map((transition, index) => (
              <div key={transition.id} className="border rounded p-3 bg-white">
                <div className="flex items-start gap-3">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getActionColor(transition.action)}`}>
                    {transition.action.toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {formatState(transition.from_state)}
                      </span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900">
                        {formatState(transition.to_state)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      By {transition.actor_name || "System"} at {formatDate(transition.created_at)}
                    </p>
                    {transition.comment && (
                      <p className="text-xs text-gray-700 mt-2 italic">"{transition.comment}"</p>
                    )}
                  </div>
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
