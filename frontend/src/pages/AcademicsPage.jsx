import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  CalendarDays,
  GraduationCap,
  School,
  Search,
} from "lucide-react";
import { apiFetch, jsonHeaders } from "../api";
import { EmptyState, PageHeader, PanelHeader, StateArea, StatusBadge } from "./ui";
import { formatDate } from "./format";

const YEARS_URL = "/api/schools/academic-years/";
const TERMS_URL = "/api/schools/terms/";
const CAMPUSES_URL = "/api/schools/campuses/";
const CLASSES_URL = "/api/schools/classes/";
const SECTIONS_URL = "/api/schools/sections/";
const SUBJECTS_URL = "/api/schools/subjects/";
const OFFERINGS_URL = "/api/schools/offerings/";
const EVENTS_URL = "/api/events/";
const PROMOTIONS_URL = "/api/students/promotions/";
const STUDENTS_URL = "/api/students/";

function toList(data) {
  return Array.isArray(data) ? data : data.results || [];
}

const EMPTY_PROMO = {
  from_academic_year: "",
  to_academic_year: "",
  campus: "",
  reason: "",
  effective_date: "",
};

export default function AcademicsPage() {
  const [tab, setTab] = useState("calendar");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [years, setYears] = useState([]);
  const [terms, setTerms] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [classes, setClasses] = useState([]);
  const [sections, setSections] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const [events, setEvents] = useState([]);
  const [students, setStudents] = useState([]);

  const [structureCampus, setStructureCampus] = useState("");
  const [structureClass, setStructureClass] = useState("");

  const [promoForm, setPromoForm] = useState(EMPTY_PROMO);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [studentSearch, setStudentSearch] = useState("");
  const [promoting, setPromoting] = useState(false);
  const [promoResult, setPromoResult] = useState("");

  const loadAll = useCallback(() => {
    setLoading(true);
    const toListOrEmpty = (response) => (response.ok ? response.json() : []);
    const emptyList = (data) => toList(data);
    return Promise.all([
      fetch(YEARS_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(TERMS_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(CAMPUSES_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${CLASSES_URL}?page_size=500`, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${SECTIONS_URL}?page_size=500`, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${SUBJECTS_URL}?page_size=500`, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${OFFERINGS_URL}?page_size=500`, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${EVENTS_URL}?page_size=200`, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${STUDENTS_URL}?page_size=500`, { credentials: "include" }).then(toListOrEmpty),
    ])
      .then(([y, t, c, cl, se, su, of, ev, st]) => {
        setYears(emptyList(y));
        setTerms(emptyList(t));
        setCampuses(emptyList(c));
        setClasses(emptyList(cl));
        setSections(emptyList(se));
        setSubjects(emptyList(su));
        setOfferings(emptyList(of));
        setEvents(emptyList(ev));
        setStudents(emptyList(st));
        setError("");
      })
      .catch((requestError) => setError(requestError.message || "Failed to load academic data."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const visibleClasses = useMemo(() => {
    if (!structureCampus) return classes;
    return classes.filter((c) => Number(c.campus) === Number(structureCampus));
  }, [classes, structureCampus]);

  const visibleSections = useMemo(() => {
    if (!structureClass) return [];
    return sections.filter((s) => Number(s.class_obj) === Number(structureClass));
  }, [sections, structureClass]);

  const eventsSorted = useMemo(() => {
    return [...events].sort((a, b) => new Date(a.start_datetime) - new Date(b.start_datetime));
  }, [events]);

  const filteredStudents = useMemo(() => {
    const term = studentSearch.trim().toLowerCase();
    return students.filter((s) => {
      if (!term) return true;
      return [s.full_name, s.admission_number].some((value) => value && value.toLowerCase().includes(term));
    });
  }, [students, studentSearch]);

  const toggleStudent = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const promoField = (name) => (event) => {
    setPromoForm((prev) => ({ ...prev, [name]: event.target.value }));
  };

  const submitPromotion = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    setPromoResult("");
    if (!promoForm.from_academic_year) {
      setError("Select a source academic year.");
      return;
    }
    if (selectedIds.size === 0) {
      setError("Select at least one student.");
      return;
    }
    setPromoting(true);
    try {
      const result = await apiFetch(PROMOTIONS_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify({
          student_ids: Array.from(selectedIds),
          from_academic_year: Number(promoForm.from_academic_year),
          to_academic_year: promoForm.to_academic_year ? Number(promoForm.to_academic_year) : null,
          to_class: null,
          to_section: null,
          to_campus: promoForm.campus ? Number(promoForm.campus) : null,
          reason: promoForm.reason || "",
          effective_date: promoForm.effective_date || null,
        }),
      });
      const created = (result.created || []).length;
      const skipped = (result.skipped || []).length;
      setNotice(`Promotion applied to ${created} student${created === 1 ? "" : "s"}.`);
      setPromoResult(skipped ? `${skipped} student${skipped === 1 ? "" : "s"} skipped by the progression rules.` : "All selected students were promoted.");
      setSelectedIds(new Set());
      loadAll();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPromoting(false);
    }
  };

  const renderCalendar = () => (
    <>
      <div className="panel">
        <PanelHeader title="Academic Sessions" count={`${years.length} years · ${terms.length} terms`} />
        {years.length === 0 ? (
          <div className="state-card">No academic years configured.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>YEAR</th><th>STARTS</th><th>ENDS</th><th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {years.map((y) => (
                  <tr key={y.id}>
                    <td><strong>{y.name}</strong></td>
                    <td>{formatDate(y.start_date)}</td>
                    <td>{formatDate(y.end_date)}</td>
                    <td><StatusBadge status={y.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <PanelHeader title="Terms" />
        {terms.length === 0 ? (
          <div className="state-card">No terms configured.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>TERM</th><th>YEAR</th><th>STARTS</th><th>ENDS</th>
                </tr>
              </thead>
              <tbody>
                {terms.map((t) => (
                  <tr key={t.id}>
                    <td><strong>{t.name}</strong></td>
                    <td>{t.academic_year_name || "—"}</td>
                    <td>{formatDate(t.start_date)}</td>
                    <td>{formatDate(t.end_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel">
        <PanelHeader title="Upcoming Events" count={`${events.length} events`} />
        {eventsSorted.length === 0 ? (
          <EmptyState icon={CalendarDays} title="No events scheduled" message="School events will appear here." />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>START</th><th>EVENT</th><th>LOCATION</th><th>CAMPUS</th><th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {eventsSorted.slice(0, 40).map((e) => (
                  <tr key={e.id}>
                    <td>{formatDate(e.start_datetime)}</td>
                    <td><strong>{e.title}</strong></td>
                    <td>{e.location || "—"}</td>
                    <td>{e.campus_name || "—"}</td>
                    <td><StatusBadge status={e.status} label={e.status_label} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );

  const renderStructure = () => {
    const selectedClass = classes.find((c) => Number(c.id) === Number(structureClass));
    return (
      <>
        <div className="panel students-filters">
          <div className="filter-row">
            <div className="filter-search">
              <School size={18} />
              <select value={structureCampus} onChange={(event) => { setStructureCampus(event.target.value); setStructureClass(""); }}>
                <option value="">All campuses</option>
                {campuses.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="panel">
          <PanelHeader title="Classes" count={`${visibleClasses.length} classes`} />
          {visibleClasses.length === 0 ? (
            <div className="state-card">No classes found.</div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>CLASS</th><th>UNIT</th><th>LEVEL</th><th>SECTIONS</th><th>STUDENTS</th><th>STATUS</th><th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleClasses.map((c) => (
                    <tr key={c.id}>
                      <td><strong>{c.name}</strong></td>
                      <td>{c.unit_name || "—"}</td>
                      <td>{c.level || "—"}</td>
                      <td>{c.section_count ?? "—"}</td>
                      <td>{c.student_count ?? "—"}</td>
                      <td><StatusBadge status={c.status} /></td>
                      <td>
                        <button className="secondary-button secondary-button-sm" onClick={() => setStructureClass(String(c.id))}>
                          View sections
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selectedClass && (
          <div className="panel">
            <PanelHeader title={`Sections — ${selectedClass.name}`} count={`${visibleSections.length} sections`} />
            {visibleSections.length === 0 ? (
              <div className="state-card">No sections for this class.</div>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SECTION</th><th>CAPACITY</th><th>STUDENTS</th><th>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleSections.map((s) => (
                      <tr key={s.id}>
                        <td><strong>{s.name}</strong></td>
                        <td>{s.capacity ?? "—"}</td>
                        <td>{s.student_count ?? "—"}</td>
                        <td><StatusBadge status={s.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </>
    );
  };

  const renderSubjects = () => (
    <>
      <div className="panel">
        <PanelHeader title="Subjects" count={`${subjects.length} subjects`} />
        {subjects.length === 0 ? (
          <div className="state-card">No subjects configured.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>CODE</th><th>SUBJECT</th><th>TYPE</th><th>PRACTICAL</th><th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {subjects.map((s) => (
                  <tr key={s.id}>
                    <td>{s.code || "—"}</td>
                    <td><strong>{s.name}</strong></td>
                    <td>{s.subject_type || "—"}</td>
                    <td>{s.practical_required ? "Yes" : "No"}</td>
                    <td><StatusBadge status={s.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel">
        <PanelHeader title="Subject Offerings" count={`${offerings.length} offerings`} />
        {offerings.length === 0 ? (
          <EmptyState icon={BookOpen} title="No offerings" message="Subject-offering assignments will appear here." />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>YEAR</th><th>CAMPUS</th><th>CLASS</th><th>SUBJECT</th>
                </tr>
              </thead>
              <tbody>
                {offerings.map((o) => (
                  <tr key={o.id}>
                    <td>{o.academic_year_name || "—"}</td>
                    <td>{o.campus_name || "—"}</td>
                    <td>{o.class_name || "—"}</td>
                    <td><strong>{o.subject_name}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );

  const renderPromotions = () => (
    <div className="panel">
      <PanelHeader title="Batch Promotion / Transfer" subtitle="" />
      <p className="hint" style={{ marginBottom: 14 }}>Cross-year moves are promotions; keeping the same academic year performs a transfer. The school's progression rules decide the outcome for each student.</p>

      <form onSubmit={submitPromotion} style={{ marginBottom: 18 }}>
        <div className="form-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
          <label>
            From academic year *
            <select name="from_academic_year" value={promoForm.from_academic_year} onChange={promoField("from_academic_year")} required>
              <option value="">Select year</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>{y.name}</option>
              ))}
            </select>
          </label>
          <label>
            To academic year
            <select name="to_academic_year" value={promoForm.to_academic_year} onChange={promoField("to_academic_year")}>
              <option value="">— Same year (transfer) —</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>{y.name}</option>
              ))}
            </select>
          </label>
          <label>
            Campus
            <select name="campus" value={promoForm.campus} onChange={promoField("campus")}>
              <option value="">Any campus</option>
              {campuses.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          <label>
            Effective date
            <input type="date" name="effective_date" value={promoForm.effective_date} onChange={promoField("effective_date")} />
          </label>
          <label>
            Reason
            <input name="reason" value={promoForm.reason} onChange={promoField("reason")} placeholder="Optional reason" />
          </label>
        </div>
      </form>

      <div className="filter-search" style={{ marginBottom: 12 }}>
        <Search size={18} />
        <input
          placeholder="Search students to include..."
          value={studentSearch}
          onChange={(event) => setStudentSearch(event.target.value)}
        />
      </div>

      {filteredStudents.length === 0 ? (
        <div className="state-card">No students to promote.</div>
      ) : (
        <div className="table-wrapper" style={{ maxHeight: 420, overflowY: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}>#</th><th>STUDENT</th><th>ADMISSION NO</th><th>CURRENT CLASS</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((s) => (
                <tr key={s.id} style={selectedIds.has(s.id) ? { background: "var(--primary-soft)" } : undefined}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(s.id)}
                      onChange={() => toggleStudent(s.id)}
                    />
                  </td>
                  <td><strong>{s.full_name}</strong></td>
                  <td>{s.admission_number}</td>
                  <td>{s.current_enrollment?.class_name || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 14, flexWrap: "wrap" }}>
        <button type="button" className="primary-button" disabled={promoting} onClick={submitPromotion}>
          <GraduationCap size={15} /> {promoting ? "Applying..." : `Apply to ${selectedIds.size} student${selectedIds.size === 1 ? "" : "s"}`}
        </button>
        {promoResult && <span className="hint">{promoResult}</span>}
      </div>
    </div>
  );

  const tabs = [
    { key: "calendar", label: "Calendar", icon: CalendarDays, render: renderCalendar },
    { key: "structure", label: "Structure", icon: School, render: renderStructure },
    { key: "subjects", label: "Subjects", icon: BookOpen, render: renderSubjects },
    { key: "promotions", label: "Promotions", icon: GraduationCap, render: renderPromotions },
  ];

  const currentTab = tabs.find((t) => t.key === tab) || tabs[0];

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Academics"
        title="Academics"
        subtitle="Academic calendar, class structure, subjects, and batch promotions."
      />

      {notice && (
        <div className="state-card success">
          <strong>{notice}</strong>
        </div>
      )}

      {error && (
        <div className="state-card error">
          <strong>{error}</strong>
        </div>
      )}

      <div className="tabs" style={{ marginBottom: 16 }}>
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button key={t.key} type="button" className={currentTab.key === t.key ? "active" : ""} onClick={() => setTab(t.key)}>
              <Icon size={14} style={{ verticalAlign: -2, marginRight: 6 }} />
              {t.label}
            </button>
          );
        })}
      </div>

      <StateArea loading={loading} error={error} onRetry={loadAll}>
        {currentTab.render()}
      </StateArea>
    </section>
  );
}