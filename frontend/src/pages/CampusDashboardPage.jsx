import { useCallback, useEffect, useState } from "react";
import { Building2, DollarSign, GraduationCap } from "lucide-react";
import { apiFetch } from "../api";
import { PageHeader, StateArea } from "./ui";
import { formatCurrency } from "./format";

const CAMPUSES_URL = "/api/schools/campuses/";
const FINANCE_BREAKDOWN_URL = "/api/dashboard/finance/breakdown/";

export default function CampusDashboardPage() {
  const [campuses, setCampuses] = useState([]);
  const [finance, setFinance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [campusData, financeData] = await Promise.all([
        apiFetch(CAMPUSES_URL, {}, "Failed to load campuses."),
        fetch(FINANCE_BREAKDOWN_URL, { credentials: "include" })
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null),
      ]);

      setCampuses(Array.isArray(campusData) ? campusData : campusData.results || []);
      setFinance(financeData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalStudents = campuses.reduce((sum, c) => sum + Number(c.student_count || 0), 0);
  const totalCollected = finance?.by_campus?.reduce((sum, c) => sum + Number(c.collected || 0), 0) || 0;
  const totalOutstanding = finance?.by_campus?.reduce((sum, c) => sum + Number(c.outstanding || 0), 0) || 0;

  const campusFinanceMap = {};
  if (finance?.by_campus) {
    finance.by_campus.forEach((cf) => {
      campusFinanceMap[cf.campus] = cf;
    });
  }

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Campus Dashboard"
        title="Multi-Campus Dashboard"
        subtitle="Compare performance and metrics across all campuses."
      />

      <StateArea loading={loading} error={error} onRetry={fetchData}>
        {/* Overall stats */}
        <div className="stats-grid" style={{ marginBottom: 24 }}>
          <div className="stat-card">
            <div className="stat-icon"><Building2 size={21} /></div>
            <div>
              <h3>{campuses.length}</h3>
              <p>Total Campuses</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><GraduationCap size={21} /></div>
            <div>
              <h3>{totalStudents}</h3>
              <p>Total Students</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><DollarSign size={21} /></div>
            <div>
              <h3>{formatCurrency(totalCollected)}</h3>
              <p>Total Collected</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ color: totalOutstanding > 0 ? "var(--danger)" : undefined }}>
              <DollarSign size={21} />
            </div>
            <div>
              <h3 style={{ color: totalOutstanding > 0 ? "var(--danger)" : undefined }}>{formatCurrency(totalOutstanding)}</h3>
              <p>Total Outstanding</p>
            </div>
          </div>
        </div>

        {/* Campus cards */}
        <div className="panel">
          <div className="teacher-list-header">
            <h3>Campus Comparison</h3>
          </div>

          <div className="campus-grid">
            {campuses.map((campus) => {
              const cf = campusFinanceMap[campus.name] || {};
              const campusPercent = totalStudents > 0
                ? Math.round((campus.student_count || 0) / totalStudents * 100)
                : 0;

              return (
                <div key={campus.id} className="campus-card">
                  <div className="campus-card-head">
                    <span className="campus-card-icon"><Building2 size={18} /></span>
                    <div>
                      <strong>{campus.name}</strong>
                      <div className="campus-card-city">{campus.city || "No city"}</div>
                    </div>
                    <span className="campus-card-share">{campusPercent}% of students</span>
                  </div>

                  {/* Student bar */}
                  <div className="campus-bar-wrap">
                    <div className="campus-bar-label">
                      <span><GraduationCap size={12} /> Students</span>
                      <strong>{campus.student_count || 0}</strong>
                    </div>
                    <div className="campus-bar">
                      <div className="campus-bar-fill" style={{ width: `${campusPercent}%` }} />
                    </div>
                  </div>

                  <div className="campus-metrics">
                    <div className="campus-metric">
                      <span>Classes</span>
                      <strong>{campus.class_count || 0}</strong>
                    </div>
                    <div className="campus-metric">
                      <span>Sections</span>
                      <strong>{campus.section_count || 0}</strong>
                    </div>
                    {cf.billed !== undefined && (
                      <div className="campus-metric">
                        <span>Billed</span>
                        <strong>{formatCurrency(cf.billed)}</strong>
                      </div>
                    )}
                    {cf.collected !== undefined && (
                      <div className="campus-metric">
                        <span>Collected</span>
                        <strong>{formatCurrency(cf.collected)}</strong>
                      </div>
                    )}
                    {cf.outstanding !== undefined && cf.outstanding > 0 && (
                      <div className="campus-metric danger wide">
                        <span>Outstanding</span>
                        <strong>{formatCurrency(cf.outstanding)}</strong>
                      </div>
                    )}
                  </div>

                  <div className="campus-card-status">Status: {campus.status}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Finance by campus table */}
        {finance?.by_campus?.length > 0 && (
          <div className="panel">
            <div className="teacher-list-header">
              <h3>Finance Comparison by Campus</h3>
            </div>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>CAMPUS</th>
                    <th>BILLED</th>
                    <th>COLLECTED</th>
                    <th>OUTSTANDING</th>
                    <th>COLLECTION RATE</th>
                  </tr>
                </thead>
                <tbody>
                  {finance.by_campus.map((row) => {
                    const rate = row.billed > 0 ? Math.round((row.collected / row.billed) * 100) : 0;
                    return (
                      <tr key={row.campus}>
                        <td><strong>{row.campus}</strong></td>
                        <td>{formatCurrency(row.billed)}</td>
                        <td>{formatCurrency(row.collected)}</td>
                        <td className={row.outstanding > 0 ? "cell-danger" : undefined}>
                          {formatCurrency(row.outstanding)}
                        </td>
                        <td>
                          <div className="rate-bar">
                            <div className="rate-track">
                              <div
                                className="rate-bar-fill"
                                style={{
                                  width: `${Math.min(100, rate)}%`,
                                  background: rate >= 80 ? "var(--success)" : rate >= 50 ? "var(--warn)" : "var(--danger)",
                                }}
                              />
                            </div>
                            <span>{rate}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </StateArea>
    </section>
  );
}
