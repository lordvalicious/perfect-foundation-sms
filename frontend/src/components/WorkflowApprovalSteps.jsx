import { CheckCircle, Clock, XCircle } from "lucide-react";

/**
 * Displays the approval queue steps in sequence.
 */
export function WorkflowApprovalSteps({ approvals }) {
  const getStatusIcon = (status) => {
    if (status === "approved") return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (status === "rejected") return <XCircle className="w-5 h-5 text-red-600" />;
    if (status === "pending") return <Clock className="w-5 h-5 text-yellow-600" />;
    return <CheckCircle className="w-5 h-5 text-gray-400" />; // skipped
  };

  const getStatusBg = (status) => {
    if (status === "approved") return "bg-green-50";
    if (status === "rejected") return "bg-red-50";
    if (status === "pending") return "bg-yellow-50";
    return "bg-gray-50";
  };

  const formatRole = (role) => {
    return role.replace(/_/g, " ").toUpperCase();
  };

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-900">Approval Queue</h3>
      <div className="space-y-2">
        {approvals.length === 0 ? (
          <p className="text-sm text-gray-500">No approvals required</p>
        ) : (
          approvals.map((approval, index) => (
            <div key={approval.id} className={`border rounded p-3 ${getStatusBg(approval.status)}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  {getStatusIcon(approval.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Step {index + 1}: {formatRole(approval.role)}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      Status: <span className="font-medium capitalize">{approval.status}</span>
                    </p>
                    {approval.approver_name && (
                      <p className="text-xs text-gray-600">
                        {approval.status === "pending" ? "Waiting for" : "Approved by"}: {approval.approver_name}
                      </p>
                    )}
                    {approval.comment && (
                      <p className="text-xs text-gray-700 mt-2 italic">"{approval.comment}"</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
