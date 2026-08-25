import { useCallback, useEffect, useState } from "react";
import {
  BookOpenCheck,
  CheckCircle2,
  Circle,
  Plus,
  Send,
  Trash2,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/lms/";

export default function LMSPage({ isStudent }) {
  const [courses, setCourses] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    is_published: true,
  });

  const [selected, setSelected] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [quizzes, setQuizzes] = useState([]);

  const [showQuizForm, setShowQuizForm] = useState(false);
  const [quizForm, setQuizForm] = useState({ title: "", due_date: "" });

  const [openQuiz, setOpenQuiz] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [newQ, setNewQ] = useState({
    text: "", option_a: "", option_b: "", option_c: "",
    option_d: "", correct_option: "a", marks: 1,
  });

  const [myAttempt, setMyAttempt] = useState(null);
  const [takingAnswers, setTakingAnswers] = useState({});
  const [submitResult, setSubmitResult] = useState(null);

  useEffect(() => {
    if (isStudent) {
      apiFetch(`${BASE}my-progress/`)
        .then((data) => setProgress(data.results || data))
        .catch(() => {});
    }
  }, [isStudent]);

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    apiFetch(`${BASE}courses/`)
      .then((data) => setCourses(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createCourse = (event) => {
    event.preventDefault();
    setSaving(true);

    apiFetch(`${BASE}courses/`, {
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

  const openCourse = (course) => {
    setSelected(course);
    setQuizzes([]);
    setOpenQuiz(null);
    setNotice("");

    apiFetch(`${BASE}courses/${course.id}/lessons/`)
      .then((data) => setLessons(data.results || data))
      .catch(() => setLessons([]));

    apiFetch(`${BASE}quizzes/?course=${course.id}`)
      .then((data) => setQuizzes(data.results || data))
      .catch(() => setQuizzes([]));
  };

  const addLesson = (event) => {
    event.preventDefault();
    if (!selected) return;

    apiFetch(`${BASE}courses/${selected.id}/lessons/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        title: event.target.elements.title.value,
        content: event.target.elements.content.value,
        video_url: event.target.elements.video_url.value,
      }),
    })
      .then(() => openCourse(selected))
      .catch((err) => setError(err.message));
  };

  const toggleComplete = (lessonId) => {
    apiFetch(`${BASE}lessons/${lessonId}/complete/`, { method: "POST" })
      .then(() => openCourse(selected))
      .catch((err) => setError(err.message));
  };

  // ---------- quizzes ----------
  const createQuiz = (event) => {
    event.preventDefault();

    apiFetch(`${BASE}quizzes/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        ...quizForm,
        course: selected.id,
        is_published: true,
      }),
    })
      .then(() => {
        setShowQuizForm(false);
        setQuizForm({ title: "", due_date: "" });
        openCourse(selected);
      })
      .catch((err) => setError(err.message));
  };

  const openQuizTeacher = (quiz) => {
    setOpenQuiz(quiz);
    setAttempts([]);

    apiFetch(`${BASE}quizzes/${quiz.id}/questions/`)
      .then((data) => setQuestions(data.results || data))
      .catch(() => setQuestions([]));

    apiFetch(`${BASE}quizzes/${quiz.id}/attempts/`)
      .then((data) => setAttempts(data.results || data))
      .catch(() => setAttempts([]));
  };

  const addQuestion = (event) => {
    event.preventDefault();
    if (!openQuiz) return;

    apiFetch(`${BASE}quizzes/${openQuiz.id}/questions/new/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(newQ),
    })
      .then(() => {
        setNewQ({
          text: "", option_a: "", option_b: "", option_c: "",
          option_d: "", correct_option: "a", marks: 1,
        });
        openQuizTeacher(openQuiz);
        openCourse(selected);
      })
      .catch((err) => setError(err.message));
  };

  const deleteQuestion = (qid) => {
    apiFetch(`${BASE}questions/${qid}/`, { method: "DELETE" })
      .then(() => {
        openQuizTeacher(openQuiz);
        openCourse(selected);
      })
      .catch((err) => setError(err.message));
  };

  const openQuizStudent = (quiz) => {
    setOpenQuiz(quiz);
    setSubmitResult(null);
    setTakingAnswers({});
    setQuestions([]);

    apiFetch(`${BASE}quizzes/${quiz.id}/my-attempt/`)
      .then((attempt) => setMyAttempt(attempt))
      .catch(() => setMyAttempt(null));

    apiFetch(`${BASE}quizzes/${quiz.id}/questions/`)
      .then((data) => setQuestions(data.results || data))
      .catch(() => setQuestions([]));
  };

  const submitQuiz = () => {
    apiFetch(`${BASE}quizzes/${openQuiz.id}/submit/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ answers: takingAnswers }),
    })
      .then((attempt) => {
        setSubmitResult(attempt);
        setMyAttempt(attempt);
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Online Courses"
        title="Online Courses"
        subtitle={
          isStudent
            ? "Your courses, lessons and quizzes."
            : "Publish lessons and auto-graded quizzes."
        }
        action={
          !isStudent ? (
            <button type="button" className="primary-button" onClick={() => setShowForm((v) => !v)}>
              <Plus size={15} /> New Course
            </button>
          ) : undefined
        }
      />

      {isStudent && progress.length > 0 && (
        <div className="dashboard-grid">
          {progress.slice(0, 4).map((item) => (
            <div key={item.course_id} className="stat-card">
              <strong>{item.progress}%</strong>
              <span>{item.course}</span>
              <small>{item.lessons_done}/{item.lessons_total} lessons</small>
            </div>
          ))}
        </div>
      )}

      {showForm && !isStudent && (
        <div className="panel">
          <PanelHeader title="Create course" />
          <form onSubmit={createCourse} className="filter-row">
            <input required placeholder="Course title *" value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <input placeholder="Description" value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Create"}
            </button>
          </form>
        </div>
      )}

      <div className="panel">
        <PanelHeader title="Courses" subtitle={`${courses.length} available${notice ? ` · ${notice}` : ""}`} />

        <StateArea loading={loading} error={error} onRetry={load}>
          {courses.length === 0 ? (
            <div className="empty-state">
              <BookOpenCheck size={42} />
              <h3>No courses</h3><p>Nothing published yet.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    {!isStudent && <th>Teacher</th>}
                    <th>Class</th><th>Subject</th><th>Lessons</th><th>Status</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {courses.map((course) => (
                    <tr key={course.id}>
                      <td><strong>{course.title}</strong></td>
                      {!isStudent && <td>{course.teacher_name}</td>}
                      <td>{course.class_name || "—"}</td>
                      <td>{course.subject_name || "—"}</td>
                      <td>{course.lesson_count}</td>
                      <td>{course.is_published ? "Published" : "Draft"}</td>
                      <td>
                        <button type="button" className="primary-button" onClick={() => openCourse(course)}>Open</button>
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
        <>
          <div className="panel">
            <PanelHeader
              title={`Lessons — ${selected.title}`}
              subtitle={`${lessons.length} lessons`}
              action={
                <button type="button" className="primary-button" onClick={() => setSelected(null)}>Close</button>
              }
            />

            {lessons.map((lesson) => (
              <div key={lesson.id} style={{ padding: "10px 0", borderBottom: "1px solid #e2e8f0", display: "flex", gap: 12 }}>
                <span style={{ fontWeight: 700 }}>#{lesson.order}</span>
                <div style={{ flex: 1 }}>
                  <strong>{lesson.title}</strong>
                  {lesson.video_url && (
                    <a href={lesson.video_url} target="_blank" rel="noreferrer" style={{ marginLeft: 8 }}>Watch</a>
                  )}
                  {lesson.content && <p>{lesson.content}</p>}
                </div>
                {isStudent && (
                  <button type="button" className="table-action" onClick={() => toggleComplete(lesson.id)}>
                    {lesson.completed ? <CheckCircle2 size={15} color="#16a34a" /> : <Circle size={15} />} Done
                  </button>
                )}
              </div>
            ))}

            {!isStudent && (
              <form onSubmit={addLesson} className="filter-row" style={{ marginTop: 12 }}>
                <input required name="title" placeholder="Lesson title *" />
                <input name="video_url" placeholder="Video URL (optional)" />
                <textarea name="content" placeholder="Lesson content" rows={2} />
                <button className="primary-button">Add lesson</button>
              </form>
            )}
          </div>

          {/* ---------------- QUIZZES ---------------- */}
          <div className="panel">
            <PanelHeader
              title="Quizzes"
              subtitle={`${quizzes.length} in this course`}
              action={
                !isStudent ? (
                  <button type="button" className="primary-button" onClick={() => setShowQuizForm((v) => !v)}>
                    <Plus size={15} /> New Quiz
                  </button>
                ) : undefined
              }
            />

            {showQuizForm && showQuizFormFor(selected, createQuiz, quizForm, setQuizForm)}

            {quizzes.length === 0 && <p>No quizzes yet.</p>}

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th><th>Questions</th><th>Due</th><th>Status</th>
                    {!isStudent && <th>Attempts</th>}
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {quizzes.map((quiz) => (
                    <tr key={quiz.id}>
                      <td><strong>{quiz.title}</strong></td>
                      <td>{quiz.question_count}</td>
                      <td>{quiz.due_date || "—"}</td>
                      <td>{quiz.is_published ? "Published" : "Draft"}</td>
                      {!isStudent && <td>{quiz.attempt_count}</td>}
                      <td>
                        <button
                          type="button"
                          className="primary-button"
                          onClick={() =>
                            isStudent ? openQuizStudent(quiz) : openQuizTeacher(quiz)
                          }
                        >
                          {isStudent ? "Take" : "Manage"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* teacher manage panel */}
            {!isStudent && openQuiz && (
              <div style={{ marginTop: 16 }}>
                <h4>Questions — {openQuiz.title}</h4>

                {questions.map((q) => (
                  <div key={q.id} style={{ padding: "8px 0", borderBottom: "1px solid #e2e8f0", display: "flex", gap: 10 }}>
                    <div style={{ flex: 1 }}>
                      <strong>{q.text}</strong>
                      <small style={{ display: "block" }}>
                        a) {q.option_a} · b) {q.option_b} · c) {q.option_c} · d) {q.option_d}
                        {" "}— <strong>answer: {q.correct_option}</strong> ({q.marks} mk)
                      </small>
                    </div>
                    <button type="button" className="table-action" onClick={() => deleteQuestion(q.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}

                <form onSubmit={addQuestion} className="filter-row" style={{ marginTop: 10 }}>
                  <input required placeholder="Question *" value={newQ.text}
                    onChange={(e) => setNewQ({ ...newQ, text: e.target.value })} />
                  <input required placeholder="Option A" value={newQ.option_a}
                    onChange={(e) => setNewQ({ ...newQ, option_a: e.target.value })} />
                  <input required placeholder="Option B" value={newQ.option_b}
                    onChange={(e) => setNewQ({ ...newQ, option_b: e.target.value })} />
                  <input required placeholder="Option C" value={newQ.option_c}
                    onChange={(e) => setNewQ({ ...newQ, option_c: e.target.value })} />
                  <input required placeholder="Option D" value={newQ.option_d}
                    onChange={(e) => setNewQ({ ...newQ, option_d: e.target.value })} />
                  <select value={newQ.correct_option}
                    onChange={(e) => setNewQ({ ...newQ, correct_option: e.target.value })}>
                    <option value="a">Answer: A</option><option value="b">B</option>
                    <option value="c">C</option><option value="d">D</option>
                  </select>
                  <input type="number" min="1" style={{ width: 70 }} value={newQ.marks}
                    onChange={(e) => setNewQ({ ...newQ, marks: e.target.value })} />
                  <button className="primary-button">Add</button>
                </form>

                <h4 style={{ marginTop: 14 }}>Attempts ({attempts.length})</h4>
                {attempts.length > 0 && (
                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr><th>Student</th><th>Score</th><th>%</th><th>Submitted</th></tr>
                      </thead>
                      <tbody>
                        {attempts.map((a) => (
                          <tr key={a.id}>
                            <td>{a.student_name} ({a.admission_number})</td>
                            <td><strong>{a.score}/{a.total_marks}</strong></td>
                            <td>{a.percentage}%</td>
                            <td>{a.submitted_at?.slice(0, 10)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* student take panel */}
            {isStudent && openQuiz && (
              <div style={{ marginTop: 16 }}>
                {myAttempt && !submitResult ? (
                  <p>
                    You scored <strong>{myAttempt.score}/{myAttempt.total_marks}</strong>{" "}
                    ({myAttempt.percentage}%).
                  </p>
                ) : null}

                {submitResult ? (
                  <p>
                    Submitted! Score:{" "}
                    <strong>
                      {submitResult.score}/{submitResult.total_marks}
                    </strong>{" "}
                    ({submitResult.percentage}%)
                  </p>
                ) : (!myAttempt &&
                  questions.length > 0 && (
                    <>
                      {questions.map((question) => (
                        <div key={question.id} style={{ padding: "10px 0" }}>
                          <strong>{question.text}</strong> ({question.marks} mk)
                          {["a", "b", "c", "d"].map((opt) => (
                            <label key={opt} style={{ display: "block", marginLeft: 14 }}>
                              <input
                                type="radio"
                                name={`q${question.id}`}
                                checked={takingAnswers[String(question.id)] === opt}
                                onChange={() =>
                                  setTakingAnswers({
                                    ...takingAnswers,
                                    [String(question.id)]: opt,
                                  })
                                }
                              />{" "}
                              {question[`option_${opt}`]}
                            </label>
                          ))}
                        </div>
                      ))}

                      <button
                        type="button"
                        className="primary-button"
                        disabled={Object.keys(takingAnswers).length < questions.length}
                        onClick={submitQuiz}
                      >
                        <Send size={15} /> Submit answers
                      </button>
                    </>
                  )
                )}

                {!myAttempt && !submitResult && questions.length === 0 && (
                  <p>No questions yet — check back later.</p>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}

function showQuizFormFor(_selected, onSubmit, quizForm, setQuizForm) {
  return (
    <form onSubmit={onSubmit} className="filter-row">
      <input required placeholder="Quiz title *" value={quizForm.title}
        onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })} />
      <input type="date" value={quizForm.due_date}
        onChange={(e) => setQuizForm({ ...quizForm, due_date: e.target.value })} />
      <button className="primary-button">Create</button>
    </form>
  );
}
