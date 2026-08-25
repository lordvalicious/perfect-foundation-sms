import { useState } from "react";
import { Building2, BookOpen, Users, LayoutGrid, Plus } from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  StatusBadge,
} from "./ui";
import { apiFetch, authHeaders } from "../api";

const API_URL = "/api/schools/campuses/";

export default function CampusesPage() {
  const { rows, count, loading, error, refresh } =
    useApiList(API_URL);

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState({
    name: "",
    city: "",
    address: "",
  });

  const submit = (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");

    apiFetch(API_URL, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(form),
    })
      .then(() => {
        setShowForm(false);
        setForm({ name: "", city: "", address: "" });
        refresh(new URLSearchParams());
      })
      .catch((err) => setFormError(err.message))
      .finally(() => setSaving(false));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Campuses"
        title="Campuses"
        subtitle="Manage campuses and their statistics."
        action={
          <button
            type="button"
            className="primary-button"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus size={15} />
            Add Campus
          </button>
        }
      />

      {showForm && (
        <div className="panel">
          <PanelHeader
            title="Add a new campus"
            subtitle="Campuses are created under your school automatically."
          />
          <form onSubmit={submit} className="filter-row">
            <input
              required
              placeholder="Campus name *"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              placeholder="City"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
            />
            <input
              placeholder="Address"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save Campus"}
            </button>
          </form>
          {formError && (
            <div className="state-card error" style={{ marginTop: 10 }}>
              {formError}
            </div>
          )}
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Campus List"
          subtitle="campuses found"
          count={count}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => refresh(new URLSearchParams())}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={Building2}
              title="No campuses found"
              message="Click 'Add Campus' to create your first campus."
            />
          ) : (
            <div className="campuses-grid">
              {rows.map((campus) => (
                <div className="campus-card" key={campus.id}>
                  <div className="campus-card-head">
                    <div className="campus-card-icon">
                      <Building2 size={22} />
                    </div>

                    <div>
                      <strong>{campus.name}</strong>

                      <span>
                        {[campus.city, campus.address]
                          .filter(Boolean)
                          .join(", ") || "—"}
                      </span>
                    </div>

                    <StatusBadge status={campus.status} />
                  </div>

                  <div className="campus-stats">
                    <div>
                      <Users size={17} />
                      <strong>
                        {campus.student_count ?? 0}
                      </strong>
                      <span>Students</span>
                    </div>

                    <div>
                      <BookOpen size={17} />
                      <strong>
                        {campus.class_count ?? 0}
                      </strong>
                      <span>Classes</span>
                    </div>

                    <div>
                      <LayoutGrid size={17} />
                      <strong>
                        {campus.section_count ?? 0}
                      </strong>
                      <span>Sections</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}