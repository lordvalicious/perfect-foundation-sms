import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { apiFetch } from "../api";

const CAMPUSES_URL = "/api/schools/campuses/";
const YEARS_URL = "/api/schools/academic-years/";
const TERMS_URL = "/api/schools/terms/";
const CLASSES_URL = "/api/schools/classes/?page_size=500";

const EXAM_TYPES = [
  ["monthly", "Monthly Test"],
  ["midterm", "Mid-Term"],
  ["final", "Final-Term"],
  ["annual", "Annual"],
];

const EXAM_STATUSES = [
  ["draft", "Draft"],
  ["scheduled", "Scheduled"],
  ["completed", "Completed"],
];

function toList(data) {
  return Array.isArray(data) ? data : data.results || [];
}

function emptyForm() {
  return {
    name: "",
    exam_type: "",
    campus: "",
    academic_year: "",
    term: "",
    class_obj: "",
    start_date: "",
    end_date: "",
    status: "draft",
  };
}

export default function ExamFormModal({ open, exam, onClose, onSaved }) {
  const [form, setForm] = useState(emptyForm());
  const [campuses, setCampuses] = useState([]);
  const [years, setYears] = useState([]);
  const [terms, setTerms] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingRefs, setLoadingRefs] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    setForm(
      exam
        ? {
            name: exam.name || "",
            exam_type: exam.exam_type || "",
            campus: exam.campus || "",
            academic_year: exam.academic_year || "",
            term: exam.term || "",
            class_obj: exam.class_obj || "",
            start_date: exam.start_date || "",
            end_date: exam.end_date || "",
            status: exam.status || "draft",
          }
        : emptyForm()
    );

    setError("");
    setLoadingRefs(true);

    const toListOrEmpty = (response) =>
      response.ok ? response.json() : [];

    Promise.all([
      fetch(CAMPUSES_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(YEARS_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(TERMS_URL, { credentials: "include" }).then(toListOrEmpty),
      fetch(CLASSES_URL, { credentials: "include" }).then(toListOrEmpty),
    ])
      .then(([c, y, t, cl]) => {
        setCampuses(toList(c));
        setYears(toList(y));
        setTerms(toList(t));
        setClasses(toList(cl));

        if (!exam) {
          const activeYear = toList(y).find((item) => item.status === "active");
          setForm((current) => ({
            ...current,
            academic_year: current.academic_year || activeYear?.id || "",
          }));
        }
      })
      .catch(() => setError("Failed to load campuses and classes."))
      .finally(() => setLoadingRefs(false));

    return undefined;
  }, [open, exam]);

  if (!open) {
    return null;
  }

  const campusClasses = classes.filter(
    (klass) => String(form.campus) === String(klass.campus)
  );

  const yearTerms = terms.filter(
    (term) => String(form.academic_year) === String(term.academic_year)
  );

  const setField = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }));

  const handleCampusChange = (value) =>
    setForm((current) => ({
      ...current,
      campus: value,
      class_obj: "",
    }));

  const handleYearChange = (value) =>
    setForm((current) => ({
      ...current,
      academic_year: value,
      term: "",
    }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = {
        name: form.name.trim(),
        exam_type: form.exam_type,
        academic_year: form.academic_year,
        campus: form.campus,
        class_obj: form.class_obj,
        start_date: form.start_date,
        end_date: form.end_date,
        status: form.status,
        term: form.term || null,
      };

      if (exam) {
        await apiFetch(
          `/api/exams/${exam.id}/`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
          "Failed to update the exam."
        );
      } else {
        await apiFetch(
          "/api/exams/",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
          "Failed to create the exam."
        );
      }

      onSaved();
      onClose();
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !loading) onClose();
      }}
    >
      <div className="modal">
        <div className="modal-header">
          <div>
            <h3>{exam ? "Edit Exam" : "New Exam"}</h3>
            <p>
              {exam
                ? "Update the examination details."
                : "Create an examination for a class."}
            </p>
          </div>

          <button
            className="modal-close"
            onClick={onClose}
            disabled={loading}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-section">
              <h4>Exam details</h4>

              <div className="form-grid">
                <label>
                  Exam name
                  <input
                    type="text"
                    required
                    placeholder="e.g. 2026 Mid-Term"
                    value={form.name}
                    onChange={(event) => setField("name", event.target.value)}
                  />
                </label>

                <label>
                  Exam type
                  <select
                    required
                    value={form.exam_type}
                    onChange={(event) =>
                      setField("exam_type", event.target.value)
                    }
                  >
                    <option value="">Select type</option>

                    {EXAM_TYPES.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Academic year
                  <select
                    required
                    value={form.academic_year}
                    onChange={(event) =>
                      handleYearChange(event.target.value)
                    }
                    disabled={loadingRefs}
                  >
                    <option value="">Select year</option>

                    {years.map((year) => (
                      <option key={year.id} value={year.id}>
                        {year.name}
                        {year.status === "active" ? " (active)" : ""}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Term (optional)
                  <select
                    value={form.term}
                    onChange={(event) => setField("term", event.target.value)}
                    disabled={loadingRefs || !form.academic_year}
                  >
                    <option value="">Entire academic year</option>

                    {yearTerms.map((term) => (
                      <option key={term.id} value={term.id}>
                        {term.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Campus
                  <select
                    required
                    value={form.campus}
                    onChange={(event) =>
                      handleCampusChange(event.target.value)
                    }
                    disabled={loadingRefs}
                  >
                    <option value="">Select campus</option>

                    {campuses.map((campus) => (
                      <option key={campus.id} value={campus.id}>
                        {campus.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Class
                  <select
                    required
                    value={form.class_obj}
                    onChange={(event) =>
                      setField("class_obj", event.target.value)
                    }
                    disabled={loadingRefs || !form.campus}
                  >
                    <option value="">Select class</option>

                    {campusClasses.map((klass) => (
                      <option key={klass.id} value={klass.id}>
                        {klass.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Start date
                  <input
                    type="date"
                    required
                    value={form.start_date}
                    onChange={(event) =>
                      setField("start_date", event.target.value)
                    }
                  />
                </label>

                <label>
                  End date
                  <input
                    type="date"
                    required
                    value={form.end_date}
                    onChange={(event) =>
                      setField("end_date", event.target.value)
                    }
                  />
                </label>

                {exam && (
                  <label>
                    Status
                    <select
                      value={form.status}
                      onChange={(event) => setField("status", event.target.value)}
                    >
                      {EXAM_STATUSES.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <div className="modal-footer">
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={
                loading ||
                loadingRefs ||
                !form.name.trim() ||
                !form.exam_type ||
                !form.academic_year ||
                !form.campus ||
                !form.class_obj ||
                !form.start_date ||
                !form.end_date
              }
            >
              {loading
                ? "Saving..."
                : exam
                  ? "Save changes"
                  : "Create exam"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}