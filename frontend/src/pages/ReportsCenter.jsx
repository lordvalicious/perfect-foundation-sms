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
  Clock,
  Filter,
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
  Users,
  GraduationCap,
  Wallet,
  BookOpen,
  Bus,
  Package,
  Wrench,
  CalendarDays,
  MessageSquare,
  Trophy,
  Table2,
  Siren,
  ClipboardCheck,
} from "lucide-react";
import { PageHeader, PanelHeader, StateArea, StatCard, Button, TabButton, Badge } from "./ui";
import { apiFetch } from "../api";
import { formatCurrency } from "./format";
import { REPORT_CATEGORIES } from "../config/reports";

const BASE = "/api/reports/";

export default function ReportsCenter() {
  const [activeCategory, setActiveCategory] = useState("Dashboard");
  const [activeReport, setActiveReport] = useState("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("grid");
  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem("report-favorites");
    return saved ? JSON.parse(favorites) : [];
  });
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const toggleFavorite = useCallback((reportKey: string) => {
    setFavorites((prev) =>
      favorites.includes(reportKey)
        ? prev.filter((k) => k !== reportKey)
        : [...prev, reportKey]
    );
  }, []);

  const isFavorite = useCallback((reportKey: string) => favorites.includes(reportKey), [favorites]);

  const filteredCategories = useMemo(() => {
    if (!searchQuery) return REPORT_CATEGORIES;

    const query = searchQuery.toLowerCase();
    return REPORT_CATEGORIES.map((cat) => ({
      ...cat,
      reports: cat.reports.filter(
        (r) =>
          r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          r.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          r.key.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    }).filter((cat) => cat.reports.length > 0);
  }, [searchQuery]);

  const totalReports = useMemo(() => REPORT_CATEGORIES.reduce((sum, cat) => sum + cat.reports.length, 0), []);

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
            <Button variant="primary" onClick={() => { /* Open Report Builder */ }}>
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
            placeholder="Search reports..."
          </input>
        </div>

        <div className="reports-stats">
          <StatCard label="Total Reports" value={REPORT_CATEGORIES.reduce((sum, c) => sum + c.reports.length, 0)} icon={FileText} />
          <StatCard label="Categories" value={REPORT_CATEGORIES.length} icon={LayoutDashboard} />
          <StatCard label="Favorites", value={favorites.length}, icon={Star} />
        </div>
      </div>

      <div className="categories-tabs">
        {REPORT_CATEGORIES.map((cat) => (
          <TabButton
            key={cat.category}
            active={activeCategory === cat.category}
            onClick={() => setActiveCategory(cat.category)}
            icon={cat.icon}
          >
            {cat.category} ({cat.reports.length})
          </TabButton>
        ))}
      </div>

      <StateArea
        loading={false}
        error={null}
        onRetry={() => {}}
      >
        {viewMode === "grid" ? (
          <div className="reports-grid">
            {REPORT_CATEGORIES.map((cat) => (
              cat.reports.length > 0 && (
                <div key={cat.category} className="category-section">
                  <div className="category-header">
                    <span className="category-icon">{cat.icon}</span>
                    <h3>{cat.category}</h3>
                    <span className="report-count">{cat.reports.length} reports</span>
                  </div>
                  <div className="reports-row">
                    {cat.reports.map((report) => (
                      <ReportCard
                        key={report.key}
                        report={{
                          ...report,
                          isFavorite: false, // Would check from favorites
                        }}
                        onClick={() => navigate(`/reports/${report.key}`)}
                        onFavoriteToggle={(e) => { e.stopPropagation(); /* toggleFavorite(report.key) */ }}
                      />
                    ))}
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="reports-list">
            {REPORT_CATEGORIES.map((cat) => (
              cat.reports.length > 0 && (
                <div key={cat.category} className="category-section">
                  <div className="category-header">
                    <span className="category-icon">{cat.icon}</span>
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
                          <tr key={report.key} onClick={() => navigate(`/reports/${report.key}`)} style={{ cursor: "pointer" }}>
                            <td>
                              <span className="report-icon">{report.icon}</span>
                              <div>
                                <strong>{report.title}</strong>
                                <p>{report.description}</p>
                              </div>
                            </td>
                            <td className="actions-col">
                              <Star onClick={(e) => { e.stopPropagation(); /* toggleFavorite(report.key) */ }} className="favorite-btn" />
                              <ChevronRight />
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
      </div>
    </section>
  );
}

export default ReportsCenter;