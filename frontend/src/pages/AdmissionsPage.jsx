import { useEffect, useState } from "react";
import { Check, FilePlus2, Search, X } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, StatusBadge } from "./ui";

const API_URL = "/api/students/admissions/";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop().split(";").shift() : null;
}

function authHeaders() {
  const csrfToken = getCookie("csrftoken");
  return csrfToken ? { "X-CSRFToken": csrfToken } : {};
}

export default function AdmissionsPage() {
  const [applications, setApplications] = useState([]);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState(null);

  const loadApplications = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    fetch(`${API_URL}?${params}`, { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load admission applications.");
        return response.json();
      })
      .then((data) => {
        setApplications(Array.isArray(data) ? data : data.results || []);
        setError("");
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadApplications(); // eslint-disable-line react-hooks/set-state-in-effect
  }, [status]); // eslint-disable-line react-hooks/exhaustive-deps

  const review = (application, action) => {
    setBusyId(application.id);
    setNotice("");
    fetch(`${API_URL}${application.id}/review/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ action }),
    })
      .then((response) => response.json().then((data) => ({ response, data })))
      .then(({ response, data }) => {
        if (!response.ok) throw new Error(data.detail || "Could not update application.");
        setNotice("Application status updated.");
        loadApplications();
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setBusyId(null));
  };

  const accept = (application) => {
    const admissionNumber = window.prompt(
      "Admission number",
      application.application_number,
    );
    if (!admissionNumber) return;
    setBusyId(application.id);
    setNotice("");
    fetch(`${API_URL}${application.id}/accept/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ admission_number: admissionNumber }),
    })
      .then((response) => response.json().then((data) => ({ response, data })))
      .then(({ response, data }) => {
        if (!response.ok) throw new Error(data.detail || "Could not accept application.");
        setNotice(`Application accepted for ${data.student?.full_name || "the student"}.`);
        loadApplications();
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setBusyId(null));
  };

  const visibleApplications = applications.filter((application) =>
    application.applicant_name.toLowerCase().includes(search.toLowerCase())
    || application.application_number.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <section className="content">
      <PageHeader
        crumb="Home / People / Admissions"
        title="Admissions"
        subtitle="Review applicants and convert accepted applications into enrolled students."
      />

      <div className="panel students-filters">
        <div className="filter-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              placeholder="Search applicants or application number..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under review</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
          </select>
          <button type="button" className="secondary-button" onClick={loadApplications}>
            Refresh
          </button>
        </div>
      </div>

      {notice && <div className="state-card">{notice}</div>}
      <div className="panel">
        <PanelHeader
          title="Application queue"
          subtitle="applications"
          count={visibleApplications.length}
          action={<FilePlus2 size={20} />}
        />
        <StateArea loading={loading} error={error} onRetry={loadApplications}>
          {visibleApplications.length === 0 ? (
            <div className="state-card">No admission applications found.</div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>APPLICANT</th>
                    <th>APPLICATION</th>
                    <th>CAMPUS</th>
                    <th>CLASS</th>
                    <th>GUARDIAN</th>
                    <th>STATUS</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleApplications.map((application) => (
                    <tr key={application.id}>
                      <td><strong>{application.applicant_name}</strong></td>
                      <td>{application.application_number}</td>
                      <td>{application.campus_name || "-"}</td>
                      <td>{application.class_name || "-"}</td>
                      <td>{application.guardian || "Not linked"}</td>
                      <td><StatusBadge status={application.status} label={application.status_display} /></td>
                      <td>
                        <div className="table-actions">
                          {(application.status === "submitted") && (
                            <button className="secondary-button" disabled={busyId === application.id} onClick={() => review(application, "under_review")}>
                              Review
                            </button>
                          )}
                          {(application.status === "submitted" || application.status === "under_review") && (
                            <>
                              <button className="primary-button" disabled={busyId === application.id} onClick={() => accept(application)} title="Accept application">
                                <Check size={15} /> Accept
                              </button>
                              <button className="danger-button" disabled={busyId === application.id} onClick={() => review(application, "reject")} title="Reject application">
                                <X size={15} /> Reject
                              </button>
                            </>
                          )}
                        </div>
                      </td>
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
