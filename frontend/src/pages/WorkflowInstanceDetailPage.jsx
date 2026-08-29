import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PageHeader, StateArea } from "./ui";
import { WorkflowStateCard } from "../components/WorkflowStateCard";
import { WorkflowApprovalSteps } from "../components/WorkflowApprovalSteps";
import { WorkflowTimeline } from "../components/WorkflowTimeline";

const API_URL = "/api/workflow/instances";

export default function WorkflowInstanceDetailPage() {
  const { id } = useParams();
  const [instance, setInstance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchInstance = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/${id}/`, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        setInstance(data);
      } else {
        setError("Failed to fetch workflow instance");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstance();
  }, [id]);

  return (
    <div className="space-y-6">
      {instance && (
        <PageHeader
          title={instance.definition_name || "Workflow"}
          description={`Instance #${instance.id} - Object: ${instance.object_type} (ID: ${instance.object_id})`}
        />
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-sm">
          {error}
        </div>
      )}

      <StateArea loading={loading}>
        {instance && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
                <WorkflowStateCard instance={instance} />

                <div className="space-y-2">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Submitted by:</span> {instance.created_by_name}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Created at:</span>{" "}
                    {new Date(instance.created_at).toLocaleString()}
                  </p>
                  {instance.submitted_at && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Submitted at:</span>{" "}
                      {new Date(instance.submitted_at).toLocaleString()}
                    </p>
                  )}
                  {instance.completed_at && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Completed at:</span>{" "}
                      {new Date(instance.completed_at).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <WorkflowTimeline transitions={instance.transitions || []} />
              </div>
            </div>

            <div className="lg:col-span-1">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <WorkflowApprovalSteps approvals={instance.approvals || []} />
              </div>
            </div>
          </div>
        )}
      </StateArea>
    </div>
  );
}
