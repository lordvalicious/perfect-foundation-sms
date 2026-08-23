import { useCallback, useEffect, useState } from "react";
import { Check, FilePlus2, Search, X } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, StatusBadge } from "./ui";

const API_URL = "/api/students/admissions/";
const CAMPUSES_URL = "/api/schools/campuses/";
const ACADEMIC_YEARS_URL = "/api/schools/academic-years/";
const CLASSES_URL = "/api/schools/classes/";
const SECTIONS_URL = "/api/schools/sections/";
const GUARDIANS_URL = "/api/students/guardians/";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop().split(";").shift() : null;
}

function authHeaders() {
  const csrfToken = getCookie("csrftoken");
  return csrfToken ? { "X-CSRFToken": csrfToken } : {};
}

function generateApplicationNumber() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, "");
  const rand = String(Math.floor(Math.random() * 9000) + 1000);
  return `APP-${date}-${rand}`;
}

const EMPTY_FORM = {
  first_name: "",
  middle_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "male",
  phone: "",
  address: "",
  campus: "",
  academic_year: "",
  class_obj: "",
  section: "",
  guardian: "",
};

export default function AdmissionsPage() {
  const [applications, setApplications] = useState([]);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const [campuses, setCampuses] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [classes, setClasses] = useState([]);
  const [sections, setSections] = useState([]);
  const [guardians, setGuardians] = useState([]);

  const loadApplications = useCallback(() => {
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
  }, [status]);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  useEffect(() => {
    fetch(CAMPUSES_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setCampuses(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});

    fetch(ACADEMIC_YEARS_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setAcademicYears(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});

    fetch(GUARDIANS_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setGuardians(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!form.campus) {
      setClasses([]);
      setSections([]);
      return;
    }
    fetch(`${CLASSES_URL}?campus=${form.campus}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setClasses(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
    setForm((prev) => ({ ...prev, class_obj: "", section: "" }));
    setSections([]);
  }, [form.campus]);

  useEffect(() => {
    if (!form.class_obj) {
      setSections([]);
      return;
    }
    fetch(`${SECTIONS_URL}?class=${form.class_obj}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setSections(Array.isArray(d) ? d : d.results || []))
      .catch(() => {});
    setForm((prev) => ({ ...prev, section: "" }));
  }, [form.class_obj]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setNotice("");
    setError("");
    setShowForm(true);
  };

  const handleCreate = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    const body = {
      application_number: generateApplicationNumber(),
      first_name: form.first_name,
      middle_name: form.middle_name,
      last_name: form.last_name,
      date_of_birth: form.date_of_birth || null,
      gender: form.gender,
      phone: form.phone,
      address: form.address,
      campus: Number(form.campus),
      academic_year: Number(form.academic_year),
      class_obj: Number(form.class_obj),
      section: form.section ? Number(form.section) : null,
      guardian: form.guardian ? Number(form.guardian) : null,
      status: "submitted",
    };

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        const message = Object.entries(data)
          .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
          .join(" | ");
        throw new Error(message || "Could not create application.");
      }

      setShowForm(false);
      setForm(EMPTY_FORM);
      setNotice("Admission application created successfully.");
      loadApplications();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

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
          <button type="button" className="primary-button" onClick={openCreate}>
            <FilePlus2 size={15} />
            New Application
          </button>
        </div>
      </div>

      <div className="panel">
        <PanelHeader
          title="Application queue"
          subtitle="applications"
          count={visibleApplications.length}
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

      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowForm(false);
          }}
        >
          <div className="teacher-modal event-modal">
            <div className="modal-header">
              <div>
                <h3>New Admission Application</h3>
                <p>Fill in the applicant details below.</p>
              </div>
              <button
                className="modal-close"
                onClick={() => setShowForm(false)}
                disabled={saving}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-section">
                <h4>Applicant Information</h4>
                <div className="form-grid">
                  <label>
                    First Name *
                    <input
                      name="first_name"
                      value={form.first_name}
                      onChange={handleChange}
                      placeholder="First name"
                      required
                    />
                  </label>

                  <label>
                    Middle Name
                    <input
                      name="middle_name"
                      value={form.middle_name}
                      onChange={handleChange}
                      placeholder="Middle name"
                    />
                  </label>

                  <label>
                    Last Name
                    <input
                      name="last_name"
                      value={form.last_name}
                      onChange={handleChange}
                      placeholder="Last name"
                    />
                  </label>

                  <label>
                    Date of Birth
                    <input
                      type="date"
                      name="date_of_birth"
                      value={form.date_of_birth}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Gender *
                    <select name="gender" value={form.gender} onChange={handleChange} required>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </label>

                  <label>
                    Phone
                    <input
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="03XX-XXXXXXX"
                    />
                  </label>

                  <label className="form-span">
                    Address
                    <textarea
                      name="address"
                      value={form.address}
                      onChange={handleChange}
                      placeholder="Full address"
                      rows="2"
                    />
                  </label>
                </div>
              </div>

              <div className="form-section">
                <h4>Academic Details</h4>
                <div className="form-grid">
                  <label>
                    Campus *
                    <select name="campus" value={form.campus} onChange={handleChange} required>
                      <option value="">Select campus</option>
                      {campuses.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Academic Year *
                    <select name="academic_year" value={form.academic_year} onChange={handleChange} required>
                      <option value="">Select year</option>
                      {academicYears.map((y) => (
                        <option key={y.id} value={y.id}>{y.name}</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Class *
                    <select name="class_obj" value={form.class_obj} onChange={handleChange} required disabled={!form.campus}>
                      <option value="">Select class</option>
                      {classes.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Section
                    <select name="section" value={form.section} onChange={handleChange} disabled={!form.class_obj}>
                      <option value="">Select section</option>
                      {sections.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Guardian
                    <select name="guardian" value={form.guardian} onChange={handleChange}>
                      <option value="">Select guardian</option>
                      {guardians.map((g) => (
                        <option key={g.id} value={g.id}>{g.name} ({g.relationship})</option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowForm(false)}
                  disabled={saving}
                >
                  <X size={15} />
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  <Check size={15} />
                  {saving ? "Submitting..." : "Submit Application"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
