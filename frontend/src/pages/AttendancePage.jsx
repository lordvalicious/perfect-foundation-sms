import { useState } from "react";
import { Search, ClipboardCheck } from "lucide-react";
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

const API_URL = "/api/attendance/";

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

  const applyFilters = (pageNumber = 1) => {
    refresh(buildParams(search, status, date, pageNumber));
  };

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
        subtitle="View daily attendance records for all students."
      />

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
                onChange={(event) =>
                  setSearch(event.target.value)
                }
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

            <button
              type="button"
              className="secondary-button"
              onClick={clearFilters}
            >
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
              icon={ClipboardCheck}
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
                          <strong>
                            {record.student_name || "—"}
                          </strong>
                        </td>

                        <td>
                          {record.admission_number || "—"}
                        </td>

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
                onPage={(pageNumber) =>
                  applyFilters(pageNumber)
                }
              />
            </>
          )}
        </StateArea>
      </div>
    </section>
  );
}
