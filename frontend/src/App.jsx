import { useCallback, useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Navigate,
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
  Menu,
  LogOut,
  CalendarClock,
  ScrollText,
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

const API_URL = "/api/dashboard/overview/";

const STUDENTS_API_URL = "/api/students/";

const navigation = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, roles: [] },
  { label: "Students", path: "/students", icon: Users, roles: ["super_admin", "admin", "academic", "accountant", "teacher"] },
  { label: "Teachers", path: "/teachers", icon: GraduationCap, roles: ["super_admin", "admin", "academic"] },
  { label: "Attendance", path: "/attendance", icon: ClipboardCheck, roles: ["super_admin", "admin", "academic", "teacher"] },
  { label: "Finance", path: "/finance", icon: Wallet, roles: ["super_admin", "admin", "academic", "accountant"] },
  { label: "Exams", path: "/exams", icon: FileText, roles: ["super_admin", "admin", "academic", "teacher"] },
  { label: "Report Cards", path: "/report-cards", icon: BookOpen, roles: ["super_admin", "admin", "academic", "teacher"] },
  { label: "Timetable", path: "/timetable", icon: CalendarDays, roles: ["super_admin", "admin", "academic", "teacher", "staff"] },
  { label: "Campuses", path: "/campuses", icon: Building2, roles: ["super_admin", "admin", "academic"] },
  { label: "Events", path: "/events", icon: CalendarClock, roles: [] },
];

const systemNavigation = [
  { label: "Settings", path: "/settings", icon: Settings, roles: ["super_admin", "admin", "academic"] },
  { label: "Audit Logs", path: "/audit-logs", icon: ScrollText, roles: ["super_admin", "admin"] },
];

function Layout({ children }) {
  const { user, logout, hasRole } = useAuth();

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

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">PF</div>

          <div>
            <strong>Perfect Foundation</strong>
            <span>School Management</span>
          </div>
        </div>

        <nav>
          <div className="nav-title">MAIN MENU</div>

          {visibleNavigation.map(
            ({ label, path, icon: Icon }) => (
              <NavLink
                key={label}
                to={path}
                end={path === "/"}
                className={({ isActive }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
              >
                <Icon size={19} />
                <span>{label}</span>
              </NavLink>
            )
          )}

          <div className="nav-title settings-title">SYSTEM</div>

          {visibleSystemNavigation.map(
            ({ label, path, icon: Icon }) => (
              <NavLink
                key={label}
                to={path}
                className={({ isActive }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
              >
                <Icon size={19} />
                <span>{label}</span>
              </NavLink>
            )
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="school-year">Academic Year</div>
          <strong>2026–2027</strong>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="mobile-menu">
            <Menu size={22} />
          </button>

          <div className="search">
            <Search size={18} />
            <input placeholder="Search students, teachers..." />
          </div>

          <div className="topbar-right">
            <button className="icon-button">
              <Bell size={20} />
              <span className="notification-dot" />
            </button>

            <div className="profile">
              <div className="avatar">{initials}</div>

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

        {children}
      </main>
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
                  <strong>{value.toLocaleString()}</strong>
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
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [gender, setGender] = useState("");
  const [status, setStatus] = useState("");

  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
  });

  const loadStudents = useCallback((params) => {
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
        setStudents(data.results || []);

        setPagination({
          count: data.count || 0,
          next: data.next,
          previous: data.previous,
        });

        setPage(Number(params.get("page") || 1));
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const fetchStudents = (pageNumber = 1) => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();

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

    return loadStudents(params);
  };

  useEffect(() => {
    loadStudents(new URLSearchParams({ page: "1" }));
  }, [loadStudents]);

  const handleSearch = (event) => {
    event.preventDefault();
    fetchStudents(1);
  };

  const clearFilters = () => {
    setSearch("");
    setGender("");
    setStatus("");

    setTimeout(() => {
      fetchStudents(1);
    }, 0);
  };

  const totalPages = Math.ceil(
    pagination.count / 20
  );

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            Home / Students
          </div>

          <h2>Students</h2>

          <p className="subtitle">
            Manage students enrolled at Perfect Foundation School.
          </p>
        </div>
      </div>

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
                  fetchStudents(1);
                }, 0);
              }}
            >
              <option value="">All genders</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>

            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setTimeout(() => {
                  fetchStudents(1);
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

      {/* Student list */}
      <div className="panel">

        <div className="panel-header">
          <div>
            <h3>Student List</h3>

            <p>
              {pagination.count.toLocaleString()} students
              found
            </p>
          </div>

          <button className="primary-button">
            + Add Student
          </button>
        </div>

        {loading && (
          <div className="state-card">
            Loading students...
          </div>
        )}

        {error && (
          <div className="state-card error">
            <strong>Unable to load students.</strong>

            <span>
              Make sure Django is running at
              127.0.0.1:8000.
            </span>

            <code>{error}</code>
          </div>
        )}

        {!loading && !error && (
          <>
            {students.length === 0 ? (
              <div className="state-card">
                No students found.
              </div>
            ) : (
              <div className="students-table-wrapper">
                <table className="students-table">
                  <thead>
                    <tr>
                      <th>Admission No.</th>
                      <th>Student</th>
                      <th>Date of Birth</th>
                      <th>Gender</th>
                      <th>Guardian</th>
                      <th>Phone</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {students.map((student) => (
                      <tr key={student.id}>

                        <td>
                          <strong>
                            {student.admission_number}
                          </strong>
                        </td>

                        <td>
                          <div className="student-name">
                            {student.full_name ||
                              `${student.first_name || ""} ${
                                student.middle_name || ""
                              } ${
                                student.last_name || ""
                              }`.trim()}
                          </div>
                        </td>

                        <td>
                          {student.date_of_birth || "—"}
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
                          {student.guardian_details?.name ||
                            "—"}
                        </td>

                        <td>
                          {student.phone || "—"}
                        </td>

                        <td>
                          <span
                            className={`status-badge ${
                              student.status === "active"
                                ? "active"
                                : "inactive"
                            }`}
                          >
                            {student.status || "—"}
                          </span>
                        </td>

                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {pagination.count > 0 && (
              <div className="pagination">

                <button
                  disabled={!pagination.previous}
                  onClick={() =>
                    fetchStudents(page - 1)
                  }
                >
                  Previous
                </button>

                <span>
                  Page {page} of {totalPages}
                </span>

                <button
                  disabled={!pagination.next}
                  onClick={() =>
                    fetchStudents(page + 1)
                  }
                >
                  Next
                </button>

              </div>
            )}
          </>
        )}

      </div>
    </section>
  );
}

/* =========================
   TEACHERS MODULE
========================= */

const TEACHERS_API_URL = "/api/teachers/";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }

  return null;
}

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
  };

  const [form, setForm] = useState(emptyForm);

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

  const openAddTeacher = () => {
    setEditingTeacher(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const openEditTeacher = (teacher) => {
    setEditingTeacher(teacher);

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
    });

    setShowForm(true);
  };

  const closeForm = () => {
    if (saving) return;

    setShowForm(false);
    setEditingTeacher(null);
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

    const headers = {
      "Content-Type": "application/json",
    };

    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    const response = await fetch(url, {
      method: isEditing ? "PUT" : "POST",
      credentials: "include",
      headers,
      body: JSON.stringify({
        employee_number: form.employee_number,
        first_name: form.first_name,
        last_name: form.last_name,
        gender: form.gender,
        date_of_birth: form.date_of_birth || null,
        phone: form.phone,
        email: form.email,
        campus: form.campus || null,
        joining_date: form.joining_date || null,
        designation: form.designation,
        status: form.status,
      }),
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
                        <div className="teacher-avatar">
                          {getTeacherName(teacher)
                            .charAt(0)
                            .toUpperCase()}
                        </div>

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
                          openEditTeacher(teacher)
                        }
                      >
                        Edit
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
    </section>
  );
}

/* =========================
   APP ROUTES
========================= */

function Shell() {
  const { user, loading } = useAuth();

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
          path="/students"
          element={
            <RequireRoles
              roles={["super_admin", "admin", "academic", "accountant", "teacher"]}
            >
              <StudentsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/teachers"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic"]}>
              <TeachersPage />
            </RequireRoles>
          }
        />

        <Route
          path="/attendance"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic", "teacher"]}>
              <AttendancePage />
            </RequireRoles>
          }
        />

        <Route
          path="/finance"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic", "accountant"]}>
              <FinancePage />
            </RequireRoles>
          }
        />

        <Route
          path="/exams"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic", "teacher"]}>
              <ExamsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/report-cards"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic", "teacher"]}>
              <ReportCardsPage />
            </RequireRoles>
          }
        />

        <Route
          path="/timetable"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic", "teacher", "staff"]}>
              <TimetablePage />
            </RequireRoles>
          }
        />

        <Route
          path="/campuses"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic"]}>
              <CampusesPage />
            </RequireRoles>
          }
        />

        <Route path="/events" element={<EventsPage />} />

        <Route
          path="/settings"
          element={
            <RequireRoles roles={["super_admin", "admin", "academic"]}>
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
