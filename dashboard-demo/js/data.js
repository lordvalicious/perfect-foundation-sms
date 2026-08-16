/* ==========================================================================
   PF ENTERPRISE DASHBOARD — REALISTIC DEMO DATA
   Deterministic (seeded) generator so every load looks the same.
   In production these values come from the school's REST API.
   ========================================================================== */

window.PFData = (() => {
  // --- seeded PRNG ----------------------------------------------------------
  function mulberry32(seed) {
    return function () {
      seed |= 0;
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const rand = mulberry32(20260816);
  const pick = (arr) => arr[Math.floor(rand() * arr.length)];
  const rint = (min, max) => Math.floor(rand() * (max - min + 1)) + min;

  // --- pools ----------------------------------------------------------------
  const FIRST = ["Ayesha", "Bilal", "Zara", "Hamza", "Fatima", "Ali", "Mariam", "Usman", "Hina", "Ahmad", "Sara", "Omar", "Noor", "Kashif", "Iqra", "Raza", "Mahnoor", "Salman", "Aiza", "Tariq", "Eman", "Fahad", "Rabia", "Danish", "Sana", "Waleed", "Amna", "Imran", "Khadija", "Saad"];
  const LAST = ["Khan", "Ahmed", "Hussain", "Malik", "Qureshi", "Shah", "Ali", "Butt", "Farooq", "Sheikh", "Mirza", "Chaudhry", "Raza", "Abbasi", "Tariq", "Anwar", "Siddiqui", "Bokhari", "Yousaf", "Hashmi"];
  const DEPTS = ["Mathematics", "Sciences", "Languages", "Humanities", "Computer Studies", "Physical Education"];
  const SUBJECTS = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Urdu", "Computer Science", "History", "Geography", "Islamiyat"];
  const METHODS = ["Cash", "Card", "Bank Transfer", "Mobile Wallet", "Cheque"];
  const EVENT_TYPES = ["Exam", "Holiday", "Sports Day", "PTM", "Annual Day", "National Day", "Meeting", "Workshop"];
  const STATUSES = ["active", "active", "active", "inactive"];

  const GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"];
  const SECTIONS = ["A", "B", "C"];

  // --- derived KPIs ----------------------------------------------------------
  const kpis = {
    totalStudents: 1842,
    activeStudents: 1726,
    newAdmissions: 96,
    graduated: 214,
    alumni: 3418,
    teachers: 118,
    staff: 64,
    parents: 1430,
    classes: 72,
    sections: 186,
    subjects: 28,
    departments: DEPTS.length,
    sessions: 3,
    events: 24,
    announcements: 9,
    libraryBooks: 12480,
    booksIssued: 382,
    vehicles: 12,
    houses: 4,
    clubs: 16,
    assignments: 38,
    examinations: 6,
    invoices: 2110,
    paidInvoices: 1574,
    pendingInvoices: 398,
    overdueInvoices: 138,
    monthlyRevenue: 8450000,
    yearlyRevenue: 96800000,
    outstandingFees: 4260000,
    collectionRate: 84.6,
    attendanceToday: 1589,
    studentAttPercent: 93.2,
    teacherAttPercent: 96.4,
    staffAttPercent: 95.8,
    avgClassSize: 26,
    studentTeacherRatio: "15:1",
    avgScore: 71.4,
    passRate: 88.7,
    systemUsers: 26,
    todayCollection: 684000,
    scholarships: 640000,
    discounts: 118000,
    refunds: 42000,
  };

  // --- time series -----------------------------------------------------------
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const trend = (years, base, variance, seed) => {
    const r = mulberry32(seed);
    return years.map((year, i) => ({
      year,
      value: Math.round(base * (0.82 + i * 0.04) + r() * variance),
    }));
  };
  const enrollmentTrend = trend(["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"], 1300, 90, 11);
  const monthlyAdmissions = months.map((m, i) => ({ month: m, value: rint(40, 130) + (i === 7 ? 60 : 0) }));

  const attendanceTrend = Array.from({ length: 30 }, (_, i) => {
    const day = new Date(2026, 7, 1 + i);
    const label = day.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
    const p = rint(82, 97), l = rint(2, 8), a = rint(1, 6), e = rint(0, 3);
    return { day: label, present: p, late: l, absent: a, excused: e, percent: +((p / (p + l + a + e)) * 100).toFixed(1) };
  });

  const feeCollection = months.map((m) => {
    const paid = rint(480, 760);
    return { month: m, paid: paid, pending: rint(60, 160), overdue: rint(20, 70) };
  });

  const revenueExpenses = months.map((m) => ({
    month: m,
    revenue: rint(6.2, 9.6) * 1000000,
    expenses: rint(4.1, 6.4) * 1000000,
  }));

  const expenseBreakdown = [
    { name: "Salaries", value: 41 },
    { name: "Facilities", value: 18 },
    { name: "Transport", value: 9 },
    { name: "Technology", value: 8 },
    { name: "Scholarships", value: 11 },
    { name: "Operations", value: 13 },
  ];

  const gradeDistribution = GRADES.map((g, i) => ({ grade: g, count: rint(180, 260) }));
  const studentsPerClass = GRADES.map((g, i) => ({ cls: g.replace("Grade ", "G"), count: rint(150, 240) }));
  const genderSplit = { male: 974, female: 868 };
  const subjectPopularity = SUBJECTS.map((s) => ({ subject: s, value: rint(480, 940) }));
  const teachersByDept = DEPTS.map((d) => ({ dept: d, count: rint(12, 26) }));
  const examResults = SUBJECTS.map((s) => ({ subject: s, score: rint(62, 88) }));
  const topClasses = ["Grade 7", "Grade 5", "Grade 6", "Grade 8", "Grade 4", "Grade 3"].map((c, i) => ({
    cls: c,
    pass: [96, 93, 91, 89, 87, 84][i],
  }));
  const invoiceStatus = { paid: 1574, pending: 398, overdue: 138 };
  const attendanceStatus = { present: 1589, late: 142, absent: 61, excused: 39 };

  // --- finance widgets -------------------------------------------------------
  const topDefaulters = [
    { name: "Hassan Raza", studentId: "PFS-2026-0184", amount: 184500, overdue: 92 },
    { name: "Mina Qureshi", studentId: "PFS-2026-0077", amount: 162300, overdue: 61 },
    { name: "Omar Sheikh", studentId: "PFS-2026-0911", amount: 131800, overdue: 48 },
    { name: "Dua Anwar", studentId: "PFS-2026-0234", amount: 118200, overdue: 35 },
    { name: "Zain Bokhari", studentId: "PFS-2026-1050", amount: 96400, overdue: 21 },
  ];

  // --- recent tables ---------------------------------------------------------
  const recentStudents = Array.from({ length: 8 }, (_, i) => ({
    id: `PFS-2026-${String(rint(100, 999)).padStart(4, "0")}`,
    name: `${pick(FIRST)} ${pick(LAST)}`,
    grade: pick(GRADES),
    section: pick(SECTIONS),
    admissionDate: new Date(2026, rint(2, 7), rint(1, 27)).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }),
    status: pick(STATUSES),
  }));

  const recentInvoices = Array.from({ length: 6 }, () => ({
    number: `INV-${2026}${String(rint(10000, 99999))}`,
    student: `${pick(FIRST)} ${pick(LAST)}`,
    amount: rint(15, 90) * 1000,
    due: new Date(2026, 7, rint(1, 28)).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }),
    status: pick(["paid", "pending", "overdue"]),
  }));

  const recentPayments = Array.from({ length: 6 }, () => ({
    receipt: `RCPT-${String(rint(100000, 999999))}`,
    student: `${pick(FIRST)} ${pick(LAST)}`,
    amount: rint(8, 70) * 1000,
    method: pick(METHODS),
    date: new Date(2026, 7, rint(1, 15)).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }),
  }));

  // --- activity / notifications / messages / tasks ---------------------------
  const activity = [
    { actor: "Ayesha Khan", action: "was admitted to", target: "Grade 6 – B", time: "5m ago", tone: "indigo", icon: "fa-user-plus" },
    { actor: "Bilal Ahmed", action: "paid invoice", target: "INV-202698321", time: "18m ago", tone: "emerald", icon: "fa-money-check-dollar" },
    { actor: "Ms. Fatima Noor", action: "marked attendance for", target: "Grade 4 – A", time: "32m ago", tone: "sky", icon: "fa-clipboard-user" },
    { actor: "Hamza Malik", action: "scored 94% in", target: "Mathematics (Weekly Quiz)", time: "1h ago", tone: "violet", icon: "fa-star" },
    { actor: "Zara Hussain", action: "returned 3 library books", target: "Library – Central", time: "2h ago", tone: "amber", icon: "fa-book" },
    { actor: "Ali Shah", action: "submitted homework", target: "Computer Science", time: "3h ago", tone: "rose", icon: "fa-pen-to-square" },
    { actor: "System", action: "generated report card for", target: "Grade 8 – C", time: "4h ago", tone: "slate", icon: "fa-file-lines" },
  ];

  const notifications = [
    { title: "Fee deadline reminder", msg: "138 invoices overdue for the Fall Semester.", time: "10m", tone: "danger", unread: true },
    { title: "Attendance alert", msg: "Student 'Omar Sheikh' marked absent in 5 sessions this week.", time: "42m", tone: "warning", unread: true },
    { title: "Exam scheduled", msg: "Mid-term examinations begin 12 Aug 2026.", time: "2h", tone: "info", unread: true },
    { title: "New admission approved", msg: "3 applications pending final approval.", time: "5h", tone: "success", unread: false },
    { title: "Staff anniversary", msg: "Congratulate Ms. Iqra Raza — 5 years with PFS.", time: "1d", tone: "violet", unread: false },
    { title: "System backup complete", msg: "Database snapshot taken successfully.", time: "1d", tone: "success", unread: false },
  ];

  const messages = [
    { from: "Mr. Usman Tariq", preview: "Please share the Grade 7 timetable before Friday...", time: "8m", unread: true },
    { from: "Accounts Office", preview: "Payment receipt RCPT-582913 confirmed...", time: "1h", unread: true },
    { from: "Sports Committee", preview: "Sports Day rehearsal moved to 4:00 PM...", time: "3h", unread: false },
  ];

  const tasks = [
    { label: "Approve new admissions", due: "Today", priority: "High", done: false },
    { label: "Review overdue invoices", due: "Tomorrow", priority: "High", done: false },
    { label: "Finalize exam center list", due: "12 Aug", priority: "Med", done: false },
    { label: "Update staff leave register", due: "Done", priority: "Low", done: true },
  ];

  // --- calendar / events -----------------------------------------------------
  const calendarEvents = [
    { day: 3,  title: "Parent Teacher Meeting", type: "PTM", color: "#4f46e5" },
    { day: 5,  title: "Independence Day", type: "National Day", color: "#dc2626" },
    { day: 8,  title: "Mid-term Exams Begin", type: "Exam", color: "#d97706" },
    { day: 11, title: "Faculty Meeting", type: "Meeting", color: "#64748b" },
    { day: 14, title: "Summer Sports Gala", type: "Sports Day", color: "#0ea5e9" },
    { day: 18, title: "Mid-term Exams End", type: "Exam", color: "#d97706" },
    { day: 21, title: "Annual Science Fair", type: "Workshop", color: "#16a34a" },
    { day: 26, title: "Cultural Day", type: "Annual Day", color: "#7c3aed" },
    { day: 29, title: "School Holiday", type: "Holiday", color: "#f59e0b" },
  ];

  const upcomingEvents = [
    { title: "Mid-term Examinations", date: "12 Aug – 18 Aug", type: "Exam" },
    { title: "Parent Teacher Meeting", date: "Fri, 7 Aug", type: "PTM" },
    { title: "Annual Science Fair", date: "21 Aug", type: "Workshop" },
    { title: "Summer Sports Gala", date: "14 Aug", type: "Sports" },
  ];

  return {
    kpis,
    enrollmentTrend,
    monthlyAdmissions,
    attendanceTrend,
    attendanceStatus,
    feeCollection,
    revenueExpenses,
    expenseBreakdown,
    gradeDistribution,
    studentsPerClass,
    genderSplit,
    subjectPopularity,
    teachersByDept,
    examResults,
    topClasses,
    invoiceStatus,
    topDefaulters,
    recentStudents,
    recentInvoices,
    recentPayments,
    activity,
    notifications,
    messages,
    tasks,
    calendarEvents,
    upcomingEvents,
  };
})();
