import { useCallback, useEffect, useState } from "react";
import {
  ClipboardList,
  Coins,
  FileWarning,
  Layers,
  Receipt,
  Users,
  Wallet,
} from "lucide-react";
import { apiFetch, jsonHeaders } from "../api";
import { useLang } from "../i18n";
import { PageHeader, PanelHeader, StateArea, EmptyState, StatusBadge } from "./ui";
import { formatCurrency, formatDate } from "./format";

const ACADEMIC_YEARS_URL = "/api/schools/academic-years/";
const CAMPUSES_URL = "/api/schools/campuses/";
const CLASSES_URL = "/api/schools/classes/";
const SECTIONS_URL = "/api/schools/sections/";
const FEE_ASSIGNMENT_PREVIEW_URL = "/api/finance/fee-assignment/preview/";
const OUTSTANDING_URL = "/api/finance/outstanding/";
const FEE_OVERRIDES_URL = "/api/finance/fee-overrides/";

const TABS = [
  { key: "config", label: "Fee Configuration", icon: Layers },
  { key: "outstanding", label: "Outstanding Fees", icon: FileWarning },
];

export default function StudentFeesPage() {
  const { t } = useLang();
  const [tab, setTab] = useState("config");

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Finance / Student Fees"
        title="Student Fees"
        subtitle="Configure and review student fee assignments and outstanding balances."
      />

      <div className="tabs" style={{ marginBottom: "1.2rem" }}>
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            className={`tab-button ${tab === key ? "active" : ""}`}
            onClick={() => setTab(key)}
          >
            <Icon size={15} />
            {t(label)}
          </button>
        ))}
      </div>

      {tab === "config" && <FeeConfiguration />}
      {tab === "outstanding" && <OutstandingFees />}
    </section>
  );
}

function FeeConfiguration() {
  const [academicYears, setAcademicYears] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [classes, setClasses] = useState([]);
  const [allSections, setAllSections] = useState([]);
  const [overrides, setOverrides] = useState([]);

  const [academicYear, setAcademicYear] = useState("");
  const [campus, setCampus] = useState("");
  const [classObj, setClassObj] = useState("");
  const [section, setSection] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadLookups = useCallback(() => {
    fetch(ACADEMIC_YEARS_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setAcademicYears(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
    fetch(CAMPUSES_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setCampuses(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
    fetch(CLASSES_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setClasses(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
    fetch(SECTIONS_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setAllSections(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
    fetch(FEE_OVERRIDES_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setOverrides(Array.isArray(data) ? data : data.results || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadLookups();
  }, [loadLookups]);

  const classSections = classObj
    ? allSections.filter((s) => String(s.class_obj) === String(classObj))
    : [];

  const handleClassChange = (value) => {
    setClassObj(value);
    setSection("");
  };

  const handlePreview = async () => {
    setError("");
    if (!academicYear || !campus || !classObj) {
      setError("Academic year, campus and class are required.");
      return;
    }
    setLoading(true);
    try {
      const body = { academic_year: Number(academicYear), campus: Number(campus), class_obj: Number(classObj) };
      if (section) body.section = Number(section);
      const data = await apiFetch(
        FEE_ASSIGNMENT_PREVIEW_URL,
        { method: "POST", headers: jsonHeaders(), body: JSON.stringify(body) },
        "Could not preview fee assignments."
      );
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const hasFiltersSelected = academicYear && campus && classObj;

  return (
    <div>
      <div className="panel students-filters">
        <div className="filter-row">
          <select value={academicYear} onChange={(e) => setAcademicYear(e.target.value)}>
            <option value="">Academic Year</option>
            {academicYears.map((y) => (
              <option key={y.id} value={y.id}>{y.name}</option>
            ))}
          </select>
          <select value={campus} onChange={(e) => setCampus(e.target.value)}>
            <option value="">Campus</option>
            {campuses.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select value={classObj} onChange={(e) => handleClassChange(e.target.value)}>
            <option value="">Class</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select value={section} onChange={(e) => setSection(e.target.value)}>
            <option value="">All Sections</option>
            {classSections.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button className="primary-button" onClick={handlePreview} disabled={loading}>
            {loading ? "Loading..." : "Preview Fees"}
          </button>
        </div>
      </div>

      {error && (
        <div className="state-card error" style={{ marginTop: "0.8rem" }}>
          <strong>Unable to preview.</strong>
          <code>{error}</code>
        </div>
      )}

      {!hasFiltersSelected && !result && !error && (
        <EmptyState
          icon={ClipboardList}
          title="Select a class to preview fees"
          message="Choose an academic year, campus and class, then press Preview Fees."
        />
      )}

      {result && !error && (
        <div style={{ marginTop: "1.2rem" }}>
          <div className="stats-grid" style={{ marginBottom: "1rem" }}>
            <div className="stat-card">
              <div className="stat-icon"><Users size={20} /></div>
              <div>
                <h3>{result.total_students || 0}</h3>
                <p>Students</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon"><Wallet size={20} /></div>
              <div>
                <h3>{formatCurrency(result.total_amount)}</h3>
                <p>Total Payable</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon"><Layers size={20} /></div>
              <div>
                <h3>{result.class}</h3>
                <p>{result.campus}</p>
              </div>
            </div>
          </div>

          {result.preview && result.preview.length > 0 ? (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>STUDENT</th>
                    <th>ADM. NO.</th>
                    <th>SECTION</th>
                    <th>FEE TYPE</th>
                    <th>DETAIL</th>
                    <th>FINAL PAYABLE</th>
                  </tr>
                </thead>
                <tbody>
                  {result.preview.map((row) => (
                    <tr key={row.enrollment_id || row.student_id}>
                      <td><strong>{row.student_name}</strong></td>
                      <td>{row.admission_number}</td>
                      <td>{row.section || "—"}</td>
                      <td>
                        {row.warning ? (
                          <span className="status-badge warn">No structure</span>
                        ) : row.has_override ? (
                          <span className="status-badge warn">Student Fee</span>
                        ) : (
                          <span className="status-badge active">Standard Fee</span>
                        )}
                      </td>
                      <td>
                        {row.items && row.items.length > 0 ? (
                          <div>
                            {row.items.map((item, idx) => (
                              <div key={idx} style={{ fontSize: "0.85rem", padding: "0.1rem 0" }}>
                                <span>
                                  {item.category} — {formatCurrency(item.amount)}
                                </span>
                                {item.overridden && (
                                  <span className="status-badge warn" style={{ marginLeft: "0.4rem" }}>
                                    adjusted
                                  </span>
                                )}
                                {item.frequency && (
                                  <span style={{ color: "#666", marginLeft: "0.4rem", fontSize: "0.75rem" }}>
                                    {item.frequency} × {item.installments || 1}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        <strong>{formatCurrency(row.total_amount)}</strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              icon={Users}
              title="No enrollments found"
              message="No active enrollments match this class selection."
            />
          )}
        </div>
      )}

      {overrides.length > 0 && (
        <div style={{ marginTop: "1.4rem" }}>
          <PanelHeader title="Student Fee Overrides" count={overrides.length} subtitle="records" />
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>STUDENT</th>
                  <th>ADM. NO.</th>
                  <th>FEE STRUCTURE</th>
                  <th>AMOUNT</th>
                  <th>REASON</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {overrides.map((o) => (
                  <tr key={o.id}>
                    <td><strong>{o.student_name}</strong></td>
                    <td>{o.admission_number}</td>
                    <td>{o.fee_structure_name}</td>
                    <td>{formatCurrency(o.amount)}</td>
                    <td>{o.reason || "—"}</td>
                    <td><StatusBadge status={o.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function OutstandingFees() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch(OUTSTANDING_URL, {}, "Could not load outstanding fees.");
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

  const rows = data?.rows || [];
  const summary = data?.summary || {};

  return (
    <StateArea loading={loading} error={error} onRetry={load}>
      <div className="stats-grid" style={{ marginBottom: "1rem" }}>
        <div className="stat-card">
          <div className="stat-icon"><Coins size={20} /></div>
          <div>
            <h3>{formatCurrency(summary.total_outstanding)}</h3>
            <p>Total Outstanding</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Users size={20} /></div>
          <div>
            <h3>{summary.total_students || 0}</h3>
            <p>Students</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Receipt size={20} /></div>
          <div>
            <h3>{summary.total_invoices || 0}</h3>
            <p>Invoices</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><FileWarning size={20} /></div>
          <div>
            <h3>{summary.overdue_invoices || 0}</h3>
            <p>Overdue</p>
          </div>
        </div>
      </div>

      {rows.length > 0 ? (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>STUDENT</th>
                <th>INVOICE</th>
                <th>CLASS</th>
                <th>DUE DATE</th>
                <th>TOTAL</th>
                <th>PAID</th>
                <th>BALANCE</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.invoice_id}>
                  <td>
                    <strong>{row.student_name}</strong>
                    <div style={{ fontSize: "0.75rem", color: "#666" }}>{row.admission_number}</div>
                  </td>
                  <td>{row.invoice_number}</td>
                  <td>{`${row.class}${row.section ? " · " + row.section : ""}`}</td>
                  <td>{formatDate(row.due_date)}</td>
                  <td>{formatCurrency(row.total_amount)}</td>
                  <td>{formatCurrency(row.paid_amount)}</td>
                  <td>
                    <strong style={{ color: row.is_overdue ? "#c0392b" : undefined }}>
                      {formatCurrency(row.balance)}
                    </strong>
                  </td>
                  <td>
                    {row.is_overdue ? (
                      <span className="status-badge inactive">{row.days_overdue}d overdue</span>
                    ) : (
                      <StatusBadge status={row.status} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          icon={Wallet}
          title="No outstanding fees"
          message="All invoices are settled for the active school."
        />
      )}
    </StateArea>
  );
}
