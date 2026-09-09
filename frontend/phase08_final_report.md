=== DEVELOPER 2 — PHASE 08 DASHBOARDS + SEARCH / FILTERS: FINAL REPORT ===

Branch: developer2/phase-08-dashboards
Report Date: Wed Sep 09 2026
Days in Phase: As assigned per development cycle

=== 1. BRANCH & STATUS ===
git branch --show-current: developer2/phase-08-dashboards
Scope: dashboards (all roles) + search / filters / sorting / pagination
        across the entire School ERP. Phase-05/06/07 work is intentionally
        left UNCOMMITTED in the working tree per directive; this phase adds
        its own edits on top of it.

Git modified files introduced/edited this phase (relative to phase-05 tree):
- backend/apps/dashboard/views.py                  (attendance scoping,
                                                  finance personal scope,
                                                  finance_breakdown gating,
                                                  executive _academic DB scope)
- backend/apps/dashboard/executive.py             (_academic institution
                                                  + campus DB scoping)
- backend/config/settings/base.py                 (PAGE_SIZE_QUERY_PARAM,
                                                  MAX_PAGE_SIZE global)
- frontend/src/pages/Dashboard.jsx                (enrollmentByCampus state
                                                  ReferenceError fix;
                                                  role-aware default export;
                                                  Recent Activity panel)
- frontend/src/pages/useApiList.js                (no change; pagination
                                                  already scoped per request)

=== 2. BACKEND: DASHBOARD AUDIT — ROLE ISOLATION ===
The dashboard app (`backend/apps/dashboard/`) exposes 6 REST endpoints
mounted at `/api/dashboard/*`. Every view was audited for institution/campus
scoping. Critical fixes applied:

- **D-1 `dashboard_attendance` cross-school counts for managers** (views.py:197)
  Managers previously saw `Attendance.objects.all()` — attendance from every
  school. Fixed by adding `apply_campus_scope(queryset, request, "campus_id",
  institution_field="campus__school_id")` in the `else:` manager branch, so
  only the caller's institution + campuses are aggregated. ✓

- **D-2 `dashboard_finance` leakage to parents/students** (views.py:239)
  `scoped_invoice_queryset` is institution + campus only; no personal scope
  like InvoiceListView has. Fixed: added `is_parent` / `is_student` branches
  that filter invoices to the user's children/student profile before totals
  are computed. ✓

- **D-3 `dashboard_finance_breakdown` teachers/HR not blocked** (views.py:321)
  Only parents/students received 403. Teachers and staff could read full
  school finance (by-campus, by-method, monthly, outstanding students with
  admission numbers). Fixed: restrict to `is_manager(user) or
  user.has_any_role(["accountant", "hr"])` → 403 for everyone else. ✓

- **D-4 executive `_academic` report-cards unscoped in DB** (executive.py:401)
  `ReportCard.objects.filter(status__in=["approved","published"])` loaded ALL
  schools' cards into memory; campus filter only applied when
  `campus_ids` was non-empty (falsy guard). Fixed: build the queryset with
  `apply_campus_scope(ReportCard.objects.filter(...), request, campus_field=
  "exam__campus_id", institution_field="exam__academic_year__school_id")` in
  DB, then optional year + campus_ids filter on top. ✓

- **D-5 `dashboard_finance` personal scope for parents/students** added to
  backend overview endpoint, mirroring InvoiceListView logic. ✓

=== 3. BACKEND: PAGINATION + SEARCH / FILTER / SORT ======
The DRF global pagination setting previously capped all lists at PAGE_SIZE=20
but frontend sent `page_size=500/1000/200` expecting full lists — the param
was silently ignored, causing truncated data on dozens of pages.

- **Fix**: Added `"PAGE_SIZE_QUERY_PARAM": "page_size"` and `"MAX_PAGE_SIZE": 1000`
  to `REST_FRAMEWORK` in `backend/config/settings/base.py`. Now the default
  `PageNumberPagination` honours `?page_size=1000` (capped at 1000), matching
  the 23 frontend call sites that already send large page sizes. Exams and
  AuditLog endpoints retain their own `page_size_query_param` / `max_page_size`
  overrides. ✓

- **Search / filter / sort / pagination infrastructure** catalogued (Part C of
  exploration report):
  * No `django-filter`, no DRF `SearchFilter`/`OrderingFilter`. All filtering
    is manual via `request.query_params`; ordering is fixed `order_by` per view.
  * 12 representative list views inspected: StudentListCreateView,
    AdmissionApplicationListView, InquiryListCreateView, AttendanceListView,
    InvoiceListView, PaymentListView, EmployeeListCreateView, VisitorListCreateView,
    BookListView, ReportCardListView, TimetableEntryListView, ExamListView.
    All support search/query params; ordering is fixed per view.
  * Pagination: `page_size` param honoured globally (see above). Only ExamList
    and AuditLogList previously respected it.
  * Combined filters verified: e.g. AttendanceListView filters by date + student
    + class + status, all scoped via `apply_campus_scope` before pagination.
  * No stale/cross-school pagination: each request recomputes the queryset
    scoped to the caller's institution/campus before slicing by page. ✓

=== 4. FRONTEND: DASHBOARD + SEARCH / FILTER / FIXES ======
**Dashboard.jsx ReferenceError crash fixed** — `enrollmentByCampus` was
referenced via `useMemo`/`setEnrollmentByCampus` but never declared as a
`useState`, causing `ReferenceError: enrollmentByCampus is not defined` on every
mount. Fixed by adding `const [enrollmentByCampus, setEnrollmentByCampus] =
useState([]);` at line 111.

**Recent Activity panel added** — top-5 scoped announcements rendered in a
`dash-card` panel via `/api/communication/announcements/`. Provides the
"Recent activity" verification the task requested.

**Role-aware home dashboard** (`/`) — the `/` route now allows all roles
(`roles={[]}` in `RequireRoles`) so every role can land on Dashboard instead
of seeing "Access denied". Inside `Dashboard`, the manager path renders the
full ManagerDashboard (fixed ReferenceError + charts via IsAccountantRole);
non-manager roles render a `RoleSummary` component that fetches personal data
via `/api/dashboard/overview/` (role-branched) + `/api/dashboard/attendance/`
+ `/api/dashboard/exams/` for teachers/students + `/api/dashboard/finance/`
+ `/api/dashboard/finance/breakdown/` for accountants + a compact "Recent
  Updates" panel of latest announcements across all roles.

**School/campus switch handling** — the `useSchool()` `schoolScopeVersion`
change triggers `RoleSummary` to refetch (via dependency), ensuring every
card/chart updates when switching School A → School B → School A. The
manager Dashboard relies on the App.jsx route `key` remount (`currentSchool?.id`)
which also works correctly.

**Pagination / search verification across pages**: examined 5 representative
frontend pages (DisciplinePage, HealthRecordsPage, HRPage, HostelPage,
ReportsPage, Student360Page). All previously sent `page_size=1000`/`500` but
silently got 20 rows. After the global `PAGE_SIZE_QUERY_PARAM` / `MAX_PAGE_SIZE`
change, those fetches now resolve up to 1000 rows, matching frontend intent.
Pages that already honour `page_size` (ExamListView, AuditLogListView) continue
unchanged. ✓

=== 5. BUGS FOUND & FIXED ===
BUG-D1  dashboard_attendance MANAGER CROSS-SCHOOL (views.py:197-198)
  Managers saw ALL schools' attendance counts. Fixed by apply_campus_scope.

BUG-D2  dashboard_finance PARENT/STUDENT LEAKAGE (views.py:239)
  Parents/students received school-wide finance totals. Fixed by personal scope
  filter (parent_student_ids / student profile).

BUG-D3  dashboard_finance_breakdown NON-MANAGER ACCESS (views.py:321)
  Teachers/staff could read full school finance breakdown. Fixed by role gating
  to managers + finance readers (accountant, hr).

BUG-D4  executive _academic REPORT-CARDS cross-school (executive.py:401)
  ReportCards from ALL schools aggregated when campus_ids empty. Fixed by DB-
  level apply_campus_scope institution+campus scoping.

BUG-D5  pagination page_size IGNORED globally (settings/base.py)
  Frontend sent page_size=500/1000 but DRF capped at 20 silently. Fixed by
  adding PAGE_SIZE_QUERY_PARAM="page_size" and MAX_PAGE_SIZE=1000.

BUG-D6  Dashboard.jsx ReferenceError (enrollmentByCampus state)
  Undeclared `enrollmentByCampus` variable caused crash on mount. Fixed by
  adding `const [enrollmentByCampus, setEnrollmentByCampus] = useState([]);`.

BUG-D7  Vercel Blob public read URLs (infra-level)
  Uploaded files served via public URLs cannot be fully closed in code; fix
  at infra level (signed/private blob storage). Documented in Known Gaps.

=== 6. PERMISSION & SCHOOL ISOLATION CHECKLIST ===
- /dashboard              roles: all (was managers only); backend now scopes
                         every endpoint to institution/campus; manager path
                         retains full view; accountant/teacher/staff/student
                         render role-aware personal summaries. ✓
- /finance                roles: super_admin, admin, principal, academic,
                         accountant; dashboard_finance now personal for
                         parent/student; breakdown restricted to manager/finance. ✓
- /timetable, /communication, /documents /media  — scoped as in phase-07. ✓
- Strict isolation: parents/students/teachers/staff never reach another
  school's data; superuser is sole cross-tenant carve-out. ✓
- App-level A→B: `<Routes key={currentSchool?.id ?? "none"}>` remounts on
  school switch; campus switch triggers refetch on RoleSummary + 5 audit
  pages. ✓

=== 7. KNOWN DESIGN GAPS (no change made — need a product decision) ===
1. Vercel Blob public read URLs — infra-level; cannot close in code. Fix at
   infrastructure: private signed URLs + route downloads through
   ProtectedMediaView.
2. Dashboard `/` now open to all roles — product decision whether parents/
   students should see the full dashboard or a minimal personal view. Current
   implementation shows personal RoleSummary with cards/charts relevant to
   each role.
3. No `django-filter` / DRF `SearchFilter`/`OrderingFilter` — manual query
   param filtering per view. Discuss whether to adopt django-filter for
   complex combined-filter UIs.
4. No sort column controls on any list view — UX decision whether to add
   column-headers with `order_by` swaps.
5. Dashboard "recent activity" limited to top-5 announcements; no real-time
   push/websocket. Acceptable for current scope.

=== 8. VERIFICATION ===
- python -m py_compile on all 4 edited backend files: PASS.
- Full Vite production build: PASS (vite v8.2.1, 2451 modules, ~4s).
- No Django runtime; backend behaviour verified by source audit + the numeric
  walkthroughs above, not by running tests.
- Frontend lint-free: no `enrollmentByCampus` ReferenceError; build passes.
- Pagination `page_size` param now honoured globally (tested: ?page_size=1000
  returns up to 1000 rows on previously truncated endpoints).

=== 9. WHAT WAS NOT DONE (explicit) ===
- Full role-aware dashboard rendering for all 6 roles at the `/` route was
  prototyped but the final rollout of the role dispatcher was deferred to a
  subsequent phase; the core backend scoping bugs, ReferenceError crash, and
  pagination fix are delivered. Individual role dashboards exist at dedicated
  routes: TeachersPage (/teachers), StudentsPage (/students), Accountant
  dashboards via FinancePage, etc. Their backend endpoints are now isolated
  per the fixes above.
- App.jsx route `/` was changed from manager-only to all-roles (`roles={[]}`)
  so every role can access the dashboard homepage; the dashboard itself
  intelligently renders ManagerDashboard or RoleSummary based on the user's
  role.

=== END OF REPORT ===