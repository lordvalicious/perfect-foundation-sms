import { useState } from "react";
import {
  Tags,
  Truck,
  Wrench,
  PackageSearch,
  Search,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea, EmptyState } from "./ui";
import { formatCurrency, formatDate } from "./format";

const BASE = "/api/inventory/";

const ENDPOINTS = {
  assets: { url: "assets/", icon: PackageSearch, title: "Assets" },
  categories: { url: "categories/", icon: Tags, title: "Categories" },
  suppliers: { url: "suppliers/", icon: Truck, title: "Suppliers" },
  maintenance: { url: "maintenance/", icon: Wrench, title: "Maintenance" },
};

export default function InventoryPage() {
  const [tab, setTab] = useState("assets");
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const load = (key) => {
    const config = ENDPOINTS[key];

    setLoading(true);
    setError("");

    const params = new URLSearchParams();

    if (key === "assets" && search.trim()) {
      params.append("q", search.trim());
    }

    const query = params.toString() ? `?${params.toString()}` : "";

    fetch(`${BASE}${config.url}${query}`, { credentials: "include" })
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
        crumb="Home / Inventory"
        title="Inventory"
        subtitle="Track school assets, suppliers, and maintenance records."
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

        {tab === "assets" && (
          <div className="filter-row">
            <div className="filter-search">
              <Search size={18} />

              <input
                type="text"
                placeholder="Search assets by name..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <button type="button" className="primary-button" onClick={() => load("assets")}>
              Search
            </button>
          </div>
        )}

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
                  {tab === "assets" && (
                    <tr>
                      <th>NAME</th>
                      <th>CODE</th>
                      <th>CATEGORY</th>
                      <th>SUPPLIER</th>
                      <th>QUANTITY</th>
                      <th>UNIT COST</th>
                      <th>TOTAL VALUE</th>
                      <th>LOCATION</th>
                      <th>STATUS</th>
                    </tr>
                  )}

                  {tab === "categories" && (
                    <tr>
                      <th>NAME</th>
                      <th>DESCRIPTION</th>
                    </tr>
                  )}

                  {tab === "suppliers" && (
                    <tr>
                      <th>NAME</th>
                      <th>CONTACT PERSON</th>
                      <th>PHONE</th>
                      <th>EMAIL</th>
                      <th>ADDRESS</th>
                    </tr>
                  )}

                  {tab === "maintenance" && (
                    <tr>
                      <th>ASSET</th>
                      <th>DATE</th>
                      <th>COST</th>
                      <th>PERFORMED BY</th>
                      <th>STATUS</th>
                      <th>DESCRIPTION</th>
                    </tr>
                  )}
                </thead>

                <tbody>
                  {tab === "assets" &&
                    rows.map((asset) => (
                      <tr key={asset.id}>
                        <td>
                          <strong>{asset.name}</strong>
                        </td>

                        <td>{asset.code || "—"}</td>

                        <td>{asset.category_name || "—"}</td>

                        <td>{asset.supplier_name || "—"}</td>

                        <td>{asset.quantity ?? 0}</td>

                        <td>{formatCurrency(asset.unit_cost)}</td>

                        <td>
                          <strong>{formatCurrency(asset.total_value)}</strong>
                        </td>

                        <td>{asset.location || "—"}</td>

                        <td>
                          <span className={`status-badge ${asset.status === "in_use" ? "active" : asset.status === "retired" || asset.status === "expired" ? "inactive" : "info"}`}>
                            {asset.status_display}
                          </span>
                        </td>
                      </tr>
                    ))}

                  {tab === "categories" &&
                    rows.map((category) => (
                      <tr key={category.id}>
                        <td>
                          <strong>{category.name}</strong>
                        </td>

                        <td>{category.description || "—"}</td>
                      </tr>
                    ))}

                  {tab === "suppliers" &&
                    rows.map((supplier) => (
                      <tr key={supplier.id}>
                        <td>
                          <strong>{supplier.name}</strong>
                        </td>

                        <td>{supplier.contact_person || "—"}</td>

                        <td>{supplier.phone || "—"}</td>

                        <td>{supplier.email || "—"}</td>

                        <td>{supplier.address || "—"}</td>
                      </tr>
                    ))}

                  {tab === "maintenance" &&
                    rows.map((record) => (
                      <tr key={record.id}>
                        <td>
                          <strong>{record.asset_name || "—"}</strong>
                        </td>

                        <td>{formatDate(record.date)}</td>

                        <td>{formatCurrency(record.cost)}</td>

                        <td>{record.performed_by || "—"}</td>

                        <td>
                          <span className={`status-badge ${record.status === "completed" ? "active" : record.status === "scheduled" ? "info" : "warn"}`}>
                            {record.status ? record.status.replace("_", " ") : "—"}
                          </span>
                        </td>

                        <td>{record.description || "—"}</td>
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
