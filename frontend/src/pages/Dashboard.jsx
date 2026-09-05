import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useSchool } from "../schoolContext";
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

function Dashboard() {
  const navigate = useNavigate();
  const { currentSchool } = useSchool();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrollmentByCampus, setEnrollmentByCampus] = useState([]);
  const [attendanceRows, setAttendanceRows] = useState([]);
  const [collectionTrend, setCollectionTrend] = useState([]);
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
      .catch(() => {});
  }, []);

  useEffect(() => {
    const clock = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(clock);
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

  const style = `
/* ---- Dashboard hero ---- */
.dash-hero {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  padding: 2.2rem 2.4rem;
  margin-bottom: 1.6rem;
  color: #fff;
  background: linear-gradient(120deg, #1e1b4b 0%, #312e81 45%, #4338ca 100%);
  box-shadow: 0 18px 40px -18px rgba(67, 56, 202, 0.55);
}
.dash-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.14) 1px, transparent 1px);
  background-size: 22px 22px;
  opacity: 0.45;
  -webkit-mask-image: radial-gradient(ellipse at 30% 40%, #000 0%, transparent 70%);
  mask-image: radial-gradient(ellipse at 30% 40%, #000 0%, transparent 70%);
}
.dash-hero-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
  pointer-events: none;
}
.dash-hero-top {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
}
.dash-hello {
  font-size: 0.82rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #c7d2fe;
  margin: 0;
}
.dash-hero h2 {
  font-size: 2.1rem;
  font-weight: 800;
  margin: 0.35rem 0 0;
  letter-spacing: -0.02em;
  line-height: 1.15;
}
.dash-hero-sub {
  color: #c7d2fe;
  margin: 0.7rem 0 0;
  max-width: 48ch;
  font-size: 0.95rem;
}
.dash-clock {
  position: relative;
  text-align: right;
  min-width: 160px;
}
.dash-time {
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
.dash-date {
  font-size: 0.88rem;
  color: #c7d2fe;
  margin-top: 0.2rem;
}
.dash-term {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.7rem;
  padding: 0.3rem 0.8rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 0.78rem;
  color: #e0e7ff;
}
.dash-active-school {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.55rem;
  padding: 0.32rem 0.85rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.28);
  font-size: 0.8rem;
  font-weight: 600;
  color: #e0e7ff;
}
.dash-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1.5rem;
  position: relative;
}
.dash-action {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.52rem 0.95rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.15s ease, background 0.2s ease;
}
.dash-action:hover {
  background: rgba(255, 255, 255, 0.24);
  transform: translateY(-2px);
}

/* ---- Stat cards ---- */
.dash-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
  gap: 1rem;
  margin-bottom: 1.6rem;
}
.dash-stat {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.1rem 1.2rem;
  box-shadow: 0 4px 14px -8px rgba(15, 23, 42, 0.18);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  animation: dash-in 0.35s ease both;
}
.dash-stat:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 28px -12px rgba(15, 23, 42, 0.28);
}
.dash-stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dash-stat-chip {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
}
.dash-stat-value {
  font-size: 1.95rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-top: 0.75rem;
  color: #0f172a;
  line-height: 1;
}
.dash-stat-label {
  font-size: 0.86rem;
  font-weight: 600;
  color: #334155;
  margin-top: 0.35rem;
}
.dash-stat-sub {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 0.15rem;
}

/* ---- Bento grid ---- */
.bento {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.2rem;
  margin-bottom: 1rem;
}
@media (min-width: 1000px) {
  .bento {
    grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  }
  .bento-wide {
    grid-column: 1 / -1;
  }
}
.dash-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.3rem 1.4rem;
  box-shadow: 0 4px 14px -8px rgba(15, 23, 42, 0.12);
  animation: dash-in 0.4s ease both;
}
.dash-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
  flex-wrap: wrap;
}
.dash-card-header h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 700;
  color: #0f172a;
}
.dash-card-header p {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: #64748b;
}
.dash-chip-row {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}
.dash-chip {
  border-radius: 999px;
  padding: 0.32rem 0.85rem;
  font-size: 0.78rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-variant-numeric: tabular-nums;
}
.dash-chip-rate { color: #047857; background: #ecfdf5; }
.dash-chip-sum { color: #1d4ed8; background: #eff6ff; }
.dash-chip-muted { color: #64748b; background: #f1f5f9; }

/* Custom tooltip */
.dash-tooltip {
  background: #0f172a;
  color: #fff;
  border-radius: 10px;
  padding: 0.6rem 0.85rem;
  font-size: 0.8rem;
  box-shadow: 0 10px 24px -10px rgba(0, 0, 0, 0.4);
}
.dash-tooltip-label {
  color: #cbd5e1;
  margin-bottom: 0.35rem;
  font-weight: 600;
}
.dash-tooltip-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.1rem 0;
}
.dash-tooltip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
}
.dash-tooltip-name {
  color: #cbd5e1;
  flex: 1;
}
.dash-tooltip-row strong {
  font-variant-numeric: tabular-nums;
}

/* Campus ranking bars */
.dash-camp-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.7rem;
  margin: 0.6rem 0;
}
.dash-camp-name {
  font-size: 0.88rem;
  color: #334155;
  min-width: 88px;
  max-width: 132px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dash-camp-track {
  height: 8px;
  border-radius: 999px;
  background: #eef2ff;
  overflow: hidden;
}
.dash-camp-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width 0.7s ease;
}
.dash-camp-val {
  font-size: 0.8rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

/* Spotlight row */
.dash-spotlight {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.dash-spotlight-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #14b8a6, #0d9488);
  flex: none;
}
.dash-spotlight-metrics {
  display: flex;
  gap: 1.6rem;
  margin-left: auto;
  text-align: center;
}
.dash-metric b {
  display: block;
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
}
.dash-metric span {
  font-size: 0.74rem;
  color: #64748b;
}

@keyframes dash-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}
`;

  return (
    <section className="content">
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
                    <h3 style={{ margin: 0, fontWeight: 700, color: "#0f172a" }}>
                      {activeSchoolName || "Your school"}
                    </h3>
                    <p style={{ margin: "0.15rem 0 0", fontSize: "0.8rem", color: "#64748b" }}>
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
          </div>
        </>
      )}
    </section>
  );
}

export default Dashboard;