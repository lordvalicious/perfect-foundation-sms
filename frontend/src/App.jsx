import {
  useCallback,
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
import ProfileModal from "./pages/ProfileModal";
import StaffPage from "./pages/StaffPage";
import ParentPortalPage from "./pages/ParentPortalPage";
import LibraryPage from "./pages/LibraryPage";
import TransportPage from "./pages/TransportPage";
import InventoryPage from "./pages/InventoryPage";
import PayrollPage from "./pages/PayrollPage";
import ReportsPage from "./pages/ReportsPage";
import AnnouncementsPage from "./pages/AnnouncementsPage";
import MessagesPage from "./pages/MessagesPage";

const API_URL = "/api/dashboard/overview/";

const STUDENTS_API_URL = "/api/students/";

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

function useCountUp(value) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value === null || value === undefined) {
      setDisplay(0);
      return undefined;
    }

    const duration = 900;
    const start = performance.now();
    let frame;

    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(value * eased));

      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frame);
  }, [value]);

  return display;
}

function CountUp({ value }) {
  const display = useCountUp(value);

  return <strong>{display.toLocaleString()}</strong>;
}

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
   DASHBOARD
========================= */

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(API_URL, { credentials: "include" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load dashboard data.");
        }

        return response.json();
      })
      .then((data) => {
        setDashboard(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const stats = dashboard
    ? [
        {
          label: "Total Students",
          value: dashboard.students?.total ?? 0,
          icon: Users,
        },
        {
          label: "Active Students",
          value: dashboard.students?.active ?? 0,
          icon: GraduationCap,
        },
        {
          label: "Teachers",
          value: dashboard.teachers?.total ?? 0,
          icon: Users,
        },
        {
          label: "Campuses",
          value: dashboard.campuses ?? 0,
          icon: Building2,
        },
        {
          label: "Classes",
          value: dashboard.classes ?? 0,
          icon: BookOpen,
        },
        {
          label: "Sections",
          value: dashboard.sections ?? 0,
          icon: LayoutDashboard,
        },
        {
          label: "Enrollments",
          value: dashboard.enrollments ?? 0,
          icon: ClipboardCheck,
        },
      ]
    : [];

  return (
    <section className="content">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Home / Dashboard</p>

          <h2>Dashboard Overview</h2>

          <p className="subtitle">
            Welcome back. Here's what's happening at Perfect Foundation
            School.
          </p>
        </div>

        <div className="date-badge">
          <CalendarDays size={17} />
          <span>2026–2027</span>
        </div>
      </div>

      {loading && (
        <div className="state-card">
          Loading dashboard data...
        </div>
      )}

      {error && (
        <div className="state-card error">
          <strong>Unable to load dashboard.</strong>

          <span>
            Make sure Django is running at 127.0.0.1:8000.
          </span>

          <code>{error}</code>
        </div>
      )}

      {!loading && !error && dashboard && (
        <>
          <div className="stats-grid">
            {stats.map(({ label, value, icon: Icon }) => (
              <div className="stat-card" key={label}>
                <div className="stat-icon">
                  <Icon size={21} />
                </div>

                <div className="stat-info">
                  <span>{label}</span>
                  <CountUp value={value} />
                </div>
              </div>
            ))}
          </div>

          <div className="dashboard-grid">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>School Overview</h3>
                  <p>Current academic year statistics</p>
                </div>
              </div>

              <div className="overview-list">
                <div>
                  <span>Active students</span>
                  <strong>
                    {dashboard.students?.active ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Active teachers</span>
                  <strong>
                    {dashboard.teachers?.active ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Campuses</span>
                  <strong>{dashboard.campuses ?? 0}</strong>
                </div>

                <div>
                  <span>Classes</span>
                  <strong>{dashboard.classes ?? 0}</strong>
                </div>

                <div>
                  <span>Sections</span>
                  <strong>{dashboard.sections ?? 0}</strong>
                </div>

                <div>
                  <span>Enrollments</span>
                  <strong>{dashboard.enrollments ?? 0}</strong>
                </div>
              </div>
            </div>

            <div className="panel welcome-panel">
              <div className="welcome-icon">
                <GraduationCap size={30} />
              </div>

              <h3>Perfect Foundation School</h3>

              <p>
                Manage students, teachers, attendance, examinations,
                finance, report cards and timetables from one place.
              </p>

              <div className="campus-count">
                <Building2 size={17} />

                <strong>{dashboard.campuses ?? 0}</strong>

                <span>campuses connected</span>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

/*********************************
 * STUDENTS
 *********************************/

function StudentsPage() {
  const { hasRole } = useAuth();
  const campusSectionRefs = useRef({});

  const isStudentSelf =
    hasRole(["student"]) &&
    !hasRole([
      "super_admin",
      "admin",
      "principal",
      "academic",
      "accountant",
      "teacher",
      "staff",
    ]);

  const canManage = hasRole([
    "super_admin",
    "admin",
    "principal",
    "academic",
  ]);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [gender, setGender] = useState("");
  const [status, setStatus] = useState("");

  const [section, setSection] = useState("");
  const [campusOptions, setCampusOptions] = useState([]);
  const [sectionOptions, setSectionOptions] = useState([]);

  const [campusData, setCampusData] = useState({});

  const [showForm, setShowForm] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [saving, setSaving] = useState(false);

  const [profileView, setProfileView] = useState(null);

  const emptyForm = {
    admission_number: "",
    first_name: "",
    middle_name: "",
    last_name: "",
    gender: "",
    date_of_birth: "",
    phone: "",
    address: "",
    status: "active",
    admission_date: "",
    guardian_name: "",
    guardian_relationship: "",
    guardian_phone: "",
    guardian_alternate_phone: "",
    guardian_email: "",
    guardian_address: "",
  };

  const [form, setForm] = useState(emptyForm);
  const [photoFile, setPhotoFile] = useState(null);

  const [myProfile, setMyProfile] = useState(null);
  const [myProfileLoading, setMyProfileLoading] = useState(
    isStudentSelf
  );

  const buildStudentParams = (campusId, pageNumber) => {
    const params = new URLSearchParams();

    params.append("campus", campusId);
    params.append("page", pageNumber);

    if (search.trim()) {
      params.append("search", search.trim());
    }

    if (gender) {
      params.append("gender", gender);
    }

    if (status) {
      params.append("status", status);
    }

    if (section) {
      params.append("section", section);
    }

    return params;
  };

  const fetchCampusStudents = (campusId, pageNumber = 1) => {
    const params = buildStudentParams(campusId, pageNumber);

    setCampusData((prev) => ({
      ...prev,
      [campusId]: { ...(prev[campusId] || {}), loading: true },
    }));

    return fetch(`${STUDENTS_API_URL}?${params.toString()}`, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load students.");
        }

        return response.json();
      })
      .then((data) => {
        setCampusData((prev) => ({
          ...prev,
          [campusId]: {
            students: data.results || [],
            count: data.count || 0,
            page: pageNumber,
            next: data.next,
            previous: data.previous,
            loaded: true,
            loading: false,
            error: "",
          },
        }));
      })
      .catch((err) => {
        setCampusData((prev) => ({
          ...prev,
          [campusId]: {
            ...(prev[campusId] || {}),
            loaded: true,
            loading: false,
            error: err.message,
          },
        }));
      });
  };

  const fetchAllCampuses = (pageNumber = 1) => {
    campusOptions.forEach((campus) => {
      fetchCampusStudents(campus.id, pageNumber);
    });
  };

  useEffect(() => {
    if (isStudentSelf) {
      fetch("/api/students/me/", { credentials: "include" })
        .then((response) => {
          if (!response.ok) {
            throw new Error("No student profile linked.");
          }

          return response.json();
        })
        .then((data) => {
          setMyProfile(data);
          setError("");
        })
        .catch((err) => {
          setError(err.message);
        })
        .finally(() => {
          setMyProfileLoading(false);
        });

      return;
    }

    const loadCampusStudents = (campus, pageNumber) => {
      const params = new URLSearchParams();

      params.append("campus", campus.id);
      params.append("page", pageNumber);

      fetch(`${STUDENTS_API_URL}?${params.toString()}`, {
        credentials: "include",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to load students.");
          }

          return response.json();
        })
        .then((data) => {
          setCampusData((prev) => ({
            ...prev,
            [campus.id]: {
              students: data.results || [],
              count: data.count || 0,
              page: pageNumber,
              next: data.next,
              previous: data.previous,
              loaded: true,
              loading: false,
              error: "",
            },
          }));
        })
        .catch((err) => {
          setCampusData((prev) => ({
            ...prev,
            [campus.id]: {
              ...(prev[campus.id] || {}),
              loaded: true,
              loading: false,
              error: err.message,
            },
          }));
        });
    };

    fetch("/api/schools/campuses/", {
      credentials: "include",
    })
      .then((response) =>
        response.ok ? response.json() : []
      )
      .then((data) => {
        const campuses = Array.isArray(data) ? data : [];

        setCampusOptions(campuses);

        campuses.forEach((campus) => {
          loadCampusStudents(campus, 1);
        });
      })
      .catch(() => {});

    fetch("/api/schools/sections/", {
      credentials: "include",
    })
      .then((response) =>
        response.ok ? response.json() : []
      )
      .then((data) =>
        setSectionOptions(
          Array.isArray(data) ? data : []
        )
      )
      .catch(() => {});
  }, [isStudentSelf]);

  const viewCampusStudents = (campusId) => {
    campusSectionRefs.current[campusId]?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleSectionChange = (value) => {
    setSection(value);

    setTimeout(() => {
      fetchAllCampuses(1);
    }, 0);
  };

  const handleSearch = (event) => {
    event.preventDefault();
    fetchAllCampuses(1);
  };

  const clearFilters = () => {
    setSearch("");
    setGender("");
    setStatus("");
    setSection("");

    setTimeout(() => {
      fetchAllCampuses(1);
    }, 0);
  };

  /* --------------------------
     FORM HANDLING
  -------------------------- */

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handlePhoto = (event) => {
    setPhotoFile(event.target.files[0] || null);
  };

  const openAddStudent = () => {
    setEditingStudent(null);
    setPhotoFile(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const openEditStudent = (student) => {
    setEditingStudent(student);
    setPhotoFile(null);

    setForm({
      admission_number: student.admission_number || "",
      first_name: student.first_name || "",
      middle_name: student.middle_name || "",
      last_name: student.last_name || "",
      gender: student.gender || "",
      date_of_birth: student.date_of_birth || "",
      phone: student.phone || "",
      address: student.address || "",
      status: student.status || "active",
      admission_date: student.admission_date || "",
      guardian_name:
        student.guardian_details?.name || "",
      guardian_relationship:
        student.guardian_details?.relationship || "",
      guardian_phone:
        student.guardian_details?.phone || "",
      guardian_alternate_phone:
        student.guardian_details?.alternate_phone || "",
      guardian_email:
        student.guardian_details?.email || "",
      guardian_address:
        student.guardian_details?.address || "",
    });

    setShowForm(true);
  };

  const closeForm = () => {
    if (saving) return;

    setShowForm(false);
    setEditingStudent(null);
    setPhotoFile(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSaving(true);
    setError("");

    try {
      const isEditing = Boolean(editingStudent);

      const url = isEditing
        ? `${STUDENTS_API_URL}${editingStudent.id}/`
        : STUDENTS_API_URL;

      const body = new FormData();

      for (const [key, value] of Object.entries(form)) {
        body.append(key, value === "" ? "" : value);
      }

      if (photoFile) {
        body.append("photo", photoFile);
      }

      const response = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        credentials: "include",
        headers: authHeaders(),
        body,
      });

      const responseText = await response.text();

      let data = {};

      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        data = {};
      }

      if (!response.ok) {
        let message = "Unable to save student.";

        if (data && typeof data === "object") {
          message = Object.entries(data)
            .map(([field, value]) => {
              const text = Array.isArray(value)
                ? value.join(", ")
                : String(value);

              return `${field}: ${text}`;
            })
            .join(" | ");
        }

        if (
          !message ||
          message === "Unable to save student."
        ) {
          message =
            responseText ||
            `Request failed (${response.status})`;
        }

        throw new Error(message);
      }

      closeForm();
      await fetchAllCampuses(1);

      if (isStudentSelf) {
        fetch("/api/students/me/", {
          credentials: "include",
        })
          .then((response) => response.json())
          .then((profile) => setMyProfile(profile))
          .catch(() => {});
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (student) => {
    const confirmed = window.confirm(
      `Delete student "${student.full_name || student.admission_number}"? ` +
        "This cannot be undone."
    );

    if (!confirmed) return;

    setSaving(true);
    setError("");

    try {
      const response = await fetch(
        `${STUDENTS_API_URL}${student.id}/`,
        {
          method: "DELETE",
          credentials: "include",
          headers: authHeaders(),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to delete student.");
      }

      const campusId = student.current_enrollment?.campus_id;

      if (campusId) {
        const entry = campusData[campusId] || {};
        await fetchCampusStudents(campusId, entry.page || 1);
      } else {
        await fetchAllCampuses(1);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  /* --------------------------
     STUDENT SELF PROFILE
  -------------------------- */

  if (isStudentSelf) {
    return (
      <section className="content">
        <div className="page-header">
          <div>
            <div className="breadcrumb">Home / My Profile</div>
            <h2>My Profile</h2>

            <p className="subtitle">
              Your student information at Perfect Foundation
              School.
            </p>
          </div>
        </div>

        {myProfileLoading && (
          <div className="state-card">
            Loading your profile...
          </div>
        )}

        {!myProfileLoading && error && (
          <div className="state-card error">
            <strong>Unable to load your profile.</strong>
            <span>{error}</span>
          </div>
        )}

        {!myProfileLoading && !error && myProfile && (
          <div className="profile-grid">
            <div className="panel profile-card">
              {myProfile.photo_url ? (
                <img
                  className="profile-photo"
                  src={myProfile.photo_url}
                  alt={myProfile.full_name}
                />
              ) : (
                <div className="profile-photo placeholder">
                  {(myProfile.full_name || "S")
                    .charAt(0)
                    .toUpperCase()}
                </div>
              )}

              <h3>{myProfile.full_name}</h3>
              <span className="status-badge active">
                {myProfile.status}
              </span>

              <p className="muted">
                {myProfile.admission_number}
              </p>

              <div className="profile-detail">
                <strong>Date of Birth</strong>
                <span>{myProfile.date_of_birth || "—"}</span>
              </div>

              <div className="profile-detail">
                <strong>Gender</strong>
                <span>
                  {myProfile.gender
                    ? myProfile.gender.charAt(0).toUpperCase() +
                      myProfile.gender.slice(1)
                    : "—"}
                </span>
              </div>

              <div className="profile-detail">
                <strong>Phone</strong>
                <span>{myProfile.phone || "—"}</span>
              </div>

              <div className="profile-detail">
                <strong>Address</strong>
                <span>{myProfile.address || "—"}</span>
              </div>
            </div>

            <div className="profile-grid-main">
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3>Guardian</h3>
                    <p>Contact information of your guardian</p>
                  </div>
                </div>

                <div className="overview-list">
                  <div>
                    <span>Name</span>
                    <strong>
                      {myProfile.guardian_details?.name || "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Relationship</span>
                    <strong>
                      {myProfile.guardian_details?.relationship ||
                        "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Phone</span>
                    <strong>
                      {myProfile.guardian_details?.phone || "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Email</span>
                    <strong>
                      {myProfile.guardian_details?.email || "—"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3>Enrollments</h3>
                    <p>Classes you are enrolled in</p>
                  </div>
                </div>

                {(myProfile.enrollments || []).length === 0 ? (
                  <div className="state-card">
                    No enrollments found.
                  </div>
                ) : (
                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>ACADEMIC YEAR</th>
                          <th>CLASS</th>
                          <th>SECTION</th>
                          <th>STATUS</th>
                        </tr>
                      </thead>

                      <tbody>
                        {myProfile.enrollments.map(
                          (enrollment) => (
                            <tr key={enrollment.id}>
                              <td>
                                {enrollment.academic_year_name}
                              </td>
                              <td>
                                <strong>
                                  {enrollment.class_name}
                                </strong>
                              </td>
                              <td>{enrollment.section_name}</td>
                              <td>
                                <span
                                  className={`status-badge ${
                                    enrollment.status === "active"
                                      ? "active"
                                      : "inactive"
                                  }`}
                                >
                                  {enrollment.status}
                                </span>
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>
    );
  }

  /* --------------------------
     ADMIN / TEACHER LIST VIEW
  -------------------------- */

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <div className="breadcrumb">Home / Students</div>

          <h2>Students</h2>

          <p className="subtitle">
            Manage students enrolled at Perfect Foundation School.
          </p>
        </div>

        {canManage && (
          <button
            className="primary-button"
            onClick={openAddStudent}
          >
            + Add Student
          </button>
        )}
      </div>

      {/* Campus overview */}
      {campusOptions.length > 0 && (
        <div className="campus-cards">
          {campusOptions.map((item) => (
            <div key={item.id} className="campus-card">
              <div className="campus-card-header">
                <Building2 size={20} />
                <strong>{item.name}</strong>
              </div>

              <p className="campus-card-sub">
                {[item.city, item.address]
                  .filter(Boolean)
                  .join(", ") || "Perfect Foundation School"}
              </p>

              <div className="campus-card-stats">
                <div>
                  <span>{item.student_count || 0}</span>
                  <small>Students</small>
                </div>

                <div>
                  <span>{item.class_count || 0}</span>
                  <small>Classes</small>
                </div>

                <div>
                  <span>{item.section_count || 0}</span>
                  <small>Sections</small>
                </div>
              </div>

              <button
                className="primary-button campus-card-button"
                onClick={() => viewCampusStudents(item.id)}
              >
                View All Students
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="panel students-filters">
        <form onSubmit={handleSearch}>
          <div className="filter-row">
            <div className="filter-search">
              <Search size={18} />

              <input
                type="text"
                placeholder="Search by name, admission number or phone..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>

            <select
              value={gender}
              onChange={(event) => {
                setGender(event.target.value);
                setTimeout(() => {
                  fetchAllCampuses(1);
                }, 0);
              }}
            >
              <option value="">All genders</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>

            <select
              value={section}
              onChange={(event) =>
                handleSectionChange(event.target.value)
              }
            >
              <option value="">All sections</option>

              {sectionOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.class_name} - {item.name}
                </option>
              ))}
            </select>

            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setTimeout(() => {
                  fetchAllCampuses(1);
                }, 0);
              }}
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>

            <button type="submit" className="primary-button">
              Search
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={clearFilters}
            >
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Student lists by campus */}
      {campusOptions.length === 0 ? (
        <div className="state-card">
          No campuses found.
        </div>
      ) : (
        <div className="campus-student-lists">
          {campusOptions.map((campus) => {
            const data =
              campusData[campus.id] || {
                students: [],
                count: 0,
                page: 1,
                next: null,
                previous: null,
                loading: true,
                error: "",
              };

            const campusTotalPages = Math.max(
              1,
              Math.ceil(data.count / 20)
            );

            return (
              <div
                key={campus.id}
                className="panel campus-student-list"
                ref={(el) => {
                  campusSectionRefs.current[campus.id] = el;
                }}
              >
                <div className="panel-header">
                  <div>
                    <h3>{campus.name}</h3>

                    <p>
                      {data.count.toLocaleString()} students
                      found
                    </p>
                  </div>
                </div>

                {data.loading && (
                  <div className="state-card">
                    Loading students...
                  </div>
                )}

                {!data.loading && data.error && (
                  <div className="state-card error">
                    <strong>
                      Unable to load students.
                    </strong>

                    <span>
                      Make sure Django is running at
                      127.0.0.1:8000.
                    </span>

                    <code>{data.error}</code>
                  </div>
                )}

                {!data.loading && !data.error && (
                  <>
                    {data.students.length === 0 ? (
                      <div className="state-card">
                        No students found.
                      </div>
                    ) : (
                      <div className="students-table-wrapper">
                        <table className="students-table">
                          <thead>
                            <tr>
                              <th>Student</th>
                              <th>Admission No.</th>
                              <th>Class</th>
                              <th>Section</th>
                              <th>Date of Birth</th>
                              <th>Gender</th>
                              <th>Guardian</th>
                              <th>Phone</th>
                              <th>Status</th>
                              <th></th>
                            </tr>
                          </thead>

                          <tbody>
                            {data.students.map((student) => (
                              <tr key={student.id}>
                                <td>
                                  <div className="student-name-cell">
                                    {student.photo_url ? (
                                      <img
                                        className="table-photo"
                                        src={student.photo_url}
                                        alt={student.full_name}
                                      />
                                    ) : (
                                      <div className="table-avatar">
                                        {(
                                          student.full_name ||
                                          "S"
                                        )
                                          .charAt(0)
                                          .toUpperCase()}
                                      </div>
                                    )}

                                    <strong>
                                      {student.full_name ||
                                        `${student.first_name ||
                                          ""} ${
                                          student.middle_name ||
                                          ""
                                        } ${
                                          student.last_name ||
                                          ""
                                        }`.trim()}
                                    </strong>
                                  </div>
                                </td>

                                <td>
                                  <strong>
                                    {student.admission_number}
                                  </strong>
                                </td>

                                <td>
                                  {student.current_enrollment
                                    ?.class_name || "—"}
                                </td>

                                <td>
                                  {student.current_enrollment
                                    ?.section_name || "—"}
                                </td>

                                <td>
                                  {student.date_of_birth ||
                                    "—"}
                                </td>

                                <td>
                                  {student.gender
                                    ? student.gender
                                        .charAt(0)
                                        .toUpperCase() +
                                      student.gender.slice(1)
                                    : "—"}
                                </td>

                                <td>
                                  {student.guardian_details
                                    ?.name || "—"}
                                </td>

                                <td>{student.phone || "—"}</td>

                                <td>
                                  <span
                                    className={`status-badge ${
                                      student.status ===
                                      "active"
                                        ? "active"
                                        : "inactive"
                                    }`}
                                  >
                                    {student.status || "—"}
                                  </span>
                                </td>

                                <td>
                                  <button
                                    className="table-action"
                                    onClick={() =>
                                      setProfileView({
                                        type: "student",
                                        id: student.id,
                                      })
                                    }
                                  >
                                    View Profile
                                  </button>

                                  {canManage && (
                                    <>
                                      <button
                                        className="table-action"
                                        onClick={() =>
                                          openEditStudent(
                                            student
                                          )
                                        }
                                      >
                                        Edit
                                      </button>

                                      <button
                                        className="table-action danger"
                                        onClick={() =>
                                          handleDelete(student)
                                        }
                                      >
                                        Delete
                                      </button>
                                    </>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {data.count > 0 && (
                      <div className="pagination">
                        <button
                          disabled={!data.previous}
                          onClick={() =>
                            fetchCampusStudents(
                              campus.id,
                              data.page - 1
                            )
                          }
                        >
                          Previous
                        </button>

                        <span>
                          Page {data.page} of{" "}
                          {campusTotalPages}
                        </span>

                        <button
                          disabled={!data.next}
                          onClick={() =>
                            fetchCampusStudents(
                              campus.id,
                              data.page + 1
                            )
                          }
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add / Edit Student Modal */}
      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeForm();
            }
          }}
        >
          <div className="teacher-modal student-modal">
            <div className="modal-header">
              <div>
                <h3>
                  {editingStudent
                    ? "Edit Student"
                    : "Add Student"}
                </h3>

                <p>
                  {editingStudent
                    ? "Update student information."
                    : "Create a new student profile."}
                </p>
              </div>

              <button
                className="modal-close"
                onClick={closeForm}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-section">
                <h4>Personal Information</h4>

                <div className="form-grid">
                  <label>
                    Admission Number
                    <input
                      name="admission_number"
                      value={form.admission_number}
                      onChange={handleChange}
                      placeholder="PF-ST-0001"
                      required
                    />
                  </label>

                  <label>
                    Gender
                    <select
                      name="gender"
                      value={form.gender}
                      onChange={handleChange}
                      required
                    >
                      <option value="">Select gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </label>

                  <label>
                    First Name
                    <input
                      name="first_name"
                      value={form.first_name}
                      onChange={handleChange}
                      placeholder="First name"
                      required
                    />
                  </label>

                  <label>
                    Middle Name
                    <input
                      name="middle_name"
                      value={form.middle_name}
                      onChange={handleChange}
                      placeholder="Middle name"
                    />
                  </label>

                  <label>
                    Last Name
                    <input
                      name="last_name"
                      value={form.last_name}
                      onChange={handleChange}
                      placeholder="Last name"
                    />
                  </label>

                  <label>
                    Date of Birth
                    <input
                      type="date"
                      name="date_of_birth"
                      value={form.date_of_birth}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Admission Date
                    <input
                      type="date"
                      name="admission_date"
                      value={form.admission_date}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Status
                    <select
                      name="status"
                      value={form.status}
                      onChange={handleChange}
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="graduated">
                        Graduated
                      </option>
                      <option value="withdrawn">
                        Withdrawn
                      </option>
                    </select>
                  </label>

                  <label>
                    Photo
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhoto}
                    />
                  </label>

                  {photoFile && (
                    <div className="photo-preview">
                      <img
                        src={URL.createObjectURL(photoFile)}
                        alt="preview"
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="form-section">
                <h4>Contact Information</h4>

                <div className="form-grid">
                  <label>
                    Phone
                    <input
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="03XX-XXXXXXX"
                    />
                  </label>

                  <label>
                    Address
                    <input
                      name="address"
                      value={form.address}
                      onChange={handleChange}
                      placeholder="Home address"
                    />
                  </label>
                </div>
              </div>

              <div className="form-section">
                <h4>Guardian Information</h4>

                <div className="form-grid">
                  <label>
                    Guardian Name
                    <input
                      name="guardian_name"
                      value={form.guardian_name}
                      onChange={handleChange}
                      placeholder="Full name"
                      required={!editingStudent}
                    />
                  </label>

                  <label>
                    Relationship
                    <input
                      name="guardian_relationship"
                      value={form.guardian_relationship}
                      onChange={handleChange}
                      placeholder="e.g. Father, Mother"
                      required={!editingStudent}
                    />
                  </label>

                  <label>
                    Guardian Phone
                    <input
                      name="guardian_phone"
                      value={form.guardian_phone}
                      onChange={handleChange}
                      placeholder="03XX-XXXXXXX"
                      required={!editingStudent}
                    />
                  </label>

                  <label>
                    Alternate Phone
                    <input
                      name="guardian_alternate_phone"
                      value={form.guardian_alternate_phone}
                      onChange={handleChange}
                      placeholder="Alternate phone"
                    />
                  </label>

                  <label>
                    Guardian Email
                    <input
                      type="email"
                      name="guardian_email"
                      value={form.guardian_email}
                      onChange={handleChange}
                      placeholder="guardian@example.com"
                    />
                  </label>

                  <label>
                    Guardian Address
                    <input
                      name="guardian_address"
                      value={form.guardian_address}
                      onChange={handleChange}
                      placeholder="Guardian address"
                    />
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingStudent
                    ? "Save Changes"
                    : "Add Student"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {profileView && (
        <ProfileModal
          type={profileView.type}
          id={profileView.id}
          onClose={() => setProfileView(null)}
        />
      )}
    </section>
  );
}

/* =========================
   TEACHERS MODULE
========================= */

const TEACHERS_API_URL = "/api/teachers/";

function TeachersPage() {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [campus, setCampus] = useState("");
  const [gender, setGender] = useState("");
  const [status, setStatus] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);

  const [profileView, setProfileView] = useState(null);

  const emptyForm = {
    employee_number: "",
    first_name: "",
    last_name: "",
    gender: "",
    date_of_birth: "",
    phone: "",
    email: "",
    campus: "",
    joining_date: "",
    designation: "Teacher",
    status: "active",
    create_account: false,
    username: "",
    password: "",
  };

  const [form, setForm] = useState(emptyForm);
  const [photoFile, setPhotoFile] = useState(null);
  const [accountCreated, setAccountCreated] = useState(null);

  /* =========================
     LOAD TEACHERS
  ========================= */

  const loadTeachersData = useCallback(() => {
    return fetch(TEACHERS_API_URL, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load teachers.");
        }

        return response.json();
      })
      .then((data) => {
        const teacherData = Array.isArray(data)
          ? data
          : data.results || data.teachers || [];

        setTeachers(teacherData);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const loadTeachers = () => {
    setLoading(true);
    setError("");

    return loadTeachersData();
  };

  useEffect(() => {
    loadTeachersData();
  }, [loadTeachersData]);

  /* =========================
     FORM HANDLING
  ========================= */

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handlePhoto = (event) => {
    setPhotoFile(event.target.files[0] || null);
  };

  const openAddTeacher = () => {
    setEditingTeacher(null);
    setPhotoFile(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const openEditTeacher = (teacher) => {
    setEditingTeacher(teacher);
    setPhotoFile(null);

    setForm({
      employee_number: teacher.employee_number || "",
      first_name:
        teacher.first_name ||
        teacher.user?.first_name ||
        "",
      last_name:
        teacher.last_name ||
        teacher.user?.last_name ||
        "",
      gender: teacher.gender || "",
      date_of_birth: teacher.date_of_birth || "",
      phone: teacher.phone || "",
      email: teacher.email || "",
      campus:
        teacher.campus?.id ||
        teacher.campus ||
        "",
      joining_date: teacher.joining_date || "",
      designation: teacher.designation || "Teacher",
      status: teacher.status || "active",
      create_account: false,
      username: teacher.linked_username || "",
      password: "",
    });

    setShowForm(true);
  };

  const closeForm = () => {
    if (saving) return;

    setShowForm(false);
    setEditingTeacher(null);
    setPhotoFile(null);
    setForm(emptyForm);
  };

  /* =========================
     SAVE TEACHER
  ========================= */

  const handleSubmit = async (event) => {
  event.preventDefault();

  setSaving(true);
  setError("");

  try {
    const isEditing = Boolean(editingTeacher);

    const url = isEditing
      ? `${TEACHERS_API_URL}${editingTeacher.id}/`
      : TEACHERS_API_URL;

    const csrfToken = getCookie("csrftoken");

    const headers = {};

    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    const body = new FormData();

    body.append("employee_number", form.employee_number);
    body.append("first_name", form.first_name);
    body.append("last_name", form.last_name);
    body.append("gender", form.gender);
    body.append(
      "date_of_birth",
      form.date_of_birth || ""
    );
    body.append("phone", form.phone || "");
    body.append("email", form.email || "");
    body.append("campus", form.campus || "");
    body.append(
      "joining_date",
      form.joining_date || ""
    );
    body.append("designation", form.designation || "");
    body.append("status", form.status);

    body.append(
      "create_account",
      String(Boolean(form.create_account))
    );

    if (form.create_account) {
      body.append("username", form.username || "");
      body.append("password", form.password || "");
    }

    if (photoFile) {
      body.append("photo", photoFile);
    }

    const response = await fetch(url, {
      method: isEditing ? "PUT" : "POST",
      credentials: "include",
      headers,
      body,
    });

    // Read response body ONLY ONCE
    const responseText = await response.text();

    let data = {};

    try {
      data = responseText
        ? JSON.parse(responseText)
        : {};
    } catch {
      data = {};
    }

    if (!response.ok) {
      let message = "Unable to save teacher.";

      if (data && typeof data === "object") {
        message = Object.entries(data)
          .map(([field, value]) => {
            const text = Array.isArray(value)
              ? value.join(", ")
              : String(value);

            return `${field}: ${text}`;
          })
          .join(" | ");
      }

      if (
        !message ||
        message === "Unable to save teacher."
      ) {
        message =
          responseText ||
          `Request failed (${response.status})`;
      }

      throw new Error(message);
    }

    closeForm();
    await loadTeachers();

    if (data.linked_username && data.generated_password) {
      setAccountCreated({
        username: data.linked_username,
        password: data.generated_password,
        name: getTeacherName({
          first_name: data.first_name,
          last_name: data.last_name,
        }),
      });
    }

  } catch (err) {
    setError(err.message);

  } finally {
    setSaving(false);
  }
};

  const handleDeleteTeacher = async (teacher) => {
    const confirmed = window.confirm(
      `Delete teacher "${getTeacherName(teacher)}"? ` +
        "This cannot be undone."
    );

    if (!confirmed) return;

    setSaving(true);
    setError("");

    try {
      const response = await fetch(
        `${TEACHERS_API_URL}${teacher.id}/`,
        {
          method: "DELETE",
          credentials: "include",
          headers: authHeaders(),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to delete teacher.");
      }

      await loadTeachers();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  /* =========================
     FILTERS
  ========================= */

  const filteredTeachers = teachers.filter((teacher) => {
    const fullName =
      `${teacher.first_name || teacher.user?.first_name || ""} ${
        teacher.last_name || teacher.user?.last_name || ""
      }`.trim();

    const employeeNumber =
      teacher.employee_number || "";

    const phone = teacher.phone || "";

    const campusName =
      typeof teacher.campus === "object"
        ? teacher.campus?.name || ""
        : teacher.campus_name || "";

    const teacherGender =
      teacher.gender || "";

    const teacherStatus =
      teacher.status || "";

    const searchValue = search.toLowerCase();

    const matchesSearch =
      !search ||
      fullName.toLowerCase().includes(searchValue) ||
      employeeNumber.toLowerCase().includes(searchValue) ||
      phone.toLowerCase().includes(searchValue);

    const matchesCampus =
      !campus ||
      campusName.toLowerCase() === campus.toLowerCase();

    const matchesGender =
      !gender ||
      teacherGender.toLowerCase() === gender.toLowerCase();

    const matchesStatus =
      !status ||
      teacherStatus.toLowerCase() === status.toLowerCase();

    return (
      matchesSearch &&
      matchesCampus &&
      matchesGender &&
      matchesStatus
    );
  });

  /* =========================
     UNIQUE CAMPUSES
  ========================= */

  const campusOptions = [
    ...new Set(
      teachers
        .map((teacher) =>
          typeof teacher.campus === "object"
            ? teacher.campus?.name
            : teacher.campus_name || teacher.campus
        )
        .filter(Boolean)
    ),
  ];

  /* =========================
     HELPERS
  ========================= */

  const getTeacherName = (teacher) => {
    const firstName =
      teacher.first_name ||
      teacher.user?.first_name ||
      "";

    const lastName =
      teacher.last_name ||
      teacher.user?.last_name ||
      "";

    return `${firstName} ${lastName}`.trim() || "Unnamed Teacher";
  };

  const getCampusName = (teacher) => {
    if (typeof teacher.campus === "object") {
      return teacher.campus?.name || "—";
    }

    return teacher.campus_name || teacher.campus || "—";
  };

  const getStatus = (teacher) => {
    return teacher.status || "active";
  };

  const getStatusLabel = (value) => {
    if (!value) return "Active";

    return value.charAt(0).toUpperCase() + value.slice(1);
  };

  return (
    <section className="content">
      {/* PAGE HEADER */}

      <div className="page-header">
        <div>
          <div className="breadcrumb">
            Home / Teachers
          </div>

          <h2>Teachers</h2>

          <p className="subtitle">
            Manage teachers and teaching staff at Perfect
            Foundation School.
          </p>
        </div>
      </div>

      {/* SUCCESS (ACCOUNT CREATED) */}

      {accountCreated && (
        <div className="state-card success">
          <strong>
            Login account created for {accountCreated.name}.
          </strong>

          <span>
            Username:{" "}
            <strong>{accountCreated.username}</strong>
          </span>

          <span>
            Password:{" "}
            <strong>{accountCreated.password}</strong>
          </span>

          <span>
            Share these credentials with the teacher and
            remind them to change their password after first
            login.
          </span>

          <button
            className="secondary-button"
            onClick={() => setAccountCreated(null)}
            style={{ alignSelf: "flex-start" }}
          >
            Got It
          </button>
        </div>
      )}

      {/* ERROR */}

      {error && (
        <div className="state-card error">
          <strong>Unable to complete request.</strong>

          <span>{error}</span>

          <button
            className="secondary-button"
            onClick={loadTeachers}
          >
            Try Again
          </button>
        </div>
      )}

      {/* SEARCH PANEL */}

      <div className="teacher-filter-panel">
        <div className="teacher-search">
          <Search size={18} />

          <input
            type="text"
            placeholder="Search by name, employee number or phone..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <select
          value={campus}
          onChange={(event) =>
            setCampus(event.target.value)
          }
        >
          <option value="">All campuses</option>

          {campusOptions.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select
          value={gender}
          onChange={(event) =>
            setGender(event.target.value)
          }
        >
          <option value="">All genders</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>

        <select
          value={status}
          onChange={(event) =>
            setStatus(event.target.value)
          }
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>

        <button
          className="primary-button"
          onClick={loadTeachers}
        >
          Search
        </button>

        <button
          className="secondary-button"
          onClick={() => {
            setSearch("");
            setCampus("");
            setGender("");
            setStatus("");
          }}
        >
          Clear
        </button>
      </div>

      {/* TEACHER LIST */}

      <div className="panel teacher-list-panel">
        <div className="teacher-list-header">
          <div>
            <h3>Teacher List</h3>

            <p>
              {loading
                ? "Loading teachers..."
                : `${filteredTeachers.length} teachers found`}
            </p>
          </div>

          <button
            className="primary-button add-teacher-button"
            onClick={openAddTeacher}
          >
            + Add Teacher
          </button>
        </div>

        {loading ? (
          <div className="state-card">
            Loading teacher data...
          </div>
        ) : filteredTeachers.length === 0 ? (
          <div className="empty-state">
            <GraduationCap size={42} />

            <h3>No teachers found</h3>

            <p>
              No teachers match the current search or filters.
            </p>

            <button
              className="primary-button"
              onClick={openAddTeacher}
            >
              + Add Teacher
            </button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>EMPLOYEE NO.</th>
                  <th>TEACHER</th>
                  <th>DESIGNATION</th>
                  <th>CAMPUS</th>
                  <th>PHONE</th>
                  <th>GENDER</th>
                  <th>STATUS</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {filteredTeachers.map((teacher) => (
                  <tr key={teacher.id}>
                    <td>
                      <strong>
                        {teacher.employee_number || "—"}
                      </strong>
                    </td>

                    <td>
                      <div className="teacher-name-cell">
                        {teacher.photo_url ? (
                          <img
                            className="table-photo"
                            src={teacher.photo_url}
                            alt={getTeacherName(teacher)}
                          />
                        ) : (
                          <div className="teacher-avatar">
                            {getTeacherName(teacher)
                              .charAt(0)
                              .toUpperCase()}
                          </div>
                        )}

                        <div>
                          <strong>
                            {getTeacherName(teacher)}
                          </strong>

                          <span>
                            {teacher.email || "—"}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td>
                      {teacher.designation || "Teacher"}
                    </td>

                    <td>
                      {getCampusName(teacher)}
                    </td>

                    <td>
                      {teacher.phone || "—"}
                    </td>

                    <td>
                      {teacher.gender
                        ? teacher.gender
                            .charAt(0)
                            .toUpperCase() +
                          teacher.gender.slice(1)
                        : "—"}
                    </td>

                    <td>
                      <span
                        className={`status-badge ${getStatus(
                          teacher
                        )}`}
                      >
                        {getStatusLabel(
                          getStatus(teacher)
                        )}
                      </span>
                    </td>

                    <td>
                      <button
                        className="table-action"
                        onClick={() =>
                          setProfileView({
                            type: "teacher",
                            id: teacher.id,
                          })
                        }
                      >
                        View Profile
                      </button>

                      <button
                        className="table-action"
                        onClick={() =>
                          openEditTeacher(teacher)
                        }
                      >
                        Edit
                      </button>

                      <button
                        className="table-action danger"
                        onClick={() =>
                          handleDeleteTeacher(teacher)
                        }
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ADD / EDIT MODAL */}

      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeForm();
            }
          }}
        >
          <div className="teacher-modal">
            <div className="modal-header">
              <div>
                <h3>
                  {editingTeacher
                    ? "Edit Teacher"
                    : "Add Teacher"}
                </h3>

                <p>
                  {editingTeacher
                    ? "Update teacher information."
                    : "Create a new teacher profile."}
                </p>
              </div>

              <button
                className="modal-close"
                onClick={closeForm}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-section">
                <h4>Personal Information</h4>

                <div className="form-grid">
                  <label>
                    Employee Number
                    <input
                      name="employee_number"
                      value={form.employee_number}
                      onChange={handleChange}
                      placeholder="PF-T-0001"
                      required
                    />
                  </label>

                  <label>
                    Designation
                    <input
                      name="designation"
                      value={form.designation}
                      onChange={handleChange}
                      placeholder="Teacher"
                    />
                  </label>

                  <label>
                    First Name
                    <input
                      name="first_name"
                      value={form.first_name}
                      onChange={handleChange}
                      placeholder="First name"
                      required
                    />
                  </label>

                  <label>
                    Last Name
                    <input
                      name="last_name"
                      value={form.last_name}
                      onChange={handleChange}
                      placeholder="Last name"
                      required
                    />
                  </label>

                  <label>
                    Gender
                    <select
                      name="gender"
                      value={form.gender}
                      onChange={handleChange}
                      required
                    >
                      <option value="">
                        Select gender
                      </option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </label>

                  <label>
                    Date of Birth
                    <input
                      type="date"
                      name="date_of_birth"
                      value={form.date_of_birth}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Photo
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhoto}
                    />
                  </label>

                  {photoFile && (
                    <div className="photo-preview">
                      <img
                        src={URL.createObjectURL(photoFile)}
                        alt="preview"
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="form-section">
                <h4>Contact Information</h4>

                <div className="form-grid">
                  <label>
                    Phone
                    <input
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="03XX-XXXXXXX"
                    />
                  </label>

                  <label>
                    Email
                    <input
                      type="email"
                      name="email"
                      value={form.email}
                      onChange={handleChange}
                      placeholder="teacher@example.com"
                    />
                  </label>
                </div>
              </div>

              <div className="form-section">
                <h4>Employment</h4>

                <div className="form-grid">
                  <label>
                    Campus
                    <select
                      name="campus"
                      value={form.campus}
                      onChange={handleChange}
                    >
                      <option value="">
                        Select campus
                      </option>

                      {campusOptions.map((item) => (
                        <option
                          key={item}
                          value={item}
                        >
                          {item}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Joining Date
                    <input
                      type="date"
                      name="joining_date"
                      value={form.joining_date}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Status
                    <select
                      name="status"
                      value={form.status}
                      onChange={handleChange}
                    >
                      <option value="active">
                        Active
                      </option>

                      <option value="inactive">
                        Inactive
                      </option>
                    </select>
                  </label>
                </div>
              </div>

              <div className="form-section">
                <h4>Login Account</h4>

                {editingTeacher &&
                  editingTeacher.linked_username && (
                    <p className="field-hint">
                      This teacher is linked to username{" "}
                      <strong>
                        {editingTeacher.linked_username}
                      </strong>
                      .
                    </p>
                  )}

                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={Boolean(form.create_account)}
                    onChange={(event) =>
                      setForm((previous) => ({
                        ...previous,
                        create_account:
                          event.target.checked,
                      }))
                    }
                  />

                  <span>
                    {editingTeacher &&
                    editingTeacher.linked_username
                      ? "Reset this teacher's password"
                      : "Create a login account for this teacher"}
                  </span>
                </label>

                {form.create_account && (
                  <div className="form-grid">
                    {!(editingTeacher &&
                      editingTeacher.linked_username) && (
                      <label>
                        Username
                        <input
                          name="username"
                          value={form.username}
                          onChange={handleChange}
                          placeholder="Leave blank to auto-generate"
                        />
                      </label>
                    )}

                    <label>
                      Password
                      <input
                        type="text"
                        name="password"
                        value={form.password}
                        onChange={handleChange}
                        placeholder="Leave blank to auto-generate"
                        autoComplete="new-password"
                      />
                    </label>
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingTeacher
                    ? "Save Changes"
                    : "Add Teacher"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {profileView && (
        <ProfileModal
          type={profileView.type}
          id={profileView.id}
          onClose={() => setProfileView(null)}
        />
      )}
    </section>
  );
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
