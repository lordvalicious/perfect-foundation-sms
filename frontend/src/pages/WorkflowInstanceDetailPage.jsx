import { useCallback, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader, StateArea } from "./ui";
import { WorkflowStateCard } from "../components/WorkflowStateCard";
import { WorkflowApprovalSteps } from "../components/WorkflowApprovalSteps";
import { WorkflowTimeline } from "../components/WorkflowTimeline";
import { apiFetch } from "../api";

const API_URL = "/api/workflow/instances";

export default function WorkflowInstanceDetailPage() {
  const { id } = useParams();
  const [instance, setInstance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchInstance = useCallback(async () => {
    try {
      setError("");
      setLoading(true);
      const data = await apiFetch(`${API_URL}/${id}/`);
      setInstance(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchInstance();
  }, [fetchInstance]);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Workflows / Instances"
        title={instance?.definition_name || "Workflow Instance"}
        subtitle={
          instance
            ? `Instance #${instance.id} - Object: ${instance.object_type} (ID: ${instance.object_id})`
            : "Loading workflow instance..."
        }
        action={
          <Link to="/workflow/approvals" className="secondary-button">
            <ArrowLeft size={14} /> Approvals
          </Link>
        }
      />

      <StateArea
        loading={loading}
        error={error}
        onRetry={fetchInstance}
        errorTitle="Unable to load workflow instance."
        errorText={error}
      >
        {instance && (
          <div className="dashboard-grid two" style={{ gridTemplateColumns: "2fr 1fr", alignItems: "start" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <WorkflowStateCard instance={instance} />

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Details</h3>
                    <p className="stat-label">Submitted information</p>
                  </div>
                </div>

                <div className="panel-body">
                  <div className="overview-list">
                    <div>
                      <span>Submitted by</span>
                      <strong>{instance.created_by_name || "—"}</strong>
                    </div>
                    <div>
                      <span>Created at</span>
                      <strong>
                        {instance.created_at
                          ? new Date(instance.created_at).toLocaleString()
                          : "—"}
                      </strong>
                    </div>
                    {instance.submitted_at && (
                      <div>
                        <span>Submitted at</span>
                        <strong>{new Date(instance.submitted_at).toLocaleString()}</strong>
                      </div>
                    )}
                    {instance.completed_at && (
                      <div>
                        <span>Completed at</span>
                        <strong>{new Date(instance.completed_at).toLocaleString()}</strong>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <WorkflowTimeline transitions={instance.transitions || []} />
            </div>

            <WorkflowApprovalSteps approvals={instance.approvals || []} />
          </div>
        )}
      </StateArea>
    </section>
  );
}
