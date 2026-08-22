import { useEffect, useMemo, useState } from "react";
import {
  Users,
  Phone,
  Mail,
  MapPin,
  ClipboardCheck,
  BookOpen,
  Wallet,
  FileText,
  Download,
  CalendarDays,
  Megaphone,
  Receipt,
  Send,
} from "lucide-react";
import { PageHeader, StateArea, EmptyState, StatusBadge } from "./ui";
import { formatDate, formatCurrency } from "./format";

async function fetchJson(url, fallback) {
  const response = await fetch(url, { credentials: "include" });

  if (!response.ok) {
    throw new Error(fallback);
  }

  const text = await response.text();

  try {
    return text ? JSON.parse(text) : {};
  } catch {
    throw new Error(fallback);
  }
}

async function fetchAllPages(url) {
  const results = [];

  let page = 1;
  let next = true;

  while (next) {
    const separator = url.includes("?") ? "&" : "?";
    const data = await fetchJson(
      `${url}${separator}page=${page}`,
      "Unable to load portal data."
    );

    results.push(...(Array.isArray(data) ? data : data.results || []));

    next = Boolean(data.next);
    page += 1;
  }

  return results;
}

function initialsOf(name) {
  return (name || "P")
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export default function ParentPortalPage() {
  const [guardian, setGuardian] = useState(null);
  const [children, setChildren] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [reportCards, setReportCards] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [timetable, setTimetable] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState("");
  const [leaveForm, setLeaveForm] = useState({ start_date: "", end_date: "", reason: "" });
  const [leaveSaving, setLeaveSaving] = useState(false);
  const [leaveNotice, setLeaveNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      fetchJson(
        "/api/students/guardians/me/",
        "Unable to load your guardian profile."
      ).catch(() => null),
      fetchAllPages("/api/students/").catch(() => []),
      fetchAllPages("/api/attendance/").catch(() => []),
      fetchAllPages("/api/report-cards/").catch(() => []),
      fetchAllPages("/api/finance/invoices/").catch(() => []),
      fetchAllPages("/api/finance/payments/").catch(() => []),
      fetchAllPages("/api/timetable/entries/").catch(() => []),
      fetchAllPages("/api/communication/announcements/").catch(() => []),
      fetchAllPages("/api/students/leave/").catch(() => []),
    ])
      .then(
        ([
          guardianData,
          students,
          attendanceData,
          cards,
          invoiceData,
          paymentData,
          timetableData,
          announcementData,
          leaveData,
        ]) => {
          setGuardian(guardianData);
          setChildren(students);
          setAttendance(attendanceData);
          setReportCards(cards);
          setInvoices(invoiceData);
          setPayments(paymentData);
          setTimetable(timetableData);
          setAnnouncements(announcementData);
          setLeaveRequests(leaveData);
          setError("");
        }
      )
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const selectedChild = children.find(
    (child) => String(child.id) === String(selectedChildId)
  ) || children[0];

  const visibleChildren = selectedChild ? [selectedChild] : [];

  const submitLeave = async (event) => {
    event.preventDefault();
    if (!selectedChild) return;
    setLeaveSaving(true);
    setLeaveNotice("");
    try {
      const response = await fetch("/api/students/leave/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.cookie.split("csrftoken=")[1]?.split(";")[0] || "",
        },
        body: JSON.stringify({ student: selectedChild.id, ...leaveForm }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(Object.values(data).flat().join(" ") || "Unable to submit leave request.");
      setLeaveRequests((current) => [data, ...current]);
      setLeaveForm({ start_date: "", end_date: "", reason: "" });
      setLeaveNotice("Leave request submitted for school review.");
    } catch (requestError) {
      setLeaveNotice(requestError.message);
    } finally {
      setLeaveSaving(false);
    }
  };

  const stats = useMemo(() => {
    const totalAttendance = attendance.length;
    const present = attendance.filter(
      (record) =>
        record.status === "present" || record.status === "late"
    ).length;

    const attendanceRate =
      totalAttendance > 0
        ? Math.round((present / totalAttendance) * 100)
        : null;

    const published = reportCards.length;

    const outstanding = invoices.reduce(
      (sum, invoice) =>
        sum + Number(invoice.balance || 0),
      0
    );

    return { totalAttendance, attendanceRate, published, outstanding };
  }, [attendance, reportCards, invoices]);

  const attendanceByStudent = useMemo(() => {
    const grouped = {};

    for (const record of attendance) {
      const id = record.student;
      grouped[id] = grouped[id] || [];
      grouped[id].push(record);
    }

    return grouped;
  }, [attendance]);

  const reportCardsByStudent = useMemo(() => {
    const grouped = {};

    for (const card of reportCards) {
      const id = card.student;
      grouped[id] = grouped[id] || [];
      grouped[id].push(card);
    }

    return grouped;
  }, [reportCards]);

  const invoicesByStudent = useMemo(() => {
    const grouped = {};

    for (const invoice of invoices) {
      const id = invoice.student;
      grouped[id] = grouped[id] || [];
      grouped[id].push(invoice);
    }

    return grouped;
  }, [invoices]);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Parent Portal"
        title="Parent Portal"
        subtitle="Attendance, results and fee statements for your children."
      />

      <StateArea
        loading={loading}
        loadingText="Loading your portal..."
        error={error}
        onRetry={() => window.location.reload()}
      >
        {children.length === 0 && guardian && (
          <EmptyState
            icon={Users}
            title="No children linked"
            message="No students are linked to your guardian profile yet. Contact the school office for help."
          />
        )}

        {children.length === 0 && !guardian && (
          <EmptyState
            icon={Users}
            title="No guardian profile"
            message="Your account is not linked to a guardian profile. Contact the school office for help."
          />
        )}

        {children.length > 0 && (
          <>
            <div className="panel students-filters">
              <div className="filter-row">
                <label>
                  Viewing child
                  <select
                    value={selectedChild?.id || ""}
                    onChange={(event) => setSelectedChildId(event.target.value)}
                  >
                    {children.map((child) => (
                      <option key={child.id} value={child.id}>
                        {child.full_name} · {child.admission_number}
                      </option>
                    ))}
                  </select>
                </label>
                <a className="secondary-button" href="/messages">
                  <Send size={15} /> Message school
                </a>
              </div>
            </div>

            <div className="portal-hero">
              <div className="portal-hero-info">
                <span className="portal-hero-label">
                  GUARDIAN
                </span>

                <h3>
                  {guardian?.name || "Parent / Guardian"}
                </h3>

                <div className="portal-hero-contact">
                  {guardian?.relationship && (
                    <span>
                      {guardian.relationship}
                    </span>
                  )}

                  {guardian?.phone && (
                    <span>
                      <Phone size={14} />
                      {guardian.phone}
                    </span>
                  )}

                  {guardian?.email && (
                    <span>
                      <Mail size={14} />
                      {guardian.email}
                    </span>
                  )}

                  {guardian?.address && (
                    <span>
                      <MapPin size={14} />
                      {guardian.address}
                    </span>
                  )}
                </div>
              </div>

              <div className="portal-hero-stats">
                <div>
                  <Users size={18} />
                  <strong>{children.length}</strong>
                  <span>Children</span>
                </div>

                <div>
                  <ClipboardCheck size={18} />
                  <strong>
                    {stats.attendanceRate === null
                      ? "—"
                      : `${stats.attendanceRate}%`}
                  </strong>
                  <span>Attendance rate</span>
                </div>

                <div>
                  <BookOpen size={18} />
                  <strong>{stats.published}</strong>
                  <span>Results</span>
                </div>

                <div>
                  <Wallet size={18} />
                  <strong>
                    {formatCurrency(stats.outstanding)}
                  </strong>
                  <span>Outstanding</span>
                </div>
              </div>
            </div>

            {visibleChildren.map((child) => {
              const childAttendance =
                attendanceByStudent[child.id] || [];
              const childCards =
                reportCardsByStudent[child.id] || [];
              const childInvoices =
                invoicesByStudent[child.id] || [];
              const childPayments = payments.filter(
                (payment) => payment.invoice && childInvoices.some((invoice) => invoice.id === payment.invoice)
              );
              const childLeaves = leaveRequests.filter(
                (leave) => leave.student === child.id
              );
              const childTimetable = timetable.filter(
                (entry) => entry.section === child.current_enrollment?.section_id
              );

              const present = childAttendance.filter(
                (record) =>
                  record.status === "present" ||
                  record.status === "late"
              ).length;

              const absent = childAttendance.filter(
                (record) => record.status === "absent"
              ).length;

              const rate =
                childAttendance.length > 0
                  ? Math.round(
                      (present / childAttendance.length) * 100
                    )
                  : null;

              const childBalance = childInvoices.reduce(
                (sum, invoice) =>
                  sum + Number(invoice.balance || 0),
                0
              );

              return (
                <div className="panel portal-child" key={child.id}>
                  <div className="portal-child-header">
                    {child.photo_url ? (
                      <img
                        className="table-photo"
                        src={child.photo_url}
                        alt={child.full_name}
                      />
                    ) : (
                      <div className="table-avatar">
                        {initialsOf(child.full_name)}
                      </div>
                    )}

                    <div>
                      <h3>{child.full_name}</h3>

                      <p>
                        {child.admission_number} ·{" "}
                        {child.current_enrollment?.class_name ||
                          "—"}{" "}
                        {child.current_enrollment?.section_name
                          ? `- ${child.current_enrollment.section_name}`
                          : ""}
                        {child.current_enrollment?.campus_name
                          ? ` · ${child.current_enrollment.campus_name}`
                          : ""}
                      </p>
                    </div>
                  </div>

                  <div className="stats-grid portal-stats">
                    <div className="stat-card">
                      <div className="stat-icon">
                        <ClipboardCheck size={21} />
                      </div>

                      <div className="stat-info">
                        <span>Attendance rate</span>
                        <strong>
                          {rate === null ? "—" : `${rate}%`}
                        </strong>
                      </div>
                    </div>

                    <div className="stat-card">
                      <div className="stat-icon">
                        <Users size={21} />
                      </div>

                      <div className="stat-info">
                        <span>Days recorded</span>
                        <strong>
                          {childAttendance.length}
                        </strong>
                      </div>
                    </div>

                    <div className="stat-card">
                      <div className="stat-icon">
                        <ClipboardCheck size={21} />
                      </div>

                      <div className="stat-info">
                        <span>Present / Absent</span>
                        <strong>
                          {present} / {absent}
                        </strong>
                      </div>
                    </div>

                    <div className="stat-card">
                      <div className="stat-icon">
                        <BookOpen size={21} />
                      </div>

                      <div className="stat-info">
                        <span>Results published</span>
                        <strong>{childCards.length}</strong>
                      </div>
                    </div>

                    <div className="stat-card">
                      <div className="stat-icon">
                        <Wallet size={21} />
                      </div>

                      <div className="stat-info">
                        <span>Fee balance</span>
                        <strong>
                          {formatCurrency(childBalance)}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="portal-sections">
                    <div className="portal-section">
                      <div className="panel-header">
                        <div>
                          <h4>Leave requests</h4>
                          <p>Request and track absence approval</p>
                        </div>
                      </div>
                      <form onSubmit={submitLeave}>
                        <div className="form-grid">
                          <label>From<input type="date" value={leaveForm.start_date} onChange={(event) => setLeaveForm({ ...leaveForm, start_date: event.target.value })} required /></label>
                          <label>To<input type="date" value={leaveForm.end_date} onChange={(event) => setLeaveForm({ ...leaveForm, end_date: event.target.value })} required /></label>
                          <label>Reason<textarea value={leaveForm.reason} onChange={(event) => setLeaveForm({ ...leaveForm, reason: event.target.value })} required /></label>
                        </div>
                        <button className="primary-button" type="submit" disabled={leaveSaving}>
                          <Send size={15} /> {leaveSaving ? "Submitting..." : "Submit leave request"}
                        </button>
                      </form>
                      {leaveNotice && <div className="state-card">{leaveNotice}</div>}
                      {childLeaves.length > 0 && (
                        <div className="overview-list">
                          {childLeaves.slice(0, 5).map((leave) => (
                            <div key={leave.id}><span>{formatDate(leave.start_date)} - {formatDate(leave.end_date)}</span><StatusBadge status={leave.status} label={leave.status_display} /></div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="portal-section">
                      <div className="panel-header"><div><h4>Payments and receipts</h4><p>Payment history for this child</p></div></div>
                      {childPayments.length === 0 ? <div className="state-card">No payments recorded yet.</div> : (
                        <div className="table-wrapper"><table className="data-table"><thead><tr><th>RECEIPT</th><th>DATE</th><th>METHOD</th><th>AMOUNT</th><th></th></tr></thead><tbody>
                          {childPayments.slice(0, 10).map((payment) => <tr key={payment.id}><td><strong>{payment.receipt_number}</strong></td><td>{formatDate(payment.payment_date)}</td><td>{payment.payment_method_display}</td><td>{formatCurrency(payment.net_amount || payment.amount)}</td><td><a className="table-action" href={`/api/finance/payments/${payment.id}/receipt/`} target="_blank" rel="noreferrer"><Receipt size={15} /> View receipt</a><a className="table-action" href={`/api/finance/payments/${payment.id}/receipt.pdf/`} target="_blank" rel="noreferrer"><Download size={15} /> PDF</a></td></tr>)}
                        </tbody></table></div>
                      )}
                    </div>

                    <div className="portal-section">
                      <div className="panel-header"><div><h4>Class timetable</h4><p>Current schedule for this child</p></div><CalendarDays size={20} /></div>
                      {childTimetable.length === 0 ? <div className="state-card">No timetable entries found.</div> : <div className="overview-list">{childTimetable.slice(0, 10).map((entry) => <div key={entry.id}><span>{entry.day_display || entry.day} · {entry.subject_name || entry.subject}</span><strong>{entry.start_time || ""} {entry.room ? `· ${entry.room}` : ""}</strong></div>)}</div>}
                    </div>

                    <div className="portal-section">
                      <div className="panel-header"><div><h4>School announcements</h4><p>Published notices for your family</p></div><Megaphone size={20} /></div>
                      {announcements.length === 0 ? <div className="state-card">No announcements available.</div> : <div className="overview-list">{announcements.slice(0, 5).map((announcement) => <div key={announcement.id}><span><strong>{announcement.title}</strong><br />{announcement.message}</span><small>{formatDate(announcement.published_at || announcement.created_at)}</small></div>)}</div>}
                    </div>

                    <div className="portal-section">
                      <div className="panel-header">
                        <div>
                          <h4>Report Cards</h4>
                          <p>Latest published results</p>
                        </div>
                      </div>

                      {childCards.length === 0 ? (
                        <div className="state-card">
                          No published results yet.
                        </div>
                      ) : (
                        <div className="table-wrapper">
                          <table className="data-table">
                            <thead>
                              <tr>
                                <th>EXAM</th>
                                <th>DATE</th>
                                <th>PERCENTAGE</th>
                                <th>GRADE</th>
                                <th>RESULT</th>
                              </tr>
                            </thead>

                            <tbody>
                              {childCards.map((card) => (
                                <tr key={card.id}>
                                  <td>
                                    <strong>
                                      {card.exam_name}
                                    </strong>
                                    <span className="cell-sub">
                                      {card.exam_type_display}
                                    </span>
                                  </td>

                                  <td>
                                    {formatDate(
                                      card.published_at
                                    )}
                                  </td>

                                  <td>
                                    <strong>
                                      {card.percentage
                                        ? `${card.percentage}%`
                                        : "—"}
                                    </strong>
                                  </td>

                                  <td>
                                    <span className="grade-badge">
                                      {card.grade || "—"}
                                    </span>
                                  </td>

                                  <td>
                                    <span
                                      className={`status-badge ${
                                        card.is_pass
                                          ? "active"
                                          : "inactive"
                                      }`}
                                    >
                                      {card.is_pass
                                        ? "Pass"
                                        : "Fail"}
                                    </span>
                                    <a className="table-action" href={`/api/report-cards/${card.id}/pdf/`} target="_blank" rel="noreferrer"><Download size={14} /> PDF</a>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    <div className="portal-section">
                      <div className="panel-header">
                        <div>
                          <h4>Fee Invoices</h4>
                          <p>Recent fee statements</p>
                        </div>
                      </div>

                      {childInvoices.length === 0 ? (
                        <div className="state-card">
                          No invoices found.
                        </div>
                      ) : (
                        <div className="table-wrapper">
                          <table className="data-table">
                            <thead>
                              <tr>
                                <th>INVOICE</th>
                                <th>ISSUED</th>
                                <th>DUE</th>
                                <th>AMOUNT</th>
                                <th>BALANCE</th>
                                <th>STATUS</th>
                              </tr>
                            </thead>

                            <tbody>
                              {childInvoices.map((invoice) => (
                                <tr key={invoice.id}>
                                  <td>
                                    <strong>
                                      {invoice.invoice_number}
                                    </strong>
                                  </td>

                                  <td>
                                    {formatDate(
                                      invoice.issue_date
                                    )}
                                  </td>

                                  <td>
                                    {formatDate(invoice.due_date)}
                                  </td>

                                  <td>
                                    {formatCurrency(
                                      invoice.total_amount
                                    )}
                                  </td>

                                  <td>
                                    <strong>
                                      {formatCurrency(
                                        invoice.balance
                                      )}
                                    </strong>
                                  </td>

                                  <td>
                                    <span
                                      className={`status-badge ${
                                        invoice.status === "paid"
                                          ? "active"
                                          : invoice.status ===
                                            "partial"
                                          ? "warn"
                                          : "inactive"
                                      }`}
                                    >
                                      {invoice.status_display ||
                                        invoice.status}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    <div className="portal-section">
                      <div className="panel-header">
                        <div>
                          <h4>Recent Attendance</h4>
                          <p>Last ten recorded days</p>
                        </div>
                      </div>

                      {childAttendance.length === 0 ? (
                        <div className="state-card">
                          No attendance records yet.
                        </div>
                      ) : (
                        <div className="table-wrapper">
                          <table className="data-table">
                            <thead>
                              <tr>
                                <th>DATE</th>
                                <th>STATUS</th>
                                <th>CLASS</th>
                              </tr>
                            </thead>

                            <tbody>
                              {childAttendance
                                .slice(0, 10)
                                .map((record) => (
                                  <tr key={record.id}>
                                    <td>
                                      {formatDate(record.date)}
                                    </td>

                                    <td>
                                      <span
                                        className={`status-badge ${
                                          record.status ===
                                          "present"
                                            ? "active"
                                            : record.status ===
                                              "late"
                                            ? "warn"
                                            : "inactive"
                                        }`}
                                      >
                                        {record.status_display}
                                      </span>
                                    </td>

                                    <td>
                                      {record.class_name} -{" "}
                                      {record.section_name}
                                    </td>
                                  </tr>
                                ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    {(child.documents || []).length > 0 && (
                      <div className="portal-section">
                        <div className="panel-header">
                          <div>
                            <h4>Documents</h4>
                            <p>Files attached to this student</p>
                          </div>
                        </div>

                        <div className="document-grid">
                          {(child.documents || []).map(
                            (document) => (
                              <a
                                className="document-card"
                                key={document.id}
                                href={document.file_url}
                                target="_blank"
                                rel="noreferrer"
                              >
                                <FileText size={22} />

                                <div>
                                  <strong>
                                    {document.title}
                                  </strong>
                                  <span>
                                    {
                                      document.document_type_label
                                    }
                                  </span>
                                </div>

                                <Download size={16} />
                              </a>
                            )
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </>
        )}
      </StateArea>
    </section>
  );
}
