import { useState, useEffect } from "react";
import { Plus, X, Trash2 } from "lucide-react";
import { Modal } from "./Modal";

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
    <Modal
      isOpen={true}
      onClose={onClose}
      title={definition ? "Edit Workflow" : "Create New Workflow"}
      size="lg"
      closeOnEscape={!loading}
      closeOnOverlayClick={!loading}
    >
      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <label>
            Name *
            <input
              type="text"
              value={form.name}
              onChange={(e) => handleChange("name", e.target.value)}
              required
              disabled={loading}
            />
          </label>

          <label>
            Slug *
            <input
              type="text"
              value={form.slug}
              onChange={(e) => handleChange("slug", e.target.value)}
              required
              disabled={loading || !!definition}
              placeholder="e.g., hr.leave.request"
            />
          </label>

          <label>
            Object Type *
            <input
              type="text"
              value={form.object_type}
              onChange={(e) => handleChange("object_type", e.target.value)}
              required
              disabled={loading}
              placeholder="e.g., hr.leaverequest"
            />
          </label>
        </div>

        <div className="form-section">
          <label>
            States *
            <input
              type="text"
              value={newState}
              onChange={(e) => setNewState(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && addState()}
              disabled={loading}
              placeholder="Enter state name"
            />
          </label>

          <div
            style={{
              display: "flex",
              gap: 4,
              flexWrap: "wrap",
              margin: "8px 2px 0",
            }}
          >
            {form.states.map((state) => (
              <span key={state} className="role-chip">
                {state}
                {form.states.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeState(state)}
                    disabled={loading}
                    aria-label={`Remove state ${state}`}
                    style={{
                      display: "inline-flex",
                      marginLeft: 6,
                      color: "inherit",
                      background: "none",
                      border: 0,
                      padding: 0,
                      cursor: loading ? "not-allowed" : "pointer",
                    }}
                  >
                    <X size={12} />
                  </button>
                )}
              </span>
            ))}
          </div>

          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button
              type="button"
              className="secondary-button"
              onClick={addState}
              disabled={loading}
            >
              <Plus size={14} /> Add state
            </button>
          </div>
        </div>

        <div className="form-section">
          <label>
            Initial State *
            <select
              value={form.initial_state}
              onChange={(e) => handleChange("initial_state", e.target.value)}
              required
              disabled={loading}
            >
              {form.states.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-section">
          <label>
            Approval Steps
            <input
              type="text"
              value={newStep}
              onChange={(e) => setNewStep(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && addStep()}
              disabled={loading}
              placeholder="Enter role name (e.g., manager)"
            />
          </label>

          <div
            style={{
              display: "flex",
              gap: 4,
              flexWrap: "wrap",
              margin: "8px 2px 0",
            }}
          >
            {form.approval_steps.map((step, index) => (
              <span key={step} className="role-chip secondary">
                #{index + 1} {step}
                <button
                  type="button"
                  onClick={() => removeStep(step)}
                  disabled={loading}
                  aria-label={`Remove approval step ${step}`}
                  style={{
                    display: "inline-flex",
                    marginLeft: 6,
                    color: "inherit",
                    background: "none",
                    border: 0,
                    padding: 0,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}
                >
                  <Trash2 size={12} />
                </button>
              </span>
            ))}
          </div>

          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button
              type="button"
              className="secondary-button"
              onClick={addStep}
              disabled={loading}
            >
              <Plus size={14} /> Add step
            </button>
          </div>
        </div>

        <label className="checkbox-label" style={{ marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={Boolean(form.is_active)}
            onChange={(e) => handleChange("is_active", e.target.checked)}
            disabled={loading}
          />
          <span>Active</span>
        </label>
      </form>

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
          {loading ? "Saving..." : "Save"}
        </button>
      </div>
    </Modal>
  );
}
