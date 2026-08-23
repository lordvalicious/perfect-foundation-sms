import { useCallback, useEffect, useState } from "react";
import { Building2, DollarSign, GraduationCap, Users } from "lucide-react";
import { apiFetch } from "../api";
import { PageHeader, StateArea } from "./ui";
import { formatCurrency, formatDate } from "./format";

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
  const totalClasses = campuses.reduce((sum, c) => sum + Number(c.class_count || 0), 0);
  const totalSections = campuses.reduce((sum, c) => sum + Number(c.section_count || 0), 0);
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
            <div className="stat-icon" style={{ color: totalOutstanding > 0 ? "#e74c3c" : undefined }}>
              <DollarSign size={21} />
            </div>
            <div>
              <h3 style={{ color: totalOutstanding > 0 ? "#e74c3c" : undefined }}>{formatCurrency(totalOutstanding)}</h3>
              <p>Total Outstanding</p>
            </div>
          </div>
        </div>

        {/* Campus cards */}
        <div className="panel">
          <div className="teacher-list-header">
            <h3>Campus Comparison</h3>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16, padding: 16 }}>
            {campuses.map((campus) => {
              const cf = campusFinanceMap[campus.name] || {};
              const campusPercent = totalStudents > 0
                ? Math.round((campus.student_count || 0) / totalStudents * 100)
                : 0;

              return (
                <div key={campus.id} style={{
                  border: "1px solid #e0e0e0",
                  borderRadius: 8,
                  padding: 16,
                  background: "#fff",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                    <Building2 size={18} style={{ color: "#1a73e8" }} />
                    <div>
                      <strong>{campus.name}</strong>
                      <div style={{ fontSize: 12, color: "#666" }}>{campus.city || "No city"}</div>
                    </div>
                    <span style={{ marginLeft: "auto", fontSize: 12, opacity: 0.6 }}>
                      {campusPercent}% of students
                    </span>
                  </div>

                  {/* Student bar */}
                  <div style={{ marginBottom: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                      <span><GraduationCap size={12} /> Students</span>
                      <strong>{campus.student_count || 0}</strong>
                    </div>
                    <div style={{ background: "#e0e0e0", borderRadius: 4, height: 6 }}>
                      <div style={{
                        background: "#1a73e8",
                        height: "100%",
                        borderRadius: 4,
                        width: `${campusPercent}%`,
                        transition: "width 0.5s",
                      }} />
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 13, marginTop: 12 }}>
                    <div style={{ background: "#f5f5f5", padding: "6px 8px", borderRadius: 4 }}>
                      <div style={{ fontSize: 11, color: "#666" }}>Classes</div>
                      <strong>{campus.class_count || 0}</strong>
                    </div>
                    <div style={{ background: "#f5f5f5", padding: "6px 8px", borderRadius: 4 }}>
                      <div style={{ fontSize: 11, color: "#666" }}>Sections</div>
                      <strong>{campus.section_count || 0}</strong>
                    </div>
                    {cf.billed !== undefined && (
                      <div style={{ background: "#f5f5f5", padding: "6px 8px", borderRadius: 4 }}>
                        <div style={{ fontSize: 11, color: "#666" }}>Billed</div>
                        <strong>{formatCurrency(cf.billed)}</strong>
                      </div>
                    )}
                    {cf.collected !== undefined && (
                      <div style={{ background: "#f5f5f5", padding: "6px 8px", borderRadius: 4 }}>
                        <div style={{ fontSize: 11, color: "#666" }}>Collected</div>
                        <strong>{formatCurrency(cf.collected)}</strong>
                      </div>
                    )}
                    {cf.outstanding !== undefined && cf.outstanding > 0 && (
                      <div style={{ background: "#fde8e8", padding: "6px 8px", borderRadius: 4, gridColumn: "1 / -1" }}>
                        <div style={{ fontSize: 11, color: "#c0392b" }}>Outstanding</div>
                        <strong style={{ color: "#c0392b" }}>{formatCurrency(cf.outstanding)}</strong>
                      </div>
                    )}
                  </div>

                  <div style={{ marginTop: 8, fontSize: 11, color: "#999" }}>
                    Status: {campus.status}
                  </div>
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
                        <td style={{ color: row.outstanding > 0 ? "#c0392b" : undefined }}>
                          {formatCurrency(row.outstanding)}
                        </td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <div style={{ background: "#e0e0e0", borderRadius: 4, height: 6, width: 60 }}>
                              <div style={{
                                background: rate >= 80 ? "#27ae60" : rate >= 50 ? "#f39c12" : "#e74c3c",
                                height: "100%",
                                borderRadius: 4,
                                width: `${rate}%`,
                              }} />
                            </div>
                            {rate}%
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
