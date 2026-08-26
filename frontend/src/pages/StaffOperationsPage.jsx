import { useCallback, useEffect, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Plus,
  XCircle,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/staff/";

const LEAVE_TYPES = [
  ["casual", "Casual Leave"],
  ["sick", "Sick Leave"],
  ["annual", "Annual Leave"],
  ["maternity", "Maternity Leave"],
  ["paternity", "Paternity Leave"],
  ["unpaid", "Unpaid Leave"],
  ["other", "Other"],
];

const ATT_STATUS = [
  ["present", "Present"],
  ["absent", "Absent"],
  ["late", "Late"],
  ["half_day", "Half Day"],
  ["leave", "On Leave"],
];

export default function StaffOperationsPage({ canReview }) {
  const [tab, setTab] = useState("leave");
  const [leaves, setLeaves] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const today = new Date().toISOString().slice(0, 10);

  const [leaveFilter, setLeaveFilter] = useState("pending");
  const [showLeaveForm, setShowLeaveForm] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    leave_type: "casual",
    start_date: today,
    end_date: today,
    reason: "",
  });

  const [attDate, setAttDate] = useState(today);
  const [attForm, setAttForm] = useState({
    staff: "",
    status: "present",
    check_in: "",
    check_out: "",
    notes: "",
  });

  useEffect(() => {
    fetch(`${BASE}?page_size=500`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { results: [] }))
      .then((json) => setStaffList(json.results || []))
      .catch(() => setStaffList([]));
  }, []);

  const loadLeaves = useCallback(() => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();
    if (leaveFilter) params.append("status", leaveFilter);

    apiFetch(`${BASE}leave/?${params.toString()}`)
      .then((data) => setLeaves(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [leaveFilter]);

  const loadAttendance = useCallback(() => {
    setLoading(true);

    apiFetch(`${BASE}attendance/?date=${attDate}`)
      .then((data) => setAttendance(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [attDate]);

  useEffect(() => {
    if (tab === "leave") loadLeaves();
    else loadAttendance();
  }, [tab, loadLeaves, loadAttendance]);

  const submitLeave = (event) => {
    event.preventDefault();
    setNotice("");

    apiFetch(`${BASE}leave/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(leaveForm),
    })
      .then(() => {
        setShowLeaveForm(false);
        setLeaveForm({ ...leaveForm, reason: "" });
        setNotice("Leave request submitted.");
        loadLeaves();
      })
      .catch((err) => setError(err.message));
  };

  const reviewLeave = (id, decision) => {
    setNotice("");

    apiFetch(`${BASE}leave/${id}/action/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        action: decision,
        review_notes: `${decision === "approve" ? "Approved" : "Rejected"} from staff portal`,
      }),
    })
      .then(() => {
        setNotice(`Request ${decision === "approve" ? "approved" : "rejected"}.`);
        loadLeaves();
      })
      .catch((err) => setError(err.message));
  };

  const markAttendance = (event) => {
    event.preventDefault();
    setNotice("");

    apiFetch(`${BASE}attendance/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        ...attForm,
        check_in: attForm.check_in || null,
        check_out: attForm.check_out || null,
        date: attDate,
      }),
    })
      .then(() => {
        setAttForm({ ...attForm, notes: "" });
        setNotice("Attendance recorded.");
        loadAttendance();
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Staff Operations"
        title="Staff Leave & Attendance"
        subtitle="Track leave requests and daily staff attendance."
        action={
          tab === "leave" ? (
            <button
              type="button"
              className="primary-button"
              onClick={() => setShowLeaveForm((v) => !v)}
            >
              <Plus size={15} />
              New Request
            </button>
          ) : undefined
        }
      />

      <div className="tabs">
        <button
          className={`tab-button ${tab === "leave" ? "active" : ""}`}
          onClick={() => setTab("leave")}
        >
          <CalendarClock size={15} />
          Leave Requests
        </button>

        <button
          className={`tab-button ${tab === "attendance" ? "active" : ""}`}
          onClick={() => setTab("attendance")}
        >
          <ClipboardCheck size={15} />
          Daily Attendance
        </button>
      </div>

      <div className="panel">
        <PanelHeader
          title={tab === "leave" ? "Leave Requests" : "Attendance Register"}
          subtitle={notice || "live data"}
        />

        <StateArea loading={loading} error={error} onRetry={tab === "leave" ? loadLeaves : loadAttendance}>
          {tab === "leave" && (
            <>
              {showLeaveForm && (
                <form onSubmit={submitLeave} className="filter-row">
                  <select
                    value={leaveForm.leave_type}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, leave_type: e.target.value })
                    }
                  >
                    {LEAVE_TYPES.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>

                  <input
                    type="date"
                    required
                    value={leaveForm.start_date}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, start_date: e.target.value })
                    }
                  />

                  <input
                    type="date"
                    required
                    value={leaveForm.end_date}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, end_date: e.target.value })
                    }
                  />

                  <input
                    required
                    placeholder="Reason"
                    value={leaveForm.reason}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, reason: e.target.value })
                    }
                  />

                  <button className="primary-button">Submit</button>
                </form>
              )}

              <div className="filter-row">
                <select
                  value={leaveFilter}
                  onChange={(e) => setLeaveFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              {leaves.length === 0 ? (
                <div className="empty-state">
                  <CalendarClock size={42} />
                  <h3>No leave requests</h3>
                  <p>Nothing matches this filter.</p>
                </div>
              ) : (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Staff</th>
                        <th>Type</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Status</th>
                        {canReview && <th>Review</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {leaves.map((leave) => (
                        <tr key={leave.id}>
                          <td><strong>{leave.staff_name}</strong></td>
                          <td>{leave.leave_type_label}</td>
                          <td>{leave.start_date}</td>
                          <td>{leave.end_date}</td>
                          <td>{leave.status}</td>
                          {canReview && (
                            <td>
                              {leave.status === "pending" && (
                                <>
                                  <button
                                    type="button"
                                    className="primary-button"
                                    onClick={() => reviewLeave(leave.id, "approve")}
                                  >
                                    <CheckCircle2 size={14} /> Approve
                                  </button>{" "}
                                  <button
                                    type="button"
                                    className="primary-button"
                                    onClick={() => reviewLeave(leave.id, "reject")}
                                  >
                                    <XCircle size={14} /> Reject
                                  </button>
                                </>
                              )}
                              {leave.status !== "pending" && "—"}
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {tab === "attendance" && (
            <>
              <div className="filter-row">
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  Date
                  <input
                    type="date"
                    value={attDate}
                    onChange={(e) => setAttDate(e.target.value)}
                  />
                </label>
              </div>

              <form onSubmit={markAttendance} className="filter-row">
                <select
                  required
                  value={attForm.staff}
                  onChange={(e) => setAttForm({ ...attForm, staff: e.target.value })}
                >
                  <option value="">Staff member...</option>
                  {staffList.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.full_name}
                    </option>
                  ))}
                </select>

                <select
                  value={attForm.status}
                  onChange={(e) => setAttForm({ ...attForm, status: e.target.value })}
                >
                  {ATT_STATUS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>

                <input
                  type="time"
                  placeholder="Check-in"
                  value={attForm.check_in}
                  onChange={(e) =>
                    setAttForm({ ...attForm, check_in: e.target.value })
                  }
                />

                <input
                  type="time"
                  placeholder="Check-out"
                  value={attForm.check_out}
                  onChange={(e) =>
                    setAttForm({ ...attForm, check_out: e.target.value })
                  }
                />

                <input
                  placeholder="Notes (optional)"
                  value={attForm.notes}
                  onChange={(e) =>
                    setAttForm({ ...attForm, notes: e.target.value })
                  }
                />

                <button className="primary-button">Mark</button>
              </form>

              {attendance.length === 0 ? (
                <div className="empty-state">
                  <ClipboardCheck size={42} />
                  <h3>No records for this date</h3>
                  <p>Mark attendance using the form above.</p>
                </div>
              ) : (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Staff</th>
                        <th>Date</th>
                        <th>Status</th>
                        <th>Check-in</th>
                        <th>Check-out</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attendance.map((record) => (
                        <tr key={record.id}>
                          <td><strong>{record.staff_name}</strong></td>
                          <td>{record.date}</td>
                          <td>{record.status.replace("_", " ")}</td>
                          <td>{record.check_in || "—"}</td>
                          <td>{record.check_out || "—"}</td>
                          <td>{record.notes || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </StateArea>
      </div>
    </section>
  );
}
