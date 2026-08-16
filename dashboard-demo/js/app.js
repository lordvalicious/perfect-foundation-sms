/* ==========================================================================
   PF ENTERPRISE DASHBOARD — APP LOGIC
   Renders sidebar from config, wires theme, clock, KPI counters, tables,
   calendar, exports, quick actions, settings modal and module navigation.
   ========================================================================== */

(() => {
  const C = window.PFConfig;
  const D = window.PFData;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const money = (v) =>
    new Intl.NumberFormat(C.locale.currencyLocale, {
      style: "currency",
      currency: C.locale.currency,
      maximumFractionDigits: C.locale.decimals,
      minimumFractionDigits: C.locale.decimals,
    }).format(v);

  /* ---------- live clock ---------- */
  function fmtDate(d) {
    return new Intl.DateTimeFormat(C.locale.language, {
      timeZone: C.locale.timezone,
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(d);
  }

  function tick() {
    const now = new Date();
    const timeOpts = {
      timeZone: C.locale.timezone,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    };
    $("#liveDate").textContent = fmtDate(now);
    $("#liveTime").textContent = new Intl.DateTimeFormat(C.locale.language, timeOpts).format(now);
  }

  /* ---------- sidebar ---------- */
  function renderSidebar() {
    const groups = {};
    C.modules.forEach((m) => {
      if (!m.enabled) return;
      (groups[m.group] = groups[m.group] || []).push(m);
    });

    const root = $("#sidebarGroups");
    root.innerHTML = Object.entries(groups)
      .map(([group, items]) => `
        <div class="sidebar-group">
          <p class="sidebar-group-title">${group}</p>
          ${items.map((m) => `
            <button class="sidebar-link" data-module="${m.id}" data-icon="${m.icon}" title="${m.label}">
              <i class="fa-solid ${m.icon}"></i>
              <span>${m.label}</span>
            </button>`).join("")}
        </div>`)
      .join("");
  }

  /* ---------- navigation ---------- */
  function showModule(id) {
    $$(".sidebar-link").forEach((l) => l.classList.toggle("active", l.dataset.module === id));
    const isDashboard = id === "dashboard";
    $("#section-dashboard").classList.toggle("active", isDashboard);
    $("#section-module").classList.toggle("active", !isDashboard);

    if (!isDashboard) {
      const mod = C.modules.find((m) => m.id === id);
      $("#moduleTitle").textContent = mod ? mod.label : id;
      $("#moduleIcon").className = `fa-solid ${mod ? mod.icon : "fa-cube"}`;
      $("#moduleDesc").textContent =
        `${mod ? mod.label : "This module"} is configured and ready. Wire it to the school's API endpoints to stream real data.`;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ---------- KPI groups ---------- */
  const KPI_GROUPS = [
    {
      id: "overview",
      label: "Overview",
      items: [
        { k: "totalStudents", label: "Total Students", icon: "fa-user-graduate", color: "indigo" },
        { k: "activeStudents", label: "Active Students", icon: "fa-user-check", color: "emerald" },
        { k: "newAdmissions", label: "New Admissions", icon: "fa-user-plus", color: "sky" },
        { k: "graduated", label: "Graduated", icon: "fa-graduation-cap", color: "violet" },
        { k: "alumni", label: "Alumni", icon: "fa-people-group", color: "amber" },
        { k: "teachers", label: "Teachers", icon: "fa-chalkboard-user", color: "sky" },
        { k: "staff", label: "Staff", icon: "fa-id-badge", color: "rose" },
        { k: "parents", label: "Parents", icon: "fa-people-roof", color: "emerald" },
        { k: "classes", label: "Classes", icon: "fa-school", color: "indigo" },
        { k: "sections", label: "Sections", icon: "fa-layer-group", color: "violet" },
        { k: "subjects", label: "Subjects", icon: "fa-book-open", color: "amber" },
        { k: "departments", label: "Departments", icon: "fa-building-columns", color: "sky" },
      ],
    },
    {
      id: "finance",
      label: "Finance",
      items: [
        { k: "monthlyRevenue", label: "Monthly Revenue", icon: "fa-coins", color: "emerald", money: true },
        { k: "yearlyRevenue", label: "Yearly Revenue", icon: "fa-sack-dollar", color: "indigo", money: true },
        { k: "outstandingFees", label: "Outstanding Fees", icon: "fa-hourglass-half", color: "amber", money: true },
        { k: "collectionRate", label: "Collection Rate", icon: "fa-percent", color: "sky", suffix: "%" },
        { k: "invoices", label: "Invoices", icon: "fa-file-invoice-dollar", color: "violet" },
        { k: "paidInvoices", label: "Paid Invoices", icon: "fa-circle-check", color: "emerald" },
        { k: "pendingInvoices", label: "Pending Invoices", icon: "fa-clock", color: "amber" },
        { k: "overdueInvoices", label: "Overdue", icon: "fa-triangle-exclamation", color: "rose" },
      ],
    },
    {
      id: "attendance",
      label: "Attendance",
      items: [
        { k: "attendanceToday", label: "Today's Attendance", icon: "fa-clipboard-user", color: "indigo" },
        { k: "studentAttPercent", label: "Student %", icon: "fa-user-graduate", color: "emerald", suffix: "%" },
        { k: "teacherAttPercent", label: "Teacher %", icon: "fa-chalkboard-user", color: "sky", suffix: "%" },
        { k: "staffAttPercent", label: "Staff %", icon: "fa-id-badge", color: "violet", suffix: "%" },
      ],
    },
    {
      id: "academic",
      label: "Academic",
      items: [
        { k: "avgClassSize", label: "Avg Class Size", icon: "fa-people-group", color: "sky" },
        { k: "studentTeacherRatio", label: "Student : Teacher", icon: "fa-scale-balanced", color: "indigo" },
        { k: "avgScore", label: "Average Score", icon: "fa-ranking-star", color: "violet", suffix: "%" },
        { k: "passRate", label: "Pass Rate", icon: "fa-medal", color: "emerald", suffix: "%" },
        { k: "assignments", label: "Assignments", icon: "fa-pen-to-square", color: "amber" },
        { k: "examinations", label: "Exams", icon: "fa-file-circle-check", color: "rose" },
      ],
    },
  ];

  const TONES = {
    indigo: { color: "var(--primary)", soft: "var(--primary-soft)", glow: "rgba(99,102,241,0.14)" },
    emerald: { color: "var(--emerald)", soft: "var(--success-soft)", glow: "rgba(16,185,129,0.15)" },
    sky: { color: "var(--sky)", soft: "var(--info-soft)", glow: "rgba(14,165,233,0.15)" },
    violet: { color: "var(--violet)", soft: "var(--violet-soft)", glow: "rgba(124,58,237,0.15)" },
    amber: { color: "var(--amber)", soft: "var(--warning-soft)", glow: "rgba(245,158,11,0.15)" },
    rose: { color: "var(--rose)", soft: "var(--danger-soft)", glow: "rgba(244,63,94,0.15)" },
  };

  function kpiCard(item) {
    const v = D.kpis[item.k];
    const t = TONES[item.color] || TONES.indigo;
    const fmt = item.money ? money : (x) => x.toLocaleString(C.locale.language);
    const suffix = item.suffix ? `<span class="kpi-suffix">${item.suffix}</span>` : "";
    return `
      <div class="kpi-card" data-count data-value="${v}" data-money="${item.money ? 1 : 0}" style="--kpi-color:${t.color};--kpi-soft:${t.soft};--kpi-glow:${t.glow}">
        <div class="kpi-top">
          <span class="kpi-icon"><i class="fa-solid ${item.icon}"></i></span>
          <span class="kpi-trend up"><i class="fa-solid fa-arrow-trend-up"></i> 4.2%</span>
        </div>
        <div class="kpi-label">${item.label}</div>
        <div class="kpi-value">0${suffix}</div>
        <div class="kpi-sub">vs last ${item.money ? "month" : "term"}</div>
      </div>`;
  }

  function renderKpis() {
    $("#kpiTabs").innerHTML = KPI_GROUPS.map(
      (g, i) => `<button class="kpi-chip ${i === 0 ? "active" : ""}" data-group="${g.id}" role="tab">${g.label}</button>`
    ).join("");
    $("#kpiGroups").innerHTML = KPI_GROUPS.map((g, i) => `
      <div class="kpi-group ${i === 0 ? "active" : ""}" id="kpi-${g.id}" data-group="${g.id}">
        <div class="kpi-grid">${g.items.map(kpiCard).join("")}</div>
      </div>`).join("");

    $$(".kpi-chip").forEach((chip) =>
      chip.addEventListener("click", () => {
        $$(".kpi-chip").forEach((c) => c.classList.toggle("active", c === chip));
        $$(".kpi-group").forEach((g) => g.classList.toggle("active", g.dataset.group === chip.dataset.group));
      })
    );
  }

  /* ---------- animated counters ---------- */
  function animateCount(el) {
    const target = parseFloat(el.dataset.value);
    const moneyFlag = el.dataset.money === "1";
    const suffix = el.querySelector(".kpi-suffix")?.textContent || "";
    const duration = 1100;
    const start = performance.now();
    function frame(now) {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = Math.round(target * eased);
      el.querySelector(".kpi-value").innerHTML =
        (moneyFlag ? money(val) : val.toLocaleString(C.locale.language)) + (suffix ? ` <span class="kpi-suffix">${suffix}</span>` : "");
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function bindCounters() {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.dataset.animated = "1";
            animateCount(e.target);
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.2 }
    );

    $$(".kpi-card[data-count]").forEach((el) => {
      // If the card is already in the viewport, animate immediately —
      // avoids any observer timing issues on first paint.
      const rect = el.getBoundingClientRect();
      const inView = rect.top < window.innerHeight && rect.bottom > 0;
      if (inView && el.dataset.animated !== "1") {
        el.dataset.animated = "1";
        animateCount(el);
      } else if (el.dataset.animated !== "1") {
        io.observe(el);
      }
    });

    // Animate cards when their KPI group tab is switched into view.
    $$(".kpi-chip").forEach((chip) =>
      chip.addEventListener("click", () => {
        const groupId = chip.dataset.group;
        $$(`.kpi-group[data-group="${groupId}"] .kpi-card[data-count]`).forEach((el) => {
          if (el.dataset.animated !== "1") {
            el.dataset.animated = "1";
            animateCount(el);
          }
        });
      })
    );
  }

  /* ---------- finance widgets ---------- */
  function renderFinanceWidgets() {
    const k = D.kpis;
    const widgets = [
      { label: "Today's Collection", value: money(k.todayCollection), icon: "fa-hand-holding-dollar", color: "emerald", sub: "+8.4% vs yesterday" },
      { label: "Monthly Collection", value: money(k.monthlyRevenue), icon: "fa-coins", color: "indigo", sub: "of ₨9.2M target", rate: 92 },
      { label: "Annual Revenue", value: money(k.yearlyRevenue), icon: "fa-sack-dollar", color: "sky", sub: "+14.2% vs last year" },
      { label: "Outstanding Fees", value: money(k.outstandingFees), icon: "fa-hourglass-half", color: "amber", sub: "536 invoices open" },
    ];
    $("#financeWidgets").innerHTML = widgets
      .map((w) => {
        const tone = {
          emerald: ["var(--emerald)", "var(--success-soft)"],
          indigo: ["var(--primary)", "var(--primary-soft)"],
          sky: ["var(--sky)", "var(--info-soft)"],
          amber: ["var(--amber)", "var(--warning-soft)"],
        }[w.color];
        return `
        <div class="col-xl-3 col-md-6">
          <div class="fin-widget">
            <span class="fw-ico" style="color:${tone[0]};background:${tone[1]}"><i class="fa-solid ${w.icon}"></i></span>
            <div>
              <small>${w.label}</small>
              <strong>${w.value}</strong>
              <div class="fw-sub">${w.sub}</div>
            </div>
          </div>
        </div>`;
      })
      .join("") +
      `
      <div class="col-xl-4 col-md-6">
        <div class="pf-card">
          <div class="pf-card-head"><h2>Top Fee Defaulters</h2></div>
          <table class="defaulters-table">
            ${D.topDefaulters.map((d) => `<tr><td><strong>${d.name}</strong><br><small>${d.studentId}</small></td><td class="text-end"><strong>${money(d.amount)}</strong><br><small class="text-danger">${d.overdue} days overdue</small></td></tr>`).join("")}
          </table>
        </div>
      </div>`;
  }

  /* ---------- tables ---------- */
  function statusPill(status) {
    return `<span class="pill ${status.toLowerCase()}">${status[0].toUpperCase() + status.slice(1)}</span>`;
  }

  function renderTables() {
    $("#studentsTable tbody").innerHTML = D.recentStudents
      .map((s) => `<tr>
        <td><strong>${s.id}</strong></td>
        <td><strong>${s.name}</strong></td>
        <td>${s.grade}</td>
        <td>${s.section}</td>
        <td>${s.admissionDate}</td>
        <td>${statusPill(s.status)}</td>
        <td><div class="cell-actions"><button class="icon-btn" title="View"><i class="fa-regular fa-eye"></i></button><button class="icon-btn" title="Edit"><i class="fa-regular fa-pen-to-square"></i></button></div></td>
      </tr>`)
      .join("");

    $("#invoicesTable tbody").innerHTML = D.recentInvoices
      .map((inv) => `<tr>
        <td><strong>${inv.number}</strong></td>
        <td>${inv.student}</td>
        <td><strong>${money(inv.amount)}</strong></td>
        <td>${inv.due}</td>
        <td>${statusPill(inv.status)}</td>
        <td><div class="cell-actions"><button class="icon-btn" title="View"><i class="fa-regular fa-eye"></i></button><button class="icon-btn" title="Download"><i class="fa-solid fa-download"></i></button></div></td>
      </tr>`)
      .join("");

    $("#paymentsTable tbody").innerHTML = D.recentPayments
      .map((p) => `<tr>
        <td><strong>${p.receipt}</strong></td>
        <td>${p.student}</td>
        <td><strong>${money(p.amount)}</strong></td>
        <td><span class="pill info">${p.method}</span></td>
        <td>${p.date}</td>
        <td><div class="cell-actions"><button class="icon-btn" title="Receipt"><i class="fa-solid fa-receipt"></i></button></div></td>
      </tr>`)
      .join("");
  }

  function bindTableSearch() {
    const bind = (inputId, tableId) => {
      const input = $(inputId);
      const rows = $$(`${tableId} tbody tr`);
      input.addEventListener("input", () => {
        const q = input.value.toLowerCase();
        rows.forEach((row) => {
          row.style.display = row.innerText.toLowerCase().includes(q) ? "" : "none";
        });
      });
    };
    bind("#searchStudents", "#studentsTable");
    bind("#searchInvoices", "#invoicesTable");
    bind("#searchPayments", "#paymentsTable");
  }

  /* ---------- export CSV / Excel / Print ---------- */
  function exportTable(tableId, fmt) {
    const table = $(tableId);
    const rows = [...table.querySelectorAll("tr")].map((tr) =>
      [...tr.querySelectorAll("th, td")].map((c) => c.innerText.trim()).join(",")
    );
    const csv = "\uFEFF" + rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    if (fmt === "csv") {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${tableId.replace("#", "")}.csv`;
      a.click();
    } else if (fmt === "excel") {
      const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="utf-8"></head><body><table>${table.outerHTML}</table></body></html>`;
      const b = new Blob(["\uFEFF" + html], { type: "application/vnd.ms-excel" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(b);
      a.download = `${tableId.replace("#", "")}.xls`;
      a.click();
    } else {
      window.print();
    }
  }

  /* ---------- activity ---------- */
  function renderActivity() {
    const toneMap = {
      indigo: ["var(--primary-soft)", "var(--primary)"],
      emerald: ["var(--success-soft)", "var(--emerald)"],
      sky: ["var(--info-soft)", "var(--sky)"],
      violet: ["var(--violet-soft)", "var(--violet)"],
      amber: ["var(--warning-soft)", "var(--amber)"],
      rose: ["var(--danger-soft)", "var(--rose)"],
      slate: ["var(--surface-3)", "var(--muted)"],
    };
    $("#activityList").innerHTML = D.activity
      .map((a) => {
        const t = toneMap[a.tone] || toneMap.slate;
        return `<li class="activity-item">
          <span class="a-ico" style="color:${t[1]};background:${t[0]}"><i class="fa-solid ${a.icon}"></i></span>
          <div><p><strong>${a.actor}</strong> ${a.action} <strong>${a.target}</strong></p><small>${a.time}</small></div>
        </li>`;
      })
      .join("");
  }

  /* ---------- notif / messages / tasks / language menus ---------- */
  const TONE_VAR = {
    danger: ["var(--danger)", "var(--danger-soft)", "fa-circle-exclamation"],
    warning: ["var(--amber)", "var(--warning-soft)", "fa-triangle-exclamation"],
    info: ["var(--sky)", "var(--info-soft)", "fa-calendar"],
    success: ["var(--emerald)", "var(--success-soft)", "fa-circle-check"],
    violet: ["var(--violet)", "var(--violet-soft)", "fa-cake-candles"],
  };

  function renderMenus() {
    $("#notifCount").textContent = `${D.notifications.filter((n) => n.unread).length} unread`;
    $("#notifList").innerHTML = D.notifications
      .map((n) => {
        const t = TONE_VAR[n.tone] || TONE_VAR.info;
        return `<div class="notif-item ${n.unread ? "unread" : ""}">
          <span class="n-ico" style="color:${t[0]};background:${t[1]}"><i class="fa-regular ${t[2]}"></i></span>
          <div><strong>${n.title}</strong><p>${n.msg}</p><small>${n.time} ago</small></div>
        </div>`;
      })
      .join("");

    $("#msgList").innerHTML = D.messages
      .map((m) => `<div class="notif-item ${m.unread ? "unread" : ""}">
          <span class="n-ico" style="color:var(--primary);background:var(--primary-soft)"><i class="fa-regular fa-envelope-open"></i></span>
          <div><strong>${m.from}</strong><p>${m.preview}</p><small>${m.time}</small></div>
        </div>`)
      .join("");

    $("#taskList").innerHTML = D.tasks
      .map((t) => {
        const pri = {
          High: ["var(--danger-soft)", "var(--danger)"],
          Med: ["var(--warning-soft)", "var(--warning)"],
          Low: ["var(--success-soft)", "var(--success)"],
        }[t.priority] || ["var(--success-soft)", "var(--success)"];
        return `<label class="task-item ${t.done ? "done" : ""}">
          <input type="checkbox" ${t.done ? "checked" : ""} />
          <span>${t.label}</span>
          <span class="t-meta"><span class="tone-tag" style="background:${pri[0]};color:${pri[1]}">${t.priority}</span><small>${t.due}</small></span>
        </label>`;
      })
      .join("");

    $("#languageMenu").innerHTML = C.locale.languages
      .map((l) => `<li><button class="dropdown-item ${l.code === C.locale.language ? "active" : ""}" data-lang="${l.code}">${l.label}</button></li>`)
      .join("");
    $$("#languageMenu [data-lang]").forEach((b) =>
      b.addEventListener("click", () => {
        C.locale.language = b.dataset.lang;
        tick();
        $$("#languageMenu [data-lang]").forEach((x) => x.classList.toggle("active", x === b));
      })
    );
  }

  /* ---------- calendar ---------- */
  const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const MONTH_SHORT = MONTH_NAMES.map((m) => m.slice(0, 3));
  const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  function renderCalendar() {
    const el = $("#calendar");
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const first = new Date(year, month, 1);
    const startDow = (first.getDay() - C.locale.weekStart + 7) % 7;
    const days = new Date(year, month + 1, 0).getDate();
    const prevDays = new Date(year, month, 0).getDate();
    const dowNames = C.locale.weekStart === 1
      ? ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
      : ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
    const today = now.getDate();

    let cells = "";
    for (let i = 0; i < startDow; i++) {
      cells += `<div class="cal-day out">${prevDays - startDow + i + 1}</div>`;
    }
    for (let d = 1; d <= days; d++) {
      const evs = D.calendarEvents.filter((e) => e.day === d);
      const isToday = d === today;
      const cls = ["cal-day", isToday ? "today" : "", evs.length ? "has-events" : ""].join(" ").trim();
      const dots = evs.length
        ? `<span class="cal-dots">${evs.map((e) => `<span style="background:${e.color}" title="${e.title}"></span>`).join("")}</span>`
        : "";
      cells += `<div class="${cls}" title="${evs.map((e) => e.title).join(", ")}" data-day="${d}">${d}${dots}</div>`;
    }

    el.innerHTML = `<div class="cal-head"><strong>${MONTH_NAMES[month]} ${year}</strong><span class="text-muted small">${D.upcomingEvents[0]?.title || ""}</span></div>
      <div class="cal-grid">${dowNames.map((d) => `<div class="cal-dow">${d}</div>`).join("")}${cells}</div>`;

    $$(".cal-day[data-day]").forEach((cell) =>
      cell.addEventListener("click", () => {
        const d = +cell.dataset.day;
        const evs = D.calendarEvents.filter((e) => e.day === d);
        const dayName = DAY_NAMES[new Date(year, month, d).getDay()];
        const list = $("#upcomingList");
        if (!evs.length) {
          list.innerHTML = `<li class="event-item"><p class="text-muted mb-0">No events on ${dayName}, ${d} ${MONTH_NAMES[month]}.</p></li>`;
        } else {
          list.innerHTML = evs.map((e) => `<li class="event-item"><span class="event-date" style="border-top:3px solid ${e.color}"><strong>${d}</strong><small>${MONTH_SHORT[month]}</small></span><div><h3>${e.title}</h3><p>${e.type} · ${dayName}</p></div></li>`).join("");
        }
      })
    );
  }

  function renderUpcoming() {
    $("#upcomingList").innerHTML = D.upcomingEvents
      .map((e) => {
        const num = e.date.match(/\d+/)?.[0] || "";
        const m = e.date.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/)?.[1] || MONTH_SHORT[new Date().getMonth()];
        const mi = MONTH_SHORT.indexOf(m);
        return `<li class="event-item"><span class="event-date"><strong>${num}</strong><small>${MONTH_SHORT[mi]}</small></span><div><h3>${e.title}</h3><p>${e.date} · ${e.type}</p></div></li>`;
      })
      .join("");
  }

  /* ---------- theme ---------- */
  function setTheme(theme, persist = true) {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.setAttribute("data-bs-theme", theme);
    $("#themeToggle").innerHTML = `<i class="fa-solid ${theme === "dark" ? "fa-sun" : "fa-moon"}"></i>`;
    if (window.PFCharts) window.PFCharts.updateTheme();
    if (persist) localStorage.setItem("pf-theme", theme);
  }

  /* ---------- quick actions ---------- */
  function renderQuickActions() {
    $("#quickGrid").innerHTML = C.quickActions
      .map((q) => `<div class="quick-item" tabindex="0" role="button">
          <span class="q-ico" style="color:var(--primary);background:var(--primary-soft)"><i class="fa-solid ${q.icon}"></i></span>
          <span>${q.label}</span>
        </div>`)
      .join("");
  }

  /* ---------- settings modal ---------- */
  function fillConfigModal() {
    $("#cfgName").value = C.school.name;
    $("#cfgMotto").value = C.school.motto;
    $("#cfgSessionLabel").value = C.academic.sessionLabel;
    $("#cfgSession").value = C.academic.session;
    $("#cfgVersion").value = C.school.version;
    $("#cfgLevelLabel").value = C.academic.levelLabel;
    $("#cfgTermLabel").value = C.academic.termLabel;
    $("#cfgTerm").value = C.academic.term;
    $("#cfgGrading").value = C.academic.grading.style;
    $("#cfgCurrency").value = C.locale.currency;
    $("#cfgSymbol").value = C.locale.currencySymbol;
    $("#cfgDateFmt").value = C.locale.dateFormat;
    $("#cfgTz").value = C.locale.timezone;
    $("#cfgLang").innerHTML = C.locale.languages.map((l) => `<option value="${l.code}" ${l.code === C.locale.language ? "selected" : ""}>${l.label}</option>`).join("");
    $("#cfgModuleList").innerHTML = C.modules.map((m) => `
      <div class="col-md-4 col-lg-3">
        <div class="form-check p-0 border rounded-3 p-2" style="border-color:var(--border)!important">
          <label class="form-check-label d-flex align-items-center gap-2 m-0" style="cursor:pointer">
            <input class="form-check-input" type="checkbox" ${m.enabled ? "checked" : ""} data-module-check="${m.id}" />
            <i class="fa-solid ${m.icon} text-muted"></i> ${m.label}
          </label>
        </div>
      </div>`).join("");
  }

  function applyConfig() {
    C.school.name = $("#cfgName").value;
    C.school.motto = $("#cfgMotto").value;
    C.school.version = $("#cfgVersion").value;
    C.academic.sessionLabel = $("#cfgSessionLabel").value;
    C.academic.session = $("#cfgSession").value;
    C.academic.levelLabel = $("#cfgLevelLabel").value;
    C.academic.termLabel = $("#cfgTermLabel").value;
    C.academic.term = $("#cfgTerm").value;
    C.academic.grading.style = $("#cfgGrading").value;
    C.locale.currency = $("#cfgCurrency").value;
    C.locale.currencySymbol = $("#cfgSymbol").value;
    C.locale.dateFormat = $("#cfgDateFmt").value;
    C.locale.timezone = $("#cfgTz").value;
    C.locale.language = $("#cfgLang").value;
    C.modules.forEach((m) => {
      const el = $(`[data-module-check="${m.id}"]`);
      m.enabled = el ? el.checked : m.enabled;
    });

    $("#schoolName").textContent = C.school.name;
    $("#schoolMotto").textContent = C.school.motto;
    $("#appVersion").textContent = C.school.version;
    $("#copySchool").textContent = C.school.name;
    $("#sessionValue").textContent = C.academic.session;
    $("#sessionLabel").textContent = C.academic.sessionLabel;
    $("#wSession").textContent = C.academic.session;
    $("#wTerm").textContent = `${C.academic.term} (1 of ${C.academic.termsPerYear})`;
    $("#welcomeSub").innerHTML = `Here's what's happening at <strong>${C.school.name}</strong> today.`;

    renderSidebar();
    $$(".sidebar-link").forEach((l) => l.addEventListener("click", () => showModule(l.dataset.module)));
    $$(".sidebar-link").forEach((l) => l.classList.toggle("active", l.dataset.module === "dashboard"));
    renderKpis();
    bindCounters();
    renderFinanceWidgets();
    tick();

    const modal = bootstrap.Modal.getInstance($("#configModal"));
    if (modal) modal.hide();
  }

  /* ---------- bootstrap ---------- */
  function init() {
    $("#schoolName").textContent = C.school.name;
    $("#schoolMotto").textContent = C.school.motto;
    $("#appVersion").textContent = C.school.version;
    $("#copySchool").textContent = C.school.name;
    $("#sessionValue").textContent = C.academic.session;
    $("#sessionLabel").textContent = C.academic.sessionLabel;
    $("#wSession").textContent = C.academic.session;
    $("#wTerm").textContent = `${C.academic.term} (1 of ${C.academic.termsPerYear})`;

    renderSidebar();
    $$(".sidebar-link").forEach((l) => l.addEventListener("click", () => showModule(l.dataset.module)));
    $$(".sidebar-link").forEach((l) => l.classList.toggle("active", l.dataset.module === "dashboard"));

    renderKpis();
    bindCounters();
    renderFinanceWidgets();
    renderTables();
    bindTableSearch();
    renderActivity();
    renderMenus();
    renderCalendar();
    renderUpcoming();
    renderQuickActions();
    fillConfigModal();

    if (window.PFCharts) window.PFCharts.init();

    $("#globalSearch").addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) return;
      const hit = C.modules.find((m) => m.enabled && (m.label.toLowerCase().includes(q) || m.id.includes(q)));
      if (hit) showModule(hit.id);
    });

    const saved = localStorage.getItem("pf-theme");
    setTheme(saved === "dark" ? "dark" : "light", false);
    $("#themeToggle").addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      setTheme(next);
    });

    $$("[data-export]").forEach((btn) =>
      btn.addEventListener("click", () => exportTable("#" + btn.dataset.export + "Table", btn.dataset.fmt))
    );

    $("#sidebarToggle").addEventListener("click", () => {
      const isMobile = window.innerWidth <= 991;
      if (isMobile) {
        $("#sidebar").classList.toggle("open");
        $("#sidebarBackdrop").classList.toggle("show");
      } else {
        $("#sidebar").classList.toggle("collapsed-desktop");
      }
    });
    $("#sidebarBackdrop").addEventListener("click", () => {
      $("#sidebar").classList.remove("open");
      $("#sidebarBackdrop").classList.remove("show");
    });

    $("#quickActionsBtn").addEventListener("click", () => bootstrap.Modal.getOrCreateInstance($("#quickModal")).show());
    $$(".quick-item").forEach((q) => q.addEventListener("click", () => bootstrap.Modal.getInstance($("#quickModal")).hide()));

    $("#cfgApply").addEventListener("click", applyConfig);
    $("#configModal").addEventListener("show.bs.modal", fillConfigModal);

    $("#calToday").addEventListener("click", renderCalendar);

    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        $("#globalSearch").focus();
      }
    });

    window.addEventListener("resize", () => {
      if (window.PFCharts) window.PFCharts.resizeAll();
    });

    tick();
    setInterval(tick, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
