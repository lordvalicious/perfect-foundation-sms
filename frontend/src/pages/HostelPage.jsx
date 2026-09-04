import { useCallback, useEffect, useState } from "react";
import { BedDouble, Plus } from "lucide-react";
import { PageHeader, PanelHeader, StateArea } from "./ui";
import { apiFetch, authHeaders } from "../api";

const BASE = "/api/hostel/";
const CAMPUSES_URL = "/api/schools/campuses/";

export default function HostelPage() {
  const [tab, setTab] = useState("hostels");
  const [rows, setRows] = useState([]);
  const [students, setStudents] = useState([]);
  const [roomOptions, setRoomOptions] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const [hostelForm, setHostelForm] = useState({
    name: "",
    campus: "",
    warden: "",
    gender: "mixed",
    address: "",
  });

  const loadCampuses = useCallback(() => {
    fetch(CAMPUSES_URL, { credentials: "include" })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setCampuses(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadCampuses();
  }, [loadCampuses]);

  const [roomForm, setRoomForm] = useState({
    hostel: "",
    room_number: "",
    capacity: 4,
  });

  const [allocForm, setAllocForm] = useState({
    room: "",
    student: "",
    start_date: new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    fetch("/api/students/?page_size=1000", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { results: [] }))
      .then((json) => setStudents(json.results || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch(`${BASE}rooms/`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setRoomOptions(data.results || data))
      .catch(() => {});
  }, [rows]);

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    const url =
      tab === "hostels"
        ? `${BASE}hostels/`
        : tab === "rooms"
          ? `${BASE}rooms/`
          : `${BASE}allocations/?status=active`;

    apiFetch(url)
      .then((data) => setRows(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");

    const url =
      tab === "hostels"
        ? `${BASE}hostels/`
        : tab === "rooms"
          ? `${BASE}rooms/`
          : `${BASE}allocations/`;

    const body =
      tab === "hostels"
        ? hostelForm
        : tab === "rooms"
          ? roomForm
          : allocForm;

    apiFetch(url, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    })
      .then(() => {
        setShowForm(false);
        setNotice("Saved.");
        load();
      })
      .catch((err) => setFormError(err.message))
      .finally(() => setSaving(false));
  };

  const vacate = (id) => {
    apiFetch(`${BASE}allocations/${id}/vacate/`, { method: "POST" })
      .then(() => {
        setNotice("Room vacated.");
        load();
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Hostel"
        title="Hostel Management"
        subtitle="Boarding houses, rooms and student allocations."
        action={
          <button
            type="button"
            className="primary-button"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus size={15} />
            Add
          </button>
        }
      />

      <div className="tabs">
        {[
          ["hostels", "Hostels"],
          ["rooms", "Rooms"],
          ["allocations", "Allocations"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={`tab-button ${tab === key ? "active" : ""}`}
            onClick={() => setTab(key)}
          >
            <BedDouble size={15} />
            {label}
          </button>
        ))}
      </div>

      <div className="panel">
        <PanelHeader
          title={notice || "live data"}
          subtitle={`${rows.length} records`}
        />

        <StateArea loading={loading} error={error} onRetry={load}>
          {showForm && (
            <form onSubmit={submit} className="filter-row">
              {tab === "hostels" && (
                <>
                  <input
                    required
                    placeholder="Hostel name *"
                    value={hostelForm.name}
                    onChange={(e) =>
                      setHostelForm({ ...hostelForm, name: e.target.value })
                    }
                  />
                  <select
                    required
                    value={hostelForm.campus}
                    onChange={(e) =>
                      setHostelForm({ ...hostelForm, campus: e.target.value })
                    }
                  >
                    <option value="">Campus *</option>
                    {campuses.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                  <input
                    placeholder="Warden"
                    value={hostelForm.warden}
                    onChange={(e) =>
                      setHostelForm({ ...hostelForm, warden: e.target.value })
                    }
                  />
                  <select
                    value={hostelForm.gender}
                    onChange={(e) =>
                      setHostelForm({ ...hostelForm, gender: e.target.value })
                    }
                  >
                    <option value="boys">Boys</option>
                    <option value="girls">Girls</option>
                    <option value="mixed">Mixed</option>
                  </select>
                  <input
                    placeholder="Address"
                    value={hostelForm.address}
                    onChange={(e) =>
                      setHostelForm({ ...hostelForm, address: e.target.value })
                    }
                  />
                </>
              )}

              {tab === "rooms" && (
                <>
                  <select
                    required
                    value={roomForm.hostel}
                    onChange={(e) =>
                      setRoomForm({ ...roomForm, hostel: e.target.value })
                    }
                  >
                    <option value="">Hostel...</option>
                    {rows.map((h) => (
                      <option key={h.id} value={h.id}>{h.name}</option>
                    ))}
                  </select>
                  <input
                    required
                    placeholder="Room no. *"
                    value={roomForm.room_number}
                    onChange={(e) =>
                      setRoomForm({ ...roomForm, room_number: e.target.value })
                    }
                  />
                  <input
                    type="number"
                    min="1"
                    value={roomForm.capacity}
                    onChange={(e) =>
                      setRoomForm({ ...roomForm, capacity: e.target.value })
                    }
                  />
                </>
              )}

              {tab === "allocations" && (
                <>
                  <select
                    required
                    value={allocForm.room}
                    onChange={(e) =>
                      setAllocForm({ ...allocForm, room: e.target.value })
                    }
                  >
                    <option value="">Room...</option>
                    {roomOptions.map((room) => (
                      <option key={room.id} value={room.id}>
                        {room.hostel_name || `Hostel #${room.hostel}`} - {room.room_number}
                      </option>
                    ))}
                  </select>

                  <select
                    required
                    value={allocForm.student}
                    onChange={(e) =>
                      setAllocForm({ ...allocForm, student: e.target.value })
                    }
                  >
                    <option value="">Student...</option>
                    {students.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.full_name} ({s.admission_number})
                      </option>
                    ))}
                  </select>

                  <input
                    type="date"
                    required
                    value={allocForm.start_date}
                    onChange={(e) =>
                      setAllocForm({ ...allocForm, start_date: e.target.value })
                    }
                  />
                </>
              )}

              <button className="primary-button" disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </button>
            </form>
          )}

          {formError && (
            <div className="state-card error">{formError}</div>
          )}

          {rows.length === 0 ? (
            <div className="empty-state">
              <BedDouble size={42} />
              <h3>Nothing here yet</h3>
              <p>Add records using the button above.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              {tab === "hostels" && (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th><th>Campus</th><th>Warden</th>
                      <th>Gender</th><th>Occupied / Capacity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <td><strong>{row.name}</strong></td>
                        <td>{row.campus_name}</td>
                        <td>{row.warden || "—"}</td>
                        <td>{row.gender}</td>
                        <td>{row.occupied ?? 0} / {row.total_capacity ?? 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {tab === "rooms" && (
                <table className="data-table">
                  <thead>
                    <tr><th>Hostel</th><th>Room</th><th>Capacity</th><th>Occupied</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <td>{row.hostel_name || `#${row.hostel}`}</td>
                        <td><strong>{row.room_number}</strong></td>
                        <td>{row.capacity}</td>
                        <td>{row.occupied}</td>
                        <td>{row.is_full ? "Full" : "Available"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {tab === "allocations" && (
                <table className="data-table">
                  <thead>
                    <tr><th>Student</th><th>Admission No</th><th>Room</th><th>Since</th><th></th></tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <td><strong>{row.student_name}</strong></td>
                        <td>{row.admission_number}</td>
                        <td>{row.room_label}</td>
                        <td>{row.start_date}</td>
                        <td>
                          <button
                            type="button"
                            className="table-action"
                            onClick={() => vacate(row.id)}
                          >
                            Vacate
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
