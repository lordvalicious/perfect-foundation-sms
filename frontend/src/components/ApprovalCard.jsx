import { Clock, CheckCircle, XCircle } from "lucide-react";

/**
 * Card displaying a single pending approval for the approvals list.
 */
export function ApprovalCard({ approval, instance, onDecide, loading = false }) {
  const getStatusIcon = (status) => {
    if (status === "pending") return <Clock className="w-5 h-5 text-yellow-600" />;
    if (status === "approved") return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (status === "rejected") return <XCircle className="w-5 h-5 text-red-600" />;
    return null;
  };

  const formatRole = (role) => {
    return role.replace(/_/g, " ").toUpperCase();
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          {getStatusIcon(approval.status)}
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              {instance.definition_name}
            </h3>
            <p className="text-xs text-gray-600 mt-1">
              Step {approval.sequence + 1}: {formatRole(approval.role)}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${
          approval.status === "pending" ? "bg-yellow-100 text-yellow-800" :
          approval.status === "approved" ? "bg-green-100 text-green-800" :
          approval.status === "rejected" ? "bg-red-100 text-red-800" :
          "bg-gray-100 text-gray-800"
        }`}>
          {approval.status}
        </span>
      </div>

      <div className="mb-3 space-y-1 text-xs text-gray-600">
        <p>
          <span className="font-medium">Submitted by:</span> {instance.created_by_name}
        </p>
        <p>
          <span className="font-medium">Submitted at:</span> {formatDate(instance.created_at)}
        </p>
        {approval.decided_at && (
          <p>
            <span className="font-medium">Decided at:</span> {formatDate(approval.decided_at)}
          </p>
        )}
      </div>

      {approval.comment && (
        <div className="mb-3 p-2 bg-gray-50 rounded">
          <p className="text-xs text-gray-700 italic">"{approval.comment}"</p>
        </div>
      )}

      {approval.status === "pending" && (
        <button
          onClick={() => onDecide(approval)}
          className="w-full px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Processing..." : "Review & Decide"}
        </button>
      )}
    </div>
  );
}
