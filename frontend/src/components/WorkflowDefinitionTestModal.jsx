import { useState } from "react";
import { X, Play } from "lucide-react";

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
      const response = await fetch(`/api/workflow/definitions/${definition.id}/test/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          from_state: fromState,
          action: action,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setTestResult(data);
      } else {
        const error = await response.json();
        setTestResult({ error: error.detail || "Test failed" });
      }
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-lg w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Test Workflow: {definition?.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={loading || testLoading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">Action</label>
            <select
              value={action}
              onChange={(e) => {
                setAction(e.target.value);
                setTestResult(null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={testLoading}
            >
              {Object.keys(definition?.transitions || {}).map((act) => (
                <option key={act} value={act}>
                  {act.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">From State</label>
            <select
              value={fromState}
              onChange={(e) => {
                setFromState(e.target.value);
                setTestResult(null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={testLoading}
            >
              {definition?.states?.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-600 mt-1">
              Allowed from:{" "}
              {getAllowedFromStates().length > 0
                ? getAllowedFromStates().join(", ")
                : "None"}
            </p>
          </div>

          {testResult && (
            <div
              className={`border rounded p-3 ${
                testResult.error
                  ? "bg-red-50 border-red-200"
                  : "bg-green-50 border-green-200"
              }`}
            >
              {testResult.error ? (
                <p className="text-sm text-red-800">
                  <span className="font-medium">Error:</span> {testResult.error}
                </p>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-green-800">
                    <span className="font-medium">✓ Valid Transition</span>
                  </p>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-700">
                      <span className="font-medium">From:</span> {testResult.from_state}
                    </p>
                    <p className="text-xs text-gray-700">
                      <span className="font-medium">To:</span> {testResult.to_state}
                    </p>
                    {testResult.approval_steps?.length > 0 && (
                      <p className="text-xs text-gray-700">
                        <span className="font-medium">Approvals:</span>{" "}
                        {testResult.approval_steps.length} step(s)
                      </p>
                    )}
                    {testResult.is_terminal && (
                      <p className="text-xs text-gray-700">
                        <span className="font-medium">Terminal State:</span> Yes
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 p-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            disabled={testLoading}
          >
            Close
          </button>
          <button
            onClick={handleTest}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            disabled={testLoading}
          >
            <Play className="w-4 h-4" />
            <span>{testLoading ? "Testing..." : "Test Transition"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
