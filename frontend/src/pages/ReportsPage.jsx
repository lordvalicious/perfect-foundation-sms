import { useState } from "react";
import {
  BarChart3,
  FileSpreadsheet,
  Download,
  ClipboardCheck,
  GraduationCap,
  Wallet,
  Users,
  FileText,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { formatCurrency, formatDate } from "./format";
import { apiDownload } from "../api";

const BASE = "/api/reports/";

const REPORTS = [
  {
    key: "enrollment",
    url: "enrollment/",
    title: "Enrollment Report",
    icon: GraduationCap,
  },
  {
    key: "attendance",
    url: "attendance/",
    title: "Attendance Report",
    icon: ClipboardCheck,
  },
  {
    key: "results",
    url: "results/",
    title: "Results Report",
    icon: FileText,
  },
  {
    key: "fees",
    url: "fees/",
    title: "Fees Report",
    icon: Wallet,
  },
  {
    key: "staff",
    url: "staff/",
    title: "Staff Report",
    icon: Users,
  },
];

export default function ReportsPage() {
  const [active, setActive] = useState("enrollment");
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exam, setExam] = useState("");
  const [downloading, setDownloading] = useState(false);

  const load = (key) => {
    const config = REPORTS.find((item) => item.key === key);

    setLoading(true);
    setError("");

    const params = new URLSearchParams();

    if (key === "results" && exam) {
      params.append("exam", exam);
    }

    const query = params.toString() ? `?${params.toString()}` : "";

    fetch(`${BASE}${config.url}${query}`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : {}))
      .then((json) => {
        setData((previous) => ({ ...previous, [key]: json }));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const switchReport = (key) => {
    setActive(key);

    if (data[key] === undefined) {
      load(key);
    }
  };

  const handleDownload = () => {
    const config = REPORTS.find((item) => item.key === active);

    setDownloading(true);

    const params = new URLSearchParams();

    if (active === "results" && exam) {
      params.append("exam", exam);
    }

    params.append("format", "csv");

    apiDownload(`${BASE}${config.url}?${params.toString()}`, `${config.key}_report.csv`)
      .catch(() => setError("Could not download the report."))
      .finally(() => setDownloading(false));
  };

  const current = data[active] || {};

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Reports"
        title="Reports"
        subtitle="Generate and export school-wide reports as CSV."
      />

      <div className="tabs">
        {REPORTS.map((report) => {
          const Icon = report.icon;

          return (
            <button
              key={report.key}
              className={`tab-button ${active === report.key ? "active" : ""}`}
              onClick={() => switchReport(report.key)}
            >
              <Icon size={15} />
              {report.title}
            </button>
          );
        })}
      </div>

      <div className="panel">
        <PanelHeader
          title={REPORTS.find((item) => item.key === active).title}
          subtitle="generated from live data"
          action={
            <button
              type="button"
              className="primary-button"
              onClick={handleDownload}
              disabled={downloading || !data[active]}
            >
              <Download size={15} />
              {downloading ? "Preparing..." : "Export CSV"}
            </button>
          }
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => load(active)}
        >
          {active === "enrollment" && (
            <ReportContent
              summary={[
                { label: "Total Students", value: current.total_students ?? 0 },
                { label: "Classes", value: current.total_classes ?? 0 },
                { label: "Avg Class Size", value: current.average_class_size ?? 0 },
              ]}
              headers={["Campus", "Class", "Total", "Male", "Female"]}
              rows={(current.classes || []).map((row) => [
                row.campus,
                row.class,
                row.total,
                row.male,
                row.female,
              ])}
            />
          )}

          {active === "attendance" && (
            <ReportContent
              summary={[
                {
                  label: "Overall Rate",
                  value: current.overall_attendance_rate != null
                    ? `${current.overall_attendance_rate}%`
                    : 0,
                },
              ]}
              headers={["Campus", "Class", "Records", "Present", "Absent", "Late", "Leave", "Rate %"]}
              rows={(current.classes || []).map((row) => [
                row.campus,
                row.class,
                row.total_records,
                row.present,
                row.absent,
                row.late,
                row.leave,
                `${row.attendance_rate}%`,
              ])}
            />
          )}

          {active === "results" && (
            <div className="report-results">
              <div className="filter-row">
                <input
                  type="text"
                  placeholder="Exam ID (required for results report)"
                  value={exam}
                  onChange={(event) => setExam(event.target.value)}
                />

                <button type="button" className="primary-button" onClick={() => load("results")}>
                  Load
                </button>
              </div>

              <ReportContent
                summary={[
                  { label: "Students", value: current.summary?.total_students ?? 0 },
                  { label: "Passed", value: current.summary?.passed ?? 0 },
                  { label: "Pass Rate", value: current.summary?.pass_rate != null ? `${current.summary.pass_rate}%` : 0 },
                  { label: "Average %", value: current.summary?.average_percentage ?? 0 },
                  { label: "Highest", value: current.summary?.highest ?? 0 },
                  { label: "Lowest", value: current.summary?.lowest ?? 0 },
                ]}
                headers={["Admission No", "Student", "Total", "Max", "Percentage", "Grade", "Result", "Position"]}
                rows={(current.students || []).map((row) => [
                  row.admission_number,
                  row.student,
                  row.total_marks,
                  row.maximum_marks,
                  `${row.percentage}%`,
                  row.grade,
                  row.result,
                  row.position,
                ])}
              />
            </div>
          )}

          {active === "fees" && (
            <ReportContent
              summary={[
                { label: "Invoiced", value: formatCurrency(current.summary?.total_invoiced) },
                { label: "Collected", value: formatCurrency(current.summary?.total_collected) },
                { label: "Outstanding", value: formatCurrency(current.summary?.total_outstanding) },
                { label: "Collection Rate", value: current.summary?.collection_rate != null ? `${current.summary.collection_rate}%` : 0 },
              ]}
              headers={["Campus", "Invoiced", "Collected", "Outstanding"]}
              rows={(current.by_campus || []).map((row) => [
                row.campus,
                formatCurrency(row.invoiced),
                formatCurrency(row.collected),
                formatCurrency(row.outstanding),
              ])}
            />
          )}

          {active === "staff" && (
            <ReportContent
              summary={[
                { label: "Total Staff", value: current.total_staff ?? 0 },
              ]}
              headers={["Campus", "Designation", "Count"]}
              rows={(current.groups || []).map((row) => [
                row.campus,
                row.designation,
                row.count,
              ])}
            />
          )}
        </StateArea>
      </div>
    </section>
  );
}

function ReportContent({ summary, headers, rows }) {
  if (rows.length === 0) {
    return (
      <div className="empty-state">
        <BarChart3 size={42} />
        <h3>No data available</h3>
        <p>Adjust the filters to generate this report.</p>
      </div>
    );
  }

  return (
    <div className="report-content">
      <div className="dashboard-grid">
        {summary.map((item) => (
          <div key={item.label} className="stat-card">
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {headers.map((header) => (
                <th key={header}>{header.toUpperCase()}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row, index) => (
              <tr key={index}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>
                    {cellIndex === 0 ? <strong>{cell}</strong> : cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
