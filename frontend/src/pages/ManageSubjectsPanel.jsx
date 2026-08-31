import { useEffect, useState } from "react";
import { AlertTriangle, BookOpen, Pencil, Plus, Trash2, X } from "lucide-react";
import { apiFetch } from "../api";
import { EmptyState, PanelHeader, StateArea } from "./ui";

const SUBJECTS_URL = "/api/exams/subjects/";
const OFFERINGS_URL = "/api/schools/offerings/?page_size=500";

function toList(data) {
  return Array.isArray(data) ? data : data.results || [];
}

const EMPTY_FORM = {
  subject: "",
  maximum_marks: "100",
  passing_marks: "40",
};

export default function ManageSubjectsPanel({ exam, onChanged }) {
  const [rows, setRows] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [modalError, setModalError] = useState("");

  const isDraft = exam.status === "draft";

  const load = () => {
    setLoading(true);
    setError("");

    const toListOrEmpty = (response) =>
      response.ok ? response.json() : [];

    Promise.all([
      fetch(`${SUBJECTS_URL}?exam=${exam.id}`, { credentials: "include" })
        .then(toListOrEmpty),
      fetch(OFFERINGS_URL, { credentials: "include" }).then(toListOrEmpty),
    ])
      .then(([subjects, offered]) => {
        setRows(toList(subjects));
        setOfferings(toList(offered));
      })
      .catch(() => setError("Failed to load exam subjects."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exam.id]);

  const eligibleOfferings = offerings.filter(
    (offering) =>
      String(offering.class_obj) === String(exam.class_obj) &&
      String(offering.academic_year) === String(exam.academic_year)
  );

  const existingSubjectIds = new Set(rows.map((row) => String(row.subject)));

  const addableOfferings = eligibleOfferings.filter(
    (offering) => !existingSubjectIds.has(String(offering.subject))
  );

  const openAdd = () => {
    setEditing(null);
    setForm({
      ...EMPTY_FORM,
      subject: addableOfferings[0] ? String(addableOfferings[0].subject) : "",
    });
    setModalError("");
    setModalOpen(true);
  };

  const openEdit = (row) => {
    setEditing(row);
    setForm({
      subject: String(row.subject),
      maximum_marks: String(row.maximum_marks),
      passing_marks: String(row.passing_marks),
    });
    setModalError("");
    setModalOpen(true);
  };

  const closeModal = () => {
    if (!saving) {
      setModalOpen(false);
      setEditing(null);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setModalError("");

    try {
      const payload = {
        maximum_marks: Number(form.maximum_marks),
        passing_marks: Number(form.passing_marks),
      };

      if (editing) {
        await apiFetch(
          `${SUBJECTS_URL}${editing.id}/`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
          "Failed to update the subject."
        );
      } else {
        await apiFetch(
          SUBJECTS_URL,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              ...payload,
              exam: exam.id,
              subject: form.subject,
            }),
          },
          "Failed to add the subject."
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
    if (!window.confirm(`Remove ${row.subject_name} from this exam?`)) {
      return;
    }

    try {
      await apiFetch(
        `${SUBJECTS_URL}${row.id}/`,
        { method: "DELETE" },
        "Failed to remove the subject."
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
        title="Exam Subjects"
        subtitle="subjects"
        count={rows.length}
        action={
          isDraft && (
            <button
              type="button"
              className="primary-button"
              onClick={openAdd}
              disabled={addableOfferings.length === 0}
            >
              <Plus size={16} />
              Add subject
            </button>
          )
        }
      />

      {!isDraft && (
        <div
          className="alert"
          style={{
            background: "var(--warning-soft)",
            border: "1px solid var(--warning)",
            color: "var(--warning)",
          }}
        >
          <AlertTriangle size={16} />
          Subjects are locked because this exam is no longer in draft.
        </div>
      )}

      <StateArea loading={loading} error={error} onRetry={load}>
        {rows.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No subjects added"
            message={
              addableOfferings.length === 0
                ? "No subjects are offered to this class for the selected academic year."
                : "Add subjects from the class offering list."
            }
          />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>SUBJECT</th>
                  <th>CODE</th>
                  <th>MAXIMUM MARKS</th>
                  <th>PASSING MARKS</th>
                  {isDraft && <th>ACTIONS</th>}
                </tr>
              </thead>

              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>{row.subject_name || "—"}</strong>
                    </td>

                    <td>{row.subject_code || "—"}</td>

                    <td>{row.maximum_marks}</td>

                    <td>{row.passing_marks}</td>

                    {isDraft && (
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
                ))}
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
                <h3>{editing ? "Edit Subject" : "Add Subject"}</h3>
                <p>
                  {editing
                    ? `Adjust marks for ${editing.subject_name}.`
                    : "Add an offered subject to the exam."}
                </p>
              </div>

              <button className="modal-close" onClick={closeModal}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                {!editing && (
                  <div className="form-section">
                    <h4>Subject</h4>

                    {addableOfferings.length === 0 ? (
                      <p className="muted">
                        All subjects offered to this class have already
                        been added to the exam.
                      </p>
                    ) : (
                      <label>
                        Select subject
                        <select
                          required
                          value={form.subject}
                          onChange={(event) =>
                            setForm((current) => ({
                              ...current,
                              subject: event.target.value,
                            }))
                          }
                        >
                          <option value="">Select subject</option>

                          {addableOfferings.map((offering) => (
                            <option
                              key={offering.id}
                              value={offering.subject}
                            >
                              {offering.subject_name}
                            </option>
                          ))}
                        </select>
                      </label>
                    )}
                  </div>
                )}

                <div className="form-section">
                  <h4>Marks</h4>

                  <div className="form-grid">
                    <label>
                      Maximum marks
                      <input
                        type="number"
                        required
                        min="1"
                        value={form.maximum_marks}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            maximum_marks: event.target.value,
                          }))
                        }
                      />
                    </label>

                    <label>
                      Passing marks
                      <input
                        type="number"
                        required
                        min="0"
                        value={form.passing_marks}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            passing_marks: event.target.value,
                          }))
                        }
                      />
                    </label>
                  </div>
                </div>

                {modalError && (
                  <div className="alert alert-error">{modalError}</div>
                )}
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
                  disabled={saving || (!editing && !form.subject)}
                >
                  {saving
                    ? "Saving..."
                    : editing
                      ? "Save changes"
                      : "Add subject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}