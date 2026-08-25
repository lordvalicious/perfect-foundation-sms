import { useCallback, useState } from "react";
import { BellRing, RefreshCw } from "lucide-react";
import { apiFetch } from "../api";

const JOBS = [
  {
    key: "fee-reminders",
    label: "Fee reminders",
    description:
      "SMS + email to guardians of students with overdue invoices (consolidated, once per week per student).",
    url: "/api/communication/cron/fee-reminders/",
  },
  {
    key: "absence-alerts",
    label: "Absence alerts",
    description:
      "Same-day SMS + email to guardians of students marked absent today.",
    url: "/api/attendance/cron/absence-alerts/",
  },
];

export default function NotificationsPanel() {
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState({});
  const [errors, setErrors] = useState({});

  const run = useCallback((job, dryRun) => {
    setBusy((b) => ({ ...b, [job.key]: true }));
    setErrors((e) => ({ ...e, [job.key]: "" }));

    apiFetch(`${job.url}?dry_run=${dryRun ? "1" : "0"}`)
      .then((data) =>
        setResults((r) => ({ ...r, [job.key]: { data, dryRun } }))
      )
      .catch((err) =>
        setErrors((e) => ({ ...e, [job.key]: err.message }))
      )
      .finally(() => setBusy((b) => ({ ...b, [job.key]: false })));
  }, []);

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3>Parent Notifications</h3>
          <p>
            Automated jobs run on schedule (Mon–Sat). Use these buttons to
            trigger them now — Dry Run previews without sending.
          </p>
        </div>
      </div>

      {JOBS.map((job) => {
        const result = results[job.key];

        return (
          <div
            key={job.key}
            style={{
              padding: "12px 0",
              borderBottom: "1px solid #e2e8f0",
            }}
          >
            <strong>{job.label}</strong>
            <p style={{ margin: "4px 0", fontSize: 13 }}>{job.description}</p>

            <button
              type="button"
              className="primary-button"
              disabled={!!busy[job.key]}
              onClick={() => run(job, false)}
            >
              {busy[job.key] ? (
                <RefreshCw size={14} />
              ) : (
                <BellRing size={14} />
              )}
              Run now
            </button>

            <button
              type="button"
              className="table-action"
              style={{ marginLeft: 10 }}
              disabled={!!busy[job.key]}
              onClick={() => run(job, true)}
            >
              Dry run
            </button>

            {result && (
              <pre
                style={{
                  marginTop: 10,
                  fontSize: 12,
                  background: "var(--surface-alt, #f1f5f9)",
                  padding: 10,
                  borderRadius: 8,
                  whiteSpace: "pre-wrap",
                }}
              >
                {JSON.stringify(result.data, null, 2)}
              </pre>
            )}

            {errors[job.key] && (
              <div className="state-card error" style={{ marginTop: 10 }}>
                {errors[job.key]}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
