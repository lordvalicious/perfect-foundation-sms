import { useState } from "react";
import { X, Send } from "lucide-react";

/**
 * Modal for approving or rejecting a workflow approval.
 */
export function ApprovalDecisionModal({ approval, onClose, onDecide, loading = false }) {
  const [decision, setDecision] = useState("approve");
  const [comment, setComment] = useState("");

  const handleSubmit = async () => {
    if (onDecide) {
      await onDecide(decision, comment);
    }
  };

  const formatRole = (role) => {
    return role.replace(/_/g, " ").toUpperCase();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-lg w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Make Decision</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={loading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <p className="text-sm text-gray-600">Approval Step</p>
            <p className="text-sm font-medium text-gray-900">{formatRole(approval.role)}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Decision</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="approve"
                  checked={decision === "approve"}
                  onChange={(e) => setDecision(e.target.value)}
                  className="w-4 h-4"
                  disabled={loading}
                />
                <span className="text-sm text-gray-700">Approve</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="reject"
                  checked={decision === "reject"}
                  onChange={(e) => setDecision(e.target.value)}
                  className="w-4 h-4"
                  disabled={loading}
                />
                <span className="text-sm text-gray-700">Reject</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Comment (optional)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Add a comment..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              disabled={loading}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 p-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            disabled={loading}
          >
            {loading && <span>Saving...</span>}
            {!loading && (
              <>
                <Send className="w-4 h-4" />
                <span>Submit Decision</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
