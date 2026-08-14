import { useEffect, useState } from "react";
import { PanelHeader } from "./ui";
import { jsonHeaders } from "../api";

const EXAM_SUBJECTS_URL = "/api/exams/subjects/";
const RESULTS_URL = "/api/exams/results/";
const PRACTICAL_URL = "/api/exams/practical/";
const STUDENTS_URL = "/api/students/";

export default function MarksEntryPanel({ exams, onSaved }) {
  const [exam, setExam] = useState("");
  const [subject, setSubject] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [roster, setRoster] = useState([]);
  const [existing, setExisting] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedExam = exams.find((item) => String(item.id) === String(exam));
  const selectedSubject = subjects.find(
    (item) => String(item.id) === String(subject)
  );

  useEffect(() => {
    if (!exam) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- resets dependent state
      setSubjects([]);
      setSubject("");
      return;
    }

    fetch(`${EXAM_SUBJECTS_URL}?exam=${exam}`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((data) => {
        const list = data.results || data;
        setSubjects(list);
        setSubject(list[0] ? String(list[0].id) : "");
      })
      .catch(() => setSubjects([]));
  }, [exam]);

  const loadMarksEntry = () => {
    if (!exam || !subject) {
      setError("Select an exam and a subject.");
      return;
    }

    setError("");
    setSuccess("");
    setLoading(true);

    const classId = selectedExam?.class_obj;
    const campusId = selectedExam?.campus;

    if (!classId) {
      setError("The selected exam has no class assigned.");
      setLoading(false);
      return;
    }

    const params = new URLSearchParams();
    params.append("status", "active");
    params.append("page", 1);

    if (campusId) {
      params.append("campus", campusId);
    }

    params.append("class_obj", classId);

    const fetchPage = (pageNumber, accumulator) => {
      const pageParams = new URLSearchParams(params);
      pageParams.set("page", pageNumber);

      return fetch(`${STUDENTS_URL}?${pageParams.toString()}`, {
        credentials: "include",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to load students.");
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
      const resParams = new URLSearchParams();
      resParams.append("exam", exam);
      resParams.append("exam_subject", subject);
      resParams.append("page_size", 500);

      return fetch(`${RESULTS_URL}?${resParams.toString()}`, {
        credentials: "include",
      })
        .then((response) => (response.ok ? response.json() : { results: [] }))
        .then((data) => {
          const map = {};

          for (const result of data.results || []) {
            map[result.student] = {
              theory: result.is_absent
                ? null
                : result.obtained_marks,
              practical:
                result.practical_marks?.obtained_marks ?? "",
              remarks: result.remarks || "",
              is_absent: Boolean(result.is_absent),
              theory_id: result.id,
              practical_id: result.practical_marks?.id ?? null,
            };
          }

          return map;
        })
        .catch(() => ({}));
    };

    Promise.all([fetchPage(1, []), loadExisting()])
      .then(([students, map]) => {
        setRoster(students);
        setExisting(map);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const updateField = (studentId, field, value) => {
    setExisting((previous) => ({
      ...previous,
      [studentId]: {
        theory: "",
        practical: "",
        remarks: "",
        is_absent: false,
        theory_id: null,
        practical_id: null,
        ...(previous[studentId] || {}),
        [field]: value,
      },
    }));
  };

  const handleSave = async (event) => {
    event.preventDefault();

    if (!roster.length) {
      setError("Load students before saving marks.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    const theoryErrors = [];
    const practicalErrors = [];
    const createdTheory = {};
    const createdPractical = {};

    for (const student of roster) {
      const entry = existing[student.id] || {};
      const theoryMarks = entry.theory;
      const practicalMarks = entry.practical;
      const isAbsent = Boolean(entry.is_absent);

      if (!isAbsent && theoryMarks !== "" && theoryMarks != null) {
        const payload = {
          exam: Number(exam),
          student: student.id,
          exam_subject: Number(subject),
          obtained_marks: Number(theoryMarks),
          is_absent: false,
          remarks: entry.remarks || "",
        };

        const theoryId = entry.theory_id || createdTheory[student.id];

        try {
          if (theoryId) {
            const response = await fetch(`${RESULTS_URL}${theoryId}/`, {
              method: "PATCH",
              credentials: "include",
              headers: jsonHeaders(),
              body: JSON.stringify(payload),
            });

            if (!response.ok) {
              theoryErrors.push(`${student.full_name}: PATCH failed`);
            }
          } else {
            const response = await fetch(RESULTS_URL, {
              method: "POST",
              credentials: "include",
              headers: jsonHeaders(),
              body: JSON.stringify(payload),
            });

            if (!response.ok) {
              theoryErrors.push(`${student.full_name}: POST failed`);
            } else {
              const data = await response.json();
              createdTheory[student.id] = data.id;
            }
          }
        } catch {
          theoryErrors.push(`${student.full_name}: network error`);
        }
      }

      if (!isAbsent && practicalMarks !== "" && practicalMarks != null) {
        const payload = {
          exam: Number(exam),
          student: student.id,
          exam_subject: Number(subject),
          obtained_marks: Number(practicalMarks),
          maximum_marks: selectedSubject?.maximum_marks || 0,
          passing_marks: selectedSubject?.passing_marks || 0,
          is_absent: false,
          remarks: "",
        };

        const practicalId =
          entry.practical_id || createdPractical[student.id];

        try {
          if (practicalId) {
            const response = await fetch(
              `${PRACTICAL_URL}${practicalId}/`,
              {
                method: "PATCH",
                credentials: "include",
                headers: jsonHeaders(),
                body: JSON.stringify(payload),
              }
            );

            if (!response.ok) {
              practicalErrors.push(`${student.full_name}: PATCH failed`);
            }
          } else {
            const response = await fetch(PRACTICAL_URL, {
              method: "POST",
              credentials: "include",
              headers: jsonHeaders(),
              body: JSON.stringify(payload),
            });

            if (!response.ok) {
              practicalErrors.push(`${student.full_name}: POST failed`);
            } else {
              const data = await response.json();
              createdPractical[student.id] = data.id;
            }
          }
        } catch {
          practicalErrors.push(`${student.full_name}: network error`);
        }
      }
    }

    if (Object.keys(createdTheory).length || Object.keys(createdPractical).length) {
      setExisting((previous) => {
        const next = { ...previous };

        for (const [studentId, id] of Object.entries(createdTheory)) {
          next[studentId] = { ...(next[studentId] || {}), theory_id: id };
        }

        for (const [studentId, id] of Object.entries(createdPractical)) {
          next[studentId] = {
            ...(next[studentId] || {}),
            practical_id: id,
          };
        }

        return next;
      });
    }

    setSaving(false);

    if (theoryErrors.length || practicalErrors.length) {
      const parts = [];

      if (theoryErrors.length) {
        parts.push(`Theory: ${theoryErrors.slice(0, 3).join(", ")}`);
      }

      if (practicalErrors.length) {
        parts.push(`Practical: ${practicalErrors.slice(0, 3).join(", ")}`);
      }

      setError(`Some marks could not be saved. ${parts.join(" | ")}`);
      return;
    }

    setSuccess("Marks saved successfully.");

    if (onSaved) {
      onSaved();
    }
  };

  return (
    <div className="panel">
      <PanelHeader
        title="Enter Marks"
        subtitle="Record theory and practical marks per subject"
      />

      <div className="form-section">
        <div className="form-grid">
          <label>
            Exam
            <select value={exam} onChange={(event) => setExam(event.target.value)}>
              <option value="">Select exam</option>

              {exams.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.class_name || "—"})
                </option>
              ))}
            </select>
          </label>

          <label>
            Subject
            <select
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
            >
              <option value="">Select subject</option>

              {subjects.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.subject_name} (max {item.maximum_marks})
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="filter-row" style={{ marginTop: "14px" }}>
          <button
            type="button"
            className="primary-button"
            onClick={loadMarksEntry}
            disabled={loading}
          >
            {loading ? "Loading students..." : "Load Students"}
          </button>
        </div>
      </div>

      {error && (
        <div className="state-card error">
          <strong>Unable to save marks.</strong>
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="state-card success">
          <strong>{success}</strong>
        </div>
      )}

      {roster.length > 0 && (
        <form onSubmit={handleSave}>
          <div className="table-wrapper" style={{ marginTop: "12px" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>STUDENT</th>
                  <th>ADMISSION NO.</th>
                  <th>ABSENT</th>
                  <th>THEORY MARKS</th>
                  <th>PRACTICAL MARKS</th>
                  <th>REMARKS</th>
                </tr>
              </thead>

              <tbody>
                {roster.map((student) => {
                  const entry = existing[student.id] || {};

                  return (
                    <tr key={student.id}>
                      <td>
                        <strong>{student.full_name || "—"}</strong>
                      </td>

                      <td>{student.admission_number || "—"}</td>

                      <td>
                        <input
                          type="checkbox"
                          checked={Boolean(entry.is_absent)}
                          onChange={(event) =>
                            updateField(student.id, "is_absent", event.target.checked)
                          }
                        />
                      </td>

                      <td>
                        <input
                          type="number"
                          min="0"
                          max={selectedSubject?.maximum_marks || 100}
                          step="0.01"
                          value={entry.is_absent ? "" : (entry.theory ?? "")}
                          disabled={entry.is_absent}
                          onChange={(event) =>
                            updateField(student.id, "theory", event.target.value)
                          }
                          placeholder="—"
                        />
                      </td>

                      <td>
                        <input
                          type="number"
                          min="0"
                          max={selectedSubject?.maximum_marks || 100}
                          step="0.01"
                          value={entry.is_absent ? "" : (entry.practical ?? "")}
                          disabled={entry.is_absent}
                          onChange={(event) =>
                            updateField(student.id, "practical", event.target.value)
                          }
                          placeholder="Optional"
                        />
                      </td>

                      <td>
                        <input
                          type="text"
                          value={entry.remarks || ""}
                          onChange={(event) =>
                            updateField(student.id, "remarks", event.target.value)
                          }
                          placeholder="—"
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="modal-footer">
            <button type="submit" className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save Marks"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
