import { useState, useEffect } from "react";
import { X, Plus, Trash2 } from "lucide-react";

/**
 * Form for creating/editing workflow definitions.
 */
export function WorkflowDefinitionForm({ definition, onSave, onClose, loading = false }) {
  const [form, setForm] = useState({
    name: "",
    slug: "",
    object_type: "",
    states: ["draft", "pending_approval", "approved", "rejected"],
    initial_state: "draft",
    approval_steps: ["manager", "admin"],
    is_active: true,
  });

  const [newState, setNewState] = useState("");
  const [newStep, setNewStep] = useState("");

  useEffect(() => {
    if (definition) {
      setForm(definition);
    }
  }, [definition]);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const addState = () => {
    if (newState && !form.states.includes(newState)) {
      handleChange("states", [...form.states, newState]);
      setNewState("");
    }
  };

  const removeState = (state) => {
    handleChange("states", form.states.filter((s) => s !== state));
    if (form.initial_state === state) {
      handleChange("initial_state", form.states[0] || "");
    }
  };

  const addStep = () => {
    if (newStep && !form.approval_steps.includes(newStep)) {
      handleChange("approval_steps", [...form.approval_steps, newStep]);
      setNewStep("");
    }
  };

  const removeStep = (step) => {
    handleChange("approval_steps", form.approval_steps.filter((s) => s !== step));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (onSave) {
      await onSave(form);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 my-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            {definition ? "Edit Workflow" : "Create New Workflow"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={loading}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4 max-h-[70vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => handleChange("name", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">Slug *</label>
              <input
                type="text"
                value={form.slug}
                onChange={(e) => handleChange("slug", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={loading || !!definition}
                placeholder="e.g., hr.leave.request"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">Object Type *</label>
            <input
              type="text"
              value={form.object_type}
              onChange={(e) => handleChange("object_type", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={loading}
              placeholder="e.g., hr.leaverequest"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">States *</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newState}
                onChange={(e) => setNewState(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addState()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter state name"
                disabled={loading}
              />
              <button
                type="button"
                onClick={addState}
                className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
                disabled={loading}
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="flex gap-2 flex-wrap">
              {form.states.map((state) => (
                <div
                  key={state}
                  className="flex items-center gap-2 bg-blue-100 text-blue-800 px-3 py-1 rounded"
                >
                  <span className="text-sm">{state}</span>
                  {form.states.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeState(state)}
                      disabled={loading}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">Initial State *</label>
            <select
              value={form.initial_state}
              onChange={(e) => handleChange("initial_state", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={loading}
            >
              {form.states.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Approval Steps</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newStep}
                onChange={(e) => setNewStep(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addStep()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter role name (e.g., manager)"
                disabled={loading}
              />
              <button
                type="button"
                onClick={addStep}
                className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
                disabled={loading}
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {form.approval_steps.map((step, index) => (
                <div
                  key={step}
                  className="flex items-center gap-2 bg-purple-100 text-purple-800 px-3 py-2 rounded"
                >
                  <span className="text-xs font-semibold">#{index + 1}</span>
                  <span className="text-sm flex-1">{step}</span>
                  <button
                    type="button"
                    onClick={() => removeStep(step)}
                    disabled={loading}
                    className="text-purple-600 hover:text-purple-900"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => handleChange("is_active", e.target.checked)}
              className="w-4 h-4"
              disabled={loading}
            />
            <span className="text-sm text-gray-700">Active</span>
          </label>
        </form>

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
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
