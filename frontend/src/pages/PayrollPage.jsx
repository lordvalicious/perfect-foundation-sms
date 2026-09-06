import { useCallback, useEffect, useRef, useState } from "react";
import { Banknote, BadgePoundSterling, ReceiptText } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, EmptyState } from "./ui";
import { formatCurrency, formatDate } from "./format";
import { apiFetch, apiDownload, jsonHeaders } from "../api";

const BASE = "/api/payroll/";

const ENDPOINTS = {
  structures: { url: "salary-structures/", icon: BadgePoundSterling, title: "Salary Structures" },
  records: { url: "records/", icon: Banknote, title: "Payroll Records" },
  payslips: { url: "payslips/", icon: ReceiptText, title: "Payslips" },
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function PayrollPage() {
  const [tab, setTab] = useState("records");
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [processing, setProcessing] = useState(null);

  const load = useCallback(
    (key) => {
      const config = ENDPOINTS[key];

      setLoading(true);
      setError("");

      fetch(`${BASE}${config.url}`, { credentials: "include" })
        .then((response) => (response.ok ? response.json() : { results: [] }))
        .then((json) => {
          setData((previous) => ({
            ...previous,
            [key]: json.results || json,
          }));
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    },
    []
  );

  const initialLoadDone = useRef(false);

  useEffect(() => {
    if (initialLoadDone.current) return;
    initialLoadDone.current = true;
    load(tab);
  }, [load, tab]);

  const switchTab = (key) => {
    setTab(key);
    setMessage("");

    if (data[key] === undefined) {
      load(key);
    }
  };

  const handleProcess = async (recordId) => {
    setProcessing(recordId);
    setMessage("");
    setError("");

    try {
      await apiFetch(
        `${BASE}records/${recordId}/process/`,
        { method: "POST", headers: jsonHeaders() },
        "Could not process the payroll record."
      );

      setMessage("Payroll record marked as paid.");
      setData((previous) => ({ ...previous, records: undefined }));
      load("records");
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(null);
    }
  };

  const rows = data[tab] || [];

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Payroll"
        title="Payroll"
        subtitle="Manage teacher salary structures, payroll records, and payslips."
      />

      {message && (
        <div className="state-card success">
          <strong>{message}</strong>
        </div>
      )}

      <div className="tabs">
        {Object.entries(ENDPOINTS).map(([key, config]) => {
          const Icon = config.icon;

          return (
            <button
              key={key}
              className={`tab-button ${tab === key ? "active" : ""}`}
              onClick={() => switchTab(key)}
            >
              <Icon size={15} />
              {config.title}
            </button>
          );
        })}
      </div>

      <div className="panel">
        <PanelHeader
          title={ENDPOINTS[tab].title}
          subtitle="records found"
          count={rows.length || null}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => load(tab)}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={ENDPOINTS[tab].icon}
              title={`No ${ENDPOINTS[tab].title.toLowerCase()} found`}
              message="Records will appear here once added."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  {tab === "structures" && (
                    <tr>
                      <th>TEACHER</th>
                      <th>BASIC SALARY</th>
                      <th>ALLOWANCES</th>
                      <th>GROSS SALARY</th>
                      <th>EFFECTIVE DATE</th>
                      <th>STATUS</th>
                    </tr>
                  )}

                  {tab === "records" && (
                    <tr>
                      <th>TEACHER</th>
                      <th>EMP NO.</th>
                      <th>PERIOD</th>
                      <th>WORKING</th>
                      <th>PAID</th>
                      <th>GROSS</th>
                      <th>DEDUCTIONS</th>
                      <th>NET SALARY</th>
                      <th>STATUS</th>
                      <th>ACTION</th>
                    </tr>
                  )}

                  {tab === "payslips" && (
                    <tr>
                      <th>TEACHER</th>
                      <th>PERIOD</th>
                      <th>ISSUED AT</th>
                    </tr>
                  )}
                </thead>

                <tbody>
                  {tab === "structures" &&
                    rows.map((structure) => (
                      <tr key={structure.id}>
                        <td>
                          <strong>{structure.teacher_name || "—"}</strong>
                        </td>

                        <td>{formatCurrency(structure.basic_salary)}</td>

                        <td>{formatCurrency(structure.total_allowances)}</td>

                        <td>
                          <strong>{formatCurrency(structure.gross_salary)}</strong>
                        </td>

                        <td>{formatDate(structure.effective_date)}</td>

                        <td>
                          <span className={`status-badge ${structure.status === "active" ? "active" : "inactive"}`}>
                            {structure.status ? structure.status.charAt(0).toUpperCase() + structure.status.slice(1) : "—"}
                          </span>
                        </td>
                      </tr>
                    ))}

                  {tab === "records" &&
                    rows.map((record) => (
                      <tr key={record.id}>
                        <td>
                          <strong>{record.teacher_name || "—"}</strong>
                        </td>

                        <td>{record.teacher_number || "—"}</td>

                        <td>
                          {record.month ? MONTHS[record.month - 1] : "—"} {record.year || ""}
                        </td>

                        <td>{record.working_days ?? "—"}</td>

                        <td>{record.paid_days ?? "—"}</td>

                        <td>{formatCurrency(record.gross_salary)}</td>

                        <td>{formatCurrency(record.total_deductions)}</td>

                        <td>
                          <strong>{formatCurrency(record.net_salary)}</strong>
                        </td>

                        <td>
                          <span className={`status-badge ${record.status === "paid" ? "active" : "warn"}`}>
                            {record.status ? record.status.charAt(0).toUpperCase() + record.status.slice(1) : "—"}
                          </span>
                        </td>

                        <td>
                          {record.status !== "paid" && (
                            <button
                              type="button"
                              className="table-action"
                              disabled={processing === record.id}
                              onClick={() => handleProcess(record.id)}
                            >
                              {processing === record.id ? "Processing..." : "Mark Paid"}
                            </button>
                          )}
                          {record.status === "paid" && (
                            <button
                              type="button"
                              className="table-action"
                              onClick={() =>
                                apiDownload(
                                  `${BASE}records/${record.id}/payslip.pdf`,
                                  `payslip_${record.teacher_number || record.id}_${record.year}_${String(record.month).padStart(2, "0")}.pdf`
                                ).catch(() => alert("Could not download payslip."))
                              }
                            >
                              Payslip PDF
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}

                  {tab === "payslips" &&
                    rows.map((payslip) => (
                      <tr key={payslip.id}>
                        <td>
                          <strong>{payslip.teacher_name || "—"}</strong>
                        </td>

                        <td>{payslip.period || "—"}</td>

                        <td>{formatDate(payslip.issued_at)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
