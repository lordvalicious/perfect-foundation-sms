import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { PageHeader, StateArea } from "./ui";
import { WorkflowDefinitionList } from "../components/WorkflowDefinitionList";
import { WorkflowDefinitionForm } from "../components/WorkflowDefinitionForm";
import { WorkflowDefinitionTestModal } from "../components/WorkflowDefinitionTestModal";
import { Modal } from "../components/Modal";
import { apiFetch } from "../api";

const API_URL = "/api/workflow/definitions/";

export default function WorkflowDefinitionAdminPage() {
  const [definitions, setDefinitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [showTest, setShowTest] = useState(false);
  const [selectedDefinition, setSelectedDefinition] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  const fetchDefinitions = useCallback(async () => {
    try {
      setError("");
      setLoading(true);
      const data = await apiFetch(API_URL);
      setDefinitions(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDefinitions();
  }, [fetchDefinitions]);

  const handleCreate = () => {
    setSelectedDefinition(null);
    setShowForm(true);
  };

  const handleEdit = (definition) => {
    setSelectedDefinition(definition);
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;

    try {
      setFormLoading(true);
      await apiFetch(`${API_URL}${deleteTarget.id}/`, {
        method: "DELETE",
      });
      setDefinitions((current) =>
        current.filter((d) => d.id !== deleteTarget.id)
      );
      setDeleteTarget(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  const handleTest = (definition) => {
    setSelectedDefinition(definition);
    setShowTest(true);
  };

  const handleSave = async (formData) => {
    try {
      setFormLoading(true);
      const method = selectedDefinition ? "PUT" : "POST";
      const url = selectedDefinition
        ? `${API_URL}${selectedDefinition.id}/`
        : `${API_URL}create/`;

      const saved = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (selectedDefinition) {
        setDefinitions((current) =>
          current.map((d) => (d.id === saved.id ? saved : d))
        );
      } else {
        setDefinitions((current) => [...current, saved]);
      }
      setShowForm(false);
      setSelectedDefinition(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Workflows / Definitions"
        title="Workflow Definitions"
        subtitle="Define business process workflows and their approval queues."
        action={
          <button
            type="button"
            className="primary-button"
            onClick={handleCreate}
            disabled={loading || formLoading}
          >
            <Plus size={15} /> New Workflow
          </button>
        }
      />

      <StateArea
        loading={loading}
        error={error}
        onRetry={fetchDefinitions}
        errorTitle="Unable to load workflow definitions."
        errorText={error}
      >
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3 className="panel-title">Definitions</h3>
              <p className="stat-label">{definitions.length} configured</p>
            </div>
          </div>

          <div className="panel-body">
            <WorkflowDefinitionList
              definitions={definitions}
              onEdit={handleEdit}
              onDelete={setDeleteTarget}
              onTest={handleTest}
              loading={formLoading}
            />
          </div>
        </div>
      </StateArea>

      {showForm && (
        <WorkflowDefinitionForm
          definition={selectedDefinition}
          onSave={handleSave}
          onClose={() => setShowForm(false)}
          loading={formLoading}
        />
      )}

      {showTest && selectedDefinition && (
        <WorkflowDefinitionTestModal
          definition={selectedDefinition}
          onClose={() => setShowTest(false)}
          loading={formLoading}
        />
      )}

      {deleteTarget && (
        <Modal
          isOpen={true}
          onClose={() => !formLoading && setDeleteTarget(null)}
          title="Delete workflow"
          size="md"
          closeOnEscape={!formLoading}
          closeOnOverlayClick={!formLoading}
        >
          <div className="state-card">
            <span>
              Delete workflow{" "}
              <strong>{deleteTarget.name}</strong>? This action cannot be
              undone.
            </span>
          </div>

          <div className="modal-footer" style={{ marginTop: 12 }}>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setDeleteTarget(null)}
              disabled={formLoading}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-button"
              style={{ background: "var(--danger, #dc2626)" }}
              onClick={handleDelete}
              disabled={formLoading}
            >
              {formLoading ? "Deleting..." : "Delete"}
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
