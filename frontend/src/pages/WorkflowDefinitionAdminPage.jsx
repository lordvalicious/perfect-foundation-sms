import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "./ui";
import { WorkflowDefinitionList } from "../components/WorkflowDefinitionList";
import { WorkflowDefinitionForm } from "../components/WorkflowDefinitionForm";
import { WorkflowDefinitionTestModal } from "../components/WorkflowDefinitionTestModal";

const API_URL = "/api/workflow/definitions/";

export default function WorkflowDefinitionAdminPage() {
  const [definitions, setDefinitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [showTest, setShowTest] = useState(false);
  const [selectedDefinition, setSelectedDefinition] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  const fetchDefinitions = async () => {
    try {
      setLoading(true);
      const response = await fetch(API_URL, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        setDefinitions(Array.isArray(data) ? data : data.results || []);
      } else {
        setError("Failed to fetch workflow definitions");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDefinitions();
  }, []);

  const handleCreate = () => {
    setSelectedDefinition(null);
    setShowForm(true);
  };

  const handleEdit = (definition) => {
    setSelectedDefinition(definition);
    setShowForm(true);
  };

  const handleDelete = async (definition) => {
    if (!confirm(`Delete workflow "${definition.name}"?`)) return;

    try {
      setFormLoading(true);
      const response = await fetch(`${API_URL}${definition.id}/`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        setDefinitions(definitions.filter((d) => d.id !== definition.id));
      } else {
        setError("Failed to delete workflow definition");
      }
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

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const saved = await response.json();
        if (selectedDefinition) {
          setDefinitions(
            definitions.map((d) => (d.id === saved.id ? saved : d))
          );
        } else {
          setDefinitions([...definitions, saved]);
        }
        setShowForm(false);
        setSelectedDefinition(null);
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to save workflow definition");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow Definitions"
        description="Manage business process workflows and approval queues"
      />

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Definitions</h2>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 flex items-center gap-2"
            disabled={loading || formLoading}
          >
            <Plus className="w-4 h-4" />
            New Workflow
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : (
          <div className="p-4">
            <WorkflowDefinitionList
              definitions={definitions}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onTest={handleTest}
              loading={formLoading}
            />
          </div>
        )}
      </div>

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
    </div>
  );
}
