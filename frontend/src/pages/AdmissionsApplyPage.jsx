import { useEffect, useState } from "react";
import { CheckCircle2, GraduationCap } from "lucide-react";
import { authHeaders } from "../api";

export default function AdmissionsApplyPage() {
  const [options, setOptions] = useState(null);
  const [form, setForm] = useState({
    first_name: "",
    middle_name: "",
    last_name: "",
    gender: "",
    date_of_birth: "",
    campus: "",
    class_obj: "",
    section: "",
    guardian_name: "",
    guardian_phone: "",
    phone: "",
    address: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch("/api/students/admissions/public/options/")
      .then((r) => (r.ok ? r.json() : null))
      .then(setOptions)
      .catch(() => setOptions(null));
  }, []);

  const set = (field) => (event) =>
    setForm({ ...form, [field]: event.target.value });

  const classesForCampus = (options?.classes || []).filter(
    (c) => String(c.campus_id) === String(form.campus)
  );

  const sectionsForClass = (options?.sections || []).filter(
    (s) => String(s.class_obj_id) === String(form.class_obj)
  );

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await fetch("/api/auth/csrf/", { credentials: "include" });

      const response = await fetch(
        "/api/students/admissions/public/apply/",
        {
          method: "POST",
          credentials: "include",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify(form),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Could not submit the application.");
      } else {
        setResult(data);
        window.scrollTo({ top: 0 });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "flex-start",
      padding: "40px 16px",
      background: "#f1f5f9",
    }}>
      <div className="panel" style={{ maxWidth: 620, width: "100%", padding: 28 }}>
        <div style={{ textAlign: "center", marginBottom: 18 }}>
          <GraduationCap size={34} />
          <h2>Admission Application</h2>
          <p className="subtitle">
            Fill in the form and the school office will contact you.
          </p>
        </div>

        {result ? (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <CheckCircle2 size={44} color="#16a34a" />
            <h3 style={{ marginTop: 12 }}>Application submitted</h3>
            <p>
              Your application number is{" "}
              <strong>{result.application_number}</strong>. Please keep it
              for reference.
            </p>
          </div>
        ) : (
          <form onSubmit={submit}>
            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">Student first name *</label>
              <input className="form-input" required value={form.first_name} onChange={set("first_name")} />
            </div>

            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Middle name</label>
                <input className="form-input" value={form.middle_name} onChange={set("middle_name")} />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Last name *</label>
                <input className="form-input" required value={form.last_name} onChange={set("last_name")} />
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Gender *</label>
                <select className="form-input" required value={form.gender} onChange={set("gender")}>
                  <option value="">Select...</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </select>
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Date of birth *</label>
                <input className="form-input" type="date" required value={form.date_of_birth} onChange={set("date_of_birth")} />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">Campus *</label>
              <select className="form-input" required value={form.campus} onChange={set("campus")}>
                <option value="">Select campus...</option>
                {(options?.campuses || []).map((campus) => (
                  <option key={campus.id} value={campus.id}>{campus.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">Applying for class *</label>
              <select
                className="form-input"
                required
                value={form.class_obj}
                onChange={set("class_obj")}
                disabled={!form.campus}
              >
                <option value="">Select class...</option>
                {classesForCampus.map((cls) => (
                  <option key={cls.id} value={cls.id}>{cls.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">Section preference</label>
              <select
                className="form-input"
                value={form.section}
                onChange={set("section")}
                disabled={!form.class_obj}
              >
                <option value="">No preference</option>
                {sectionsForClass.map((section) => (
                  <option key={section.id} value={section.id}>{section.name}</option>
                ))}
              </select>
            </div>

            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Guardian name *</label>
                <input className="form-input" required value={form.guardian_name} onChange={set("guardian_name")} />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">Guardian phone *</label>
                <input className="form-input" required value={form.guardian_phone} onChange={set("guardian_phone")} />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">Contact phone</label>
              <input className="form-input" value={form.phone} onChange={set("phone")} />
            </div>

            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label">Address</label>
              <textarea className="form-input" rows={2} value={form.address} onChange={set("address")} />
            </div>

            {error && (
              <div className="state-card error" style={{ marginBottom: 14 }}>{error}</div>
            )}

            <button
              type="submit"
              className="primary-button"
              disabled={submitting}
              style={{ width: "100%", justifyContent: "center" }}
            >
              {submitting ? "Submitting..." : "Submit Application"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
