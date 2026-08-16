/* ==========================================================================
   PF ENTERPRISE DASHBOARD — SCHOOL CONFIGURATION
   --------------------------------------------------------------------------
   Change this file to adapt the dashboard to any country / school:
   academic structure, terminology, locale, currency, calendar, grading,
   and which modules are enabled. The UI re-renders from these settings —
   no redesign needed.
   ========================================================================== */

window.PFConfig = {
  school: {
    name: "Perfect Foundation School",
    shortName: "PFS",
    motto: "Excellence • Integrity • Service",
    crest: "🎓", // swap with an <img> crest in production
    tagline: "Empowering learners for a changing world",
    version: "2.4.1",
  },

  locale: {
    language: "en",
    languages: [
      { code: "en", label: "English" },
      { code: "ur", label: "اردو (Urdu)" },
      { code: "fr", label: "Français" },
      { code: "es", label: "Español" },
    ],
    timezone: "Asia/Karachi", // e.g. "Africa/Lagos", "America/New_York"
    dateFormat: "dd MMM yyyy", // tokens: dd MM MMM MMMM yyyy yy
    currency: "PKR",
    currencySymbol: "₨",
    currencyLocale: "en-PK",
    decimals: 0,
    weekStart: 0, // 0 = Sunday, 1 = Monday
  },

  academic: {
    session: "2026 – 2027",
    sessionLabel: "Academic Session",
    term: "Fall Semester",
    termLabel: "Semester", // "Term" | "Semester" | "Trimester"
    termNumber: 1,
    termsPerYear: 2,
    levelLabel: "Grade", // "Grade" | "Class" | "Form" | "Standard" | "Year"
    sectionLabel: "Section",
    grading: {
      style: "percent", // "percent" | "letter" | "gpa"
      scaleLabel: "100%",
      levels: [
        { min: 90, label: "A+", color: "#16a34a" },
        { min: 80, label: "A", color: "#4f46e5" },
        { min: 70, label: "B", color: "#0ea5e9" },
        { min: 60, label: "C", color: "#d97706" },
        { min: 50, label: "D", color: "#dc2626" },
        { min: 0, label: "F", color: "#991b1b" },
      ],
    },
    houses: ["Aurora", "Crest", "Meridian", "Nova"],
  },

  /* Sidebar navigation. `enabled` toggles a module per school. */
  modules: [
    { id: "dashboard",    label: "Dashboard",      icon: "fa-gauge-high",  group: "Overview", enabled: true },
    { id: "students",     label: "Students",       icon: "fa-user-graduate", group: "Academics", enabled: true },
    { id: "admissions",   label: "Admissions",     icon: "fa-user-plus",   group: "Academics", enabled: true },
    { id: "parents",      label: "Parents",        icon: "fa-people-roof", group: "Academics", enabled: true },
    { id: "teachers",     label: "Teachers",       icon: "fa-chalkboard-user", group: "Academics", enabled: true },
    { id: "staff",        label: "Staff",          icon: "fa-id-badge",    group: "Academics", enabled: true },
    { id: "classes",      label: "Classes",        icon: "fa-school",      group: "Academics", enabled: true },
    { id: "sections",     label: "Sections",       icon: "fa-layer-group", group: "Academics", enabled: true },
    { id: "subjects",     label: "Subjects",       icon: "fa-book-open",   group: "Academics", enabled: true },
    { id: "departments",  label: "Departments",    icon: "fa-building-columns", group: "Academics", enabled: true },
    { id: "attendance",   label: "Attendance",     icon: "fa-clipboard-user", group: "Academics", enabled: true },
    { id: "timetable",    label: "Timetable",      icon: "fa-calendar-days", group: "Academics", enabled: true },
    { id: "assignments",  label: "Assignments",    icon: "fa-pen-to-square", group: "Academics", enabled: true },
    { id: "homework",     label: "Homework",       icon: "fa-book-bookmark", group: "Academics", enabled: true },
    { id: "examinations", label: "Examinations",   icon: "fa-file-circle-check", group: "Academics", enabled: true },
    { id: "grades",       label: "Grades",         icon: "fa-star",       group: "Academics", enabled: true },
    { id: "report-cards", label: "Report Cards",   icon: "fa-file-lines",  group: "Academics", enabled: true },
    { id: "behavior",     label: "Behavior",       icon: "fa-hand-holding-heart", group: "Academics", enabled: true },
    { id: "library",      label: "Library",        icon: "fa-book",        group: "Resources", enabled: true },
    { id: "transport",    label: "Transport",      icon: "fa-bus",         group: "Resources", enabled: true },
    { id: "hostel",       label: "Hostel",         icon: "fa-bed",         group: "Resources", enabled: false },
    { id: "health",       label: "Health Records", icon: "fa-heart-pulse", group: "Resources", enabled: true },
    { id: "events",       label: "Events",         icon: "fa-flag",        group: "Resources", enabled: true },
    { id: "calendar",     label: "Calendar",       icon: "fa-calendar-check", group: "Resources", enabled: true },
    { id: "finance",      label: "Finance",        icon: "fa-coins",       group: "Finance", enabled: true },
    { id: "invoices",     label: "Invoices",       icon: "fa-file-invoice-dollar", group: "Finance", enabled: true },
    { id: "payments",     label: "Payments",       icon: "fa-money-check-dollar", group: "Finance", enabled: true },
    { id: "scholarships", label: "Scholarships",   icon: "fa-award",       group: "Finance", enabled: true },
    { id: "payroll",      label: "Payroll",        icon: "fa-wallet",      group: "Finance", enabled: true },
    { id: "inventory",    label: "Inventory",      icon: "fa-boxes-stacked", group: "Finance", enabled: true },
    { id: "reports",      label: "Reports",        icon: "fa-chart-pie",   group: "Insights", enabled: true },
    { id: "analytics",    label: "Analytics",      icon: "fa-chart-line",  group: "Insights", enabled: true },
    { id: "communication",label: "Communication",  icon: "fa-comments",    group: "Communication", enabled: true },
    { id: "notifications",label: "Notifications",  icon: "fa-bell",        group: "Communication", enabled: true },
    { id: "settings",     label: "Settings",       icon: "fa-gear",        group: "System", enabled: true },
  ],

  /* Optional modules a school may or may not run. */
  features: {
    transport: true,
    hostel: false,
    library: true,
    healthRecords: true,
    clubs: true,
    scholarships: true,
    behavior: true,
  },

  quickActions: [
    { id: "add-student",   label: "Add Student",     icon: "fa-user-plus",       tone: "indigo" },
    { id: "add-teacher",   label: "Add Teacher",     icon: "fa-chalkboard-user", tone: "violet" },
    { id: "add-staff",     label: "Add Staff",       icon: "fa-id-badge",        tone: "sky" },
    { id: "create-class",  label: "Create Class",    icon: "fa-school",          tone: "emerald" },
    { id: "add-subject",   label: "Add Subject",     icon: "fa-book-open",       tone: "amber" },
    { id: "attendance",    label: "Record Attendance", icon: "fa-clipboard-user", tone: "rose" },
    { id: "invoice",       label: "Create Invoice",  icon: "fa-file-invoice-dollar", tone: "indigo" },
    { id: "payment",       label: "Collect Payment", icon: "fa-money-check-dollar", tone: "emerald" },
    { id: "exam",          label: "Schedule Exam",   icon: "fa-file-circle-check", tone: "violet" },
    { id: "event",         label: "Create Event",    icon: "fa-calendar-plus",   tone: "sky" },
    { id: "report",        label: "Generate Report", icon: "fa-chart-column",    tone: "amber" },
    { id: "notify",        label: "Send Notification", icon: "fa-paper-plane",   tone: "rose" },
  ],
};
