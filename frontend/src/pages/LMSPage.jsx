import { useCallback, useEffect, useState } from "react";
import { BookOpenCheck, CheckCircle2, Circle, Plus } from "lucide-react";
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
    setNotice("");

    apiFetch(`${BASE}courses/${course.id}/lessons/`)
      .then((data) => setLessons(data.results || data))
      .catch(() => setLessons([]));
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

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Online Courses"
        title="Online Courses"
        subtitle={
          isStudent
            ? "Your courses and lesson progress."
            : "Publish lessons your class can work through online."
        }
        action={
          !isStudent ? (
            <button
              type="button"
              className="primary-button"
              onClick={() => setShowForm((v) => !v)}
            >
              <Plus size={15} />
              New Course
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
              <small>
                {item.lessons_done}/{item.lessons_total} lessons
              </small>
            </div>
          ))}
        </div>
      )}

      {showForm && !isStudent && (
        <div className="panel">
          <PanelHeader title="Create course" />
          <form onSubmit={createCourse} className="filter-row">
            <input
              required
              placeholder="Course title *"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <input
              placeholder="Description"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />
            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Create"}
            </button>
          </form>
          {error && <div className="state-card error">{error}</div>}
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Courses"
          subtitle={`${courses.length} available${notice ? ` · ${notice}` : ""}`}
        />

        <StateArea loading={loading} error={error} onRetry={load}>
          {courses.length === 0 ? (
            <div className="empty-state">
              <BookOpenCheck size={42} />
              <h3>No courses</h3>
              <p>Nothing published yet.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    {!isStudent && <th>Teacher</th>}
                    <th>Class</th>
                    <th>Subject</th>
                    <th>Lessons</th>
                    <th>Status</th>
                    <th></th>
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
                      <td>
                        {course.is_published ? "Published" : "Draft"}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="primary-button"
                          onClick={() => openCourse(course)}
                        >
                          Open
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
            subtitle={`${lessons.length} lessons`}
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

          {lessons.length === 0 && <p>No lessons yet.</p>}

          {lessons.map((lesson) => (
            <div
              key={lesson.id}
              style={{
                padding: "10px 0",
                borderBottom: "1px solid #e2e8f0",
                display: "flex",
                gap: 12,
                alignItems: "flex-start",
              }}
            >
              <span style={{ fontWeight: 700 }}>#{lesson.order}</span>
              <div style={{ flex: 1 }}>
                <strong>{lesson.title}</strong>
                {lesson.video_url && (
                  <a
                    href={lesson.video_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ marginLeft: 8 }}
                  >
                    Watch
                  </a>
                )}
                {lesson.content && <p>{lesson.content}</p>}
              </div>

              {isStudent && (
                <button
                  type="button"
                  className="table-action"
                  onClick={() => toggleComplete(lesson.id)}
                >
                  {lesson.completed ? (
                    <CheckCircle2 size={15} color="#16a34a" />
                  ) : (
                    <Circle size={15} />
                  )}
                  Done
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
      )}
    </section>
  );
}
