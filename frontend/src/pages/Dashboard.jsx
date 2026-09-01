import { useState, useEffect } from "react";
import {
  Users,
  GraduationCap,
  Building2,
  BookOpen,
  LayoutDashboard,
  ClipboardCheck,
  CalendarDays,
  LifeBuoy,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  Legend,
} from "recharts";

const API_URL = "/api/dashboard/overview/";
const ENROLLMENT_REPORT_URL = "/api/reports/enrollment/";
const ATTENDANCE_REPORT_URL = "/api/reports/attendance/";
const COLLECTION_TREND_URL = "/api/reports/collection-trend/?months=6";

function useCountUp(value) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value === null || value === undefined) {
      setDisplay(0);
      return undefined;
    }

    const duration = 900;
    const start = performance.now();
    let frame;

    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(value * eased));

      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frame);
  }, [value]);

  return display;
}

function CountUp({ value }) {
  const display = useCountUp(value);

  return <strong>{display.toLocaleString()}</strong>;
}

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrollmentByCampus, setEnrollmentByCampus] = useState([]);
  const [attendanceRows, setAttendanceRows] = useState([]);
  const [collectionTrend, setCollectionTrend] = useState([]);
  const [schoolName, setSchoolName] = useState("");

  useEffect(() => {
    fetch("/api/schools/branding/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) =>
        setSchoolName(data?.school_name || data?.short_name || "")
      )
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch(API_URL, { credentials: "include" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load dashboard data.");
        }

        return response.json();
      })
      .then((data) => {
        setDashboard(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    // Charts — reports are optional; failures just hide the chart.
    fetch(ENROLLMENT_REPORT_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!data || !Array.isArray(data.classes)) return;

        const byCampus = {};

        for (const row of data.classes) {
          byCampus[row.campus] =
            (byCampus[row.campus] || 0) + (row.total || 0);
        }

        setEnrollmentByCampus(
          Object.entries(byCampus).map(([campus, students]) => ({
            campus,
            students,
          }))
        );
      })
      .catch(() => {});

    fetch(ATTENDANCE_REPORT_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!Array.isArray(data?.classes)) return;

        setAttendanceRows(
          data.classes.map((row) => ({
            name: `${row.class}`.slice(0, 14),
            rate: row.attendance_rate ?? 0,
          }))
        );
      })
      .catch(() => {});

    fetch(COLLECTION_TREND_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!Array.isArray(data?.months_data)) return;

        setCollectionTrend(
          data.months_data.map((row) => ({
            month: String(row.month).slice(2),
            invoiced: Number(row.invoiced),
            collected: Number(row.collected),
          }))
        );
      })
      .catch(() => {});
  }, []);

  const stats = dashboard
    ? [
        {
          label: "Total Students",
          value: dashboard.students?.total ?? 0,
          icon: Users,
        },
        {
          label: "Active Students",
          value: dashboard.students?.active ?? 0,
          icon: GraduationCap,
        },
        {
          label: "Teachers",
          value: dashboard.teachers?.total ?? 0,
          icon: Users,
        },
        {
          label: "Campuses",
          value: dashboard.campuses ?? 0,
          icon: Building2,
        },
        {
          label: "Classes",
          value: dashboard.classes ?? 0,
          icon: BookOpen,
        },
        {
          label: "Sections",
          value: dashboard.sections ?? 0,
          icon: LayoutDashboard,
        },
        {
          label: "Enrollments",
          value: dashboard.enrollments ?? 0,
          icon: ClipboardCheck,
        },
      ]
    : [];

  // ------------------------------------------------
  //  NEW: inline styles – keep the file self‑contained
  // ------------------------------------------------
  const style = `
:root {
  --primary: #2563eb;
  --secondary: #64748b;
  --accent: #10b981;
  --bg-page: #f8fafc;
  --card-bg: #ffffff;
  --text: #0f172a;
  --border: #e2e8f0;
}

/* ---- Hero banner ---- */
.hero-banner {
  background: linear-gradient(135deg, var(--primary), #1e40af);
  color: #fff;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}
.hero-banner h2 { margin: 0.5rem 0 0; }
.hero-banner p { margin: 0.5rem 0 0; font-size: 1rem; }

/* ---- Stat cards ---- */
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}
.stat-icon {
  width: 48px;
  height: 48px;
  margin-right: 1rem;
}
.stat-info span { font-size: 0.9rem; color: var(--secondary); }
.stat-info strong { font-size: 2rem; }

/* ---- Quick‑actions ---- */
.action-btn {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 0.6rem 1rem;
  border-radius: 6px;
  font-size: 0.95rem;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}
.action-btn:hover { background: #1e40af; }

/* ---- Recent activity list ---- */
.activity-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}
.activity-icon { width: 20px; height: 20px; margin-right: 0.5rem; }
.activity-text { flex: 1; }
.activity-time { font-size: 0.75rem; color: var(--secondary); margin-left: 0.5rem; }

/* ---- Responsive grid ---- */
@media (min-width: 768px) {
  .dashboard-grid { display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; }
  .dashboard-grid > * { grid-area: auto; }
}
`;

  return (
    <section className="content">
      {/* ---- Inline styles tag ---- */}
      <style>{style}</style>

      <div className="page-heading">
        <div>
          <p className="breadcrumb">Home / Dashboard</p>
          <h2>Dashboard Overview</h2>
          <p className="subtitle">
            Welcome back. Here's what's happening across your school.
          </p>
        </div>

        <div className="date-badge">
          <CalendarDays size={17} />
          <span>2026–2027</span>
        </div>
      </div>

      {/* ---- Hero banner with school name ---- */}
      <div className="hero-banner">
        <h2>{schoolName || "School Dashboard"}</h2>
        <p>Manage students, teachers, attendance, finance, report cards and timetables from one place.</p>
      </div>

      {/* ---- Loading / error states (unchanged) ---- */}
      {loading && (
        <div className="state-card">
          Loading dashboard data...
        </div>
      )}
      {error && (
        <div className="state-card error">
          <strong>Unable to load dashboard.</strong>
          <span>
            Make sure Django is running at 127.0.0.1:8000.
          </span>
          <code>{error}</code>
        </div>
      )}

      {/* ---- Main content – only show when loaded ---- */}
      {!loading && !error && dashboard && (
        <div className="dashboard-grid">
          {/* ---- Left column: stats & quick actions ---- */}
          <div style={{ flex: "0 0 300px" }}>
            <div className="stats-grid">
              {stats.map(({ label, value, icon: Icon }) => (
                <div
                  key={label}
                  className="stat-card"
                  style={{
                    borderLeft: `4px solid ${label === "Total Students" ? "#ef4442" : label === "Active Students" ? "#10b981" : label === "Teachers" ? "#3b82f6" : "#f59e0b"}`,
                  }}
                >
                  <div className="stat-icon">
                    <Icon size={21} />
                  </div>
                  <div className="stat-info">
                    <span>{label}</span>
                    <CountUp value={value} />
                  </div>
                </div>
              ))}
            </div>

            {/* ---- Quick‑actions bar ---- */}
            <div style={{ marginTop: 1.5rem }}>
              <button className="action-btn" onClick={() => window.location.href="/students/"}>
                <Users size={15} /> Students
              </button>
              <button className="action-btn" onClick={() => window.location.href="/admissions/"}>
                <GraduationCap size={15} /> Admissions
              </button>
              <button className="action-btn" onClick={() => window.location.href="/helpdesk/"}>
                <LifeBuoy size={15} /> Helpdesk
              </button>
              <button className="action-btn" onClick={() => window.location.href="/reports/"}>
                <ClipboardCheck size={15} /> Reports
              </button>
            </div>
          </div>

          {/* ---- Right column: charts & panels (unchanged) ---- */}
          <div style={{ flex: "1 1 0" }}>
            {/* ---- Existing chart grid (unchanged) ---- */}
            {(enrollmentByCampus.length > 0 ||
              attendanceRows.length > 0 ||
              collectionTrend.length > 0) && (
              <div className="dashboard-grid" style={{ marginTop: 1rem }}>
                {/* Fee Collection Trend (unchanged) */}
                {collectionTrend.length > 0 && (
                  <div className="panel">
                    <div className="panel-header">
                      <div>
                        <h3>Fee Collection Trend</h3>
                        <p>Invoiced vs collected — last 6 months</p>
                      </div>
                    </div>
                    <div style={{ width: "100%", height: 240 }}>
                      <ResponsiveContainer>
                        <AreaChart data={collectionTrend} margin={{ left: -10, right: 10, top: 5 }}>
                          <defs>
                            <linearGradient id="inv" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
                              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="col" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.35} />
                              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                          <XAxis dataKey="month" fontSize={11} />
                          <YAxis fontSize={11} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
                          <Tooltip formatter={(v) => Number(v).toLocaleString()} />
                          <Legend />
                          <Area type="monotone" dataKey="invoiced" stroke="#6366f1" fill="url(#inv)" strokeWidth={2} />
                          <Area type="monotone" dataKey="collected" stroke="#22c55e" fill="url(#col)" strokeWidth={2} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Enrollment by Campus (unchanged) */}
                {enrollmentByCampus.length > 0 && (
                  <div className="panel">
                    <div className="panel-header">
                      <div>
                        <h3>Enrollment by Campus</h3>
                        <p>Active students per campus</p>
                      </div>
                    </div>
                    <div style={{ width: "100%", height: 240 }}>
                      <ResponsiveContainer>
                        <BarChart data={enrollmentByCampus} margin={{ left: -20, right: 10, top: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                          <XAxis dataKey="campus" fontSize={11} />
                          <YAxis fontSize={11} allowDecimals={false} />
                          <Tooltip />
                          <Bar dataKey="students" fill="#6366f1" radius={[6, 6, 0, 0]} maxBarSize={48} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Attendance Rate by Class (unchanged) */}
                {attendanceRows.length > 0 && (
                  <div className="panel">
                    <div className="panel-header">
                      <div>
                        <h3>Attendance Rate by Class</h3>
                        <p>Present + late as share of all records</p>
                      </div>
                    </div>
                    <div style={{ width: "100%", height: 240 }}>
                      <ResponsiveContainer>
                        <BarChart data={attendanceRows} layout="vertical" margin={{ left: 10, right: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                          <XAxis type="number" domain={[0, 100]} fontSize={11} unit="%" />
                          <YAxis type="category" dataKey="name" fontSize={11} width={90} />
                          <Tooltip formatter={(v) => `${v}%`} />
                          <Bar dataKey="rate" fill="#22c55e" radius={[0, 6, 6, 0]} maxBarSize={18} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ---- Welcome / overview panel (unchanged) ---- */}
            <div className="panel welcome-panel">
              <div className="welcome-icon">
                <GraduationCap size={30} />
              </div>

              <h3>{schoolName || "Welcome"}</h3>

              <p>
                Manage students, teachers, attendance, examinations,
                finance, report cards and timetables from one place.
              </p>

              <div className="campus-count">
                <Building2 size={17} />
                <strong>{dashboard.campuses ?? 0}</strong>
                <span>campuses connected</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default Dashboard;