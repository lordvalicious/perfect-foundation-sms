import { useState, useEffect, useCallback } from "react";
import { Bus, Car, MapPin, UsersRound, Plus, Pencil, Trash2, X } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, EmptyState, StatusBadge } from "./ui";
import { formatDate } from "./format";
import { apiFetch, jsonHeaders } from "../api";

const BASE = "/api/transport/";
const CAMPUSES_URL = "/api/schools/campuses/";

const ENDPOINTS = {
  vehicles: { url: "vehicles/", icon: Car, title: "Vehicles" },
  drivers: { url: "drivers/", icon: UsersRound, title: "Drivers" },
  routes: { url: "routes/", icon: MapPin, title: "Routes" },
  assignments: { url: "assignments/", icon: Bus, title: "Assignments" },
};

const VEHICLE_STATUS_CHOICES = [
  { value: "operational", label: "Operational" },
  { value: "maintenance", label: "In Maintenance" },
  { value: "out_of_service", label: "Out of Service" },
];

const EMPTY_VEHICLE_FORM = {
  plate_number: "",
  campus: "",
  model: "",
  capacity: 30,
  status: "operational",
  notes: "",
};

export default function TransportPage() {
  const [tab, setTab] = useState("vehicles");
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_VEHICLE_FORM);

  const [campuses, setCampuses] = useState([]);

  const loadCampuses = useCallback(() => {
    fetch(CAMPUSES_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setCampuses(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadCampuses();
  }, [loadCampuses]);

  const load = (key) => {
    const config = ENDPOINTS[key];

    setLoading(true);
    setError("");

    fetch(`${BASE}${config.url}`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => {
        setData((previous) => ({
          ...previous,
          [key]: json.results || json,
        }));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const switchTab = (key) => {
    setTab(key);

    if (data[key] === undefined) {
      load(key);
    }
  };

  const rows = data[tab] || [];

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
    setForm(EMPTY_VEHICLE_FORM);
  };

  const openAddVehicle = () => {
    setEditing(null);
    setForm(EMPTY_VEHICLE_FORM);
    setShowForm(true);
  };

  const openEditVehicle = (vehicle) => {
    setEditing(vehicle);
    setForm({
      plate_number: vehicle.plate_number || "",
      campus: vehicle.campus ?? "",
      model: vehicle.model || "",
      capacity: vehicle.capacity ?? 30,
      status: vehicle.status || "operational",
      notes: vehicle.notes || "",
    });
    setShowForm(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);

    const payload = {
      plate_number: form.plate_number,
      campus: form.campus || null,
      model: form.model,
      capacity: Number(form.capacity) || 30,
      status: form.status,
      notes: form.notes,
    };

    try {
      const isEditing = Boolean(editing);
      const url = isEditing ? `${BASE}vehicles/${editing.id}/` : `${BASE}vehicles/`;

      await apiFetch(url, {
        method: isEditing ? "PATCH" : "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      }, `Unable to ${isEditing ? "update" : "create"} vehicle.`);

      closeForm();
      setMessage(isEditing ? "Vehicle updated successfully." : "Vehicle created successfully.");
      load("vehicles");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteVehicle = async (vehicle) => {
    if (!window.confirm(`Delete vehicle "${vehicle.plate_number}"? This cannot be undone.`)) return;

    setError("");

    try {
      await apiFetch(`${BASE}vehicles/${vehicle.id}/`, {
        method: "DELETE",
        headers: jsonHeaders(),
      }, "Unable to delete vehicle.");

      setMessage("Vehicle deleted successfully.");
      load("vehicles");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Transport"
        title="Transport"
        subtitle="Manage vehicles, drivers, routes, and student transport assignments."
        action={
          <button type="button" className="primary-button" onClick={openAddVehicle}>
            <Plus size={15} /> Add Vehicle
          </button>
        }
      />

      {message && (
        <div className="state-card success">
          <strong>{message}</strong>
        </div>
      )}

      <div className="tabs">
        {Object.entries(ENDPOINTS).map(([key, config]) => {
          const Icon = config.icon;

          return (
            <button
              key={key}
              className={`tab-button ${tab === key ? "active" : ""}`}
              onClick={() => switchTab(key)}
            >
              <Icon size={15} />
              {config.title}
            </button>
          );
        })}
      </div>

      <div className="panel">
        <PanelHeader
          title={ENDPOINTS[tab].title}
          subtitle="records found"
          count={rows.length || null}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => load(tab)}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={ENDPOINTS[tab].icon}
              title={`No ${ENDPOINTS[tab].title.toLowerCase()} found`}
              message="Records will appear here once added."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  {tab === "vehicles" && (
                    <tr>
                      <th>PLATE NUMBER</th>
                      <th>MODEL</th>
                      <th>CAPACITY</th>
                      <th>STATUS</th>
                      <th>NOTES</th>
                      <th>ACTIONS</th>
                    </tr>
                  )}

                  {tab === "drivers" && (
                    <tr>
                      <th>NAME</th>
                      <th>LICENSE NUMBER</th>
                      <th>PHONE</th>
                      <th>STATUS</th>
                    </tr>
                  )}

                  {tab === "routes" && (
                    <tr>
                      <th>NAME</th>
                      <th>START</th>
                      <th>END</th>
                      <th>VEHICLE</th>
                      <th>DRIVER</th>
                      <th>STOPS</th>
                      <th>STATUS</th>
                    </tr>
                  )}

                  {tab === "assignments" && (
                    <tr>
                      <th>STUDENT</th>
                      <th>ADMISSION NO.</th>
                      <th>ROUTE</th>
                      <th>STOP</th>
                      <th>STATUS</th>
                      <th>ASSIGNED</th>
                    </tr>
                  )}
                </thead>

                <tbody>
                  {tab === "vehicles" &&
                    rows.map((vehicle) => (
                      <tr key={vehicle.id}>
                        <td>
                          <strong>{vehicle.plate_number}</strong>
                        </td>

                        <td>{vehicle.model || "\u2014"}</td>

                        <td>{vehicle.capacity ?? 0}</td>

                        <td>
                          <StatusBadge
                            status={
                              vehicle.status === "operational"
                                ? "active"
                                : vehicle.status
                            }
                            label={vehicle.status_display}
                          />
                        </td>

                        <td>{vehicle.notes || "\u2014"}</td>

                        <td>
                          <button
                            type="button"
                            className="table-action"
                            onClick={() => openEditVehicle(vehicle)}
                          >
                            <Pencil size={13} />
                            Edit
                          </button>
                          <button
                            type="button"
                            className="table-action danger"
                            onClick={() => handleDeleteVehicle(vehicle)}
                          >
                            <Trash2 size={13} />
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}

                  {tab === "drivers" &&
                    rows.map((driver) => (
                      <tr key={driver.id}>
                        <td>
                          <strong>{driver.full_name || "\u2014"}</strong>
                        </td>

                        <td>{driver.license_number || "\u2014"}</td>

                        <td>{driver.phone || "\u2014"}</td>

                        <td>
                          <span
                            className={`status-badge ${
                              driver.status ? "active" : "inactive"
                            }`}
                          >
                            {driver.status ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))}

                  {tab === "routes" &&
                    rows.map((route) => (
                      <tr key={route.id}>
                        <td>
                          <strong>{route.name}</strong>
                        </td>

                        <td>{route.start_point || "\u2014"}</td>

                        <td>{route.end_point || "\u2014"}</td>

                        <td>{route.vehicle_plate || "\u2014"}</td>

                        <td>{route.driver_name || "\u2014"}</td>

                        <td>{route.stops?.length ?? 0}</td>

                        <td>
                          <span
                            className={`status-badge ${
                              route.status ? "active" : "inactive"
                            }`}
                          >
                            {route.status ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))}

                  {tab === "assignments" &&
                    rows.map((assignment) => (
                      <tr key={assignment.id}>
                        <td>
                          <strong>{assignment.student_name}</strong>
                        </td>

                        <td>{assignment.admission_number || "\u2014"}</td>

                        <td>{assignment.route_name || "\u2014"}</td>

                        <td>{assignment.stop_name || "\u2014"}</td>

                        <td>
                          <StatusBadge
                            status={assignment.status}
                            label={
                              assignment.status
                                ? assignment.status.charAt(0).toUpperCase() +
                                  assignment.status.slice(1)
                                : "\u2014"
                            }
                          />
                        </td>

                        <td>{formatDate(assignment.created_at)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>

      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeForm();
          }}
        >
          <div className="teacher-modal">
            <div className="modal-header">
              <div>
                <h3>{editing ? "Edit Vehicle" : "Add Vehicle"}</h3>
                <p>{editing ? "Update the vehicle details." : "Add a new vehicle to the fleet."}</p>
              </div>
              <button className="modal-close" onClick={closeForm} disabled={saving}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-section">
                <h4>Vehicle Details</h4>
                <div className="form-grid">
                  <label>
                    Plate Number
                    <input name="plate_number" value={form.plate_number} onChange={handleChange} required />
                  </label>

                  <label>
                    Campus
                    <select name="campus" value={form.campus} onChange={handleChange}>
                      <option value="">No campus</option>
                      {campuses.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Model
                    <input name="model" value={form.model} onChange={handleChange} required />
                  </label>

                  <label>
                    Capacity
                    <input type="number" name="capacity" value={form.capacity} onChange={handleChange} min="1" required />
                  </label>

                  <label>
                    Status
                    <select name="status" value={form.status} onChange={handleChange}>
                      {VEHICLE_STATUS_CHOICES.map((s) => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </label>

                  <label className="form-span">
                    Notes
                    <textarea name="notes" value={form.notes} onChange={handleChange} rows="3" />
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={closeForm} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={saving}>
                  <Plus size={17} />
                  {saving ? "Saving..." : editing ? "Save Changes" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
