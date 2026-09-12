import { Edit, Trash2, FileText } from "lucide-react";
import { EmptyState } from "../pages/ui";

/**
 * Table of workflow definitions with CRUD actions.
 */
export function WorkflowDefinitionList({
  definitions,
  onEdit,
  onDelete,
  onTest,
  loading = false,
}) {
  if (definitions.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No workflow definitions found"
        message="Create a new workflow to start modelling business processes and approval queues."
      />
    );
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>NAME</th>
            <th>SLUG</th>
            <th>OBJECT TYPE</th>
            <th>STATES</th>
            <th>STEPS</th>
            <th style={{ textAlign: "right" }}>ACTIONS</th>
          </tr>
        </thead>

        <tbody>
          {definitions.map((def) => (
            <tr key={def.id}>
              <td>
                <strong>{def.name}</strong>
              </td>

              <td>
                <code className="cell-sub" style={{ background: "transparent", padding: 0 }}>
                  {def.slug}
                </code>
              </td>

              <td>
                <span className="cell-sub">{def.object_type}</span>
              </td>

              <td>
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {(def.states || []).map((state) => (
                    <span key={state} className="role-chip">
                      {state}
                    </span>
                  ))}
                </div>
              </td>

              <td>
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {(def.approval_steps || []).map((step) => (
                    <span key={step} className="role-chip secondary">
                      {step}
                    </span>
                  ))}
                </div>
              </td>

              <td>
                <div style={{ display: "flex", gap: 4, justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    className="table-action"
                    onClick={() => onTest(def)}
                    title="Test transitions"
                    disabled={loading}
                  >
                    <FileText size={15} />
                  </button>
                  <button
                    type="button"
                    className="table-action"
                    onClick={() => onEdit(def)}
                    title="Edit"
                    disabled={loading}
                  >
                    <Edit size={15} />
                  </button>
                  <button
                    type="button"
                    className="table-action danger"
                    onClick={() => onDelete(def)}
                    title="Delete"
                    disabled={loading}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
