import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Search,
  User,
  FileText,
  Users,
  GraduationCap,
  Briefcase,
  CreditCard,
  Clock,
  BookOpen,
  ShieldAlert,
  Bus,
  Phone,
  Mail,
  Building2,
  AlertCircle,
} from "lucide-react";
import { StateArea, StatusBadge } from "./ui";
import { formatCurrency } from "./format";

const STUDENT_PROFILE_URL = "/api/reports/students/profile/";
const TEACHER_URL = "/api/reports/staff/teachers/";
const STAFF_URL = "/api/reports/staff/master/";

function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <span className="info-label">{label}</span>
      <span className="info-value">{value || "—"}</span>
    </div>
  );
}

function Section({ icon: Icon, title, children }) {
  return (
    <div className="detail-section">
      <h4 className="detail-section-title">
        {Icon && <Icon size={16} />} {title}
      </h4>
      <div className="detail-section-body">{children}</div>
    </div>
  );
}

function MiniTable({ headers, rows }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="empty-state" style={{ padding: 16 }}>
        <span>No data available.</span>
      </div>
    );
  }
  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h.toUpperCase()}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SearchPicker({ query, setQuery, options, getLabel, onSelect, placeholder }) {
  const filtered = useMemo(() => {
    const q = (query || "").trim().toLowerCase();
    if (!q) return options.slice(0, 50);
    return options.filter((o) =>
      getLabel(o).toLowerCase().includes(q)
    ).slice(0, 50);
  }, [query, options, getLabel]);

  return (
    <div className="single-search">
      <div className="search-fields">
        <Search size={18} className="search-icon" />
        <input
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search-input"
        />
      </div>
      <div className="search-results">
        {filtered.length === 0 && (
          <div className="empty-state" style={{ padding: 16 }}>
            <span>No matches found.</span>
          </div>
        )}
        {filtered.map((o, i) => (
          <button
            key={i}
            type="button"
            className="search-result-item"
            onClick={() => onSelect(o)}
          >
            {getLabel(o)}
          </button>
        ))}
      </div>
    </div>
  );
}

function StudentDetailReport() {
  const [query, setQuery] = useState("");
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [error, setError] = useState("");

  const loadStudents = useCallback((search) => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ page_size: "500" });
    if (search.trim()) params.append("search", search.trim());
    fetch(`/api/students/?${params.toString()}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject("Could not load students.")))
      .then((json) => setStudents(json.results || []))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadStudents("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelect = (student) => {
    setProfileLoading(true);
    setProfile(null);
    setError("");
    fetch(`${STUDENT_PROFILE_URL}?student=${student.id}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject("Could not load the profile.")))
      .then(setProfile)
      .catch((err) => setError(String(err)))
      .finally(() => setProfileLoading(false));
  };

  return (
    <div>
      <div className="filter-row">
        <div style={{ flex: 1, minWidth: 260 }}>
          <SearchPicker
            query={query}
            setQuery={setQuery}
            options={students}
            getLabel={(s) =>
              `${s.full_name || s.first_name || ""} — ${s.admission_number || s.roll_number || "No roll"}`
            }
            onSelect={handleSelect}
            placeholder="Search by student name or roll / admission number..."
          />
        </div>
      </div>

      {error && <div className="state-card error">{error}</div>}

      <StateArea
        loading={profileLoading}
        error={null}
        loadingText="Loading student profile..."
      >
        {profile && (
          <div className="detail-report">
            <div className="detail-hero">
              {profile.personal?.photo ? (
                <img src={profile.personal.photo} alt="" className="detail-photo" />
              ) : (
                <div className="detail-photo placeholder">
                  {(profile.personal?.full_name || "S").charAt(0)}
                </div>
              )}
              <div>
                <h3>{profile.personal?.full_name}</h3>
                <p>
                  {profile.personal?.admission_number} ·{" "}
                  {profile.personal?.primary_campus}
                </p>
                <StatusBadge status={profile.personal?.status} />
              </div>
            </div>

            <div className="detail-grid">
              <Section icon={User} title="Personal">
                <InfoRow label="Gender" value={profile.personal?.gender} />
                <InfoRow label="DOB" value={profile.personal?.date_of_birth} />
                <InfoRow label="Age" value={profile.personal?.age} />
                <InfoRow label="Phone" value={profile.personal?.phone} />
                <InfoRow label="Address" value={profile.personal?.address} />
                <InfoRow label="Admission Date" value={profile.personal?.admission_date} />
              </Section>

              <Section icon={GraduationCap} title="Academic">
                <InfoRow label="Class" value={profile.academic?.current_enrollment?.class} />
                <InfoRow label="Section" value={profile.academic?.current_enrollment?.section} />
                <InfoRow label="Campus" value={profile.academic?.current_enrollment?.campus} />
                <InfoRow label="Academic Year" value={profile.academic?.current_enrollment?.academic_year} />
                <InfoRow label="Roll No" value={profile.academic?.current_enrollment?.roll_number} />
              </Section>

              <Section icon={Clock} title="Attendance">
                <InfoRow label="Total Days" value={profile.attendance?.total_days} />
                <InfoRow label="Present" value={profile.attendance?.present} />
                <InfoRow label="Absent" value={profile.attendance?.absent} />
                <InfoRow label="Late" value={profile.attendance?.late} />
                <InfoRow label="Leave" value={profile.attendance?.leave} />
                <InfoRow label="Rate" value={profile.attendance?.attendance_rate != null ? `${profile.attendance.attendance_rate}%` : null} />
              </Section>

              <Section icon={FileText} title="Results">
                <InfoRow label="Exams" value={profile.results?.exams} />
                <InfoRow label="Passed" value={profile.results?.passed} />
                <InfoRow label="Failed" value={profile.results?.failed} />
                <InfoRow label="Pass Rate" value={profile.results?.pass_rate != null ? `${profile.results.pass_rate}%` : null} />
                <InfoRow label="Average" value={profile.results?.average_percentage} />
              </Section>

              <Section icon={CreditCard} title="Fees">
                <InfoRow label="Invoices" value={profile.fees?.total_invoices} />
                <InfoRow label="Invoiced" value={formatCurrency(profile.fees?.total_invoiced)} />
                <InfoRow label="Paid" value={formatCurrency(profile.fees?.total_paid)} />
                <InfoRow label="Outstanding" value={formatCurrency(profile.fees?.total_outstanding)} />
                <InfoRow label="Overdue" value={profile.fees?.overdue_count} />
              </Section>

              <Section icon={ShieldAlert} title="Discipline">
                <InfoRow label="Total Incidents" value={profile.discipline?.total_incidents} />
              </Section>

              <Section icon={Bus} title="Transport">
                <InfoRow label="Route" value={profile.transport?.route} />
                <InfoRow label="Vehicle" value={profile.transport?.vehicle} />
                <InfoRow label="Driver" value={profile.transport?.driver} />
              </Section>

              <Section icon={Building2} title="Guardians">
                {(profile.guardians || []).length === 0 && <span>No guardians.</span>}
                {(profile.guardians || []).map((g, i) => (
                  <div key={i} className="info-row">
                    <span className="info-label">{g.relationship} {g.is_primary ? "(Primary)" : ""}</span>
                    <span className="info-value">
                      {g.name} · <Phone size={12} /> {g.phone} · <Mail size={12} /> {g.email}
                    </span>
                  </div>
                ))}
              </Section>

              <Section icon={BookOpen} title="Enrollment History">
                <MiniTable
                  headers={["Year", "Campus", "Class", "Section", "Roll", "Status"]}
                  rows={(profile.academic?.all_enrollments || []).map((e) => [
                    e.academic_year,
                    e.campus,
                    e.class,
                    e.section,
                    e.roll_number,
                    e.status,
                  ])}
                />
              </Section>

              <Section icon={BookOpen} title="Library">
                <MiniTable
                  headers={["Book", "Issue", "Due", "Status", "Fine"]}
                  rows={(profile.library || []).map((l) => [
                    l.book,
                    l.issue_date,
                    l.due_date,
                    l.status,
                    formatCurrency(l.fine),
                  ])}
                />
              </Section>

              {profile.attendance && (
                <Section icon={AlertCircle} title="Recently Updated">
                  <p>Profile generated from live data.</p>
                </Section>
              )}
            </div>
          </div>
        )}

        {!profile && !profileLoading && (
          <div className="empty-state">
            <User size={42} />
            <h3>Search a student</h3>
            <p>Find a student by name or roll number to view their full report.</p>
          </div>
        )}
      </StateArea>
    </div>
  );
}

function PersonDetailReport({ url, title }) {
  const [query, setQuery] = useState("");
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    fetch(url, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject("Could not load the list.")))
      .then((json) => setPeople(json.results || []))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [url]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSelect = (p) => {
    setSelected(p);
    setQuery("");
  };

  const labelFor = (p) =>
    `${p.full_name || p.name || ""} — ${p.employee_number || p.user_email || "No emp no"}`;

  return (
    <div>
      <div className="filter-row">
        <div style={{ flex: 1, minWidth: 260 }}>
          <SearchPicker
            query={query}
            setQuery={setQuery}
            options={people}
            getLabel={labelFor}
            onSelect={handleSelect}
            placeholder={`Search ${title.toLowerCase()} by name or employee number...`}
          />
        </div>
      </div>

      {error && <div className="state-card error">{error}</div>}

      <StateArea loading={loading} error={null} loadingText="Loading list...">
        {selected ? (
          <div className="detail-report">
            <div className="detail-hero">
              {selected.photo ? (
                <img src={selected.photo} alt="" className="detail-photo" />
              ) : (
                <div className="detail-photo placeholder">
                  {(selected.full_name || selected.name || "P").charAt(0)}
                </div>
              )}
              <div>
                <h3>{selected.full_name || selected.name}</h3>
                <p>
                  {selected.employee_number ? `${selected.employee_number} · ` : ""}
                  {selected.designation || "Staff"}
                </p>
                <StatusBadge status={selected.status} />
              </div>
            </div>

            <div className="detail-grid">
              <Section icon={User} title="Personal">
                <InfoRow label="Gender" value={selected.gender} />
                <InfoRow label="DOB" value={selected.date_of_birth} />
                <InfoRow label="Phone" value={selected.phone || selected.user_phone} />
                <InfoRow label="Email" value={selected.email || selected.user_email} />
              </Section>

              <Section icon={Briefcase} title="Employment">
                <InfoRow label="Designation" value={selected.designation} />
                <InfoRow label="Department" value={selected.department} />
                <InfoRow label="Campus" value={selected.campus || selected.primary_campus} />
                <InfoRow label="Joining Date" value={selected.joining_date} />
              </Section>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <Users size={42} />
            <h3>Search a {title.toLowerCase()}</h3>
            <p>Find a {title.toLowerCase()} by name or employee number.</p>
          </div>
        )}
      </StateArea>
    </div>
  );
}

export function SingleStudentDetail() {
  return <StudentDetailReport />;
}

export function SingleTeacherDetail() {
  return (
    <PersonDetailReport
      url={TEACHER_URL}
      title="Teacher"
    />
  );
}

export function SingleStaffDetail() {
  return (
    <PersonDetailReport
      url={STAFF_URL}
      title="Staff member"
    />
  );
}
