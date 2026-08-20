import { useState, useEffect } from "react";
import {
  Users,
  GraduationCap,
  Building2,
  BookOpen,
  LayoutDashboard,
  ClipboardCheck,
  CalendarDays,
} from "lucide-react";

const API_URL = "/api/dashboard/overview/";

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

  return (
    <section className="content">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Home / Dashboard</p>

          <h2>Dashboard Overview</h2>

          <p className="subtitle">
            Welcome back. Here's what's happening at Perfect Foundation
            School.
          </p>
        </div>

        <div className="date-badge">
          <CalendarDays size={17} />
          <span>2026–2027</span>
        </div>
      </div>

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

      {!loading && !error && dashboard && (
        <>
          <div className="stats-grid">
            {stats.map(({ label, value, icon: Icon }) => (
              <div className="stat-card" key={label}>
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

          <div className="dashboard-grid">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>School Overview</h3>
                  <p>Current academic year statistics</p>
                </div>
              </div>

              <div className="overview-list">
                <div>
                  <span>Active students</span>
                  <strong>
                    {dashboard.students?.active ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Active teachers</span>
                  <strong>
                    {dashboard.teachers?.active ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Campuses</span>
                  <strong>{dashboard.campuses ?? 0}</strong>
                </div>

                <div>
                  <span>Classes</span>
                  <strong>{dashboard.classes ?? 0}</strong>
                </div>

                <div>
                  <span>Sections</span>
                  <strong>{dashboard.sections ?? 0}</strong>
                </div>

                <div>
                  <span>Enrollments</span>
                  <strong>{dashboard.enrollments ?? 0}</strong>
                </div>
              </div>
            </div>

            <div className="panel welcome-panel">
              <div className="welcome-icon">
                <GraduationCap size={30} />
              </div>

              <h3>Perfect Foundation School</h3>

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
        </>
      )}
    </section>
  );
}

export default Dashboard;
