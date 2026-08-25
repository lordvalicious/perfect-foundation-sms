import { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  Download,
  ClipboardCheck,
  GraduationCap,
  Wallet,
  Users,
  FileText,
  PieChart,
  Banknote,
  UserCheck,
  Tags,
  AlertTriangle,
  Briefcase,
  TrendingUp,
  LineChart,
  Activity,
  Percent,
  UserX,
  Coins,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { formatCurrency } from "./format";
import { apiDownload } from "../api";

const BASE = "/api/reports/";

const EXAM_REPORTS = ["results", "subjects", "top-performers"];
const STUDENT_REPORTS = ["student-progress"];

const REPORTS = [
  {
    key: "enrollment",
    url: "enrollment/",
    title: "Enrollment",
    icon: GraduationCap,
  },
  {
    key: "attendance",
    url: "attendance/",
    title: "Attendance",
    icon: ClipboardCheck,
  },
  {
    key: "chronic-absentee",
    url: "chronic-absentee/",
    title: "Chronic Absentees",
    icon: UserX,
  },
  {
    key: "results",
    url: "results/",
    title: "Results",
    icon: FileText,
  },
  {
    key: "top-performers",
    url: "top-performers/",
    title: "Top Performers",
    icon: Trophy,
  },
  {
    key: "class-performance",
    url: "class-performance/",
    title: "Class Performance",
    icon: TrendingUp,
  },
  {
    key: "student-progress",
    url: "student-progress/",
    title: "Student Progress",
    icon: LineChart,
  },
  {
    key: "subjects",
    url: "subjects/",
    title: "Subject Performance",
    icon: PieChart,
  },
  {
    key: "fees",
    url: "fees/",
    title: "Fees",
    icon: Wallet,
  },
  {
    key: "fee-defaulters",
    url: "fee-defaulters/",
    title: "Fee Defaulters",
    icon: AlertTriangle,
  },
  {
    key: "collection-trend",
    url: "collection-trend/",
    title: "Collection Trend",
    icon: Activity,
  },
  {
    key: "discounts",
    url: "discounts/",
    title: "Discounts",
    icon: Percent,
  },
  {
    key: "payments",
    url: "payments/",
    title: "Payment Methods",
    icon: Banknote,
  },
  {
    key: "fee-categories",
    url: "fee-categories/",
    title: "Fee Categories",
    icon: Tags,
  },
  {
    key: "payroll-summary",
    url: "payroll-summary/",
    title: "Payroll Summary",
    icon: Coins,
  },
  {
    key: "staff",
    url: "staff/",
    title: "Staff",
    icon: Users,
  },
  {
    key: "teacher-workload",
    url: "teacher-workload/",
    title: "Teacher Workload",
    icon: Briefcase,
  },
  {
    key: "student-status",
    url: "student-status/",
    title: "Student Status",
    icon: UserCheck,
  },
  {
    key: "library",
    url: "library/",
    title: "Library",
    icon: BookOpen,
  },
  {
    key: "route-utilization",
    url: "route-utilization/",
    title: "Route Utilization",
    icon: Bus,
  },
  {
    key: "inventory-value",
    url: "inventory-value/",
    title: "Inventory Value",
    icon: Package,
  },
  {
    key: "maintenance-due",
    url: "maintenance-due/",
    title: "Maintenance Due",
    icon: Wrench,
  },
  {
    key: "event-participation",
    url: "event-participation/",
    title: "Event Participation",
    icon: CalendarDays,
  },
  {
    key: "sms-usage",
    url: "sms-usage/",
    title: "SMS Usage",
    icon: MessageSquare,
  },
];

const GRADEBOOK_KEY = "gradebook";

export default function ReportsPage() {
  const [active, setActive] = useState("enrollment");
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exam, setExam] = useState("");
  const [exams, setExams] = useState([]);
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState("");
  const [threshold, setThreshold] = useState("75");
  const [downloading, setDownloading] = useState(false);
  const [gradebook, setGradebook] = useState(null);
  const [gbLoading, setGbLoading] = useState(false);
  const [gbError, setGbError] = useState("");
  const [gbFilters, setGbFilters] = useState({
    class_obj: "",
    section: "",
    subject: "",
  });
  const [classList, setClassList] = useState([]);
  const [sectionList, setSectionList] = useState([]);
  const [subjectList, setSubjectList] = useState([]);

  const needsExam = EXAM_REPORTS.includes(active);
  const needsStudent = STUDENT_REPORTS.includes(active);

  const buildParams = useCallback(
    (key) => {
      const params = new URLSearchParams();

      if (EXAM_REPORTS.includes(key) && exam) {
        params.append("exam", exam);
      }

      if (STUDENT_REPORTS.includes(key) && studentId) {
        params.append("student", studentId);
      }

      if (key === "chronic-absentee" && threshold) {
        params.append("threshold", threshold);
      }

      return params;
    },
    [exam, studentId, threshold]
  );

  const load = useCallback(
    (key) => {
      const config = REPORTS.find((item) => item.key === key);

      setLoading(true);
      setError("");

      const params = buildParams(key);
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
    },
    [buildParams]
  );

  useEffect(() => {
    load("enrollment");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetch("/api/exams/?page_size=500", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => {
        const withResults = (json.results || [])
          .filter((examItem) => examItem.result_count > 0)
          .sort((a, b) => b.result_count - a.result_count);

        setExams(withResults);

        if (withResults.length > 0) {
          setExam(String(withResults[0].id));
        }
      })
      .catch(() => setExams([]));
  }, []);

  useEffect(() => {
    fetch("/api/students/?page_size=1000", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => setStudents(json.results || []))
      .catch(() => setStudents([]));
  }, []);

  useEffect(() => {
    Promise.all([
      fetch("/api/schools/classes/", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : [])),
      fetch("/api/schools/sections/", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : [])),
      fetch("/api/schools/subjects/", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([classes, sections, subjects]) => {
        const arr = (v) => (Array.isArray(v) ? v : v.results || []);
        setClassList(arr(classes));
        setSectionList(arr(sections));
        setSubjectList(arr(subjects));
      })
      .catch(() => {});
  }, []);

  const loadGradebook = useCallback(() => {
    if (!gbFilters.class_obj || !gbFilters.subject) return;

    setGbLoading(true);
    setGbError("");

    const params = new URLSearchParams({
      class_obj: gbFilters.class_obj,
      subject: gbFilters.subject,
    });
    if (gbFilters.section) params.append("section", gbFilters.section);

    fetch(`/api/exams/gradebook/?${params.toString()}`, {
      credentials: "include",
    })
      .then((r) => (r.ok ? r.json() : r.json().then((b) => Promise.reject(b))))
      .then(setGradebook)
      .catch((err) =>
        setGbError(err.detail || err.message || "Could not load gradebook.")
      )
      .finally(() => setGbLoading(false));
  }, [gbFilters]);

  useEffect(() => {
    if ((needsExam && exam) || (needsStudent && studentId)) {
      load(active);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, exam, studentId]);

  const switchReport = (key) => {
    setActive(key);

    if (!EXAM_REPORTS.includes(key) && !STUDENT_REPORTS.includes(key) && data[key] === undefined) {
      load(key);
    }
  };

  const handleDownload = () => {
    const config = REPORTS.find((item) => item.key === active);

    setDownloading(true);

    const params = buildParams(active);
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

        <button
          className={`tab-button ${active === GRADEBOOK_KEY ? "active" : ""}`}
          onClick={() => setActive(GRADEBOOK_KEY)}
        >
          <Table2 size={15} />
          Gradebook
        </button>
      </div>

      <div className="panel">
        <PanelHeader
          title={
            active === GRADEBOOK_KEY
              ? "Gradebook"
              : REPORTS.find((item) => item.key === active)?.title || "Report"
          }
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
          {(needsExam || needsStudent || active === "chronic-absentee") && (
            <div className="filter-row">
              {needsExam && (
                <select
                  value={exam}
                  onChange={(event) => setExam(event.target.value)}
                >
                  {exams.length === 0 && <option value="">No exams with results</option>}

                  {exams.map((item) => (
                    <option key={item.id} value={String(item.id)}>
                      {item.name} - {item.exam_type_display} ({item.academic_year_name})
                    </option>
                  ))}
                </select>
              )}

              {needsStudent && (
                <select
                  value={studentId}
                  onChange={(event) => setStudentId(event.target.value)}
                >
                  <option value="">Select a student</option>

                  {students.map((student) => (
                    <option key={student.id} value={String(student.id)}>
                      {student.full_name} ({student.admission_number})
                    </option>
                  ))}
                </select>
              )}

              {active === "chronic-absentee" && (
                <label className="inline-filter">
                  Below
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={threshold}
                    onChange={(event) => setThreshold(event.target.value)}
                  />
                  % attendance
                </label>
              )}
            </div>
          )}

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

          {active === "chronic-absentee" && (
            <ReportContent
              emptyHint="No students are below this threshold. Adjust the filter to flag more."
              summary={[
                { label: "Threshold", value: `${current.summary?.threshold ?? threshold}%` },
                { label: "Tracked", value: current.summary?.students_tracked ?? 0 },
                { label: "Flagged", value: current.summary?.students_flagged ?? 0 },
              ]}
              headers={["Admission No", "Student", "Campus", "Class", "Days", "Present+Late", "Absent", "Leave", "Rate %"]}
              rows={(current.students || []).map((row) => [
                row.admission_number,
                row.student,
                row.campus,
                row.class,
                row.total_days,
                row.present,
                row.absent,
                row.leave,
                `${row.attendance_rate}%`,
              ])}
            />
          )}

          {EXAM_REPORTS.includes(active) && (
            <>
              {active === "results" && (
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
              )}

              {active === "subjects" && (
                <ReportContent
                  summary={[
                    { label: "Subjects", value: current.summary?.subjects ?? 0 },
                    { label: "Results", value: current.summary?.results ?? 0 },
                    { label: "Pass Rate", value: current.summary?.pass_rate != null ? `${current.summary.pass_rate}%` : 0 },
                    { label: "Average %", value: current.summary?.average_percentage ?? 0 },
                  ]}
                  headers={["Subject", "Students", "Average %", "Pass Rate %", "Highest %", "Lowest %"]}
                  rows={(current.subjects || []).map((row) => [
                    row.subject,
                    row.students,
                    row.average_percentage,
                    `${row.pass_rate}%`,
                    row.highest,
                    row.lowest,
                  ])}
                />
              )}

              {active === "top-performers" && (
                <ReportContent
                  summary={[
                    { label: "Classes", value: current.summary?.classes ?? 0 },
                    { label: "Students", value: current.summary?.students ?? 0 },
                    { label: "Top N", value: current.summary?.top_n ?? 3 },
                  ]}
                  headers={["Position", "Campus", "Class", "Admission No", "Student", "Percentage", "Grade"]}
                  rows={(current.performers || []).map((row) => [
                    `#${row.position}`,
                    row.campus,
                    row.class,
                    row.admission_number,
                    row.student,
                    `${row.percentage}%`,
                    row.grade,
                  ])}
                />
              )}
            </>
          )}

          {active === "class-performance" && (
            <ReportContent
              summary={[
                { label: "Students", value: current.summary?.total_students ?? 0 },
                { label: "Overall Pass Rate", value: current.summary?.overall_pass_rate != null ? `${current.summary.overall_pass_rate}%` : 0 },
                { label: "Overall Average", value: current.summary?.overall_average != null ? `${current.summary.overall_average}%` : 0 },
              ]}
              headers={["Campus", "Class", "Students", "Exams", "Passed", "Failed", "Pass Rate %", "Average %", "Highest %", "Lowest %"]}
              rows={(current.classes || []).map((row) => [
                row.campus,
                row.class,
                row.total_students,
                row.exams_covered,
                row.passed,
                row.failed,
                `${row.pass_rate}%`,
                `${row.average_percentage}%`,
                `${row.highest}%`,
                `${row.lowest}%`,
              ])}
            />
          )}

          {active === "student-progress" && !studentId && (
            <div className="empty-state">
              <LineChart size={42} />
              <h3>Select a student</h3>
              <p>Choose a student above to see their exam progress trend.</p>
            </div>
          )}

          {active === "student-progress" && studentId && (
            <ReportContent
              summary={[
                { label: "Exams", value: current.summary?.total_exams ?? 0 },
                { label: "Average %", value: current.summary?.average_percentage ?? 0 },
                { label: "Best", value: current.summary?.best_percentage ?? 0 },
                { label: "Worst", value: current.summary?.worst_percentage ?? 0 },
                { label: "Trend", value: (current.summary?.trend || "-").toUpperCase() },
              ]}
              headers={["Exam", "Type", "Campus", "Class", "Percentage", "Grade", "Result", "Position"]}
              rows={(current.exams || []).map((row) => [
                row.exam,
                row.exam_type,
                row.campus,
                row.class,
                `${row.percentage}%`,
                row.grade,
                row.result,
                row.position,
              ])}
            />
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

          {active === "fee-defaulters" && (
            <ReportContent
              summary={[
                { label: "Defaulters", value: current.summary?.total_defaulters ?? 0 },
                { label: "Outstanding", value: formatCurrency(current.summary?.total_outstanding) },
              ]}
              headers={["Admission No", "Student", "Campus", "Invoices", "Invoiced", "Paid", "Outstanding"]}
              rows={(current.students || []).map((row) => [
                row.admission_number,
                row.student,
                row.campus,
                row.invoice_count,
                formatCurrency(row.total_invoiced),
                formatCurrency(row.total_paid),
                formatCurrency(row.total_outstanding),
              ])}
            />
          )}

          {active === "collection-trend" && (
            <ReportContent
              summary={[
                { label: "Invoiced", value: formatCurrency(current.summary?.total_invoiced) },
                { label: "Collected", value: formatCurrency(current.summary?.total_collected) },
                { label: "Collection Rate", value: current.summary?.collection_rate != null ? `${current.summary.collection_rate}%` : 0 },
                { label: "Months", value: current.summary?.months ?? 0 },
              ]}
              headers={["Month", "Invoiced", "Collected", "Gap"]}
              rows={(current.months_data || []).map((row) => [
                row.month,
                formatCurrency(row.invoiced),
                formatCurrency(row.collected),
                formatCurrency(row.gap),
              ])}
            />
          )}

          {active === "discounts" && (
            <div className="report-stack">
              <ReportContent
                summary={[
                  { label: "Invoices", value: current.summary?.invoices_affected ?? 0 },
                  { label: "Discounts", value: formatCurrency(current.summary?.total_discount) },
                  { label: "Concessions", value: formatCurrency(current.summary?.total_concession) },
                  { label: "Total Reduction", value: formatCurrency(current.summary?.total_reduction) },
                ]}
                headers={["Campus", "Invoices", "Discounts", "Concessions"]}
                rows={(current.by_campus || []).map((row) => [
                  row.campus,
                  row.invoices,
                  formatCurrency(row.discounts),
                  formatCurrency(row.concessions),
                ])}
              />

              <ReportContent
                headers={["Invoice", "Student", "Campus", "Subtotal", "Discount", "Concession", "Reduction"]}
                rows={(current.invoices || []).map((row) => [
                  row.invoice_number,
                  row.student,
                  row.campus,
                  formatCurrency(row.subtotal),
                  formatCurrency(row.discount),
                  formatCurrency(row.concession),
                  formatCurrency(row.total_reduction),
                ])}
              />
            </div>
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

          {active === "teacher-workload" && (
            <ReportContent
              summary={[
                { label: "Teachers", value: current.summary?.total_teachers ?? 0 },
                { label: "Assignments", value: current.summary?.total_assignments ?? 0 },
              ]}
              headers={["Teacher", "Emp No", "Campus", "Assignments", "Subjects", "Classes", "Sections"]}
              rows={(current.teachers || []).map((row) => [
                row.teacher,
                row.employee_number,
                row.campus,
                row.assignments,
                row.subjects,
                row.classes,
                row.sections,
              ])}
            />
          )}

          {active === "payments" && (
            <div className="report-stack">
              <ReportContent
                summary={[
                  { label: "Total Collected", value: formatCurrency(current.summary?.total_collected) },
                  { label: "Methods", value: current.summary?.methods ?? 0 },
                ]}
                headers={["Method", "Payments", "Collected"]}
                rows={(current.by_method || []).map((row) => [
                  row.method,
                  row.payments,
                  formatCurrency(row.collected),
                ])}
              />

              <ReportContent
                headers={["Campus", "Payments", "Collected"]}
                rows={(current.by_campus || []).map((row) => [
                  row.campus,
                  row.payments,
                  formatCurrency(row.collected),
                ])}
              />
            </div>
          )}

          {active === "student-status" && (
            <ReportContent
              summary={[
                { label: "Total Students", value: current.total_students ?? 0 },
                ...(current.statuses || []).map((item) => ({
                  label: item.status,
                  value: item.count,
                })),
              ]}
              headers={["Campus", "Status", "Count"]}
              rows={(current.rows || []).map((row) => [
                row.campus,
                row.status,
                row.count,
              ])}
            />
          )}

          {active === "fee-categories" && (
            <div className="report-stack">
              <ReportContent
                summary={[
                  { label: "Total Invoiced", value: formatCurrency(current.summary?.total_invoiced) },
                  { label: "Categories", value: current.summary?.categories ?? 0 },
                ]}
                headers={["Fee Category", "Invoiced"]}
                rows={(current.by_category || []).map((row) => [
                  row.category,
                  formatCurrency(row.invoiced),
                ])}
              />

              <ReportContent
                headers={["Fee Category", "Campus", "Invoiced"]}
                rows={(current.by_campus_category || []).map((row) => [
                  row.category,
                  row.campus,
                  formatCurrency(row.invoiced),
                ])}
              />
            </div>
          )}

          {active === "payroll-summary" && (
            <div className="report-stack">
              <ReportContent
                summary={[
                  { label: "Records", value: current.summary?.records ?? 0 },
                  { label: "Gross", value: formatCurrency(current.summary?.total_gross) },
                  { label: "Deductions", value: formatCurrency(current.summary?.total_deductions) },
                  { label: "Net Paid", value: formatCurrency(current.summary?.total_net) },
                ]}
                headers={["Period", "Employees", "Gross", "Deductions", "Net"]}
                rows={(current.by_period || []).map((row) => [
                  row.period,
                  row.employees,
                  formatCurrency(row.gross),
                  formatCurrency(row.deductions),
                  formatCurrency(row.net),
                ])}
              />

              <ReportContent
                headers={["Campus", "Employees", "Gross", "Net"]}
                rows={(current.by_campus || []).map((row) => [
                  row.campus,
                  row.employees,
                  formatCurrency(row.gross),
                  formatCurrency(row.net),
                ])}
              />
            </div>
          )}

          {active === "library" && (
            <div className="report-stack">
              <ReportContent
                summary={[
                  { label: "Total Issues", value: current.summary?.total_issues ?? 0 },
                  { label: "Active Issues", value: current.summary?.active_issues ?? 0 },
                  { label: "Overdue", value: current.summary?.marked_overdue ?? 0 },
                  { label: "Fines Due", value: formatCurrency(current.summary?.fines_outstanding) },
                  { label: "Fines Collected", value: formatCurrency(current.summary?.fines_collected) },
                ]}
                headers={["Title", "Issues", "Currently Out"]}
                rows={(current.most_borrowed || []).map((row) => [
                  row.title,
                  row.issues,
                  row.currently_out,
                ])}
              />

              <ReportContent
                headers={["Title", "Borrower", "Due Date", "Days Overdue", "Fine"]}
                rows={(current.overdue || []).map((row) => [
                  row.title,
                  row.borrower,
                  row.due_date,
                  row.days_overdue,
                  formatCurrency(row.fine),
                ])}
              />
            </div>
          )}

          {active === "route-utilization" && (
            <ReportContent
              summary={[
                { label: "Routes", value: current.summary?.routes ?? 0 },
                { label: "Capacity", value: current.summary?.total_capacity ?? 0 },
                { label: "Students", value: current.summary?.total_students ?? 0 },
                { label: "Avg Utilization", value: current.summary?.average_utilization != null ? `${current.summary.average_utilization}%` : 0 },
                { label: "Overloaded", value: current.summary?.overloaded_routes ?? 0 },
              ]}
              headers={["Route", "Campus", "Vehicle", "Driver", "Capacity", "Students", "Free", "Utilization %"]}
              rows={(current.routes || []).map((row) => [
                row.route,
                row.campus,
                row.vehicle,
                row.driver,
                row.capacity,
                row.students,
                row.seats_free,
                `${row.utilization}%`,
              ])}
            />
          )}

          {active === "inventory-value" && (
            <div className="report-stack">
              <ReportContent
                summary={[
                  { label: "Items", value: current.summary?.items ?? 0 },
                  { label: "Units", value: current.summary?.quantity ?? 0 },
                  { label: "Total Value", value: formatCurrency(current.summary?.total_value) },
                  ...(current.summary?.statuses || []).map((item) => ({
                    label: item.status,
                    value: item.count,
                  })),
                ]}
                headers={["Category", "Items", "Quantity", "Value"]}
                rows={(current.by_category || []).map((row) => [
                  row.category,
                  row.items,
                  row.quantity,
                  formatCurrency(row.value),
                ])}
              />

              <ReportContent
                headers={["Campus", "Items", "Quantity", "Value"]}
                rows={(current.by_campus || []).map((row) => [
                  row.campus,
                  row.items,
                  row.quantity,
                  formatCurrency(row.value),
                ])}
              />
            </div>
          )}

          {active === "maintenance-due" && (
            <ReportContent
              summary={[
                { label: "Open Records", value: current.summary?.open_records ?? 0 },
                { label: "Scheduled Cost", value: formatCurrency(current.summary?.scheduled_cost) },
                { label: "In Progress Cost", value: formatCurrency(current.summary?.in_progress_cost) },
                { label: "Assets In Maintenance", value: current.summary?.assets_in_maintenance ?? 0 },
              ]}
              headers={["Asset", "Code", "Campus", "Status", "Date", "Cost", "By"]}
              rows={(current.records || []).map((row) => [
                row.asset,
                row.code,
                row.campus,
                row.status,
                row.date,
                formatCurrency(row.cost),
                row.performed_by,
              ])}
            />
          )}

          {active === "event-participation" && (
            <ReportContent
              summary={[
                { label: "Events", value: current.summary?.events ?? 0 },
                { label: "Responses", value: current.summary?.total_responses ?? 0 },
                { label: "Attending", value: current.summary?.attending ?? 0 },
                { label: "Participation Rate", value: current.summary?.participation_rate != null ? `${current.summary.participation_rate}%` : 0 },
              ]}
              headers={["Event", "Campus", "Start", "Attending", "Not Attending", "Maybe", "Responses", "Rate %"]}
              rows={(current.events || []).map((row) => [
                row.event,
                row.campus,
                row.start,
                row.attending,
                row.not_attending,
                row.maybe,
                row.responses,
                `${row.participation_rate}%`,
              ])}
            />
          )}

          {active === "sms-usage" && (
            <ReportContent
              summary={[
                { label: "Year", value: current.summary?.year ?? "-" },
                { label: "Messages", value: current.summary?.total_messages ?? 0 },
                { label: "Sent", value: current.summary?.sent ?? 0 },
                { label: "Failed", value: current.summary?.failed ?? 0 },
                { label: "Success Rate", value: current.summary?.success_rate != null ? `${current.summary.success_rate}%` : 0 },
              ]}
              headers={["Month", "Sent", "Failed", "Queued", "Total", "Success %"]}
              rows={(current.months_data || []).map((row) => [
                row.month,
                row.sent,
                row.failed,
                row.queued,
                row.total,
                `${row.success_rate}%`,
              ])}
            />
          )}

          {active === GRADEBOOK_KEY && (
            <>
              <div className="filter-row">
                <select
                  value={gbFilters.class_obj}
                  onChange={(e) =>
                    setGbFilters({ ...gbFilters, class_obj: e.target.value, section: "" })
                  }
                >
                  <option value="">Class...</option>
                  {classList.map((cls) => (
                    <option key={cls.id} value={cls.id}>{cls.name}</option>
                  ))}
                </select>

                <select
                  value={gbFilters.section}
                  onChange={(e) => setGbFilters({ ...gbFilters, section: e.target.value })}
                  disabled={!gbFilters.class_obj}
                >
                  <option value="">All sections</option>
                  {sectionList
                    .filter((s) => String(s.class_obj) === String(gbFilters.class_obj))
                    .map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                </select>

                <select
                  value={gbFilters.subject}
                  onChange={(e) => setGbFilters({ ...gbFilters, subject: e.target.value })}
                >
                  <option value="">Subject...</option>
                  {subjectList.map((sub) => (
                    <option key={sub.id} value={sub.id}>{sub.name}</option>
                  ))}
                </select>

                <button
                  type="button"
                  className="primary-button"
                  onClick={loadGradebook}
                  disabled={!gbFilters.class_obj || !gbFilters.subject || gbLoading}
                >
                  Load
                </button>
              </div>

              {gbError && <div className="state-card error">{gbError}</div>}

              {gradebook && (
                <ReportContent
                  summary={[
                    { label: "Exams", value: gradebook.exams?.length ?? 0 },
                    { label: "Students", value: gradebook.students?.length ?? 0 },
                  ]}
                  headers={[
                    "Student",
                    ...((gradebook.exams || []).map((exam) => exam.name.slice(0, 12))),
                    "Average",
                    "Grade",
                  ]}
                  rows={(gradebook.students || []).map((student) => [
                    `${student.name} (${student.admission_number})`,
                    ...(gradebook.exams || []).map((exam) => {
                      const score = student.scores[String(exam.id)];
                      return score ? `${score.percentage}%` : "—";
                    }),
                    student.average_percentage != null ? `${student.average_percentage}%` : "—",
                    student.grade || "—",
                  ])}
                />
              )}

              {!gradebook && !gbLoading && !gbError && (
                <div className="empty-state">
                  <Table2 size={42} />
                  <h3>Pick a class and subject</h3>
                  <p>The gradebook matrix will appear here.</p>
                </div>
              )}
            </>
          )}
        </StateArea>
      </div>
    </section>
  );
}

function ReportContent({ summary = [], headers, rows, emptyHint }) {
  if (rows.length === 0) {
    return (
      <div className="empty-state">
        <BarChart3 size={42} />
        <h3>No data available</h3>
        <p>{emptyHint || "Adjust the filters to generate this report."}</p>
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
