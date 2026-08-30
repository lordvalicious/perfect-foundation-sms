import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  Pencil,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import { apiFetch } from "../api";
import { EmptyState, PanelHeader, StateArea } from "./ui";
import { formatDate } from "./format";

const SCHEDULES_URL = "/api/exams/schedules/";
const SECTIONS_URL = "/api/schools/sections/?page_size=500";
const TEACHERS_URL = "/api/teachers/?page_size=500";
const EXAM_SUBJECTS_URL = "/api/exams/subjects/";

function toList(data) {
  return Array.isArray(data) ? data : data.results || [];
}

function toTime(value) {
  return value ? value.slice(0, 5) : "";
}

function overlaps(a, b) {
  return a.start_time < b.end_time && a.end_time > b.start_time;
}

function mapTime(row) {
  return {
    ...row,
    start_time: toTime(row.start_time),
    end_time: toTime(row.end_time),
  };
}

function computeConflicts(rows) {
  const conflicts = new Map();

  const addConflict = (id, reason) => {
    conflicts.set(id, [...(conflicts.get(id) || []), reason]);
  };

  for (let i = 0; i < rows.length; i += 1) {
    const a = rows[i];

    for (let j = i + 1; j < rows.length; j += 1) {
      const b = rows[j];

      if (a.date !== b.date || !overlaps(a, b)) {
        continue;
      }

      if (a.section === b.section) {
        addConflict(a.id, "Section already has an exam at this time");
        addConflict(b.id, "Section already has an exam at this time");
      }

      if (a.room && a.room === b.room) {
        addConflict(a.id, `Room "${a.room}" is double-booked`);
        addConflict(b.id, `Room "${b.room}" is double-booked`);
      }
    }
  }

  return conflicts;
}

const EMPTY_FORM = {
  section: "",
  exam_subject: "",
  subject: "",
  date: "",
  start_time: "09:00",
  end_time: "11:00",
  room: "",
  invigilator: "",
  notes: "",
};

export default function ManageSchedulePanel({ exam, onChanged }) {
  const [rows, setRows] = useState([]);
  const [sections, setSections] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [examSubjects, setExamSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [modalError, setModalError] = useState("");
  const [clientConflict, setClientConflict] = useState("");

  const isLocked = exam.status === "completed";

  const load = () => {
    setLoading(true);
    setError("");

    const toListOrEmpty = (response) =>
      response.ok ? response.json() : [];

    Promise.all([
      fetch(`${SCHEDULES_URL}?exam=${exam.id}&page_size=500`, {
        credentials: "include",
      }).then(toListOrEmpty),
      fetch(SECTIONS_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(TEACHERS_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(`${EXAM_SUBJECTS_URL}?exam=${exam.id}`, {
        credentials: "include",
      }).then(toListOrEmpty),
    ])
      .then(([sched, sec, teach, subs]) => {
        setRows(toList(sched).map(mapTime));
        setSections(toList(sec));
        setTeachers(toList(teach));
        setExamSubjects(toList(subs));
      })
      .catch(() => setError("Failed to load the exam schedule."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exam.id]);

  const classSections = sections.filter(
    (section) => String(section.class_obj) === String(exam.class_obj)
  );

  const conflicts = computeConflicts(rows);

  const openAdd = () => {
    setEditing(null);
    setForm({
      ...EMPTY_FORM,
      section: classSections[0] ? String(classSections[0].id) : "",
      date: exam.start_date,
    });
    setModalError("");
    setClientConflict("");
    setModalOpen(true);
  };

  const openEdit = (row) => {
    setEditing(row);
    setForm({
      section: String(row.section),
      exam_subject: row.exam_subject ? String(row.exam_subject) : "",
      subject: "",
      date: row.date,
      start_time: row.start_time,
      end_time: row.end_time,
      room: row.room || "",
      invigilator: row.invigilator ? String(row.invigilator) : "",
      notes: row.notes || "",
    });
    setModalError("");
    setClientConflict("");
    setModalOpen(true);
  };

  const closeModal = () => {
    if (!saving) {
      setModalOpen(false);
      setEditing(null);
    }
  };

  const checkClientConflict = (draft) => {
    const candidate = {
      ...draft,
      date: draft.date,
      start_time: draft.start_time,
      end_time: draft.end_time,
      section: draft.section,
      room: draft.room.trim(),
      id: editing ? editing.id : null,
    };

    if (
      !candidate.date ||
      !candidate.start_time ||
      !candidate.end_time ||
      candidate.start_time >= candidate.end_time
    ) {
      setClientConflict("");
      return;
    }

    const reason = rows
      .filter((row) => (editing ? row.id !== editing.id : true))
      .find((row) => {
        if (row.date !== candidate.date || !overlaps(row, candidate)) {
          return false;
        }

        if (row.section === candidate.section) {
          return true;
        }

        return Boolean(candidate.room) && row.room === candidate.room;
      });

    if (reason) {
      const label = reason.section === candidate.section
        ? `"${reason.section_name}" already has an exam at this time`
        : `Room "${candidate.room}" is already booked at this time`;

      setClientConflict(`Conflict: ${label}.`);
    } else {
      setClientConflict("");
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setModalError("");

    try {
      const payload = {
        exam: exam.id,
        section: form.section,
        exam_subject: form.exam_subject || null,
        date: form.date,
        start_time: form.start_time,
        end_time: form.end_time,
        room: form.room.trim(),
        invigilator: form.invigilator || null,
        notes: form.notes.trim(),
      };

      if (editing) {
        await apiFetch(
          `${SCHEDULES_URL}${editing.id}/`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
          "Failed to update the schedule."
        );
      } else {
        await apiFetch(
          SCHEDULES_URL,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
          "Failed to create the schedule."
        );
      }

      setModalOpen(false);
      setEditing(null);
      onChanged();
      load();
    } catch (err) {
      setModalError(err.message || String(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm("Remove this schedule slot?")) {
      return;
    }

    try {
      await apiFetch(
        `${SCHEDULES_URL}${row.id}/`,
        { method: "DELETE" },
        "Failed to delete the schedule."
      );
      onChanged();
      load();
    } catch (err) {
      setError(err.message || String(err));
    }
  };

  return (
    <div className="panel">
      <PanelHeader
        title="Exam Schedule"
        subtitle="slots"
        count={rows.length}
        action={
          !isLocked && (
            <button
              type="button"
              className="primary-button"
              onClick={openAdd}
            >
              <Plus size={16} />
              Add slot
            </button>
          )
        }
      />

      {isLocked && (
        <div
          className="alert"
          style={{
            background: "var(--warning-soft)",
            border: "1px solid var(--warning)",
            color: "var(--warning)",
          }}
        >
          <AlertTriangle size={16} />
          The schedule is locked because this exam is completed.
        </div>
      )}

      <StateArea loading={loading} error={error} onRetry={load}>
        {rows.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="No schedule yet"
            message="Add examination slots for each section, subject and date."
          />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>DATE</th>
                  <th>TIME</th>
                  <th>SECTION</th>
                  <th>SUBJECT</th>
                  <th>ROOM</th>
                  <th>INVIGILATOR</th>
                  <th>CONFLICTS</th>
                  {!isLocked && <th>ACTIONS</th>}
                </tr>
              </thead>

              <tbody>
                {rows.map((row) => {
                  const rowConflicts = conflicts.get(row.id);

                  return (
                    <tr
                      key={row.id}
                      style={
                        rowConflicts
                          ? { background: "var(--danger-soft)" }
                          : undefined
                      }
                    >
                      <td>{formatDate(row.date)}</td>

                      <td>
                        {row.start_time} - {row.end_time}
                      </td>

                      <td>{row.section_name || "—"}</td>

                      <td>{row.subject_name || (
                        <em className="muted">All subjects</em>
                      )}</td>

                      <td>{row.room || "—"}</td>

                      <td>{row.invigilator_name || "Not assigned"}</td>

                      <td>
                        {rowConflicts
                          ? (
                            <span className="text-red-500">
                              {rowConflicts.join("; ")}
                            </span>
                          ) : (
                            <span className="muted">None</span>
                          )}
                      </td>

                      {!isLocked && (
                        <td>
                          <div className="table-actions">
                            <button
                              className="table-action"
                              onClick={() => openEdit(row)}
                            >
                              <Pencil size={14} />
                            </button>

                            <button
                              className="table-action danger"
                              onClick={() => handleDelete(row)}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </StateArea>

      {modalOpen && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <div>
                <h3>{editing ? "Edit Schedule" : "Add Schedule Slot"}</h3>
                <p>
                  {editing
                    ? "Update this examination slot."
                    : "Schedule an examination for a section."}
                </p>
              </div>

              <button className="modal-close" onClick={closeModal}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-section">
                  <h4>Slot details</h4>

                  <div className="form-grid">
                    <label>
                      Section
                      <select
                        required
                        value={form.section}
                        onChange={(event) => {
                          const next = { ...form, section: event.target.value };
                          setForm(next);
                          checkClientConflict(next);
                        }}
                      >
                        <option value="">Select section</option>

                        {classSections.map((section) => (
                          <option key={section.id} value={section.id}>
                            {section.name}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Subject
                      <select
                        value={form.exam_subject}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            exam_subject: event.target.value,
                          }))
                        }
                      >
                        <option value="">All subjects</option>

                        {examSubjects.map((subject) => (
                          <option key={subject.id} value={subject.id}>
                            {subject.subject_name}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Date
                      <input
                        type="date"
                        required
                        min={exam.start_date}
                        max={exam.end_date}
                        value={form.date}
                        onChange={(event) => {
                          const next = { ...form, date: event.target.value };
                          setForm(next);
                          checkClientConflict(next);
                        }}
                      />
                    </label>

                    <label>
                      Start time
                      <input
                        type="time"
                        required
                        value={form.start_time}
                        onChange={(event) => {
                          const next = { ...form, start_time: event.target.value };
                          setForm(next);
                          checkClientConflict(next);
                        }}
                      />
                    </label>

                    <label>
                      End time
                      <input
                        type="time"
                        required
                        value={form.end_time}
                        onChange={(event) => {
                          const next = { ...form, end_time: event.target.value };
                          setForm(next);
                          checkClientConflict(next);
                        }}
                      />
                    </label>

                    <label>
                      Room / hall
                      <input
                        type="text"
                        placeholder="e.g. Hall A"
                        value={form.room}
                        onChange={(event) => {
                          const next = { ...form, room: event.target.value };
                          setForm(next);
                          checkClientConflict(next);
                        }}
                      />
                    </label>

                    <label>
                      Invigilator (optional)
                      <select
                        value={form.invigilator}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            invigilator: event.target.value,
                          }))
                        }
                      >
                        <option value="">Not assigned</option>

                        {teachers.map((teacher) => (
                          <option key={teacher.id} value={teacher.id}>
                            {teacher.full_name}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Notes (optional)
                      <input
                        type="text"
                        value={form.notes}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            notes: event.target.value,
                          }))
                        }
                      />
                    </label>
                  </div>
                </div>

                {clientConflict && (
                  <div
                    className="alert"
                    style={{
                      background: "var(--warning-soft)",
                      border: "1px solid var(--warning)",
                      color: "var(--warning)",
                    }}
                  >
                    <AlertTriangle size={16} />
                    {clientConflict}
                  </div>
                )}

                {modalError && <div className="alert alert-error">{modalError}</div>}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving || !form.section || !form.date}
                >
                  {saving
                    ? "Saving..."
                    : editing
                      ? "Save changes"
                      : "Add slot"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}