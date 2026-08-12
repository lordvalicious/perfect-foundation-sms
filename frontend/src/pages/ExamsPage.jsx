import { useState } from "react";
import { Search, FileText } from "lucide-react";
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
import MarksEntryPanel from "./MarksEntryPanel";

const API_URL = "/api/exams/";

const EXAM_STATUSES = [
  ["draft", "Draft"],
  ["scheduled", "Scheduled"],
  ["completed", "Completed"],
];

function buildParams(search, status, page) {
  const params = new URLSearchParams();

  params.append("page", page);

  if (search.trim()) {
    params.append("search", search.trim());
  }

  if (status) {
    params.append("status", status);
  }

  return params;
}

export default function ExamsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");

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
    refresh(buildParams(search, status, pageNumber));
  };

  const clearFilters = () => {
    setSearch("");
    setStatus("");
    refresh(new URLSearchParams({ page: 1 }));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Exams"
        title="Exams"
        subtitle="Schedule examinations and enter student marks."
      />

      <MarksEntryPanel
        exams={rows}
        onSaved={() => applyFilters(page)}
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
                placeholder="Search by exam name..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setTimeout(() => applyFilters(1), 0);
              }}
            >
              <option value="">All statuses</option>

              {EXAM_STATUSES.map(([value, label]) => (
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
        <PanelHeader title="Exam List" subtitle="exams found" count={count} />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => applyFilters(page)}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No exams found"
              message="No exams match the current filters."
            />
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>EXAM</th>
                      <th>TYPE</th>
                      <th>ACADEMIC YEAR</th>
                      <th>CAMPUS</th>
                      <th>CLASS</th>
                      <th>START DATE</th>
                      <th>END DATE</th>
                      <th>SUBJECTS</th>
                      <th>RESULTS</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>

                  <tbody>
                    {rows.map((exam) => (
                      <tr key={exam.id}>
                        <td>
                          <strong>{exam.name || "—"}</strong>
                        </td>

                        <td>{exam.exam_type_display || "—"}</td>

                        <td>{exam.academic_year_name || "—"}</td>

                        <td>{exam.campus_name || "—"}</td>

                        <td>{exam.class_name || "—"}</td>

                        <td>{formatDate(exam.start_date)}</td>

                        <td>{formatDate(exam.end_date)}</td>

                        <td>{exam.subject_count ?? 0}</td>

                        <td>{exam.result_count ?? 0}</td>

                        <td>
                          <StatusBadge
                            status={exam.status}
                            label={exam.status_display}
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
