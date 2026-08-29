import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  DollarSign,
  GraduationCap,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiFetch } from "../api";
import { PageHeader, StateArea } from "./ui";
import { formatCurrency, getMonthLabel } from "./format";

const EXECUTIVE_URL = "/api/dashboard/executive/";

function KpiCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="kpi-card">
      <div className="stat-icon">
        <Icon size={20} />
      </div>
      <div>
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        {sub && <div className="stat-label">{sub}</div>}
      </div>
    </div>
  );
}

function AlertCard({ alert }) {
  const tone =
    alert.severity === "high" ? "error" : alert.severity === "medium" ? "warning" : "";

  return (
    <div className={`alert-card ${tone}`}>
      <strong>{alert.title}</strong>
      <span>{alert.message}</span>
      {alert.value && <em>{alert.value}</em>}
    </div>
  );
}

export default function ExecutiveDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch(
        EXECUTIVE_URL,
        {},
        "Failed to load the executive dashboard."
      );
      setData(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const financeTrend = useMemo(
    () =>
      (data?.finance?.monthly || []).map((row) => ({
        month: getMonthLabel(row.month),
        Billed: Number(row.billed),
        Collected: Number(row.collected),
      })),
    [data]
  );

  const attendanceTrend = useMemo(
    () =>
      (data?.attendance?.trend || []).map((row) => ({
        month: getMonthLabel(row.month),
        rate: row.rate,
      })),
    [data]
  );

  const byExam = useMemo(
    () =>
      (data?.academic?.by_exam || []).map((row) => ({
        name: row.name,
        passRate: row.pass_rate,
      })),
    [data]
  );

  const s = data?.summary;

  return (
    <div className="page">
      <PageHeader
        crumb="Home / Executive Dashboard"
        title="Executive Dashboard"
        subtitle="School-wide snapshot across all campuses"
        action={
          data?.academic_year && (
            <span className="status-badge">{data.academic_year.name}</span>
          )
        }
      />

      <StateArea loading={loading} error={error} onRetry={load}>
        {data && (
          <>
            <div className="dashboard-grid four">
              <KpiCard
                icon={Users}
                label="Active Students"
                value={(s?.students?.active || 0).toLocaleString()}
                sub={`${s?.students?.male || 0} boys / ${s?.students?.female || 0} girls`}
              />
              <KpiCard
                icon={Building2}
                label="Campuses"
                value={(s?.campuses || 0).toLocaleString()}
                sub={`${s?.enrollments || 0} enrollments this year`}
              />
              <KpiCard
                icon={GraduationCap}
                label="Teachers"
                value={(s?.teachers?.active || 0).toLocaleString()}
                sub="Active teaching staff"
              />
              <KpiCard
                icon={DollarSign}
                label="Collection Rate"
                value={`${data?.finance?.collection_rate || 0}%`}
                sub={formatCurrency(data?.finance?.outstanding)}
              />
            </div>

            <div className="dashboard-grid three">
              <div className="panel">
                <div className="panel-header">
                  <h3 className="panel-title">Finance Trend</h3>
                  <p className="stat-label">Billed vs collected, last 6 months</p>
                </div>
                <div className="panel-body">
                  <ResponsiveContainer width="100%" height={240}>
                    <AreaChart data={financeTrend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area type="monotone" dataKey="Billed" stroke="#475569" fill="#94a3b8" />
                      <Area type="monotone" dataKey="Collected" stroke="#16a34a" fill="#86efac" />
                    </AreaChart>
                  </ResponsiveContainer>

                  <div className="dashboard-grid three">
                    <KpiCard
                      icon={DollarSign}
                      label="Billed"
                      value={formatCurrency(data?.finance?.total_billed)}
                    />
                    <KpiCard
                      icon={TrendingUp}
                      label="Collected"
                      value={formatCurrency(data?.finance?.collected)}
                    />
                    <KpiCard
                      icon={AlertTriangle}
                      label="Outstanding"
                      value={formatCurrency(data?.finance?.outstanding)}
                    />
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h3 className="panel-title">Attendance</h3>
                  <p className="stat-label">Monthly rate, last 6 months</p>
                </div>
                <div className="panel-body">
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={attendanceTrend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="rate" name="Attendance %" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>

                  <div className="dashboard-grid two">
                    <KpiCard
                      icon={Users}
                      label="Today"
                      value={`${data?.attendance?.today?.rate || 0}%`}
                      sub={`${data?.attendance?.today?.present || 0} present today`}
                    />
                    <KpiCard
                      icon={Users}
                      label="This Month"
                      value={`${data?.attendance?.month?.rate || 0}%`}
                      sub={`${data?.attendance?.month?.total || 0} records`}
                    />
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h3 className="panel-title">Exam Performance</h3>
                  <p className="stat-label">Pass rate by recent exam</p>
                </div>
                <div className="panel-body">
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={byExam}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="passRate" name="Pass rate %" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>

                  <div className="kpi-card">
                    <div className="stat-icon">
                      <BookOpen size={20} />
                    </div>
                    <div>
                      <div className="kpi-label">Latest Exam</div>
                      <div className="kpi-value">
                        {data?.academic?.latest_exam
                          ? `${data.academic.latest_exam.pass_rate}% pass`
                          : "No results"}
                      </div>
                      <div className="stat-label">
                        {data?.academic?.latest_exam?.name || "Publish a report card"}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="dashboard-grid two">
              <div className="panel">
                <div className="panel-header">
                  <h3 className="panel-title">Campus Comparison</h3>
                  <p className="stat-label">Active enrollments, finance, attendance</p>
                </div>
                <div className="panel-body">
                  <div className="table-card">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Campus</th>
                          <th>Students</th>
                          <th>Collected</th>
                          <th>Outstanding</th>
                          <th>Att.</th>
                          <th>Pass</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(data?.campuses || []).map((c) => (
                          <tr key={c.id}>
                            <td>{c.name}</td>
                            <td>{c.students}</td>
                            <td>{formatCurrency(c.collected)}</td>
                            <td>{formatCurrency(c.outstanding)}</td>
                            <td>{c.attendance_rate_month}%</td>
                            <td>{c.pass_rate === null ? "—" : `${c.pass_rate}%`}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h3 className="panel-title">Class Strength</h3>
                  <p className="stat-label">Enrollments by class</p>
                </div>
                <div className="panel-body">
                  {(data?.academic?.class_strength || []).map((row) => (
                    <div
                      key={row.class}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "6px 0",
                        borderBottom: "1px solid #e2e8f0",
                      }}
                    >
                      <span>{row.class}</span>
                      <strong>{row.students}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <h3 className="panel-title">Alerts</h3>
                <p className="stat-label">Things that need attention</p>
              </div>
              <div className="panel-body">
                <div className="dashboard-grid two">
                  {(data?.alerts || []).map((a, i) => (
                    <AlertCard key={i} alert={a} />
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </StateArea>
    </div>
  );
}