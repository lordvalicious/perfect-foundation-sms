import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  ClipboardCheck,
  HeartPulse,
  Wallet,
  FileText,
  CalendarDays,
  BookOpen,
  BookOpenCheck,
  Building2,
  Settings,
  Bell,
  Search,
  LogOut,
  CalendarClock,
  ScrollText,
  Layers,
  UserRound,
  HeartHandshake,
  Menu,
  X,
  ChevronDown,
  LibraryBig,
  Bus,
  Boxes,
  Banknote,
  BarChart3,
  Megaphone,
  CheckCheck,
  Mail,
  MessageSquare,
  Sun,
  Moon,
  FilePlus2,
  Briefcase,
  Palette,
  Download,
  Upload,
  Activity,
  AlertOctagon,
  BedDouble,
  MonitorPlay,
  LifeBuoy,
  ShieldCheck,
  IdCard,
} from "lucide-react";
import "./App.css";
import "./dark-dash.css";
import { AuthProvider, useAuth } from "./auth";
import { SchoolProvider, useSchool } from "./schoolContext";
import { LanguageProvider, useLang } from "./i18n";
import LanguageToggle from "./components/LanguageToggle";
import LoginPage from "./pages/LoginPage";
import AttendancePage from "./pages/AttendancePage";
import FinancePage from "./pages/FinancePage";
import ExamsPage from "./pages/ExamsPage";
import ReportCardsPage from "./pages/ReportCardsPage";
import TimetablePage from "./pages/TimetablePage";
import CampusesPage from "./pages/CampusesPage";
import SettingsPage from "./pages/SettingsPage";
import EventsPage from "./pages/EventsPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import AssignmentsPage from "./pages/AssignmentsPage";
import ProfilePage from "./pages/ProfilePage";
import StaffPage from "./pages/StaffPage";
import ParentPortalPage from "./pages/ParentPortalPage";
import LibraryPage from "./pages/LibraryPage";
import TransportPage from "./pages/TransportPage";
import InventoryPage from "./pages/InventoryPage";
import PayrollPage from "./pages/PayrollPage";
import ReportsPage from "./pages/ReportsPage";
import AnnouncementsPage from "./pages/AnnouncementsPage";
import MessagesPage from "./pages/MessagesPage";
import SMSPage from "./pages/SMSPage";
import Dashboard from "./pages/Dashboard";
import StudentsPage from "./pages/StudentsPage";
import Student360Page from "./pages/Student360Page";
import AcademicsPage from "./pages/AcademicsPage";
import TeachersPage from "./pages/TeachersPage";
import HRPage from "./pages/HRPage";
import AdmissionsPage from "./pages/AdmissionsPage";
import BulkFinancePage from "./pages/BulkFinancePage";
import DocumentsPage from "./pages/DocumentsPage";
import ReportBuilderPage from "./pages/ReportBuilderPage";
import TemplatesPage from "./pages/TemplatesPage";
import BrandingPage from "./pages/BrandingPage";
import CampusDashboardPage from "./pages/CampusDashboardPage";
import ExecutiveDashboardPage from "./pages/ExecutiveDashboardPage";
import ExportPage from "./pages/ExportPage";
import HealthPage from "./pages/HealthPage";
import DataImportPage from "./pages/DataImportPage";
import DisciplinePage from "./pages/DisciplinePage";
import StaffOperationsPage from "./pages/StaffOperationsPage";
import HomeworkPage from "./pages/HomeworkPage";
import HealthRecordsPage from "./pages/HealthRecordsPage";
import AdmissionsApplyPage from "./pages/AdmissionsApplyPage";
import AlumniPage from "./pages/AlumniPage";
import HostelPage from "./pages/HostelPage";
import LMSPage from "./pages/LMSPage";
import TenantsPage from "./pages/TenantsPage";
import HelpdeskPage from "./pages/HelpdeskPage";
import VisitorsPage from "./pages/VisitorsPage";
import DigitalIdsPage from "./pages/DigitalIdsPage";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

function authHeaders(extra = {}) {
  const csrfToken = getCookie("csrftoken");
  return { ...extra, ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}) };
}

const SEARCH_URL = "/api/search/";
const NOTIFICATIONS_URL = "/api/communication/notifications/";

function GlobalSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const value = query.trim();
    if (value.length < 2) { setResults([]); setOpen(false); return; }  
    setLoading(true);
    const timer = setTimeout(() => {
      fetch(`${SEARCH_URL}?q=${encodeURIComponent(value)}`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : { results: [] }))
        .then((data) => { setResults(data.results || []); setOpen(true); setLoading(false); })
        .catch(() => { setResults([]); setLoading(false); });
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="global-search">
      <div className="search">
        <Search size={15} />
        <input
          type="text"
          placeholder="Search..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (results.length) setOpen(true); }}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
      </div>
      {open && (
        <div className="search-dropdown">
          {loading && <div className="search-loading">Searching...</div>}
          {!loading && results.length === 0 && <div className="search-loading">No results found.</div>}
          {!loading && results.map((result, i) => (
            <button
              key={`${result.type}-${result.id}-${i}`}
              type="button"
              className="search-result"
              onMouseDown={(e) => { e.preventDefault(); setOpen(false); setQuery(""); navigate(result.link); }}
            >
              <span className="search-result-type">{result.type}</span>
              <span>
                <strong>{result.name}</strong>
                <small>{result.subtitle || result.class_name || ""}</small>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function NotificationsBell() {
  const [notifications, setNotifications] = useState(null);
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const unread = notifications ? notifications.filter((n) => !n.is_read).length : 0;

  useEffect(() => {
    if (!open || notifications !== null) return;
    fetch(NOTIFICATIONS_URL, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => { setNotifications(Array.isArray(data) ? data : data.results || []); setLoaded(true); })
      .catch(() => { setNotifications([]); setLoaded(true); });
  }, [open, notifications]);

  const markAllRead = () => {
    fetch(`${NOTIFICATIONS_URL}read-all/`, { method: "POST", credentials: "include", headers: authHeaders() })
      .then((r) => { if (r.ok) setNotifications((items) => (items || []).map((n) => ({ ...n, is_read: true }))); })
      .catch(() => {});
  };

  const markRead = (n) => {
    if (!n.is_read) {
      fetch(`${NOTIFICATIONS_URL}${n.id}/read/`, { method: "POST", credentials: "include", headers: authHeaders() })
        .then((r) => { if (r.ok) setNotifications((items) => (items || []).map((x) => x.id === n.id ? { ...x, is_read: true } : x)); })
        .catch(() => {});
    }
  };

  return (
    <div className="notifications-wrap">
      <button className="icon-button" title="Notifications" onClick={() => setOpen((v) => !v)}>
        <Bell size={18} />
        {unread > 0 && <span className="notification-dot">{unread}</span>}
      </button>
      {open && (
        <div className="notifications-dropdown">
          <div className="notifications-header">
            <strong>Notifications</strong>
            {unread > 0 && (
              <button type="button" className="text-button" onClick={markAllRead}>
                <CheckCheck size={13} /> Mark all read
              </button>
            )}
          </div>
          <div className="notifications-list">
            {!loaded && <div className="search-loading">Loading...</div>}
            {loaded && notifications.length === 0 && <div className="search-loading">No notifications.</div>}
            {loaded && notifications.slice(0, 15).map((n) => (
              <button key={n.id} type="button" className={`notification-item ${n.is_read ? "read" : ""}`} onClick={() => markRead(n)}>
                <strong>{n.title}</strong>
                {n.message && <span>{n.message}</span>}
                <small>{n.notification_type_display || "System"}</small>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const THEME_KEY = "pf-theme";

function getInitialTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

function ThemeToggle() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e) => {
      if (!localStorage.getItem(THEME_KEY)) {
        const next = e.matches ? "dark" : "light";
        setTheme(next);
        applyTheme(next);
      }
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const toggle = () => {
    document.documentElement.classList.add("theme-transitioning");
    setTheme((t) => (t === "dark" ? "light" : "dark"));
    setTimeout(() => document.documentElement.classList.remove("theme-transitioning"), 350);
  };

  return (
    <button className="theme-toggle" onClick={toggle} title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
      {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}

/* =========================
   NAVIGATION
   ========================= */

const navigation = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, roles: [] },
  { label: "My Profile", path: "/profile", icon: UserRound, roles: [] },
  { label: "Parent Portal", path: "/parent-portal", icon: HeartHandshake, roles: ["parent"] },
  { label: "Students", module: "students", path: "/students", icon: Users, roles: ["super_admin", "admin", "principal", "academic", "accountant", "teacher", "student"] },
  { label: "Admissions", module: "students", path: "/admissions", icon: FilePlus2, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Academics", module: "students", path: "/academics", icon: Layers, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Teachers", path: "/teachers", icon: GraduationCap, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Staff", path: "/staff", icon: Users, roles: ["super_admin", "admin", "principal", "academic", "vice_principal", "campus_admin", "hr"] },
  { label: "Staff Leave & Attendance", path: "/staff-operations", icon: CalendarClock, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "hr"] },
  { label: "Health Records", module: "health", path: "/health-records", icon: HeartPulse, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"] },
  { label: "Human Resources", path: "/hr", icon: Briefcase, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "hr", "accountant"] },
  { label: "Assignments", path: "/assignments", icon: Layers, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Homework", module: "homework", path: "/homework", icon: BookOpenCheck, roles: ["super_admin", "admin", "principal", "academic", "teacher", "student", "parent"] },
  { label: "Attendance", module: "attendance", path: "/attendance", icon: ClipboardCheck, roles: ["super_admin", "admin", "principal", "academic", "teacher"] },
  { label: "Discipline", module: "discipline", path: "/discipline", icon: AlertOctagon, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"] },
  { label: "Finance", module: "finance", path: "/finance", icon: Wallet, roles: ["super_admin", "admin", "principal", "academic", "accountant"] },
  { label: "Bulk Finance", module: "finance", path: "/finance/bulk", icon: Layers, roles: ["super_admin", "admin", "accountant"] },
  { label: "Exams", module: "exams", path: "/exams", icon: FileText, roles: ["super_admin", "admin", "principal", "academic", "teacher"] },
  { label: "Report Cards", module: "exams", path: "/report-cards", icon: BookOpen, roles: ["super_admin", "admin", "principal", "academic", "teacher"] },
  { label: "Timetable", path: "/timetable", icon: CalendarDays, roles: ["super_admin", "admin", "principal", "academic", "teacher", "staff", "student", "parent"] },
  { label: "Campuses", path: "/campuses", icon: Building2, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Campus Dashboard", path: "/campus-dashboard", icon: Building2, roles: ["super_admin", "admin", "principal"] },
  { label: "Executive Dashboard", path: "/executive-dashboard", icon: BarChart3, roles: ["super_admin", "admin", "academic", "principal", "vice_principal", "campus_admin"] },
  { label: "Announcements", path: "/announcements", icon: Megaphone, roles: [] },
  { label: "Messages", module: "communication", path: "/messages", icon: Mail, roles: [] },
  { label: "SMS", module: "communication", path: "/sms", icon: MessageSquare, roles: ["super_admin", "admin"] },
  { label: "Templates", module: "communication", path: "/templates", icon: FileText, roles: ["super_admin", "admin"] },
  { label: "Library", module: "library", path: "/library", icon: LibraryBig, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Transport", module: "transport", path: "/transport", icon: Bus, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Inventory", module: "inventory", path: "/inventory", icon: Boxes, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Documents", path: "/documents", icon: FileText, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Payroll", module: "payroll", path: "/payroll", icon: Banknote, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Reports", module: "reports", path: "/reports", icon: BarChart3, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Report Builder", module: "reports", path: "/report-builder", icon: BarChart3, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Data Export", module: "reports", path: "/data-export", icon: Download, roles: ["super_admin", "admin"] },
  { label: "Data Import", module: "reports", path: "/data-import", icon: Upload, roles: ["super_admin", "admin"] },
  { label: "Events", module: "events", path: "/events", icon: CalendarClock, roles: [] },
  { label: "Alumni", module: "alumni", path: "/alumni", icon: GraduationCap, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Hostel", module: "hostel", path: "/hostel", icon: BedDouble, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Online Courses", path: "/lms", icon: MonitorPlay, roles: ["super_admin", "admin", "principal", "academic", "teacher", "student"] },
  { label: "Helpdesk", module: "helpdesk", path: "/helpdesk", icon: LifeBuoy, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "hr", "receptionist", "guard", "teacher", "staff"] },
  { label: "Visitors", module: "visitors", path: "/visitors", icon: ShieldCheck, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "hr", "receptionist", "guard", "staff"] },
  { label: "Digital IDs", module: "digital_ids", path: "/digital-ids", icon: IdCard, roles: ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "hr", "receptionist", "staff"] },
];

const systemNavigation = [
  { label: "Settings", path: "/settings", icon: Settings, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Branding", path: "/branding", icon: Palette, roles: ["super_admin", "admin"] },
  { label: "Schools", path: "/tenants", icon: Building2, isPlatform: true, roles: [] },
  { label: "System Health", path: "/health", icon: Activity, roles: ["super_admin", "admin"] },
  { label: "Audit Logs", path: "/audit-logs", icon: ScrollText, roles: ["super_admin", "admin"] },
];

function findNav(path) {
  return navigation.find((n) => n.path === path);
}

const navGroups = [
  {
    label: "People",
    items: ["/students", "/admissions", "/teachers", "/staff", "/staff-operations", "/health-records", "/hr", "/parent-portal", "/profile"]
      .map(findNav)
      .filter(Boolean),
  },
  {
    label: "Academics",
    items: ["/attendance", "/discipline", "/exams", "/homework", "/lms", "/report-cards", "/timetable", "/assignments", "/academics"]
      .map(findNav)
      .filter(Boolean),
  },
  {
    label: "Finance",
    items: ["/finance", "/finance/bulk", "/payroll", "/reports", "/report-builder", "/data-export", "/data-import"]
      .map(findNav)
      .filter(Boolean),
  },
  {
    label: "Resources",
    items: ["/library", "/transport", "/inventory", "/documents", "/campuses", "/campus-dashboard", "/executive-dashboard", "/alumni", "/hostel"]
      .map(findNav)
      .filter(Boolean),
  },
  {
    label: "Communication",
    items: ["/messages", "/sms", "/templates", "/announcements", "/events"]
      .map(findNav)
      .filter(Boolean),
  },
  {
    label: "Support & Security",
    items: ["/helpdesk", "/visitors", "/digital-ids"]
      .map(findNav)
      .filter(Boolean),
  },
  {
    label: "System",
    items: [...systemNavigation.filter((n) => n.roles.length === 0 || /* hasRole check done below */ true)],
  },
];

/* =========================
   LAYOUT — Top navigation
   ========================= */

function Layout({ children, hasRole, modules = { loaded: false, enabled: [], isPlatformAdmin: false } }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [schoolDropdownOpen, setSchoolDropdownOpen] = useState(false);
  const schoolSwitcherRef = useRef(null);
  const { t } = useLang();
  const { currentSchool, availableSchools, switchSchool, loading: schoolLoading } = useSchool();

  useEffect(() => {
    if (!schoolDropdownOpen) return;
    const handleClickOutside = (e) => {
      if (schoolSwitcherRef.current && !schoolSwitcherRef.current.contains(e.target)) {
        setSchoolDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [schoolDropdownOpen]);

  const moduleAllows = (item) => {
    if (!item.module) return true;
    if (!modules.loaded) return true;
    if (modules.enabled.length === 0) return true;
    return modules.enabled.includes(item.module);
  };

  const visibleNavigation = navigation.filter(
    (item) =>
      moduleAllows(item) &&
      (item.roles.length === 0 || hasRole(item.roles))
  );
  const visibleSystemNavigation = systemNavigation.filter(
    (item) =>
      (!item.isPlatform || modules.isPlatformAdmin) &&
      (item.roles.length === 0 || hasRole(item.roles))
  );

  const visibleNavGroups = navGroups.map((group) => ({
    ...group,
    items: group.items.filter(
      (item) =>
        moduleAllows(item) &&
        (item.roles.length === 0 || hasRole(item.roles))
    ),
  })).filter((group) => group.items.length > 0);

  const visibleSystemGroup = visibleNavGroups.find((g) => g.label === "System");
  if (visibleSystemGroup) {
    visibleSystemGroup.items = visibleSystemNavigation;
  }

  const dashItem = findNav("/");

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <div className="brand-logo">S</div>
          {currentSchool && (
            <div className="school-indicator">
              {availableSchools.length > 1 && modules.isPlatformAdmin ? (
                <div className="school-switcher-wrap" ref={schoolSwitcherRef}>
                  <button
                    className="school-switcher-trigger"
                    onClick={() => setSchoolDropdownOpen((v) => !v)}
                    disabled={schoolLoading}
                  >
                    <Building2 size={14} />
                    <span>{currentSchool.name}</span>
                    <ChevronDown size={12} />
                  </button>
                  {schoolDropdownOpen && (
                    <div className="school-switcher-dropdown">
                      {availableSchools.map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          className={`school-switcher-item ${s.id === currentSchool.id ? "active" : ""}`}
                          onClick={() => {
                            setSchoolDropdownOpen(false);
                            if (s.id !== currentSchool.id) switchSchool(s.id);
                          }}
                        >
                          <Building2 size={13} />
                          {s.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <span className="school-name-readonly">
                  <Building2 size={14} />
                  {currentSchool.name}
                </span>
              )}
            </div>
          )}
          <nav className="topbar-nav">
            {dashItem && (
              <NavLink
                to={dashItem.path}
                end={dashItem.path === "/"}
                className={({ isActive }) => `topbar-link ${isActive ? "active" : ""}`}
              >
                <dashItem.icon size={15} />
                <span>{t("Dashboard")}</span>
              </NavLink>
            )}
            {visibleNavGroups.filter((g) => g.label !== "System").map((group) => (
              <div className="nav-group" key={group.label}>
                <button className="nav-group-trigger">
                  {group.label}
                  <ChevronDown className="chevron" size={14} />
                </button>
                <div className="nav-dropdown">
                  {group.items.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === "/"}
                      className={({ isActive }) => `nav-dropdown-item ${isActive ? "active" : ""}`}
                    >
                      <item.icon size={14} />
                      {t(item.label)}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
            {visibleSystemGroup && visibleSystemGroup.items.length > 0 && (
              <div className="nav-group">
                <button className="nav-group-trigger">
                  System
                  <ChevronDown className="chevron" size={14} />
                </button>
                <div className="nav-dropdown">
                  {visibleSystemGroup.items.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) => `nav-dropdown-item ${isActive ? "active" : ""}`}
                    >
                      <item.icon size={14} />
                      {t(item.label)}
                    </NavLink>
                  ))}
                </div>
              </div>
            )}
          </nav>
        </div>

        <div className="topbar-right">
          <GlobalSearch />
          <NotificationsBell />
          <LanguageToggle />
          <ThemeToggle />

          <TopbarProfile />

          <button
            className="mobile-nav-toggle"
            onClick={() => setMobileNavOpen((v) => !v)}
            title="Menu"
          >
            {mobileNavOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </header>

      <main className="main">{children}</main>

      {mobileNavOpen && (
        <div className="mobile-nav-backdrop" onClick={() => setMobileNavOpen(false)} />
      )}

      {mobileNavOpen && (
        <nav className="mobile-nav">
          <MobileNavSection
            label="Main"
            items={visibleNavigation}
            onNavigate={() => setMobileNavOpen(false)}
          />
          <MobileNavSection
            label="System"
            items={visibleSystemNavigation}
            onNavigate={() => setMobileNavOpen(false)}
          />
        </nav>
      )}
    </div>
  );
}

function TopbarProfile() {
  const { user, logout } = useAuth();
  const displayName = user?.first_name || user?.username || "User";
  const initials = displayName.split(" ").map((p) => p.charAt(0)).join("").slice(0, 2).toUpperCase();
  const roleLabel = user?.primary_role
    ? user.primary_role.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
    : "";

  return (
    <>
      <div className="profile">
        {user?.photo_url ? (
          <img className="avatar avatar-photo" src={user.photo_url} alt={displayName} />
        ) : (
          <div className="avatar">{initials}</div>
        )}
        <div>
          <strong>{displayName}</strong>
          <span>{roleLabel || "Member"}</span>
        </div>
      </div>
      <button className="logout-button" title="Sign out" onClick={logout}>
        <LogOut size={16} />
      </button>
    </>
  );
}

function MobileNavSection({ label, items, onNavigate }) {
  return (
    <div className="mobile-nav-section">
      <div className="mobile-nav-label">{label}</div>
      {items.map(({ label: itemLabel, path, icon: Icon }) => (
        <NavLink
          key={path}
          to={path}
          end={path === "/"}
          onClick={onNavigate}
          className={({ isActive }) => `mobile-nav-link ${isActive ? "active" : ""}`}
        >
          <Icon size={17} />
          {itemLabel}
        </NavLink>
      ))}
    </div>
  );
}

function RequireRoles({ roles, children }) {
  const { user, hasRole } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (roles.length > 0 && !hasRole(roles)) {
    return (
      <section className="content">
        <div className="state-card error">
          <strong>Access denied.</strong>
          <span>Your role does not have permission to view this page.</span>
        </div>
      </section>
    );
  }
  return children;
}

/* =========================
   APP ROUTES
   ========================= */

function Shell() {
  const { user, loading, hasRole } = useAuth();
  const { modules, loading: schoolLoading } = useSchool();
  const location = useLocation();

  if (loading || (user && schoolLoading)) {
    return (
      <div className="auth-loading">
        <div className="brand-logo">S</div>
        <span>Loading...</span>
      </div>
    );
  }

  // Public, unauthenticated pages.
  if (location.pathname === "/apply") {
    return <AdmissionsApplyPage />;
  }

  if (!user) return <LoginPage />;

  return (
    <Layout hasRole={hasRole} modules={modules}>
      <Routes>
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/" element={<Dashboard />} />

        <Route path="/profile" element={<ProfilePage key={location.pathname} />} />
        <Route path="/profile/teacher/:id" element={<ProfilePage key={location.pathname} />} />
        <Route path="/profile/student/:id" element={<ProfilePage key={location.pathname} />} />
        <Route path="/profile/staff/:id" element={<ProfilePage key={location.pathname} />} />

        <Route path="/students" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "teacher", "student"]}>
            <StudentsPage />
          </RequireRoles>
        } />

        <Route path="/students/:id" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "teacher", "student"]}>
            <Student360Page />
          </RequireRoles>
        } />

        <Route path="/academics" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <AcademicsPage />
          </RequireRoles>
        } />

        <Route path="/admissions" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <AdmissionsPage />
          </RequireRoles>
        } />

        <Route path="/parent-portal" element={
          <RequireRoles roles={["parent"]}>
            <ParentPortalPage />
          </RequireRoles>
        } />

        <Route path="/teachers" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <TeachersPage />
          </RequireRoles>
        } />

        <Route path="/staff" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "vice_principal", "campus_admin", "hr"]}>
            <StaffPage />
          </RequireRoles>
        } />

        <Route path="/hr" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "hr", "accountant"]}>
            <HRPage />
          </RequireRoles>
        } />

        <Route path="/assignments" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <AssignmentsPage />
          </RequireRoles>
        } />

        <Route path="/attendance" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher"]}>
            <AttendancePage />
          </RequireRoles>
        } />

        <Route path="/finance" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant"]}>
            <FinancePage />
          </RequireRoles>
        } />

        <Route path="/finance/bulk" element={
          <RequireRoles roles={["super_admin", "admin", "accountant"]}>
            <BulkFinancePage />
          </RequireRoles>
        } />

        <Route path="/exams" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher"]}>
            <ExamsPage />
          </RequireRoles>
        } />

        <Route path="/report-cards" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher"]}>
            <ReportCardsPage />
          </RequireRoles>
        } />

        <Route path="/timetable" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher", "staff", "student", "parent"]}>
            <TimetablePage />
          </RequireRoles>
        } />

        <Route path="/campuses" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <CampusesPage />
          </RequireRoles>
        } />

        <Route path="/campus-dashboard" element={
          <RequireRoles roles={["super_admin", "admin", "principal"]}>
            <CampusDashboardPage />
          </RequireRoles>
        } />

        <Route path="/executive-dashboard" element={
          <RequireRoles roles={["super_admin", "admin", "academic", "principal", "vice_principal", "campus_admin"]}>
            <ExecutiveDashboardPage />
          </RequireRoles>
        } />

        <Route path="/events" element={<EventsPage />} />

        <Route path="/announcements" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr", "teacher", "staff", "student", "parent"]}>
            <AnnouncementsPage />
          </RequireRoles>
        } />

        <Route path="/messages" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr", "teacher", "staff", "student", "parent"]}>
            <MessagesPage />
          </RequireRoles>
        } />

        <Route path="/sms" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <SMSPage />
          </RequireRoles>
        } />

        <Route path="/templates" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <TemplatesPage />
          </RequireRoles>
        } />

        <Route path="/library" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <LibraryPage />
          </RequireRoles>
        } />

        <Route path="/transport" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <TransportPage />
          </RequireRoles>
        } />

        <Route path="/inventory" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <InventoryPage />
          </RequireRoles>
        } />

        <Route path="/documents" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <DocumentsPage />
          </RequireRoles>
        } />

        <Route path="/payroll" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <PayrollPage />
          </RequireRoles>
        } />

        <Route path="/reports" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <ReportsPage />
          </RequireRoles>
        } />

        <Route path="/report-builder" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
            <ReportBuilderPage />
          </RequireRoles>
        } />

        <Route path="/data-export" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <ExportPage />
          </RequireRoles>
        } />

        <Route path="/data-import" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <DataImportPage />
          </RequireRoles>
        } />

        <Route path="/discipline" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"]}>
            <DisciplinePage />
          </RequireRoles>
        } />

        <Route path="/staff-operations" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "hr"]}>
            <StaffOperationsPage canReview />
          </RequireRoles>
        } />

        <Route path="/homework" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher", "student", "parent"]}>
            <HomeworkPage isStudent={hasRole(["student"])} />
          </RequireRoles>
        } />

        <Route path="/health-records" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "teacher"]}>
            <HealthRecordsPage />
          </RequireRoles>
        } />

        <Route path="/alumni" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <AlumniPage />
          </RequireRoles>
        } />

        {modules.isPlatformAdmin && (
          <Route path="/tenants" element={<TenantsPage />} />
        )}

        <Route path="/hostel" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin"]}>
            <HostelPage />
          </RequireRoles>
        } />

        <Route path="/lms" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher", "student"]}>
            <LMSPage isStudent={hasRole(["student"])} />
          </RequireRoles>
        } />

        <Route path="/helpdesk" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "hr", "receptionist", "guard", "teacher", "staff"]}>
            <HelpdeskPage />
          </RequireRoles>
        } />

        <Route path="/visitors" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "hr", "receptionist", "guard", "staff"]}>
            <VisitorsPage />
          </RequireRoles>
        } />

        <Route path="/digital-ids" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic", "hr", "receptionist", "staff"]}>
            <DigitalIdsPage />
          </RequireRoles>
        } />

        <Route path="/settings" element={
          <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
            <SettingsPage />
          </RequireRoles>
        } />

        <Route path="/branding" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <BrandingPage />
          </RequireRoles>
        } />

        <Route path="/health" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <HealthPage />
          </RequireRoles>
        } />

        <Route path="/audit-logs" element={
          <RequireRoles roles={["super_admin", "admin"]}>
            <AuditLogsPage />
          </RequireRoles>
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <SchoolProvider>
          <BrowserRouter>
            <Shell />
          </BrowserRouter>
        </SchoolProvider>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
