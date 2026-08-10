import { useState } from "react";
import { Search, BookOpen } from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  Pagination,
  StatusBadge,
} from "./ui";

const API_URL = "/api/report-cards/";

function buildParams(search, result, page) {
  const params = new URLSearchParams();

  params.append("page", page);

  if (search.trim()) {
    params.append("search", search.trim());
  }

  if (result) {
    params.append("result", result);
  }

  return params;
}

function formatPercentage(value) {
  const number = Number(value || 0);

  return `${number.toLocaleString(undefined, {
    maximumFractionDigits: 1,
  })}%`;
}

export default function ReportCardsPage() {
  const [search, setSearch] = useState("");
  const [result, setResult] = useState("");

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
    refresh(buildParams(search, result, pageNumber));
  };

  const clearFilters = () => {
    setSearch("");
    setResult("");
    refresh(new URLSearchParams({ page: 1 }));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Report Cards"
        title="Report Cards"
        subtitle="View student report cards and exam results."
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
                placeholder="Search by student name or admission number..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>

            <select
              value={result}
              onChange={(event) => {
                setResult(event.target.value);
                setTimeout(() => applyFilters(1), 0);
              }}
            >
              <option value="">All results</option>
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
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
          title="Report Card List"
          subtitle="report cards found"
          count={count}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => applyFilters(page)}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No report cards found"
              message="No report cards match the current filters."
            />
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>STUDENT</th>
                      <th>ADMISSION NO.</th>
                      <th>EXAM</th>
                      <th>CLASS</th>
                      <th>POSITION</th>
                      <th>MARKS</th>
                      <th>PERCENTAGE</th>
                      <th>GRADE</th>
                      <th>RESULT</th>
                    </tr>
                  </thead>

                  <tbody>
                    {rows.map((card) => (
                      <tr key={card.id}>
                        <td>
                          <strong>
                            {card.student_name || "—"}
                          </strong>
                        </td>

                        <td>{card.admission_number || "—"}</td>

                        <td>{card.exam_name || "—"}</td>

                        <td>{card.class_name || "—"}</td>

                        <td>
                          {card.position
                            ? `#${card.position}`
                            : "—"}
                        </td>

                        <td>
                          {card.total_marks ?? "—"} /{" "}
                          {card.maximum_marks ?? "—"}
                        </td>

                        <td>
                          <strong>
                            {formatPercentage(card.percentage)}
                          </strong>
                        </td>

                        <td>
                          <strong>{card.grade || "—"}</strong>
                        </td>

                        <td>
                          <StatusBadge
                            status={card.overall_result}
                            label={card.overall_result}
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
