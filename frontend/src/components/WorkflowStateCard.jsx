import { useEffect, useState } from "react";
import { CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react";

/**
 * Displays the current state of a workflow instance with visual indicator.
 */
export function WorkflowStateCard({ instance, definition }) {
  const getStateColor = (state) => {
    if (state === "approved") return "bg-green-50 border-green-200";
    if (state === "rejected") return "bg-red-50 border-red-200";
    if (state === "draft") return "bg-gray-50 border-gray-200";
    if (state === "pending_approval") return "bg-yellow-50 border-yellow-200";
    return "bg-blue-50 border-blue-200";
  };

  const getStateIcon = (state) => {
    if (state === "approved") return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (state === "rejected") return <XCircle className="w-5 h-5 text-red-600" />;
    if (state === "pending_approval") return <Clock className="w-5 h-5 text-yellow-600" />;
    return <AlertCircle className="w-5 h-5 text-blue-600" />;
  };

  const formatState = (state) => {
    return state.replace(/_/g, " ").toUpperCase();
  };

  return (
    <div className={`border rounded-lg p-4 ${getStateColor(instance.current_state)}`}>
      <div className="flex items-center gap-3">
        {getStateIcon(instance.current_state)}
        <div>
          <p className="text-sm font-medium text-gray-600">Current State</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatState(instance.current_state)}
          </p>
          {instance.is_terminal && (
            <p className="text-xs text-gray-600 mt-1">This workflow is terminal (complete)</p>
          )}
        </div>
      </div>
    </div>
  );
}
