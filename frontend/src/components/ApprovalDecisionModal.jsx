import { useState } from "react";
import { Send } from "lucide-react";
import { Modal } from "./Modal";

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
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Make Decision"
      size="md"
      closeOnEscape
      closeOnOverlayClick
    >
      <div className="form-section">
        <span className="form-hint">Approval Step</span>
        <p className="muted" style={{ marginTop: 4 }}>{formatRole(approval.role)}</p>
      </div>

      <div className="form-section">
        <span className="form-hint">Decision</span>
        <div style={{ display: "flex", gap: 16, marginTop: 6 }}>
          <label className="checkbox-label">
            <input
              type="radio"
              value="approve"
              checked={decision === "approve"}
              onChange={(e) => setDecision(e.target.value)}
              disabled={loading}
            />
            <span>Approve</span>
          </label>
          <label className="checkbox-label">
            <input
              type="radio"
              value="reject"
              checked={decision === "reject"}
              onChange={(e) => setDecision(e.target.value)}
              disabled={loading}
            />
            <span>Reject</span>
          </label>
        </div>
      </div>

      <label className="form-section">
        Comment (optional)
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Add a comment..."
          rows="3"
          disabled={loading}
        />
      </label>

      <div className="modal-footer" style={{ marginTop: 12 }}>
        <button
          type="button"
          className="secondary-button"
          onClick={onClose}
          disabled={loading}
        >
          Cancel
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={handleSubmit}
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
    </Modal>
  );
}