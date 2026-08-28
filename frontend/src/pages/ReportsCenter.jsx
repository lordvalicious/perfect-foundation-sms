import { useState, useEffect, useMemo, useCallback } from "react";
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  Search,
  Star,
  Clock,
  Download,
  Filter,
  Settings,
  Plus,
  Grid,
  List,
  ChevronRight,
  ExternalLink,
  Printer,
  Mail,
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea, StatCard, Button, TabButton, Badge } from "./ui";
import { apiFetch } from "../api";
import { formatCurrency } from "./format";
import { REPORT_CATEGORIES } from "../config/reports";
import { useNavigate } from "react-router-dom";

const BASE = "/api/reports/";

function ReportCard({ report, onClick, onFavoriteToggle, isFavorite }) {
  const Icon = report.icon;
  return (
    <div className="report-card" onClick={onClick}>
      <div className="report-card-header">
        <Icon size={24} className="report-card-icon" />
        <div className="report-card-favorite" onClick={onFavoriteToggle}>
          <Star size={16} fill={isFavorite ? "currentColor" : "none"} className={isFavorite ? "active" : ""} />
        </div>
      </div>
      <div className="report-card-body">
        <h4>{report.title}</h4>
        <p>{report.description}</p>
      </div>
      <div className="report-card-footer">
        <span className="report-card-key">{report.key}</span>
        <ChevronRight size={14} />
      </div>
    </div>
  );
}

export default function ReportsCenter() {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState("Dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid");
  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem("report-favorites");
    return saved ? JSON.parse(saved) : [];
  });

  const toggleFavorite = useCallback((reportKey) => {
    setFavorites((prev) => {
      const next = prev.includes(reportKey)
        ? prev.filter((k) => k !== reportKey)
        : [...prev, reportKey];
      localStorage.setItem("report-favorites", JSON.stringify(next));
      return next;
    });
  }, []);

  const isFavorite = useCallback((reportKey) => favorites.includes(reportKey), [favorites]);

  const filteredCategories = useMemo(() => {
    if (!searchQuery) return REPORT_CATEGORIES;

    const query = searchQuery.toLowerCase();
    return REPORT_CATEGORIES.map((cat) => ({
      ...cat,
      reports: cat.reports.filter(
        (r) =>
          r.title.toLowerCase().includes(query) ||
          r.description.toLowerCase().includes(query) ||
          r.key.toLowerCase().includes(query)
      ),
    })).filter((cat) => cat.reports.length > 0);
  }, [searchQuery]);

  const totalReports = useMemo(() => REPORT_CATEGORIES.reduce((sum, cat) => sum + cat.reports.length, 0), []);

  const handleReportClick = (reportKey) => {
    navigate(`/reports/${reportKey}`);
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Reports"
        title="Reports Center"
        subtitle="Generate, customize, and export school-wide reports"
        action={
          <div className="header-actions">
            <Button variant="outline" onClick={() => setViewMode("list")} className={viewMode === "list" ? "active" : ""}>
              <List size={16} /> List
            </Button>
            <Button variant="outline" onClick={() => setViewMode("grid")} className={viewMode === "grid" ? "active" : ""}>
              <Grid size={16} /> Grid
            </Button>
            <Button variant="primary" onClick={() => navigate("/reports/builder")}>
              <Plus size={16} /> New Report
            </Button>
          </div>
        }
      />

      <div className="reports-header">
        <div className="reports-search">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="reports-stats">
          <StatCard label="Total Reports" value={totalReports} icon={FileText} />
          <StatCard label="Categories" value={REPORT_CATEGORIES.length} icon={LayoutDashboard} />
          <StatCard label="Favorites" value={favorites.length} icon={Star} />
        </div>
      </div>

      <div className="categories-tabs">
        {REPORT_CATEGORIES.map((cat) => (
          <TabButton
            key={cat.slug || cat.category}
            active={activeCategory === cat.category}
            onClick={() => setActiveCategory(cat.category)}
            icon={cat.icon}
          >
            {cat.category} ({cat.reports.length})
          </TabButton>
        ))}
      </div>

      <StateArea loading={false} error={null} onRetry={() => {}}>
        {viewMode === "grid" ? (
          <div className="reports-grid">
            {filteredCategories.map((cat) =>
              cat.reports.length > 0 && (
                <div key={cat.slug || cat.category} className="category-section">
                  <div className="category-header">
                    <span className="category-icon"><cat.icon size={20} /></span>
                    <h3>{cat.category}</h3>
                    <span className="report-count">{cat.reports.length} reports</span>
                  </div>
                  <div className="reports-row">
                    {cat.reports.map((report) => (
                      <ReportCard
                        key={report.key}
                        report={{ ...report, isFavorite: isFavorite(report.key) }}
                        onClick={() => handleReportClick(report.key)}
                        onFavoriteToggle={(e) => { e.stopPropagation(); toggleFavorite(report.key); }}
                        isFavorite={isFavorite(report.key)}
                      />
                    ))}
                  </div>
                </div>
            ))}
          </div>
        ) : (
          <div className="reports-list">
            {filteredCategories.map((cat) =>
              cat.reports.length > 0 && (
                <div key={cat.slug || cat.category} className="category-section">
                  <div className="category-header">
                    <span className="category-icon"><cat.icon size={20} /></span>
                    <h3>{cat.category}</h3>
                    <span className="report-count">{cat.reports.length} reports</span>
                  </div>
                  <div className="reports-table">
                    <table className="reports-table">
                      <thead>
                        <tr>
                          <th>Report</th>
                          <th>Description</th>
                          <th className="actions-col">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cat.reports.map((report) => (
                          <tr
                            key={report.key}
                            onClick={() => handleReportClick(report.key)}
                            style={{ cursor: "pointer" }}
                          >
                            <td>
                              <span className="report-icon"><report.icon size={18} /></span>
                              <div>
                                <strong>{report.title}</strong>
                                <p>{report.description}</p>
                              </div>
                            </td>
                            <td className="actions-col">
                              <Star
                                onClick={(e) => { e.stopPropagation(); toggleFavorite(report.key); }}
                                className={isFavorite(report.key) ? "active" : ""}
                                fill={isFavorite(report.key) ? "currentColor" : "none"}
                              />
                              <ChevronRight size={16} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
            ))}
          </div>
        )}
      </StateArea>
    </section>
  );
}