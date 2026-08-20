import {
  useEffect,
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
  Wallet,
  FileText,
  CalendarDays,
  BookOpen,
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
  PanelLeftClose,
  PanelLeftOpen,
  LibraryBig,
  Bus,
  Boxes,
  Banknote,
  BarChart3,
  Megaphone,
  CheckCheck,
  Mail,
  MessageSquare,
} from "lucide-react";
import "./App.css";
import { AuthProvider, useAuth } from "./auth";
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
import TeachersPage from "./pages/TeachersPage";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }

  return null;
}

function authHeaders(extra = {}) {
  const csrfToken = getCookie("csrftoken");

  return {
    ...extra,
    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
  };
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

    if (value.length < 2) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- resets dependent search state
      setResults([]);
      setOpen(false);
      return;
    }

    setLoading(true);

    const timer = setTimeout(() => {
      fetch(`${SEARCH_URL}?q=${encodeURIComponent(value)}`, {
        credentials: "include",
      })
        .then((response) => (response.ok ? response.json() : { results: [] }))
        .then((data) => {
          setResults(data.results || []);
          setOpen(true);
          setLoading(false);
        })
        .catch(() => {
          setResults([]);
          setLoading(false);
        });
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="global-search">
      <div className="search">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search students, teachers..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => {
            if (results.length) {
              setOpen(true);
            }
          }}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
      </div>

      {open && (
        <div className="search-dropdown">
          {loading && <div className="search-loading">Searching...</div>}

          {!loading && results.length === 0 && (
            <div className="search-loading">No results found.</div>
          )}

          {!loading &&
            results.map((result, index) => (
              <button
                key={`${result.type}-${result.id}-${index}`}
                type="button"
                className="search-result"
                onMouseDown={(event) => {
                  event.preventDefault();
                  setOpen(false);
                  setQuery("");
                  navigate(result.link);
                }}
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

  const unread = notifications
    ? notifications.filter((item) => !item.is_read).length
    : 0;

  const load = () => {
    fetch(NOTIFICATIONS_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => {
        setNotifications(Array.isArray(data) ? data : data.results || []);
        setLoaded(true);
      })
      .catch(() => {
        setNotifications([]);
        setLoaded(true);
      });
  };

  useEffect(() => {
    if (!open || notifications !== null) {
      return;
    }

    load();
  }, [open, notifications]);

  const markAllRead = () => {
    fetch(`${NOTIFICATIONS_URL}read-all/`, {
      method: "POST",
      credentials: "include",
      headers: authHeaders(),
    })
      .then((response) => {
        if (response.ok) {
          setNotifications((items) =>
            (items || []).map((item) => ({ ...item, is_read: true }))
          );
        }
      })
      .catch(() => {});
  };

  const markRead = (notification) => {
    if (!notification.is_read) {
      fetch(`${NOTIFICATIONS_URL}${notification.id}/read/`, {
        method: "POST",
        credentials: "include",
        headers: authHeaders(),
      })
        .then((response) => {
          if (response.ok) {
            setNotifications((items) =>
              (items || []).map((item) =>
                item.id === notification.id
                  ? { ...item, is_read: true }
                  : item
              )
            );
          }
        })
        .catch(() => {});
    }
  };

  return (
    <div className="notifications-wrap">
      <button
        className="icon-button"
        title="Notifications"
        onClick={() => setOpen((value) => !value)}
      >
        <Bell size={20} />

        {unread > 0 && <span className="notification-dot">{unread}</span>}
      </button>

      {open && (
        <div className="notifications-dropdown">
          <div className="notifications-header">
            <strong>Notifications</strong>

            {unread > 0 && (
              <button
                type="button"
                className="text-button"
                onClick={markAllRead}
              >
                <CheckCheck size={14} />
                Mark all read
              </button>
            )}
          </div>

          <div className="notifications-list">
            {!loaded && <div className="search-loading">Loading...</div>}

            {loaded && notifications.length === 0 && (
              <div className="search-loading">No notifications.</div>
            )}

            {loaded &&
              notifications.slice(0, 15).map((notification) => (
                <button
                  key={notification.id}
                  type="button"
                  className={`notification-item ${
                    notification.is_read ? "read" : ""
                  }`}
                  onClick={() => markRead(notification)}
                >
                  <strong>{notification.title}</strong>

                  {notification.message && (
                    <span>{notification.message}</span>
                  )}

                  <small>
                    {notification.notification_type_display || "System"}
                  </small>
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

const navigation = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, roles: [] },
  { label: "My Profile", path: "/profile", icon: UserRound, roles: [] },
  { label: "Parent Portal", path: "/parent-portal", icon: HeartHandshake, roles: ["parent"] },
  { label: "Students", path: "/students", icon: Users, roles: ["super_admin", "admin", "principal", "academic", "accountant", "teacher", "student"] },
  { label: "Teachers", path: "/teachers", icon: GraduationCap, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Staff", path: "/staff", icon: Users, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Assignments", path: "/assignments", icon: Layers, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Attendance", path: "/attendance", icon: ClipboardCheck, roles: ["super_admin", "admin", "principal", "academic", "teacher"] },
  { label: "Finance", path: "/finance", icon: Wallet, roles: ["super_admin", "admin", "principal", "academic", "accountant"] },
  { label: "Exams", path: "/exams", icon: FileText, roles: ["super_admin", "admin", "principal", "academic", "teacher"] },
  { label: "Report Cards", path: "/report-cards", icon: BookOpen, roles: ["super_admin", "admin", "principal", "academic", "teacher"] },
  { label: "Timetable", path: "/timetable", icon: CalendarDays, roles: ["super_admin", "admin", "principal", "academic", "teacher", "staff", "student", "parent"] },
  { label: "Campuses", path: "/campuses", icon: Building2, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Announcements", path: "/announcements", icon: Megaphone, roles: [] },
  { label: "Messages", path: "/messages", icon: Mail, roles: [] },
  { label: "SMS", path: "/sms", icon: MessageSquare, roles: ["super_admin", "admin"] },
  { label: "Library", path: "/library", icon: LibraryBig, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Transport", path: "/transport", icon: Bus, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Inventory", path: "/inventory", icon: Boxes, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Payroll", path: "/payroll", icon: Banknote, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Reports", path: "/reports", icon: BarChart3, roles: ["super_admin", "admin", "principal", "academic", "accountant", "hr"] },
  { label: "Events", path: "/events", icon: CalendarClock, roles: [] },
];

const systemNavigation = [
  { label: "Settings", path: "/settings", icon: Settings, roles: ["super_admin", "admin", "principal", "academic"] },
  { label: "Audit Logs", path: "/audit-logs", icon: ScrollText, roles: ["super_admin", "admin"] },
];

function Layout({ children }) {
  const { user, logout, hasRole } = useAuth();

  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("sidebar-collapsed") === "1"
  );
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleSidebar = () => {
    if (window.matchMedia("(max-width: 960px)").matches) {
      setMobileOpen((open) => !open);
    } else {
      setCollapsed((value) => {
        const next = !value;
        localStorage.setItem("sidebar-collapsed", next ? "1" : "0");
        return next;
      });
    }
  };

  const closeMobileDrawer = () => {
    if (window.matchMedia("(max-width: 960px)").matches) {
      setMobileOpen(false);
    }
  };

  const visibleNavigation = navigation.filter(
    (item) =>
      item.roles.length === 0 || hasRole(item.roles)
  );

  const visibleSystemNavigation = systemNavigation.filter(
    (item) =>
      item.roles.length === 0 || hasRole(item.roles)
  );

  const displayName =
    user?.first_name || user?.username || "User";

  const initials = displayName
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const roleLabel = user?.primary_role
    ? user.primary_role
        .replace("_", " ")
        .replace(/\b\w/g, (letter) =>
          letter.toUpperCase()
        )
    : "";

  const sidebarClass = [
    "sidebar",
    collapsed ? "collapsed" : "",
    mobileOpen ? "mobile-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="app">
      <aside className={sidebarClass}>
        <div className="sidebar-brand">
          <div className="brand-logo">PF</div>

          <div className="sidebar-brand-text">
            <strong>Perfect Foundation</strong>
            <span>School Management System</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <span className="sidebar-section-label">Main</span>

          {visibleNavigation.map(
            ({ label, path, icon: Icon }) => (
              <NavLink
                key={label}
                to={path}
                end={path === "/"}
                title={label}
                onClick={closeMobileDrawer}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? "active" : ""}`
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            )
          )}

          <span className="sidebar-section-label">
            System
          </span>

          {visibleSystemNavigation.map(
            ({ label, path, icon: Icon }) => (
              <NavLink
                key={label}
                to={path}
                title={label}
                onClick={closeMobileDrawer}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? "active" : ""}`
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            )
          )}
        </nav>

        <div className="sidebar-footer">
          <button
            className="sidebar-collapse"
            onClick={toggleSidebar}
            title={
              collapsed ? "Expand sidebar" : "Collapse sidebar"
            }
          >
            {collapsed ? (
              <PanelLeftOpen size={18} />
            ) : (
              <PanelLeftClose size={18} />
            )}
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={toggleSidebar}
        />
      )}

      <div className="app-body">
        <header className="topbar">
          <button
            className="icon-button sidebar-toggle"
            onClick={toggleSidebar}
            title="Toggle navigation"
          >
            <Menu size={20} />
          </button>

          <GlobalSearch />

          <div className="topbar-actions">
            <NotificationsBell />

            <div className="profile">
              {user?.photo_url ? (
                <img
                  className="avatar avatar-photo"
                  src={user.photo_url}
                  alt={displayName}
                />
              ) : (
                <div className="avatar">{initials}</div>
              )}

              <div>
                <strong>{displayName}</strong>
                <span>{roleLabel || "Member"}</span>
              </div>

              <button
                className="logout-button"
                title="Sign out"
                onClick={logout}
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </header>

        <main className="main">{children}</main>
      </div>
    </div>
  );
}

function RequireRoles({ roles, children }) {
  const { user, hasRole } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles.length > 0 && !hasRole(roles)) {
    return (
      <section className="content">
        <div className="state-card error">
          <strong>Access denied.</strong>
          <span>
            Your role does not have permission to view this page.
          </span>
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
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="auth-loading">
        <div className="brand-logo">PF</div>
        <span>Loading...</span>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/login" element={<Navigate to="/" replace />} />

        <Route path="/" element={<Dashboard />} />

        <Route
          path="/profile"
          element={<ProfilePage key={location.pathname} />}
        />
        <Route
          path="/profile/teacher/:id"
          element={<ProfilePage key={location.pathname} />}
        />
        <Route
          path="/profile/student/:id"
          element={<ProfilePage key={location.pathname} />}
        />
        <Route
          path="/profile/staff/:id"
          element={<ProfilePage key={location.pathname} />}
        />

        <Route
          path="/students"
          element={
            <RequireRoles
              roles={["super_admin", "admin", "principal", "academic", "accountant", "teacher", "student"]}
            >
              <StudentsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/parent-portal"
          element={
            <RequireRoles roles={["parent"]}>
              <ParentPortalPage />
            </RequireRoles>
          }
        />

        <Route
          path="/teachers"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
              <TeachersPage />
            </RequireRoles>
          }
        />

        <Route
          path="/staff"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
              <StaffPage />
            </RequireRoles>
          }
        />

        <Route
          path="/assignments"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
              <AssignmentsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/attendance"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher"]}>
              <AttendancePage />
            </RequireRoles>
          }
        />

        <Route
          path="/finance"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant"]}>
              <FinancePage />
            </RequireRoles>
          }
        />

        <Route
          path="/exams"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher"]}>
              <ExamsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/report-cards"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher"]}>
              <ReportCardsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/timetable"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "teacher", "staff", "student", "parent"]}>
              <TimetablePage />
            </RequireRoles>
          }
        />

        <Route
          path="/campuses"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
              <CampusesPage />
            </RequireRoles>
          }
        />

        <Route path="/events" element={<EventsPage />} />

        <Route
          path="/announcements"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr", "teacher", "staff", "student", "parent"]}>
              <AnnouncementsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/messages"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr", "teacher", "staff", "student", "parent"]}>
              <MessagesPage />
            </RequireRoles>
          }
        />

        <Route
          path="/sms"
          element={
            <RequireRoles roles={["super_admin", "admin"]}>
              <SMSPage />
            </RequireRoles>
          }
        />

        <Route
          path="/library"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
              <LibraryPage />
            </RequireRoles>
          }
        />

        <Route
          path="/transport"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
              <TransportPage />
            </RequireRoles>
          }
        />

        <Route
          path="/inventory"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
              <InventoryPage />
            </RequireRoles>
          }
        />

        <Route
          path="/payroll"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
              <PayrollPage />
            </RequireRoles>
          }
        />

        <Route
          path="/reports"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic", "accountant", "hr"]}>
              <ReportsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/settings"
          element={
            <RequireRoles roles={["super_admin", "admin", "principal", "academic"]}>
              <SettingsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/audit-logs"
          element={
            <RequireRoles roles={["super_admin", "admin"]}>
              <AuditLogsPage />
            </RequireRoles>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
