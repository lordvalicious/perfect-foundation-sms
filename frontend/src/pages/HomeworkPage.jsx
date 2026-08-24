import { useCallback, useEffect, useState } from "react";
import { BookOpenCheck, ClipboardList, Plus, Send } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/homework/";

export default function HomeworkPage({ isStudent }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    assigned_date: new Date().toISOString().slice(0, 10),
    due_date: "",
    max_marks: 10,
  });
  const [saving, setSaving] = useState(false);

  const [selected, setSelected] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [mySubmission, setMySubmission] = useState(null);
  const [submitText, setSubmitText] = useState("");
  const [gradeForm, setGradeForm] = useState({ id: null, marks: "", feedback: "" });

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    apiFetch(BASE)
      .then((data) => setRows(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createHomework = async (event) => {
    event.preventDefault();
    setSaving(true);

    apiFetch(BASE, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setShowForm(false);
        setForm({ ...form, title: "", description: "" });
        load();
      })
      .catch((err) => setError(err.message))
      .finally(() => setSaving(false));
  };

  const openHomework = (homework) => {
    setSelected(homework);
    setNotice("");
    setMySubmission(null);
    setSubmitText("");

    if (isStudent) {
      apiFetch(`${BASE}${homework.id}/submissions/`)
        .then((data) => {
          const list = data.results || data;
          setMySubmission(list[0] || null);
        })
        .catch(() => setMySubmission(null));
    } else {
      apiFetch(`${BASE}${homework.id}/submissions/`)
        .then((data) => setSubmissions(data.results || data))
        .catch(() => setSubmissions([]));
    }
  };

  const submitHomework = () => {
    if (!selected) return;

    apiFetch(`${BASE}${selected.id}/submissions/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ content: submitText }),
    })
      .then(() => {
        setNotice("Submitted.");
        openHomework(selected);
      })
      .catch((err) => setError(err.message));
  };

  const saveGrade = () => {
    if (!gradeForm.id) return;

    apiFetch(`${BASE}submissions/${gradeForm.id}/grade/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        marks_obtained: gradeForm.marks === "" ? null : Number(gradeForm.marks),
        feedback: gradeForm.feedback,
      }),
    })
      .then(() => {
        setNotice("Graded.");
        openHomework(selected);
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Homework"
        title="Homework"
        subtitle={
          isStudent
            ? "Your homework assignments and submissions."
            : "Assign homework and track student submissions."
        }
        action={
          !isStudent ? (
            <button
              type="button"
              className="primary-button"
              onClick={() => setShowForm((v) => !v)}
            >
              <Plus size={15} />
              New Homework
            </button>
          ) : undefined
        }
      />

      {showForm && (
        <div className="panel">
          <PanelHeader title="Assign homework" subtitle="Visible to the class immediately" />
          <form onSubmit={createHomework} className="filter-row">
            <input
              required
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <input
              type="date"
              required
              value={form.assigned_date}
              onChange={(e) => setForm({ ...form, assigned_date: e.target.value })}
            />
            <input
              type="date"
              required
              value={form.due_date}
              onChange={(e) => setForm({ ...form, due_date: e.target.value })}
            />
            <input
              type="number"
              min="1"
              value={form.max_marks}
              onChange={(e) => setForm({ ...form, max_marks: e.target.value })}
              title="Max marks"
            />
            <textarea
              placeholder="Description (optional)"
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Assign"}
            </button>
          </form>
        </div>
      )}

      <div className="panel">
        <PanelHeader title="Homework" subtitle={`${rows.length} items · ${notice ? notice : "live"}`} />

        <StateArea loading={loading} error={error} onRetry={load}>
          {rows.length === 0 ? (
            <div className="empty-state">
              <BookOpenCheck size={42} />
              <h3>No homework</h3>
              <p>Nothing has been assigned yet.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    {!isStudent && <th>Teacher</th>}
                    <th>Class</th>
                    <th>Assigned</th>
                    <th>Due</th>
                    <th>Max Marks</th>
                    <th>Submissions</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td><strong>{row.title}</strong></td>
                      {!isStudent && <td>{row.teacher_name}</td>}
                      <td>{row.class_name}{row.section_name ? ` - ${row.section_name}` : ""}</td>
                      <td>{row.assigned_date}</td>
                      <td>{row.due_date}</td>
                      <td>{row.max_marks}</td>
                      <td>{row.submission_count}</td>
                      <td>
                        <button
                          type="button"
                          className="primary-button"
                          onClick={() => openHomework(row)}
                        >
                          {isStudent ? (
                            <>
                              <Send size={14} /> Open
                            </>
                          ) : (
                            <>
                              <ClipboardList size={14} /> Submissions
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>

      {selected && (
        <div className="panel">
          <PanelHeader
            title={selected.title}
            subtitle={`Due ${selected.due_date} · ${selected.max_marks} marks`}
            action={
              <button
                type="button"
                className="primary-button"
                onClick={() => setSelected(null)}
              >
                Close
              </button>
            }
          />

          {isStudent ? (
            mySubmission ? (
              <p>
                Submitted at {mySubmission.submitted_at}. Status:{" "}
                <strong>{mySubmission.status}</strong>
                {mySubmission.marks_obtained != null &&
                  ` — ${mySubmission.marks_obtained}/${selected.max_marks}`}
              </p>
            ) : (
              <>
                <textarea
                  rows={4}
                  placeholder="Type or paste your answer..."
                  value={submitText}
                  onChange={(e) => setSubmitText(e.target.value)}
                />
                <button className="primary-button" onClick={submitHomework}>
                  Submit homework
                </button>
              </>
            )
          ) : (
            <>
              {submissions.length === 0 && <p>No submissions yet.</p>}

              {submissions.length > 0 && (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Submitted</th>
                        <th>Marks</th>
                        <th>Status</th>
                        <th>Grade</th>
                      </tr>
                    </thead>
                    <tbody>
                      {submissions.map((s) => (
                        <tr key={s.id}>
                          <td><strong>{s.student_name}</strong></td>
                          <td>{s.submitted_at?.slice(0, 10)}</td>
                          <td>
                            {s.marks_obtained != null
                              ? `${s.marks_obtained}/${selected.max_marks}`
                              : "—"}
                          </td>
                          <td>{s.status}</td>
                          <td>
                            {s.id !== gradeForm.id && (
                              <button
                                type="button"
                                className="table-action"
                                onClick={() =>
                                  setGradeForm({
                                    id: s.id,
                                    marks: s.marks_obtained ?? "",
                                    feedback: s.feedback || "",
                                  })
                                }
                              >
                                Grade
                              </button>
                            )}

                            {s.id === gradeForm.id && (
                              <span style={{ display: "flex", gap: 6 }}>
                                <input
                                  type="number"
                                  min="0"
                                  max={selected.max_marks}
                                  value={gradeForm.marks}
                                  onChange={(e) =>
                                    setGradeForm({
                                      ...gradeForm,
                                      marks: e.target.value,
                                    })
                                  }
                                  style={{ width: 70 }}
                                />
                                <input
                                  placeholder="Feedback"
                                  value={gradeForm.feedback}
                                  onChange={(e) =>
                                    setGradeForm({
                                      ...gradeForm,
                                      feedback: e.target.value,
                                    })
                                  }
                                />
                                <button
                                  type="button"
                                  className="primary-button"
                                  onClick={saveGrade}
                                >
                                  Save
                                </button>
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}
