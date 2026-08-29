import { useEffect, useState } from "react";
import { PageHeader, StateArea } from "./ui";
import { ApprovalCard } from "../components/ApprovalCard";
import { ApprovalDecisionModal } from "../components/ApprovalDecisionModal";

const API_URL = "/api/workflow/approvals/";

export default function PendingApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [instances, setInstances] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [decidingLoading, setDecidingLoading] = useState(false);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const response = await fetch(API_URL, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        const appsList = Array.isArray(data) ? data : data.results || [];
        setApprovals(appsList);

        // Fetch related instances
        if (appsList.length > 0) {
          const instanceIds = [...new Set(appsList.map((a) => a.instance))];
          await fetchInstances(instanceIds);
        }
      } else {
        setError("Failed to fetch pending approvals");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchInstances = async (ids) => {
    try {
      const promises = ids.map((id) =>
        fetch(`/api/workflow/instances/${id}/`, { credentials: "include" })
          .then((r) => r.json())
          .then((data) => [id, data])
      );
      const results = await Promise.all(promises);
      const map = Object.fromEntries(results);
      setInstances(map);
    } catch (err) {
      console.error("Failed to fetch instances:", err);
    }
  };

  useEffect(() => {
    fetchApprovals();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchApprovals, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleDecideClick = (approval) => {
    setSelectedApproval(approval);
  };

  const handleDecide = async (decision, comment) => {
    try {
      setDecidingLoading(true);
      const response = await fetch(
        `/api/workflow/approvals/${selectedApproval.id}/decide/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            decision,
            comment,
          }),
        }
      );

      if (response.ok) {
        // Refresh data
        await fetchApprovals();
        setSelectedApproval(null);
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to submit decision");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setDecidingLoading(false);
    }
  };

  const pendingApprovals = approvals.filter((a) => a.status === "pending");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pending Approvals"
        description={`You have ${pendingApprovals.length} approval(s) waiting for your decision`}
      />

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-sm">
          {error}
        </div>
      )}

      <StateArea loading={loading}>
        {pendingApprovals.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No pending approvals</p>
            <p className="text-gray-400 text-sm mt-1">
              All approvals have been decided or none are waiting for you
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
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
    </div>
  );
}
