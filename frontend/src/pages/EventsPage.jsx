import { useCallback, useEffect, useState } from "react";
import { CalendarDays, MapPin, Plus, Users, X } from "lucide-react";
import { useAuth } from "../auth";
import { PageHeader, PanelHeader, StateArea } from "./ui";

const EVENT_STATUS = [
  { value: "draft", label: "Draft" },
  { value: "published", label: "Published" },
  { value: "cancelled", label: "Cancelled" },
];

const AUDIENCE_TYPES = [
  { value: "everyone", label: "Everyone" },
  { value: "students", label: "Students" },
  { value: "teachers", label: "Teachers" },
  { value: "staff", label: "Staff" },
  { value: "class", label: "Class" },
];

const EMPTY_FORM = {
  title: "",
  description: "",
  location: "",
  start_datetime: "",
  end_datetime: "",
  status: "published",
  audience_type: "everyone",
};

function formatDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);

  return date.toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function EventsPage() {
  const { hasRole } = useAuth();

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const canManage = hasRole([
    "super_admin",
    "admin",
    "academic",
    "teacher",
    "staff",
  ]);

  const loadEvents = useCallback(() => {
    setLoading(true);
    setError("");

    return fetch("/api/events/", {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load events.");
        }

        return response.json();
      })
      .then((data) => {
        setEvents(Array.isArray(data) ? data : []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fires a debounced data fetch
    loadEvents();
  }, [loadEvents]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSaving(true);
    setError("");

    try {
      const response = await fetch("/api/events/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: form.title,
          description: form.description,
          location: form.location,
          start_datetime: form.start_datetime,
          end_datetime: form.end_datetime,
          status: form.status,
          audiences: [
            {
              audience_type: form.audience_type,
            },
          ],
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const message = Object.entries(data)
          .map(([field, value]) => {
            const text = Array.isArray(value)
              ? value.join(", ")
              : String(value);

            return `${field}: ${text}`;
          })
          .join(" | ");

        throw new Error(message || "Unable to create event.");
      }

      setShowForm(false);
      setForm(EMPTY_FORM);
      await loadEvents();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleRsvp = async (eventId, response) => {
    await fetch(`/api/events/${eventId}/rsvp/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ response }),
    });

    await loadEvents();
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Events"
        title="Events"
        subtitle="Announcements, functions and school activities."
      />

      {error && (
        <div className="state-card error">
          <strong>Unable to complete request.</strong>
          <span>{error}</span>
          <button
            className="secondary-button"
            onClick={loadEvents}
          >
            Try Again
          </button>
        </div>
      )}

      <div className="panel">
        <PanelHeader
          title="Event List"
          subtitle="events found"
          count={events.length}
          action={
            canManage && (
              <button
                className="primary-button"
                onClick={() => setShowForm(true)}
              >
                + Add Event
              </button>
            )
          }
        />

        <StateArea loading={loading} error={error}>
          {events.length === 0 ? (
            <div className="empty-state">
              <CalendarDays size={42} />
              <h3>No events found</h3>
              <p>No events have been created yet.</p>
            </div>
          ) : (
            <div className="events-list">
              {events.map((event) => (
                <div className="event-card" key={event.id}>
                  <div className="event-card-body">
                    <div className="event-card-head">
                      <h3>{event.title}</h3>

                      <span
                        className={`status-badge ${
                          event.status === "cancelled"
                            ? "inactive"
                            : event.status === "draft"
                            ? "warn"
                            : "active"
                        }`}
                      >
                        {event.status_label ||
                          event.status}
                      </span>
                    </div>

                    <p>{event.description || "No description."}</p>

                    <div className="event-meta">
                      <span>
                        <CalendarDays size={15} />
                        {formatDateTime(
                          event.start_datetime
                        )}{" "}
                        — {formatDateTime(event.end_datetime)}
                      </span>

                      {event.location && (
                        <span>
                          <MapPin size={15} />
                          {event.location}
                        </span>
                      )}

                      <span>
                        <Users size={15} />
                        {event.rsvp_count} attending
                      </span>
                    </div>
                  </div>

                  <div className="event-card-actions">
                    {event.my_rsvp === "yes" ? (
                      <button
                        className="secondary-button"
                        onClick={() =>
                          handleRsvp(event.id, "no")
                        }
                      >
                        Cancel RSVP
                      </button>
                    ) : (
                      <button
                        className="primary-button"
                        onClick={() =>
                          handleRsvp(event.id, "yes")
                        }
                      >
                        Attend
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </StateArea>
      </div>

      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setShowForm(false);
            }
          }}
        >
          <div className="teacher-modal event-modal">
            <div className="modal-header">
              <div>
                <h3>Add Event</h3>
                <p>Create a new school event.</p>
              </div>

              <button
                className="modal-close"
                onClick={() => setShowForm(false)}
                disabled={saving}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-section">
                <h4>Event Details</h4>

                <div className="form-grid">
                  <label className="form-span">
                    Title
                    <input
                      name="title"
                      value={form.title}
                      onChange={handleChange}
                      placeholder="Annual Sports Day"
                      required
                    />
                  </label>

                  <label className="form-span">
                    Description
                    <textarea
                      name="description"
                      value={form.description}
                      onChange={handleChange}
                      placeholder="Details about the event..."
                      rows="3"
                    />
                  </label>

                  <label>
                    Location
                    <input
                      name="location"
                      value={form.location}
                      onChange={handleChange}
                      placeholder="Main Ground"
                    />
                  </label>

                  <label>
                    Status
                    <select
                      name="status"
                      value={form.status}
                      onChange={handleChange}
                    >
                      {EVENT_STATUS.map((item) => (
                        <option
                          key={item.value}
                          value={item.value}
                        >
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Start Date & Time
                    <input
                      type="datetime-local"
                      name="start_datetime"
                      value={form.start_datetime}
                      onChange={handleChange}
                      required
                    />
                  </label>

                  <label>
                    End Date & Time
                    <input
                      type="datetime-local"
                      name="end_datetime"
                      value={form.end_datetime}
                      onChange={handleChange}
                      required
                    />
                  </label>

                  <label>
                    Audience
                    <select
                      name="audience_type"
                      value={form.audience_type}
                      onChange={handleChange}
                    >
                      {AUDIENCE_TYPES.map((item) => (
                        <option
                          key={item.value}
                          value={item.value}
                        >
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowForm(false)}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  <Plus size={17} />
                  {saving ? "Creating..." : "Create Event"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
