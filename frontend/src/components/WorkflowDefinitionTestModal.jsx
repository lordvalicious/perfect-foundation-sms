import { useState } from "react";
import { Play } from "lucide-react";
import { Modal } from "./Modal";
import { apiFetch } from "../api";

/**
 * Modal for testing workflow transitions.
 */
export function WorkflowDefinitionTestModal({ definition, onClose, loading = false }) {
  const [fromState, setFromState] = useState(definition?.initial_state || "");
  const [action, setAction] = useState("submit");
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);

  const handleTest = async () => {
    setTestLoading(true);
    try {
      const data = await apiFetch(`/api/workflow/definitions/${definition.id}/test/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from_state: fromState,
          action: action,
        }),
      });
      setTestResult(data);
    } catch (err) {
      setTestResult({ error: err.message });
    } finally {
      setTestLoading(false);
    }
  };

  const getTransitionConfig = () => {
    const transitions = definition?.transitions || {};
    const actionConfig = transitions[action];
    if (!actionConfig) return null;
    return actionConfig;
  };

  const getAllowedFromStates = () => {
    const config = getTransitionConfig();
    if (!config) return [];
    return config.from || [];
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Test Workflow: ${definition?.name}`}
      size="md"
      closeOnEscape
      closeOnOverlayClick
    >
      <label className="form-section">
        Action
        <select
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setTestResult(null);
          }}
          disabled={testLoading}
        >
          {Object.keys(definition?.transitions || {}).map((act) => (
            <option key={act} value={act}>
              {act.toUpperCase()}
            </option>
          ))}
        </select>
      </label>

      <label className="form-section">
        From State
        <select
          value={fromState}
          onChange={(e) => {
            setFromState(e.target.value);
            setTestResult(null);
          }}
          disabled={testLoading}
        >
          {definition?.states?.map((state) => (
            <option key={state} value={state}>
              {state}
            </option>
          ))}
        </select>
        <span className="form-hint">
          Allowed from:{" "}
          {getAllowedFromStates().length > 0
            ? getAllowedFromStates().join(", ")
            : "None"}
        </span>
      </label>

      {testResult && (
        <div className={`state-card ${testResult.error ? "error" : ""}`}>
          {testResult.error ? (
            <span>
              <strong>Error:</strong> {testResult.error}
            </span>
          ) : (
            <>
              <strong>✓ Valid Transition</strong>
              <span>From: {testResult.from_state}</span>
              <span>To: {testResult.to_state}</span>
              {testResult.approval_steps?.length > 0 && (
                <span>Approvals: {testResult.approval_steps.length} step(s)</span>
              )}
              {testResult.is_terminal && <span>Terminal State: Yes</span>}
            </>
          )}
        </div>
      )}

      <div className="modal-footer" style={{ marginTop: 12 }}>
        <button
          type="button"
          className="secondary-button"
          onClick={onClose}
          disabled={testLoading || loading}
        >
          Close
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={handleTest}
          disabled={testLoading || loading}
        >
          <Play className="w-4 h-4" />
          <span>{testLoading ? "Testing..." : "Test Transition"}</span>
        </button>
      </div>
    </Modal>
  );
}
