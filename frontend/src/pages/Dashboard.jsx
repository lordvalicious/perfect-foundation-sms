import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useSchool } from "../schoolContext";
import { useAuth } from "../auth";
import { EmptyState } from "../components/EmptyState";
import { RetryButton } from "../components/RetryButton";
import { SkeletonBlock } from "./ui";
import {
  Users,
  GraduationCap,
  Building2,
  BookOpen,
  LayoutDashboard,
  ClipboardCheck,
  CalendarDays,
  Wallet,
  FileText,
  BarChart3,
  Sparkles,
  TrendingUp,
  Clock,
  Megaphone,
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

function ChartTooltip({ active, payload, label, fmt }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="dash-tooltip">
      <div className="dash-tooltip-label">{label}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className="dash-tooltip-row">
          <span
            className="dash-tooltip-dot"
            style={{ background: p.color || p.fill || "#6366f1" }}
          />
          <span className="dash-tooltip-name">{p.name}</span>
          <strong>{fmt ? fmt(p.value) : Number(p.value).toLocaleString()}</strong>
        </div>
      ))}
    </div>
  );
}

function greetingForHour(hour) {
  if (hour < 5) return "Working late";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function RecentActivity({ items }) {
  return (
    <div className="dash-card">
      <div className="dash-card-header">
        <div>
          <h3>Recent Activity</h3>
          <p>Latest announcements in your scope</p>
        </div>
      </div>

      {items.length === 0 ? (
        <p style={{ margin: "1rem 0", fontSize: 13, color: "var(--text-muted)" }}>
          No recent announcements.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {items.map((item) => (
            <li
              key={item.id}
              style={{
                display: "flex",
                gap: 10,
                padding: "10px 0",
                borderBottom: "1px solid var(--border, #e2e8f0)",
              }}
            >
              <Megaphone size={16} style={{ flexShrink: 0, marginTop: 2, color: "var(--text-muted)" }} />
              <div style={{ minWidth: 0 }}>
                <strong style={{ display: "block", fontSize: 13.5 }}>
                  {item.title || "Untitled"}
                </strong>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  {item.published_at || item.created_at || ""}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ManagerDashboard() {
  const navigate = useNavigate();
  const { currentSchool } = useSchool();
  const { user, hasRole } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboardError, setDashboardError] = useState("");
  const [attendanceRows, setAttendanceRows] = useState([]);
  const [enrollmentByCampus, setEnrollmentByCampus] = useState([]);
  const [collectionTrend, setCollectionTrend] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [schoolName, setSchoolName] = useState("");
  const [now, setNow] = useState(() => new Date());

  // The authoritative school context (active institution) is applied on mount
  // and the whole route remounts on school switch, so this value is always the
  // correct school for the data below — never a stale previous school. It works
  // for every role: Super Admin gets the selected school, normal users their own.
  const activeSchoolName = currentSchool?.name || schoolName;

  useEffect(() => {
    // Fallback label for contexts where the active institution is unavailable.
    fetch("/api/schools/branding/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) =>
        setSchoolName(data?.school_name || data?.short_name || "")
      )
      .catch((err) => { setDashboardError(err.message || "Failed to load school branding."); setLoading(false); }); // Fallback label for contexts where the active institution is unavailable.    fetch("/api/schools/branding/", { credentials: "include" })
  }, []);

  useEffect(() => {
    const clock = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(clock);
  }, []);

  useEffect(() => {
    fetch(API_URL, { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) {
          const text = await response.text();

          const detail = (() => {
            try {
              return JSON.parse(text || "{}").detail;
            } catch {
              return null;
            }
          })();

          throw new Error(
            (typeof detail === "string" && detail.trim()) ||
              "Failed to load dashboard data."
          );
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
      .catch((err) => { setDashboardError(err.message || "Failed to load enrollment data."); }); // Enrollment data fetch

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
      .catch((err) => { setDashboardError(err.message || "Failed to load attendance data."); }); // Attendance data fetch

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
      .catch((err) => { setDashboardError(err.message || "Failed to load collection trend data."); }); // Collection trend data fetch

    // Recent activity — institution/person-scoped announcements (top 5).
    fetch("/api/communication/announcements/", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) =>
        setAnnouncements(
          (Array.isArray(json) ? json : json.results || []).slice(0, 5)
        )
      )
      .catch(() => {});
  }, []);

  const stats = dashboard
    ? [
        {
          label: "Total Students",
          value: dashboard.students?.total ?? 0,
          icon: Users,
          color: "#6366f1",
          chip: "linear-gradient(135deg,#6366f1,#8b5cf6)",
          sub: `${dashboard.students?.active ?? 0} currently active`,
        },
        {
          label: "Teachers",
          value: dashboard.teachers?.total ?? 0,
          icon: GraduationCap,
          color: "#10b981",
          chip: "linear-gradient(135deg,#10b981,#0ea5e9)",
          sub: `${dashboard.teachers?.active ?? 0} active on staff`,
        },
        {
          label: "Campuses",
          value: dashboard.campuses ?? 0,
          icon: Building2,
          color: "#0ea5e9",
          chip: "linear-gradient(135deg,#0ea5e9,#6366f1)",
          sub: "Connected & reporting",
        },
        {
          label: "Classes",
          value: dashboard.classes ?? 0,
          icon: BookOpen,
          color: "#f59e0b",
          chip: "linear-gradient(135deg,#f59e0b,#f97316)",
          sub: "Across all campuses",
        },
        {
          label: "Sections",
          value: dashboard.sections ?? 0,
          icon: LayoutDashboard,
          color: "#8b5cf6",
          chip: "linear-gradient(135deg,#8b5cf6,#ec4899)",
          sub: "Academic groups",
        },
        {
          label: "Enrollments",
          value: dashboard.enrollments ?? 0,
          icon: ClipboardCheck,
          color: "#14b8a6",
          chip: "linear-gradient(135deg,#14b8a6,#10b981)",
          sub: "Active enrollments",
        },
      ]
    : [];

  const collectionTotals = useMemo(() => {
    const invoiced = collectionTrend.reduce(
      (sum, row) => sum + (row.invoiced || 0),
      0
    );
    const collected = collectionTrend.reduce(
      (sum, row) => sum + (row.collected || 0),
      0
    );
    const rate = invoiced > 0 ? Math.round((collected / invoiced) * 100) : 0;

    return { invoiced, collected, rate };
  }, [collectionTrend]);

  const avgAttendance = useMemo(() => {
    if (!attendanceRows.length) return null;

    return Math.round(
      attendanceRows.reduce((sum, row) => sum + (row.rate || 0), 0) /
        attendanceRows.length
    );
  }, [attendanceRows]);

  const maxEnrollment = useMemo(
    () => Math.max(...enrollmentByCampus.map((e) => e.students || 0), 1),
    [enrollmentByCampus]
  );

  const timeString = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const dateString = now.toLocaleDateString([], {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
  const greeting = greetingForHour(now.getHours());

  const quickActions = [
    { label: "Students", path: "/students", icon: Users },
    { label: "Admissions", path: "/admissions", icon: GraduationCap },
    { label: "Finance", path: "/finance", icon: Wallet },
    { label: "Attendance", path: "/attendance", icon: ClipboardCheck },
    { label: "Exams", path: "/exams", icon: FileText },
    { label: "Reports", path: "/reports", icon: BarChart3 },
  ];


  return (
    <section className="content">
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

      {/* ---- Hero ---- */}
      <div className="dash-hero">
        <div
          className="dash-hero-blob"
          style={{
            width: "220px",
            height: "220px",
            background: "#22d3ee",
            top: "-80px",
            right: "10%",
          }}
        />
        <div
          className="dash-hero-blob"
          style={{
            width: "180px",
            height: "180px",
            background: "#a855f7",
            bottom: "-90px",
            right: "28%",
          }}
        />

        <div className="dash-hero-top">
          <div>
            <p className="dash-hello">
              <Sparkles size={13} style={{ verticalAlign: "-2px", marginRight: "0.3rem" }} />
              {greeting}
            </p>
            <h2>{activeSchoolName || "School Dashboard"}</h2>
            {currentSchool && (
              <div className="dash-active-school">
                <Building2 size={14} />
                Active School: {currentSchool.name}
              </div>
            )}
            <p className="dash-hero-sub">
              Here's the live picture of your school — students, staff, campus
              pulse and finances at a glance.
            </p>
          </div>

          <div className="dash-clock">
            <div className="dash-time">
              <Clock size={18} style={{ verticalAlign: "-3px", marginRight: "0.4rem", opacity: "0.85" }} />
              {timeString}
            </div>
            <div className="dash-date">{dateString}</div>
            <div className="dash-term">Academic year 2026–2027</div>
          </div>
        </div>

        <div className="dash-actions">
          {quickActions.map(({ label, path, icon: Icon }) => (
            <button
              key={path}
              className="dash-action"
              onClick={() => navigate(path)}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ---- Loading / error states ---- */}
      {loading && !error && <SkeletonBlock rows={5} text="Loading dashboard data..." />}
      {error && (
        <div className="state-card error">
          <strong>Unable to load dashboard.</strong>
          <span>{error}</span>
        </div>
      )}

      {/* ---- Main content ---- */}
      {!loading && !error && dashboard && (
        <>
          {/* ---- Stat cards ---- */}
          <div className="dash-stats">
            {stats.map(({ label, value, icon: Icon, chip, sub }, i) => (
              <div
                key={label}
                className="dash-stat"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="dash-stat-top">
                  <div className="dash-stat-chip" style={{ background: chip }}>
                    <Icon size={20} />
                  </div>
                </div>
                <div className="dash-stat-value">
                  <CountUp value={value} />
                </div>
                <div className="dash-stat-label">{label}</div>
                <div className="dash-stat-sub">{sub}</div>
              </div>
            ))}
          </div>

          {/* ---- Bento content ---- */}
          <div className="bento">
            {/* Fee collection (wide) */}
            {collectionTrend.length > 0 && (
              <div className="dash-card bento-wide">
                <div className="dash-card-header">
                  <div>
                    <h3>Fee Collection Trend</h3>
                    <p>Invoiced vs collected — last 6 months</p>
                  </div>
                  <div className="dash-chip-row">
                    <span className="dash-chip dash-chip-sum">
                      <Wallet size={13} />
                      {Number(collectionTotals.invoiced).toLocaleString()} invoiced
                    </span>
                    <span className="dash-chip dash-chip-rate">
                      <TrendingUp size={13} />
                      {Number(collectionTotals.collected).toLocaleString()} collected
                    </span>
                    <span className="dash-chip dash-chip-muted">
                      {collectionTotals.rate}% collection rate
                    </span>
                  </div>
                </div>
                <div style={{ width: "100%", height: 250 }}>
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
                      <YAxis
                        fontSize={11}
                        tickFormatter={(v) => `${Math.round(v / 1000)}k`}
                      />
                      <Tooltip
                        content={
                          <ChartTooltip fmt={(v) => Number(v).toLocaleString()} />
                        }
                      />
                      <Legend />
                      <Area type="monotone" name="Invoiced" dataKey="invoiced" stroke="#6366f1" fill="url(#inv)" strokeWidth={2} />
                      <Area type="monotone" name="Collected" dataKey="collected" stroke="#22c55e" fill="url(#col)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Enrollment by Campus (left) */}
            {enrollmentByCampus.length > 0 && (
              <div className="dash-card">
                <div className="dash-card-header">
                  <div>
                    <h3>Enrollment by Campus</h3>
                    <p>Active students per campus</p>
                  </div>
                </div>
                <div style={{ width: "100%", height: 250 }}>
                  <ResponsiveContainer>
                    <BarChart data={enrollmentByCampus} margin={{ left: -20, right: 10, top: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                      <XAxis dataKey="campus" fontSize={11} />
                      <YAxis fontSize={11} allowDecimals={false} />
                      <Tooltip
                        content={
                          <ChartTooltip fmt={(v) => Number(v).toLocaleString()} />
                        }
                      />
                      <Bar
                        dataKey="students"
                        name="Students"
                        fill="#6366f1"
                        radius={[6, 6, 0, 0]}
                        maxBarSize={48}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div style={{ marginTop: "1rem" }}>
                  {enrollmentByCampus.map((campus) => (
                    <div key={campus.campus} className="dash-camp-row">
                      <span className="dash-camp-name">{campus.campus}</span>
                      <div className="dash-camp-track">
                        <div
                          className="dash-camp-fill"
                          style={{
                            width: `${Math.round(
                              ((campus.students || 0) / maxEnrollment) * 100
                            )}%`,
                          }}
                        />
                      </div>
                      <span className="dash-camp-val">
                        {Number(campus.students || 0).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Attendance (right) */}
            {attendanceRows.length > 0 && (
              <div className="dash-card">
                <div className="dash-card-header">
                  <div>
                    <h3>Attendance Rate by Class</h3>
                    <p>Present + late as share of all records</p>
                  </div>
                  {avgAttendance !== null && (
                    <span className="dash-chip dash-chip-rate">
                      <TrendingUp size={13} />
                      {avgAttendance}% avg
                    </span>
                  )}
                </div>
                <div style={{ width: "100%", height: 250 }}>
                  <ResponsiveContainer>
                    <BarChart
                      data={attendanceRows}
                      layout="vertical"
                      margin={{ left: 10, right: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                      <XAxis type="number" domain={[0, 100]} fontSize={11} unit="%" />
                      <YAxis type="category" dataKey="name" fontSize={11} width={90} />
                      <Tooltip
                        content={
                          <ChartTooltip fmt={(v) => `${Number(v).toFixed(0)}%`} />
                        }
                      />
                      <Bar
                        dataKey="rate"
                        name="Attendance"
                        fill="#22c55e"
                        radius={[0, 6, 6, 0]}
                        maxBarSize={18}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Spotlight (wide) */}
            {dashboard && (
              <div className="dash-card bento-wide">
                <div className="dash-spotlight">
                  <div className="dash-spotlight-icon">
                    <GraduationCap size={24} />
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontWeight: 700, color: "var(--text)" }}>
                      {activeSchoolName || "Your school"}
                    </h3>
                    <p style={{ margin: "0.15rem 0 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                      Manage students, teachers, attendance, examinations, finance,
                      report cards and timetables from one place.
                    </p>
                  </div>
                  <div className="dash-spotlight-metrics">
                    <div className="dash-metric">
                      <b>{dashboard.campuses ?? 0}</b>
                      <span>Campuses</span>
                    </div>
                    <div className="dash-metric">
                      <b>{dashboard.enrollments ?? 0}</b>
                      <span>Enrollments</span>
                    </div>
                    <div className="dash-metric">
                      <b>{dashboard.sections ?? 0}</b>
                      <span>Sections</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <RecentActivity items={announcements} />
          </div>
        </>
      )}
    </section>
  );
}

export default ManagerDashboard;
