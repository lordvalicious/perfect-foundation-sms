import { useEffect, useState } from "react";
import { BriefcaseBusiness, FileText, Search, Star, Users } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, StatusBadge } from "./ui";

const EMPLOYEES_URL = "/api/hr/employees/";

export default function HRPage() {
  const [employees, setEmployees] = useState([]);
  const [selected, setSelected] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [workload, setWorkload] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadEmployees = () => {
    setLoading(true);
    fetch(`${EMPLOYEES_URL}?search=${encodeURIComponent(search)}`, { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("Unable to load employees.");
        return response.json();
      })
      .then((data) => {
        const rows = Array.isArray(data) ? data : data.results || [];
        setEmployees(rows);
        if (!selected && rows.length) setSelected(rows[0]);
        setError("");
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadEmployees();  
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selected) return;
    const loadRelated = async () => {
      const endpoints = [
        `${EMPLOYEES_URL}${selected.id}/contracts/`,
        `${EMPLOYEES_URL}${selected.id}/workload/`,
        `${EMPLOYEES_URL}${selected.id}/reviews/`,
        "/api/hr/employment-events/",
      ];
      try {
        const responses = await Promise.all(endpoints.map((url) => fetch(url, { credentials: "include" })));
        if (responses.some((response) => !response.ok)) throw new Error("Unable to load employee details.");
        const data = await Promise.all(responses.map((response) => response.json()));
        setContracts(Array.isArray(data[0]) ? data[0] : data[0].results || []);
        setWorkload(Array.isArray(data[1]) ? data[1] : data[1].results || []);
        setReviews(Array.isArray(data[2]) ? data[2] : data[2].results || []);
        const eventRows = Array.isArray(data[3]) ? data[3] : data[3].results || [];
        setEvents(eventRows.filter((event) => event.employee === selected.id));
      } catch (requestError) {
        setError(requestError.message);
      }
    };
    loadRelated();
  }, [selected]);

  const visibleEmployees = employees.filter((employee) =>
    `${employee.full_name} ${employee.employee_number}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <section className="content">
      <PageHeader
        crumb="Home / HR"
        title="Human Resources"
        subtitle="Manage employee records, contracts, workload, reviews, and employment history."
        hero
        stats={[
          {
            label: "Employees",
            value: employees.length,
            icon: <Users size={18} />,
            sub: "on the directory",
          },
          {
            label: "Contracts",
            value: contracts.length,
            icon: <FileText size={18} />,
            sub: "in the selected record",
          },
          {
            label: "Workload",
            value: `${workload.reduce((total, item) => total + Number(item.hours_per_week || 0), 0)}h`,
            icon: <BriefcaseBusiness size={18} />,
            sub: "weekly hours",
          },
          {
            label: "Reviews",
            value: reviews.length,
            icon: <Star size={18} />,
            sub: "performance entries",
          },
        ]}
      />
      <div className="panel students-filters">
        <form onSubmit={(event) => { event.preventDefault(); loadEmployees(); }}>
          <div className="filter-row">
            <div className="filter-search"><Search size={18} /><input placeholder="Search employee number or name..." value={search} onChange={(event) => setSearch(event.target.value)} /></div>
            <button className="primary-button" type="submit">Search</button>
          </div>
        </form>
      </div>
      <div className="dashboard-grid">
        <div className="panel">
          <PanelHeader title="Employee directory" subtitle="employees" count={visibleEmployees.length} />
          <StateArea loading={loading} error={error} onRetry={loadEmployees}>
            <div className="overview-list">
              {visibleEmployees.map((employee) => (
                <button key={employee.id} type="button" className={`overview-list-row ${selected?.id === employee.id ? "active" : ""}`} onClick={() => setSelected(employee)}>
                  <span><strong>{employee.full_name}</strong><small>{employee.employee_number} · {employee.designation}</small></span>
                  <StatusBadge status={employee.status} />
                </button>
              ))}
            </div>
          </StateArea>
        </div>
        <div className="panel">
          {!selected ? <div className="state-card">Select an employee to view HR records.</div> : (
            <>
              <PanelHeader title={selected.full_name} subtitle={`${selected.employee_number} · ${selected.profile_type}`} />
              <div className="stats-grid">
                <div className="stat-card"><div className="stat-icon"><FileText size={20} /></div><div className="stat-info"><span>Contracts</span><strong>{contracts.length}</strong></div></div>
                <div className="stat-card"><div className="stat-icon"><BriefcaseBusiness size={20} /></div><div className="stat-info"><span>Workload hours</span><strong>{workload.reduce((total, item) => total + Number(item.hours_per_week || 0), 0)}</strong></div></div>
                <div className="stat-card"><div className="stat-icon"><Star size={20} /></div><div className="stat-info"><span>Reviews</span><strong>{reviews.length}</strong></div></div>
                <div className="stat-card"><div className="stat-icon"><Users size={20} /></div><div className="stat-info"><span>History events</span><strong>{events.length}</strong></div></div>
              </div>
              <div className="overview-list">
                {contracts.slice(0, 4).map((contract) => <div key={contract.id}><span>{contract.contract_number} · {contract.contract_type}</span><strong>{contract.salary} · {contract.status}</strong></div>)}
                {workload.slice(0, 4).map((item) => <div key={item.id}><span>{item.title}</span><strong>{item.hours_per_week} hrs/week</strong></div>)}
                {reviews.slice(0, 4).map((review) => <div key={review.id}><span>{review.period}</span><strong>{review.rating}/5 · {review.status}</strong></div>)}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
