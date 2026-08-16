/* ==========================================================================
   PF ENTERPRISE DASHBOARD — APEX CHARTS
   Theme-aware charts driven by PFData. Re-renders colors on theme switch.
   ========================================================================== */

window.PFCharts = (() => {
  const PALETTE = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#f43f5e", "#7c3aed", "#14b8a6", "#8b5cf6", "#ec4899", "#f97316"];
  const charts = {};

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function readTheme() {
    const dark = document.documentElement.getAttribute("data-theme") === "dark";
    return {
      dark,
      text: cssVar("--text"),
      muted: cssVar("--muted"),
      grid: cssVar("--chart-grid"),
      tooltip: dark ? "dark" : "light",
    };
  }

  function money(n) {
    const c = window.PFConfig.locale;
    return `${c.currencySymbol} ${Math.round(n).toLocaleString(c.currencyLocale)}`;
  }

  function base(type, height = 300) {
    const t = readTheme();
    return {
      chart: {
        type,
        height,
        toolbar: { show: false },
        foreColor: t.muted,
        fontFamily: cssVar("--font-sans"),
        background: "transparent",
        parentHeightOffset: 0,
        animations: { enabled: true, speed: 700 },
      },
      colors: PALETTE,
      grid: { borderColor: t.grid, strokeDashArray: 4 },
      dataLabels: { enabled: false },
      stroke: { width: 2.5, curve: "smooth" },
      tooltip: { theme: t.tooltip },
    };
  }

  function catAxis(categories) {
    return { categories, labels: { style: { colors: readTheme().muted } } };
  }

  const definitions = (D, C) => ({
    chartEnrollment: {
      type: "area", height: 320,
      series: [{ name: "Students", data: D.enrollmentTrend.map((p) => p.value) }],
      options: {
        ...base("area", 320),
        title: { text: "Student Enrollment Trend", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        chart: { ...base("area", 320).chart, id: "enrollment", sparkline: { enabled: false } },
        xaxis: catAxis(D.enrollmentTrend.map((p) => p.year)),
        yaxis: { labels: { formatter: (v) => v.toLocaleString() } },
        fill: { type: "gradient", gradient: { opacityFrom: 0.35, opacityTo: 0.02 } },
        colors: ["#4f46e5"],
      },
    },

    chartAttendanceStatus: {
      type: "donut", height: 320,
      series: Object.values(D.attendanceStatus),
      options: {
        ...base("donut", 320),
        title: { text: "Attendance Status Today", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        labels: Object.keys(D.attendanceStatus).map((k) => k[0].toUpperCase() + k.slice(1)),
        colors: ["#4f46e5", "#f59e0b", "#f43f5e", "#0ea5e9"],
        legend: { position: "bottom" },
        dataLabels: { formatter: (val) => `${val}%` },
        plotOptions: { pie: { donut: { labels: { show: true, total: { show: true, label: "Present", formatter: () => D.attendanceStatus.present.toLocaleString() } } } } },
      },
    },

    chartStudentsPerClass: {
      type: "bar", height: 300,
      series: [{ name: "Students", data: D.studentsPerClass.map((p) => p.count) }],
      options: {
        ...base("bar", 300),
        title: { text: "Students per Class", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.studentsPerClass.map((p) => p.cls)),
        plotOptions: { bar: { borderRadius: 5, columnWidth: "52%" } },
        colors: ["#0ea5e9"],
      },
    },

    chartGradeDist: {
      type: "bar", height: 300,
      series: [{ name: "Students", data: D.gradeDistribution.map((p) => p.count) }],
      options: {
        ...base("bar", 300),
        title: { text: "Student Distribution by Grade", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.gradeDistribution.map((p) => p.grade)),
        plotOptions: { bar: { borderRadius: 5, horizontal: true, barHeight: "55%" } },
        colors: ["#10b981"],
      },
    },

    chartGender: {
      type: "donut", height: 300,
      series: [D.genderSplit.male, D.genderSplit.female],
      options: {
        ...base("donut", 300),
        title: { text: "Gender Distribution", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        labels: ["Male", "Female"],
        colors: ["#4f46e5", "#ec4899"],
        legend: { position: "bottom" },
      },
    },

    chartFeeCollection: {
      type: "bar", height: 320,
      series: [
        { name: "Paid", data: D.feeCollection.map((p) => p.paid) },
        { name: "Pending", data: D.feeCollection.map((p) => p.pending) },
        { name: "Overdue", data: D.feeCollection.map((p) => p.overdue) },
      ],
      options: {
        ...base("bar", 320),
        title: { text: "Fee Collection (in thousands)", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.feeCollection.map((p) => p.month)),
        yaxis: { labels: { formatter: (v) => `${v}k` } },
        colors: ["#4f46e5", "#f59e0b", "#f43f5e"],
        plotOptions: { bar: { borderRadius: 4, columnWidth: "55%", stacked: true } },
        legend: { position: "bottom" },
      },
    },

    chartRevenueExpenses: {
      type: "line", height: 320,
      series: [
        { name: "Revenue", type: "area", data: D.revenueExpenses.map((p) => p.revenue / 1000000) },
        { name: "Expenses", type: "line", data: D.revenueExpenses.map((p) => p.expenses / 1000000) },
      ],
      options: {
        ...base("line", 320),
        title: { text: "Revenue vs Expenses (₨ millions)", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.revenueExpenses.map((p) => p.month)),
        yaxis: { labels: { formatter: (v) => `₨${v}M` } },
        colors: ["#10b981", "#f43f5e"],
        fill: { type: "solid" },
        stroke: { width: [0, 3], curve: "smooth" },
        legend: { position: "bottom" },
      },
    },

    chartAttTrend: {
      type: "line", height: 300,
      series: [{ name: "Attendance %", data: D.attendanceTrend.map((p) => p.percent) }],
      options: {
        ...base("line", 300),
        title: { text: "Attendance Trend — Last 30 Days", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.attendanceTrend.map((p) => p.day)),
        yaxis: { min: 70, max: 100, labels: { formatter: (v) => `${v}%` } },
        colors: ["#7c3aed"],
        stroke: { width: 3, curve: "smooth" },
        markers: { size: 0 },
        annotations: { yaxis: [{ y: 90, borderColor: readTheme().grid, label: { borderColor: readTheme().grid, style: { color: readTheme().muted }, text: "Target 90%" } }] },
      },
    },

    chartInvoiceStatus: {
      type: "donut", height: 300,
      series: Object.values(D.invoiceStatus),
      options: {
        ...base("donut", 300),
        title: { text: "Invoice Status", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        labels: ["Paid", "Pending", "Overdue"],
        colors: ["#10b981", "#f59e0b", "#f43f5e"],
        legend: { position: "bottom" },
      },
    },

    chartSubjectPopularity: {
      type: "polarArea", height: 300,
      series: D.subjectPopularity.map((p) => p.value),
      options: {
        ...base("polarArea", 300),
        title: { text: "Subject Popularity", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        labels: D.subjectPopularity.map((p) => p.subject),
        legend: { position: "bottom", labels: { colors: readTheme().muted } },
      },
    },

    chartTeachers: {
      type: "radar", height: 300,
      series: [{ name: "Teachers", data: D.teachersByDept.map((p) => p.count) }],
      options: {
        ...base("radar", 300),
        title: { text: "Teacher Distribution by Department", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: { categories: D.teachersByDept.map((p) => p.dept), labels: { style: { colors: Array(6).fill(readTheme().muted) } } },
        colors: ["#8b5cf6"],
        stroke: { width: 2 },
        fill: { opacity: 0.18 },
        markers: { size: 3 },
      },
    },

    chartExamResults: {
      type: "bar", height: 300,
      series: [{ name: "Average Score %", data: D.examResults.map((p) => p.score) }],
      options: {
        ...base("bar", 300),
        title: { text: "Exam Results by Subject", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.examResults.map((p) => p.subject)),
        yaxis: { max: 100, labels: { formatter: (v) => `${v}%` } },
        plotOptions: { bar: { borderRadius: 5, columnWidth: "48%" } },
        colors: ["#f97316"],
      },
    },

    chartTopClasses: {
      type: "bar", height: 300,
      series: [{ name: "Pass Rate %", data: D.topClasses.map((p) => p.pass) }],
      options: {
        ...base("bar", 300),
        title: { text: "Top Performing Classes", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.topClasses.map((p) => p.cls)),
        yaxis: { max: 100, labels: { formatter: (v) => `${v}%` } },
        plotOptions: { bar: { borderRadius: 5, columnWidth: "52%" } },
        colors: ["#14b8a6"],
      },
    },

    chartMonthlyAdmissions: {
      type: "area", height: 300,
      series: [{ name: "New Admissions", data: D.monthlyAdmissions.map((p) => p.value) }],
      options: {
        ...base("area", 300),
        title: { text: "Monthly Admissions", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.monthlyAdmissions.map((p) => p.month)),
        fill: { type: "gradient", gradient: { opacityFrom: 0.4, opacityTo: 0.02 } },
        colors: ["#ec4899"],
      },
    },

    chartExpenses: {
      type: "area", height: 300,
      series: [{ name: "Share %", data: D.expenseBreakdown.map((p) => p.value) }],
      options: {
        ...base("area", 300),
        title: { text: "Expense Breakdown", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.expenseBreakdown.map((p) => p.name)),
        yaxis: { labels: { formatter: (v) => `${v}%` } },
        fill: { type: "gradient", gradient: { opacityFrom: 0.35, opacityTo: 0.02 } },
        colors: ["#f59e0b"],
      },
    },

    chartWeeklyAttendance: {
      type: "bar", height: 220,
      series: [
        { name: "Present", data: D.attendanceWeekly.map((p) => p.present) },
        { name: "Absent", data: D.attendanceWeekly.map((p) => p.absent) },
      ],
      options: {
        ...base("bar", 220),
        xaxis: catAxis(D.attendanceWeekly.map((p) => p.day)),
        yaxis: { labels: { formatter: (v) => v.toLocaleString() } },
        plotOptions: { bar: { borderRadius: 4, columnWidth: "52%", stacked: false } },
        colors: ["#10b981", "#f43f5e"],
        legend: { position: "bottom" },
        chart: { ...base("bar", 220).chart, id: "weekly-att" },
      },
    },

    chartRevenueGrowth: {
      type: "area", height: 300,
      series: [{ name: "Revenue (₨ M)", data: D.revenueGrowth.map((p) => p.value) }],
      options: {
        ...base("area", 300),
        title: { text: "Revenue Growth", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.revenueGrowth.map((p) => p.month)),
        yaxis: { labels: { formatter: (v) => `₨${v}M` } },
        fill: { type: "gradient", gradient: { opacityFrom: 0.38, opacityTo: 0.02 } },
        colors: ["#4f46e5"],
      },
    },

    chartLibraryUsage: {
      type: "line", height: 300,
      series: [
        { name: "Issued", data: D.libraryUsage.map((p) => p.issued) },
        { name: "Returned", data: D.libraryUsage.map((p) => p.returned) },
      ],
      options: {
        ...base("line", 300),
        title: { text: "Library Usage", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.libraryUsage.map((p) => p.month)),
        yaxis: { labels: { formatter: (v) => v.toLocaleString() } },
        colors: ["#f59e0b", "#14b8a6"],
        stroke: { width: 2.5, curve: "smooth" },
        legend: { position: "bottom" },
      },
    },

    chartTransportUsage: {
      type: "donut", height: 300,
      series: D.transportUsage.map((p) => p.students),
      options: {
        ...base("donut", 300),
        title: { text: "Transport Usage", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        labels: D.transportUsage.map((p) => p.mode),
        colors: ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b"],
        legend: { position: "bottom" },
      },
    },

    chartPerformanceTrends: {
      type: "line", height: 300,
      series: [
        { name: "Average Score %", data: D.performanceTrends.map((p) => p.avg) },
        { name: "Pass Rate %", data: D.performanceTrends.map((p) => p.pass) },
      ],
      options: {
        ...base("line", 300),
        title: { text: "Performance Trends", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.performanceTrends.map((p) => p.term)),
        yaxis: { min: 60, max: 100, labels: { formatter: (v) => `${v}%` } },
        colors: ["#7c3aed", "#f97316"],
        stroke: { width: 2.5, curve: "smooth" },
        markers: { size: 3 },
        legend: { position: "bottom" },
      },
    },

    chartTopSubjects: {
      type: "bar", height: 300,
      series: [{ name: "Pass Rate %", data: D.topSubjects.map((p) => p.pass) }],
      options: {
        ...base("bar", 300),
        title: { text: "Top Performing Subjects", style: { fontSize: "14px", fontWeight: 700, color: readTheme().text } },
        xaxis: catAxis(D.topSubjects.map((p) => p.subject)),
        yaxis: { max: 100, labels: { formatter: (v) => `${v}%` } },
        plotOptions: { bar: { borderRadius: 5, horizontal: true, barHeight: "58%" } },
        colors: ["#0ea5e9"],
      },
    },
  });

  function init() {
    const defs = definitions(window.PFData, window.PFConfig);
    for (const [id, d] of Object.entries(defs)) {
      const el = document.getElementById(id);
      if (!el) continue;
      charts[id] = new ApexCharts(el, { series: d.series, ...d.options });
      charts[id].render();
    }
  }

  function updateTheme() {
    const t = readTheme();
    for (const id of Object.keys(charts)) {
      charts[id].updateOptions({
        chart: { foreColor: t.muted },
        grid: { borderColor: t.grid },
        tooltip: { theme: t.tooltip },
        xaxis: { labels: { style: { colors: t.muted } } },
        yaxis: { labels: { style: { colors: t.muted } } },
        legend: { labels: { colors: t.muted } },
      });
    }
  }

  function resizeAll() {
    for (const id of Object.keys(charts)) {
      charts[id].updateOptions({ chart: { height: charts[id].w.config.chart.height } });
    }
  }

  return { init, updateTheme, resizeAll, money };
})();
