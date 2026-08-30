import { useState } from "react";
import {
  ArrowLeft,
  Armchair,
  BookOpen,
  CalendarClock,
  FileText,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { apiFetch } from "../api";
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
import ExamFormModal from "./ExamFormModal";
import ManageSubjectsPanel from "./ManageSubjectsPanel";
import ManageSchedulePanel from "./ManageSchedulePanel";
import ManageSeatingPanel from "./ManageSeatingPanel";

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
  const [selectedExam, setSelectedExam] = useState(null);
  const [tab, setTab] = useState("subjects");
  const [formOpen, setFormOpen] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const [actionError, setActionError] = useState("");

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

  const openCreate = () => {
    setEditingExam(null);
    setActionError("");
    setFormOpen(true);
  };

  const openEdit = (exam) => {
    setEditingExam(exam);
    setActionError("");
    setFormOpen(true);
  };

  const handleSaved = async () => {
    applyFilters(page);

    if (selectedExam && editingExam && String(editingExam.id) === String(selectedExam.id)) {
      try {
        const updated = await apiFetch(
          `/api/exams/${selectedExam.id}/`,
          {},
          "Failed to refresh the exam."
        );
        setSelectedExam(updated);
      } catch {
        // Keep the stale detail; the list refresh still runs.
      }
    }
  };

  const handleDelete = async (exam) => {
    if (
      !window.confirm(
        `Delete "${exam.name}"? This also removes its subjects, schedule, seating and results.`
      )
    ) {
      return;
    }

    setActionError("");

    try {
      await apiFetch(
        `/api/exams/${exam.id}/`,
        { method: "DELETE" },
        "Failed to delete the exam."
      );

      if (selectedExam && String(selectedExam.id) === String(exam.id)) {
        setSelectedExam(null);
      }

      applyFilters(page);
    } catch (err) {
      setActionError(err.message || String(err));
    }
  };

  const openManage = (exam) => {
    setSelectedExam(exam);
    setTab("subjects");
    setActionError("");
  };

  if (selectedExam) {
    const exam = selectedExam;

    return (
      <section className="content">
        <PageHeader
          crumb="Home / Exams / Manage"
          title={exam.name}
          subtitle={`${exam.exam_type_display || "Exam"} · ${exam.class_name || ""}`}
          action={
            <button
              type="button"
              className="secondary-button"
              onClick={() => setSelectedExam(null)}
            >
              <ArrowLeft size={16} />
              Back to exams
            </button>
          }
        />

        <div className="panel">
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 16,
              padding: "14px 16px",
            }}
          >
            <StatusBadge status={exam.status} label={exam.status_display} />

            <div className="muted">
              <strong>{exam.academic_year_name || "—"}</strong>
              {exam.term_name ? ` · ${exam.term_name}` : " · Full year"}
            </div>

            <div className="muted">
              {exam.campus_name || "—"} · {exam.class_name || "—"}
            </div>

            <div className="muted">
              {formatDate(exam.start_date)} → {formatDate(exam.end_date)}
            </div>

            <div className="muted">
              {exam.subject_count ?? 0} subjects · {exam.result_count ?? 0} results
            </div>

            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              <button
                type="button"
                className="secondary-button"
                onClick={() => openEdit(exam)}
              >
                <Pencil size={16} />
                Edit
              </button>

              <button
                type="button"
                className="secondary-button"
                style={{
                  color: "var(--danger)",
                  borderColor: "var(--danger-border)",
                }}
                onClick={() => handleDelete(exam)}
              >
                <Trash2 size={16} />
                Delete
              </button>
            </div>
          </div>
        </div>

        {actionError && <div className="alert alert-error">{actionError}</div>}

        <div className="tabs" style={{ marginBottom: 16 }}>
          <button
            type="button"
            className={`tab ${tab === "subjects" ? "active" : ""}`}
            onClick={() => setTab("subjects")}
          >
            <BookOpen size={18} />
            Subjects
          </button>

          <button
            type="button"
            className={`tab ${tab === "schedule" ? "active" : ""}`}
            onClick={() => setTab("schedule")}
          >
            <CalendarClock size={18} />
            Schedule
          </button>

          <button
            type="button"
            className={`tab ${tab === "seating" ? "active" : ""}`}
            onClick={() => setTab("seating")}
          >
            <Armchair size={18} />
            Seating
          </button>
        </div>

        {tab === "subjects" && (
          <ManageSubjectsPanel exam={exam} onChanged={() => applyFilters(page)} />
        )}

        {tab === "schedule" && (
          <ManageSchedulePanel exam={exam} onChanged={() => applyFilters(page)} />
        )}

        {tab === "seating" && (
          <ManageSeatingPanel exam={exam} onChanged={() => applyFilters(page)} />
        )}

        <ExamFormModal
          open={formOpen}
          exam={editingExam}
          onClose={() => setFormOpen(false)}
          onSaved={handleSaved}
        />
      </section>
    );
  }

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Exams"
        title="Exams"
        subtitle="Schedule examinations, plan seating and enter student marks."
        action={
          <button type="button" className="primary-button" onClick={openCreate}>
            <Plus size={16} />
            New exam
          </button>
        }
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

      {actionError && <div className="alert alert-error">{actionError}</div>}

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
              message="No exams match the current filters. Create a new exam to get started."
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
                      <th>ACTIONS</th>
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

                        <td>
                          <div className="table-actions">
                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() => openManage(exam)}
                            >
                              Manage
                            </button>

                            <button
                              className="table-action"
                              onClick={() => openEdit(exam)}
                              title="Edit exam"
                            >
                              <Pencil size={14} />
                            </button>

                            <button
                              className="table-action danger"
                              onClick={() => handleDelete(exam)}
                              title="Delete exam"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
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

      <ExamFormModal
        open={formOpen}
        exam={editingExam}
        onClose={() => setFormOpen(false)}
        onSaved={handleSaved}
      />
    </section>
  );
}