import { useState } from "react";
import { Bus, Car, MapPin, UsersRound } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, EmptyState, StatusBadge } from "./ui";
import { formatDate } from "./format";

const BASE = "/api/transport/";

const ENDPOINTS = {
  vehicles: { url: "vehicles/", icon: Car, title: "Vehicles" },
  drivers: { url: "drivers/", icon: UsersRound, title: "Drivers" },
  routes: { url: "routes/", icon: MapPin, title: "Routes" },
  assignments: { url: "assignments/", icon: Bus, title: "Assignments" },
};

export default function TransportPage() {
  const [tab, setTab] = useState("vehicles");
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Transport"
        title="Transport"
        subtitle="Manage vehicles, drivers, routes, and student transport assignments."
      />

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

                        <td>{vehicle.model || "—"}</td>

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

                        <td>{vehicle.notes || "—"}</td>
                      </tr>
                    ))}

                  {tab === "drivers" &&
                    rows.map((driver) => (
                      <tr key={driver.id}>
                        <td>
                          <strong>{driver.full_name || "—"}</strong>
                        </td>

                        <td>{driver.license_number || "—"}</td>

                        <td>{driver.phone || "—"}</td>

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

                        <td>{route.start_point || "—"}</td>

                        <td>{route.end_point || "—"}</td>

                        <td>{route.vehicle_plate || "—"}</td>

                        <td>{route.driver_name || "—"}</td>

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

                        <td>{assignment.admission_number || "—"}</td>

                        <td>{assignment.route_name || "—"}</td>

                        <td>{assignment.stop_name || "—"}</td>

                        <td>
                          <StatusBadge
                            status={assignment.status}
                            label={
                              assignment.status
                                ? assignment.status.charAt(0).toUpperCase() +
                                  assignment.status.slice(1)
                                : "—"
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
    </section>
  );
}
