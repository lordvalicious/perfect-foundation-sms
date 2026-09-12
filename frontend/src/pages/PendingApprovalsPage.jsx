import { useCallback, useEffect, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { PageHeader, StateArea, EmptyState } from "./ui";
import { ApprovalCard } from "../components/ApprovalCard";
import { ApprovalDecisionModal } from "../components/ApprovalDecisionModal";
import { apiFetch } from "../api";

const API_URL = "/api/workflow/approvals/";
const INSTANCE_URL = "/api/workflow/instances/";

export default function PendingApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [instances, setInstances] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [decidingLoading, setDecidingLoading] = useState(false);

  const fetchInstances = useCallback(async (ids) => {
    try {
      const promises = ids.map(async (id) => {
        try {
          const data = await apiFetch(`${INSTANCE_URL}${id}/`);
          return [id, data];
        } catch {
          return [id, null];
        }
      });
      const results = await Promise.all(promises);
      const map = Object.fromEntries(results);
      setInstances((current) => ({ ...current, ...map }));
    } catch {
      // One or more instance lookups failed; approvals still render.
      setError((current) =>
        current || "Some workflow details could not be loaded. Pull-to-refresh to retry."
      );
    }
  }, []);

  const fetchApprovals = useCallback(async () => {
    try {
      setError("");
      setLoading(true);
      const data = await apiFetch(API_URL);
      const appsList = Array.isArray(data) ? data : data.results || [];
      setApprovals(appsList);

      // Fetch related instances
      if (appsList.length > 0) {
        const instanceIds = [...new Set(appsList.map((a) => a.instance))];
        await fetchInstances(instanceIds);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchInstances]);

  useEffect(() => {
    fetchApprovals();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchApprovals, 30000);
    return () => clearInterval(interval);
  }, [fetchApprovals]);

  const handleDecideClick = (approval) => {
    setSelectedApproval(approval);
  };

  const handleDecide = async (decision, comment) => {
    if (!selectedApproval) return;
    try {
      setDecidingLoading(true);
      await apiFetch(
        `/api/workflow/approvals/${selectedApproval.id}/decide/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision, comment }),
        }
      );

      // Refresh data
      await fetchApprovals();
      setSelectedApproval(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setDecidingLoading(false);
    }
  };

  const pendingApprovals = approvals.filter((a) => a.status === "pending");

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Workflows / Pending Approvals"
        title="Pending Approvals"
        subtitle={`${pendingApprovals.length} approval(s) waiting for your decision`}
      />

      <StateArea
        loading={loading}
        error={error}
        onRetry={fetchApprovals}
        errorTitle="Unable to load approvals."
        errorText={error}
      >
        {pendingApprovals.length === 0 ? (
          <EmptyState
            icon={ClipboardCheck}
            title="No pending approvals"
            message="All approvals have been decided or none are waiting for you."
          />
        ) : (
          <div
            className="dashboard-grid two"
            style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", alignItems: "start" }}
          >
            {pendingApprovals.map((approval) => (
              <ApprovalCard
                key={approval.id}
                approval={approval}
                instance={instances[approval.instance] || {}}
                onDecide={handleDecideClick}
                loading={decidingLoading}
              />
            ))}
          </div>
        )}
      </StateArea>

      {selectedApproval && (
        <ApprovalDecisionModal
          approval={selectedApproval}
          onClose={() => setSelectedApproval(null)}
          onDecide={handleDecide}
          loading={decidingLoading}
        />
      )}
    </section>
  );
}
