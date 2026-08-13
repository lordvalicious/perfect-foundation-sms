import { useCallback, useEffect, useState } from "react";
import { Search, CalendarCheck } from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  Pagination,
  StatusBadge,
} from "./ui";
import { formatDate } from "./format";
import { jsonHeaders } from "../api";

const API_URL = "/api/attendance/";
const BULK_URL = "/api/attendance/bulk/";
const STUDENTS_URL = "/api/students/";

const STATUS_OPTIONS = [
  ["present", "Present"],
  ["absent", "Absent"],
  ["late", "Late"],
  ["leave", "Leave"],
];

function buildParams(search, status, date, page) {
  const params = new URLSearchParams();

  params.append("page", page);

  if (search.trim()) {
    params.append("search", search.trim());
  }

  if (status) {
    params.append("status", status);
  }

  if (date) {
    params.append("date", date);
  }

  return params;
}

function MarkAttendance({ onSaved }) {
  const [campus, setCampus] = useState("");
  const [classObj, setClassObj] = useState("");
  const [section, setSection] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));

  const [campuses, setCampuses] = useState([]);
  const [classes, setClasses] = useState([]);
  const [sections, setSections] = useState([]);
  const [years, setYears] = useState([]);
  const [academicYear, setAcademicYear] = useState("");

  const [roster, setRoster] = useState([]);
  const [existing, setExisting] = useState({});
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadOptions = () => {
    fetch("/api/schools/campuses/", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => setCampuses(Array.isArray(data) ? data : []))
      .catch(() => {});

    fetch("/api/schools/classes/", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => setClasses(Array.isArray(data) ? data : []))
      .catch(() => {});

    fetch("/api/schools/sections/", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => setSections(Array.isArray(data) ? data : []))
      .catch(() => {});

    fetch("/api/schools/academic-years/", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => {
        const all = Array.isArray(data) ? data : [];
        setYears(all);
        const active = all.find((item) => item.status === "active");
        setAcademicYear(active ? String(active.id) : all[0] ? String(all[0].id) : "");
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadOptions();
  }, []);

  const loadRoster = () => {
    if (!campus || !classObj || !section) {
      setError("Select a campus, class and section to load the roster.");
      return;
    }

    setError("");
    setSuccess("");
    setLoadingRoster(true);
    setRoster([]);

    const params = new URLSearchParams();
    params.append("campus", campus);
    params.append("class_obj", classObj);
    params.append("section", section);
    params.append("status", "active");
    params.append("page", 1);

    const fetchPage = (pageNumber, accumulator) => {
      const pageParams = new URLSearchParams(params);
      pageParams.set("page", pageNumber);

      return fetch(`${STUDENTS_URL}?${pageParams.toString()}`, {
        credentials: "include",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to load the roster.");
          }

          return response.json();
        })
        .then((data) => {
          const students = [...accumulator, ...(data.results || [])];

          if (data.next) {
            return fetchPage(pageNumber + 1, students);
          }

          return students;
        });
    };

    const loadExisting = () => {
      const attParams = new URLSearchParams();
      attParams.append("date", date);
      attParams.append("campus", campus);
      attParams.append("class", classObj);
      attParams.append("page_size", 500);

      return fetch(`${API_URL}?${attParams.toString()}`, {
        credentials: "include",
      })
        .then((response) => (response.ok ? response.json() : { results: [] }))
        .then((data) => {
          const map = {};

          for (const record of data.results || []) {
            map[record.student] = record.status;
          }

          return map;
        })
        .catch(() => ({}));
    };

    Promise.all([fetchPage(1, []), loadExisting()])
      .then(([students, map]) => {
        setRoster(students);
        setExisting(map);
        setLoadingRoster(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingRoster(false);
      });
  };

  const setStatusFor = (studentId, status) => {
    setExisting((previous) => ({
      ...previous,
      [studentId]: status,
    }));
  };

  const setAll = (status) => {
    const next = { ...existing };

    for (const student of roster) {
      next[student.id] = status;
    }

    setExisting(next);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!roster.length) {
      setError("Load the roster before marking attendance.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    const records = roster.map((student) => ({
      student: student.id,
      status: existing[student.id] || "present",
      notes: "",
    }));

    try {
      const response = await fetch(BULK_URL, {
        method: "POST",
        credentials: "include",
        headers: jsonHeaders(),
        body: JSON.stringify({
          academic_year: Number(academicYear),
          campus: Number(campus),
          class: Number(classObj),
          section: Number(section),
          date: date,
          records,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        let message = "Unable to mark attendance.";

        if (data && typeof data === "object") {
          const parts = Object.entries(data).map(([field, value]) => {
            const text = Array.isArray(value)
              ? value.join(", ")
              : String(value);

            return `${field}: ${text}`;
          });

          if (parts.length) {
            message = parts.join(" | ");
          }
        }

        throw new Error(message);
      }

      setSuccess(
        `Saved ${data.created} new record(s) and updated ${data.updated} for ${formatDate(date)}.`
      );

      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="panel">
      <PanelHeader
        title="Mark Attendance"
        subtitle="Select a class and date to mark attendance"
      />

      <div className="form-section">
        <div className="form-grid">
          <label>
            Academic Year
            <select
              value={academicYear}
              onChange={(event) => setAcademicYear(event.target.value)}
            >
              <option value="">Select year</option>

              {years.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Campus
            <select value={campus} onChange={(event) => setCampus(event.target.value)}>
              <option value="">Select campus</option>

              {campuses.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Class
            <select value={classObj} onChange={(event) => setClassObj(event.target.value)}>
              <option value="">Select class</option>

              {classes
                .filter((item) => !campus || item.campus_name === campuses.find((c) => String(c.id) === String(campus))?.name)
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
            </select>
          </label>

          <label>
            Section
            <select value={section} onChange={(event) => setSection(event.target.value)}>
              <option value="">Select section</option>

              {sections
                .filter(
                  (item) => !classObj || String(item.class_obj) === String(classObj)
                )
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.class_name} - {item.name}
                  </option>
                ))}
            </select>
          </label>

          <label>
            Date
            <input
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
            />
          </label>
        </div>

        <div className="filter-row" style={{ marginTop: "14px" }}>
          <button
            type="button"
            className="primary-button"
            onClick={loadRoster}
            disabled={loadingRoster}
          >
            {loadingRoster ? "Loading roster..." : "Load Roster"}
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setCampus("");
              setClassObj("");
              setSection("");
              setRoster([]);
              setExisting({});
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {error && (
        <div className="state-card error">
          <strong>Unable to mark attendance.</strong>
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="state-card success">
          <strong>{success}</strong>
        </div>
      )}

      {roster.length > 0 && (
        <form onSubmit={handleSubmit}>
          <div className="filter-row" style={{ marginTop: "8px" }}>
            <span className="field-hint">Quick set:</span>

            {STATUS_OPTIONS.map(([value, label]) => (
              <button
                key={value}
                type="button"
                className="secondary-button"
                onClick={() => setAll(value)}
              >
                All {label}
              </button>
            ))}
          </div>

          <div className="table-wrapper" style={{ marginTop: "12px" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>STUDENT</th>
                  <th>ADMISSION NO.</th>
                  <th>STATUS</th>
                </tr>
              </thead>

              <tbody>
                {roster.map((student) => (
                  <tr key={student.id}>
                    <td>
                      <strong>{student.full_name || "—"}</strong>
                    </td>

                    <td>{student.admission_number || "—"}</td>

                    <td>
                      <select
                        value={existing[student.id] || "present"}
                        onChange={(event) =>
                          setStatusFor(student.id, event.target.value)
                        }
                      >
                        {STATUS_OPTIONS.map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="modal-footer">
            <button type="submit" className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Mark Attendance"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default function AttendancePage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [date, setDate] = useState("");

  const {
    rows,
    count,
    loading,
    error,
    page,
    next,
    previous,
    refresh,
  } = useApiList(API_URL);

  const applyFilters = useCallback(
    (pageNumber = 1) => {
      refresh(buildParams(search, status, date, pageNumber));
    },
    [refresh, search, status, date]
  );

  const clearFilters = () => {
    setSearch("");
    setStatus("");
    setDate("");
    refresh(new URLSearchParams({ page: 1 }));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Attendance"
        title="Attendance"
        subtitle="Mark and view daily attendance records for students."
      />

      <MarkAttendance onSaved={() => applyFilters(1)} />

      <div className="panel students-filters">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            applyFilters(1);
          }}
        >
          <div className="filter-row">
            <div className="filter-search">
              <Search size={18} />

              <input
                type="text"
                placeholder="Search by name or admission number..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <input
              type="date"
              value={date}
              onChange={(event) => {
                setDate(event.target.value);
                setTimeout(() => applyFilters(1), 0);
              }}
            />

            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setTimeout(() => applyFilters(1), 0);
              }}
            >
              <option value="">All statuses</option>

              {STATUS_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>

            <button type="submit" className="primary-button">
              Search
            </button>

            <button type="button" className="secondary-button" onClick={clearFilters}>
              Clear
            </button>
          </div>
        </form>
      </div>

      <div className="panel">
        <PanelHeader
          title="Attendance Records"
          subtitle="records found"
          count={count}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => applyFilters(page)}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={CalendarCheck}
              title="No attendance records found"
              message="No attendance records match the current filters."
            />
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>STUDENT</th>
                      <th>ADMISSION NO.</th>
                      <th>CAMPUS</th>
                      <th>CLASS</th>
                      <th>SECTION</th>
                      <th>DATE</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>

                  <tbody>
                    {rows.map((record) => (
                      <tr key={record.id}>
                        <td>
                          <strong>{record.student_name || "—"}</strong>
                        </td>

                        <td>{record.admission_number || "—"}</td>

                        <td>{record.campus_name || "—"}</td>

                        <td>{record.class_name || "—"}</td>

                        <td>{record.section_name || "—"}</td>

                        <td>{formatDate(record.date)}</td>

                        <td>
                          <StatusBadge
                            status={record.status}
                            label={record.status_display}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                count={count}
                page={page}
                next={next}
                previous={previous}
                onPage={(pageNumber) => applyFilters(pageNumber)}
              />
            </>
          )}
        </StateArea>
      </div>
    </section>
  );
}
