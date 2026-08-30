import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertOctagon,
  ArrowLeft,
  BookOpen,
  Bus,
  CalendarCheck,
  Download,
  FileText,
  GraduationCap,
  HeartPulse,
  LibraryBig,
  Trash2,
  Wallet,
} from "lucide-react";
import { useAuth } from "../auth";
import { apiDownload, apiFetch } from "../api";
import StudentLifecyclePanel, { CAN_MANAGE, CAN_REVIEW } from "./StudentLifecyclePanel";
import { EmptyState, PageHeader, StateArea, StatusBadge } from "./ui";
import { formatCurrency, formatDate } from "./format";

const FINANCE_ROLES = ["super_admin", "admin", "principal", "academic", "accountant"];
const HEALTH_ROLES = ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"];
const SCHOLAR_ROLES = ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "accountant", "teacher", "staff", "hr"];

function toList(data) {
  return Array.isArray(data) ? data : data.results || [];
}

function Chip({ label, value }) {
  return (
    <div className="stat-card" style={{ padding: "12px 14px", minHeight: 0 }}>
      <div className="stat-info">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

export default function Student360Page() {
  const { id } = useParams();
  const { hasRole } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyDoc, setBusyDoc] = useState(null);
  const [health, setHealth] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");

  const load = useCallback(() => {
    setLoading(true);
    return fetch(`/api/students/${id}/360/`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error("Failed to load the 360 profile."))))
      .then((student) => {
        setData(student);
        setError("");
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!id) return;
    fetch(`/api/health-records/records/?student=${id}&page_size=200`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((records) => setHealth(toList(records)))
      .catch(() => {});
  }, [id]);

  const canManage = hasRole(CAN_MANAGE);
  const canReview = hasRole(CAN_REVIEW);

  const tabs = [
    { key: "overview", label: "Overview", icon: GraduationCap, allowed: true },
    { key: "academics", label: "Academics", icon: BookOpen, allowed: true },
    { key: "attendance", label: "Attendance", icon: CalendarCheck, allowed: hasRole(SCHOLAR_ROLES) },
    { key: "exams", label: "Exams", icon: FileText, allowed: hasRole(SCHOLAR_ROLES) },
    { key: "finance", label: "Finance", icon: Wallet, allowed: hasRole(FINANCE_ROLES) },
    { key: "library", label: "Library", icon: LibraryBig, allowed: hasRole(SCHOLAR_ROLES) },
    { key: "transport", label: "Transport", icon: Bus, allowed: hasRole(SCHOLAR_ROLES) },
    { key: "discipline", label: "Discipline", icon: AlertOctagon, allowed: canReview },
    { key: "health", label: "Health", icon: HeartPulse, allowed: hasRole(HEALTH_ROLES) },
    { key: "documents", label: "Documents", icon: FileText, allowed: canManage },
    { key: "certificates", label: "Certificates", icon: GraduationCap, allowed: true },
    { key: "lifecycle", label: "Lifecycle", icon: CalendarCheck, allowed: canManage || canReview },
  ];

  const currentTab = tabs.some((t) => t.key === activeTab && t.allowed) ? activeTab : "overview";

  const s = data || {};
  const enrollment = s.current_enrollment || {};
  const records = (value) => (Array.isArray(value) ? value : []);
  const attendance = s.attendance_summary || {};
  const discipline = s.discipline_summary || {};
  const transport = s.transport_assignment || {};

  const deleteDocument = (doc) => {
    if (!window.confirm(`Delete document "${doc.title}"?`)) return;
    setBusyDoc(doc.id);
    setNotice("");
    apiFetch(`/api/students/documents/${doc.id}/`, { method: "DELETE" })
      .then(() => {
        setNotice("Document deleted.");
        load();
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setBusyDoc(null));
  };

  const renderOverview = () => (
    <div className="panel">
      <PanelHeader title="Profile" count={`${records(s.guardian_links).length} guardian${records(s.guardian_links).length === 1 ? "" : "s"}`} />
      <div style={{ display: "flex", gap: 18, flexWrap: "wrap", alignItems: "center", marginBottom: 16 }}>
        {s.photo_url ? (
          <img src={s.photo_url} alt={s.full_name} className="table-photo" style={{ width: 84, height: 84 }} />
        ) : (
          <div className="table-avatar" style={{ width: 84, height: 84, fontSize: 28 }}>{String(s.full_name || "S").charAt(0)}</div>
        )}
        <div style={{ flex: 1, minWidth: 220 }}>
          <h3 style={{ margin: 0 }}>{s.full_name}</h3>
          <p className="table-sub">{s.admission_number} · {enrollment.class_name || "No active class"}</p>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <StatusBadge status={s.status} label={s.status} />
            {enrollment.campus_name && <StatusBadge status="active" label={enrollment.campus_name} />}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" className="secondary-button" onClick={() => apiDownload(`/api/students/${id}/transcript.pdf`, "transcript.pdf").catch(() => setError("Could not download transcript."))}>
            <Download size={14} /> Transcript
          </button>
        </div>
      </div>

      <div className="detail-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 }}>
        <Meta label="Date of birth" value={`${formatDate(s.date_of_birth)}${s.age ? ` (${s.age})` : ""}`} />
        <Meta label="Gender" value={s.gender || "—"} />
        <Meta label="Phone" value={s.phone || "—"} />
        <Meta label="Address" value={s.address || "—"} />
        <Meta label="Admission date" value={formatDate(s.admission_date)} />
        <Meta label="Membership" value={s.membership || "—"} />
      </div>

      <div className="detail-strip" style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "18px 0" }}>
        <Chip label="Fee balance" value={formatCurrency(s.fee_balance)} />
        <Chip label="Attendance" value={attendance.attendance_percentage !== undefined ? `${attendance.attendance_percentage}%` : "—"} />
        <Chip label="Discipline incidents" value={discipline.total_incidents ?? "—"} />
        <Chip label="Documents" value={records(s.documents).length} />
      </div>

      <PanelHeader title="Guardians" />
      {records(s.guardian_links).length === 0 && records(s.guardian_details).length === 0 ? (
        <EmptyState icon={UserCircle} title="No guardian linked" message="This student has no guardian on file." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>NAME</th><th>RELATIONSHIP</th><th>PHONE</th><th>EMAIL</th><th>PRIMARY</th>
              </tr>
            </thead>
            <tbody>
              {s.guardian_details && (
                <tr key="primary">
                  <td><strong>{s.guardian_details.name}</strong></td>
                  <td>{s.guardian_details.relationship || "Guardian"}</td>
                  <td>{s.guardian_details.phone || "—"}</td>
                  <td>{s.guardian_details.email || "—"}</td>
                  <td><StatusBadge status="active" label="Primary" /></td>
                </tr>
              )}
              {records(s.guardian_links)
                .filter((g) => Number(g.guardian) !== Number(s.guardian))
                .map((g) => (
                <tr key={g.id}>
                  <td><strong>{g.guardian_name || g.guardian?.name || g.name}</strong></td>
                  <td>{g.relationship || "—"}</td>
                  <td>—</td>
                  <td>—</td>
                  <td>{g.is_primary ? <StatusBadge status="active" label="Primary" /> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderAcademics = () => (
    <div className="panel">
      <PanelHeader title="Enrollment history" count={`${records(s.enrollments).length} enrollments`} />
      {records(s.enrollments).length === 0 ? (
        <div className="state-card">No enrollment records.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>YEAR</th><th>CAMPUS</th><th>CLASS</th><th>SECTION</th><th>ROLL NO</th><th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {records(s.enrollments).map((e) => (
                <tr key={e.id}>
                  <td>{e.academic_year_name || e.academic_year || "—"}</td>
                  <td>{e.campus_name || "—"}</td>
                  <td>{e.class_name || "—"}</td>
                  <td>{e.section_name || "—"}</td>
                  <td>{e.roll_number || "—"}</td>
                  <td><StatusBadge status={e.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <PanelHeader title="Academic history" count={`${records(s.academic_history).length} records`} />
      {records(s.academic_history).length === 0 ? (
        <div className="state-card">No academic history.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>YEAR</th><th>CAMPUS</th><th>CLASS</th><th>SECTION</th><th>FINAL STATUS</th><th>RESULT</th>
              </tr>
            </thead>
            <tbody>
              {records(s.academic_history).map((h) => (
                <tr key={h.id}>
                  <td>{h.academic_year_name || "—"}</td>
                  <td>{h.campus_name || "—"}</td>
                  <td>{h.class_name || "—"}</td>
                  <td>{h.section_name || "—"}</td>
                  <td><StatusBadge status={h.final_status} label={h.final_status_display} /></td>
                  <td>{h.promotion_status_display || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderAttendance = () => (
    <div className="panel">
      <PanelHeader title="Attendance summary" count={attendance.academic_year ? attendance.academic_year : ""} />
      <div className="detail-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10, marginBottom: 16 }}>
        <Chip label="Total days" value={attendance.total_days ?? "—"} />
        <Chip label="Present" value={attendance.present ?? "—"} />
        <Chip label="Absent" value={attendance.absent ?? "—"} />
        <Chip label="Late" value={attendance.late ?? "—"} />
        <Chip label="Leave" value={attendance.leave ?? "—"} />
        <Chip label="Percentage" value={attendance.attendance_percentage !== undefined ? `${attendance.attendance_percentage}%` : "—"} />
      </div>
      <PanelHeader title="Recent attendance" />
      {records(s.attendance_records).length === 0 ? (
        <div className="state-card">No attendance records found.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>DATE</th><th>STATUS</th><th>NOTES</th>
              </tr>
            </thead>
            <tbody>
              {records(s.attendance_records).map((a, index) => (
                <tr key={index}>
                  <td>{formatDate(a.date)}</td>
                  <td><StatusBadge status={a.status} /></td>
                  <td>{a.notes || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderExams = () => (
    <div className="panel">
      <PanelHeader title="Exam results" />
      {records(s.exam_results).length === 0 ? (
        <div className="state-card">No exam results in the current academic year.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>EXAM</th><th>SUBJECT</th><th>MARKS</th><th>%</th><th>GRADE</th><th>RESULT</th>
              </tr>
            </thead>
            <tbody>
              {records(s.exam_results).map((r, index) => (
                <tr key={index}>
                  <td>{r.exam_name}</td>
                  <td>{r.subject_name}</td>
                  <td>{r.obtained_marks} / {r.maximum_marks}</td>
                  <td>{r.percentage}</td>
                  <td>{r.grade || "—"}</td>
                  <td><StatusBadge status={r.is_pass ? "pass" : "fail"} label={r.is_pass ? "Pass" : "Fail"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <PanelHeader title="Practical results" />
      {records(s.practical_results).length === 0 ? (
        <div className="state-card">No practical results.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>EXAM</th><th>SUBJECT</th><th>MARKS</th><th>%</th><th>GRADE</th><th>RESULT</th>
              </tr>
            </thead>
            <tbody>
              {records(s.practical_results).map((r, index) => (
                <tr key={index}>
                  <td>{r.exam_name}</td>
                  <td>{r.subject_name}</td>
                  <td>{r.obtained_marks} / {r.maximum_marks}</td>
                  <td>{r.percentage}</td>
                  <td>{r.grade || "—"}</td>
                  <td><StatusBadge status={r.is_pass ? "pass" : "fail"} label={r.is_pass ? "Pass" : "Fail"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderFinance = () => (
    <div className="panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Fee balance</h3>
        <span className="stat-value" style={{ color: Number(s.fee_balance) > 0 ? "var(--danger)" : undefined }}>{formatCurrency(s.fee_balance)}</span>
      </div>
      <PanelHeader title="Invoices" />
      {records(s.invoices).length === 0 ? (
        <div className="state-card">No invoices.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>INVOICE</th><th>ISSUED</th><th>DUE</th><th>TOTAL</th><th>PAID</th><th>BALANCE</th><th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {records(s.invoices).map((inv) => (
                <tr key={inv.id}>
                  <td>{inv.invoice_number}</td>
                  <td>{formatDate(inv.issue_date)}</td>
                  <td>{formatDate(inv.due_date)}</td>
                  <td>{formatCurrency(inv.total_amount)}</td>
                  <td>{formatCurrency(inv.paid_amount)}</td>
                  <td>{formatCurrency(inv.balance)}</td>
                  <td><StatusBadge status={inv.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <PanelHeader title="Payments" />
      {records(s.payments).length === 0 ? (
        <div className="state-card">No payments recorded.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>RECEIPT</th><th>DATE</th><th>AMOUNT</th><th>METHOD</th><th>INVOICE</th><th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {records(s.payments).map((p) => (
                <tr key={p.id}>
                  <td>{p.receipt_number}</td>
                  <td>{formatDate(p.payment_date)}</td>
                  <td>{formatCurrency(p.amount)}</td>
                  <td>{p.payment_method || "—"}</td>
                  <td>{p.invoice_number || "—"}</td>
                  <td><StatusBadge status={p.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderLibrary = () => (
    <div className="panel">
      <PanelHeader title="Book issues" count={`${records(s.book_issues).length} issues`} />
      {records(s.book_issues).length === 0 ? (
        <EmptyState icon={LibraryBig} title="No book issues" message="Borrowing history will appear here." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>BOOK</th><th>AUTHOR</th><th>ISSUED</th><th>DUE</th><th>RETURNED</th><th>STATUS</th><th>FINE</th>
              </tr>
            </thead>
            <tbody>
              {records(s.book_issues).map((b) => (
                <tr key={b.id}>
                  <td><strong>{b.book_title}</strong></td>
                  <td>{b.book_author || "—"}</td>
                  <td>{formatDate(b.issue_date)}</td>
                  <td>{formatDate(b.due_date)}</td>
                  <td>{formatDate(b.return_date)}</td>
                  <td><StatusBadge status={b.status} /></td>
                  <td>{formatCurrency(b.fine_amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderTransport = () => (
    <div className="panel">
      <PanelHeader title="Transport assignment" />
      {!transport.route_name ? (
        <EmptyState icon={Bus} title="No transport assignment" message="This student is not assigned to any active route." />
      ) : (
        <div className="detail-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10 }}>
          <Meta label="Route" value={transport.route_name} />
          <Meta label="Stop" value={transport.stop_name || "—"} />
          <Meta label="Vehicle" value={transport.vehicle_number || "—"} />
          <Meta label="Driver" value={transport.driver_name || "—"} />
          <Meta label="Status" value={transport.status || "—"} />
        </div>
      )}
    </div>
  );

  const renderDiscipline = () => (
    <div className="panel">
      <div className="detail-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10, marginBottom: 16 }}>
        <Chip label="Total incidents" value={discipline.total_incidents ?? "—"} />
        <Chip label="Open" value={discipline.open_incidents ?? "—"} />
        <Chip label="Resolved" value={discipline.resolved_incidents ?? "—"} />
        <Chip label="Total points" value={discipline.total_points ?? "—"} />
      </div>
      <PanelHeader title="Incidents" />
      {records(s.discipline_incidents).length === 0 ? (
        <div className="state-card">No discipline incidents.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>DATE</th><th>TITLE</th><th>SEVERITY</th><th>POINTS</th><th>STATUS</th><th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {records(s.discipline_incidents).map((d) => (
                <tr key={d.id}>
                  <td>{formatDate(d.incident_date)}</td>
                  <td><strong>{d.title}</strong></td>
                  <td>{d.severity_display || d.severity}</td>
                  <td>{d.points ?? "—"}</td>
                  <td><StatusBadge status={d.status} label={d.status_display} /></td>
                  <td>{d.action_taken || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderHealth = () => (
    <div className="panel">
      <PanelHeader title="Health records" count={`${health.length} records`} />
      {health.length === 0 ? (
        <EmptyState icon={HeartPulse} title="No health records" message="Medical records for this student will appear here." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>DATE</th><th>TYPE</th><th>HEIGHT</th><th>WEIGHT</th><th>TEMP</th><th>BMI</th><th>NOTES</th><th>FOLLOW-UP</th>
              </tr>
            </thead>
            <tbody>
              {health.map((h) => (
                <tr key={h.id}>
                  <td>{formatDate(h.record_date)}</td>
                  <td>{h.record_type_display || h.record_type}</td>
                  <td>{h.height_cm ? `${h.height_cm} cm` : "—"}</td>
                  <td>{h.weight_kg ? `${h.weight_kg} kg` : "—"}</td>
                  <td>{h.temperature_c ? `${h.temperature_c}°C` : "—"}</td>
                  <td>{h.bmi ?? "—"}</td>
                  <td>{h.notes || "—"}</td>
                  <td>{formatDate(h.follow_up_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderDocuments = () => (
    <div className="panel">
      <PanelHeader title="Documents" count={`${records(s.documents).length} documents`} />
      {records(s.documents).length === 0 ? (
        <EmptyState icon={FileText} title="No documents" message="Uploaded documents and certificates will appear here." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>TITLE</th><th>TYPE</th><th>UPLOADED BY</th><th>DATE</th><th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {records(s.documents).map((d) => (
                <tr key={d.id}>
                  <td><strong>{d.title}</strong></td>
                  <td>{d.document_type_label || d.document_type}</td>
                  <td>{d.uploaded_by_name || "—"}</td>
                  <td>{formatDate(d.created_at)}</td>
                  <td>
                    <div className="table-actions">
                      {d.file_url && (
                        <button className="secondary-button" onClick={() => window.open(d.file_url, "_blank")}>
                          <Download size={14} /> View
                        </button>
                      )}
                      {canManage && (
                        <button className="danger-button" disabled={busyDoc === d.id} onClick={() => deleteDocument(d)}>
                          <Trash2 size={14} /> Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderCertificates = () => (
    <div className="panel">
      <PanelHeader title="Transfer certificates" count={`${records(s.transfer_certificates).length} certificates`} />
      {records(s.transfer_certificates).length === 0 ? (
        <div className="state-card">No transfer certificates issued.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>CODE</th><th>ISSUED</th><th>CAMPUS</th><th>CLASS</th><th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {records(s.transfer_certificates).map((c) => (
                <tr key={c.id}>
                  <td>{c.code || c.id}</td>
                  <td>{formatDate(c.issue_date)}</td>
                  <td>{c.campus_name || "—"}</td>
                  <td>{c.class_name || "—"}</td>
                  <td><StatusBadge status={c.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <PanelHeader title="Downloads" />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {canManage && (
          <>
            {[["bonafide", "Bonafide"], ["character", "Character"], ["transfer", "Transfer"]].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className="primary-button"
                onClick={() => apiDownload(`/api/students/${id}/certificate/${value}/`, `${value}_certificate.pdf`).catch(() => setError("Could not download certificate."))}
              >
                <Download size={14} /> {label} Certificate
              </button>
            ))}
            <button
              type="button"
              className="primary-button"
              onClick={() => apiDownload(`/api/students/${id}/transcript.pdf`, "transcript.pdf").catch(() => setError("Could not download transcript."))}
            >
              <Download size={14} /> Transcript
            </button>
          </>
        )}
      </div>
    </div>
  );

  const renderLifecycle = () => (
    <StudentLifecyclePanel
      studentId={Number(id)}
      studentName={s.full_name}
      currentCampusId={enrollment.campus_id}
      runId={s.updated_at}
      hasRole={hasRole}
      onChanged={load}
    />
  );

  const content = {
    overview: renderOverview,
    academics: renderAcademics,
    attendance: renderAttendance,
    exams: renderExams,
    finance: renderFinance,
    library: renderLibrary,
    transport: renderTransport,
    discipline: renderDiscipline,
    health: renderHealth,
    documents: renderDocuments,
    certificates: renderCertificates,
    lifecycle: renderLifecycle,
  }[currentTab];

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Students / 360 Profile"
        title={s.full_name || "Student 360"}
        subtitle={s.admission_number ? `360° view of ${s.admission_number}` : "360° view of the student record"}
        action={
          <Link to="/students" className="secondary-button" style={{ textDecoration: "none" }}>
            <ArrowLeft size={15} /> Back to Students
          </Link>
        }
      />

      {notice && (
        <div className="state-card success">
          <strong>{notice}</strong>
        </div>
      )}

      {error && (
        <div className="state-card error">
          <strong>{error}</strong>
        </div>
      )}

      <StateArea loading={loading} error={error} onRetry={load}>
        <div className="tabs" style={{ marginBottom: 16, flexWrap: "wrap" }}>
          {tabs.filter((t) => t.allowed).map((t) => {
            const Icon = t.icon;
            return (
              <button key={t.key} type="button" className={currentTab === t.key ? "active" : ""} onClick={() => setActiveTab(t.key)}>
                <Icon size={14} style={{ verticalAlign: -2, marginRight: 6 }} />
                {t.label}
              </button>
            );
          })}
        </div>
        {content()}
      </StateArea>
    </section>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <span style={{ display: "block", color: "var(--text-muted)", fontSize: 11, fontWeight: 500, marginBottom: 3 }}>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

function PanelHeader({ title, count }) {
  return (
    <div className="teacher-list-header">
      <div>
        <h3>{title}</h3>
        {typeof count === "string" && <p>{count}</p>}
      </div>
    </div>
  );
}

function UserCircle(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
    </svg>
  );
}