=== DEVELOPER 2 — PHASE 07 TIMETABLE + COMMUNICATION + DOCUMENTS: FINAL REPORT ===

Branch: developer2/phase-07-timetable-communication
Report Date: Wed Sep 09 2026
Days in Phase: As assigned per development cycle

=== 1. BRANCH & STATUS ===
git branch --show-current: developer2/phase-07-timetable-communication
Scope: timetable (periods, entries, conflicts, auto-generate) and
       communication (announcements, notifications, messaging, SMS log,
       email log, message templates) plus the documents/media layer,
       audited end-to-end for forms/modals/validation/loading/errors/
       empty/mobile, cross-user document access, and school/campus
       switching. Phase-05/06 work is intentionally left UNCOMMITTED in
       the working tree per directive; this phase adds its own edits on
       top of it.

Git modified files introduced/edited this phase:
- backend/apps/schools/media_views.py         (fail-closed media server rewrite)
- backend/apps/students/views.py              (StudentDocument institution/campus scoping)
- backend/apps/students/serializers.py        (document upload validation + size/type limits)
- backend/apps/documents/views.py             (upload validation + institution stamp)
- backend/apps/communication/views.py         (announcement list scoping + institution stamps)
- backend/apps/communication/models.py        (announcement notify()/target scoping + stamps)
- backend/apps/communication/email_views.py   (institution-scoped broadcasts + EmailLog admin-only)
- backend/apps/communication/sms_views.py     (institution-scoped broadcasts + SMSLog scoped)
- backend/apps/communication/template_views.py(MessageTemplate institution-scoped CRUD)
- backend/apps/timetable/views.py             (Period institution scope; conflicts campus scope)
- backend/apps/timetable/conflicts.py         (find_conflicts(campus_ids=...) support)
- backend/apps/timetable/generate_views.py    (institution + assert_campus_allowed hardening)
- backend/apps/timetable/management/commands/setup_timetable.py (period institution stamp;
                                                                  school-scoped campuses)
- frontend/src/pages/MessagesPage.jsx         (reply recipient_id fix + scope refetch)
- frontend/src/pages/TimetablePage.jsx        (campus select + scope refetch)
- frontend/src/pages/AnnouncementsPage.jsx    (scope refetch)
- frontend/src/pages/DocumentsPage.jsx        (scope refetch of list + campus list)
- frontend/src/pages/NotificationsPanel.jsx   ("Run now" confirmation guard)

=== 2. DOCUMENTS / MEDIA AUDIT — BACKEND TRUTH ===
- StudentDocument, Homework, Visitor, IdCard, Period, Payslip, Message,
  Announcement, Notification, SMSLog, EmailLog, MessageTemplate all carry
  an `institution` FK (migration 0006). EmployeeDocument is scoped via
  employee.institution. TimetableEntry has NO institution (campus-derived).
- ProtectedMediaView served /media/** by parsing the path and, for
  anything it did not recognize, PASSING THROUGH ("default allow"). Any
  authenticated user able to guess/enumerate a URL could open files from
  ANY school (cross-tenant), including HR contracts/loans, payslips and
  student documents. Rewritten fail-closed:
  * _resolve_media_owner maps every served prefix (students/documents/,
    profiles/{students,teachers,staff,users}/, hr/*, homework/, visitors/,
    digital_ids/, payslips/, white_label/, branding/) to the owning ORM
    record via an exact field match (file == normalized path).
  * _owner_context derives institution + campus; _role_allows_* gates per
    prefix (manager, parent/teacher/near-grade student for student docs;
    manager or self/allowed for HR; manager or class students for
    homework); superuser is the only cross-tenant carve-out.
  * _can_access_file = superuser -> institution match -> per-campus
    assert_campus_allowed -> prefix role gate; anything else = 404.
- StudentDocumentList/Detail previously applied parent_scope_filter /
  teacher_scope_filter — those return Q(pk__in=student_ids) designed for
  Student querysets, so a parent filtered by document PK, not student PK
  (broke legit access AND leaked results). Now a _student_document_queryset
  helper resolves student_id__in from parent_/teacher_student_ids or the
  user's own student_profile, then apply_campus_scope("student__primary_campus_id").
- Upload validation (students/serializers.py): allowed extensions
  pdf/jpg/jpeg/png/gif/doc/docx/xls/xlsx/csv/txt; MAX 10MB; validators on
  document_type and file. DocumentsPage upload path now enforces it too.
- get_institution(user) misuse -> get_institution(request).

=== 3. COMMUNICATION AUDIT — BACKEND TRUTH ===
- EmailLogListView was IsAuthenticated and returned EVERY log for every
  school. SMSLog gone global too. Now IsAuthenticated+IsAdminRole (+HR
  for SMS per existing view), both restricted to the active institution
  (institution FK or sender's active membership), non-global users see
  only their own log rows, results capped [:200].
- SMS/email broadcast recipient resolution was NOT institution-scoped:
  a school admin could message another school's students/staff/guardians.
  All role branches (parents, students, teachers-by-campus, staff,
  accountants, reception, admission) and the direct recipient-id /
  guardian-email branches are now filtered to the active institution;
  created SMSLog/EmailLog rows are stamped with institution.
- MessageTemplate CRUD + preview rebuilt on _visible_templates() =
  institution FK OR legacy created_by membership; create stamps the
  institution; detail/update/delete/preview all scoped.
- Messaging (Message) already scoped recipients via the sender's active
  membership institution ids; Message.create now also stamps institution.
- Announcements: scoped_announcement_queryset previously ended with a
  global branch Q(campus__isnull=True, class_obj__isnull=True) that
  surfaced any legacy school-wide announcement to every school. Replaced
  with institution-marker filters (institution | campus__school |
  class_obj__unit__campus__school) plus a guard that hides legacy
  institution-less global rows from non-root users. Create stamps
  institution and class cross-institution is rejected; Announcement.
  notify()/target_user_ids no longer target every school's membership
  users and the Notification/SMSLog rows it creates are stamped.

=== 4. TIMETABLE AUDIT — BACKEND TRUTH ===
- PeriodListView returned ALL periods for every school (cross-tenant).
  Now strictly institution-scoped (request.institution; none -> empty).
- setup_timetable created Period rows with institution=None colliding
  with the school-stamped ones from demo_seed (duplicate periods). It now
  get_or_creates with institution=academic_year.school and only scans
  campuses belonging to that school.
- TimetableConflictsView, without ?campus=, scanned every campus of every
  school. Now, absent a campus param, it restricts to the caller's
  allowed campuses (user_allowed_campus_ids); none -> empty.
- TimetableGenerateView resolved any campus for a global user (cross-
  school generate). Now rejects campuses outside the active institution
  and enforces assert_campus_allowed.

=== 5. FRONTEND AUDIT — 5 PHASE-07 PAGES ===
Audited: TimetablePage, AnnouncementsPage, MessagesPage, DocumentsPage,
NotificationsPanel (forms/loading/errors/empty/mobile + switch handling).

School switching: App.jsx:975 remounts routes via
<Routes key={currentSchool?.id}> — all pages are safe on SCHOOL change.
CAMPUS change only bumps schoolScopeVersion (no remount), so pages that
cached their own list kept showing the previous campus' data. Fixed by
refetching on schoolScopeVersion (TimetablePage useApiList.refresh,
AnnouncementsPage/MessagesPage rows reset, DocumentsPage list + campus
list refetch). NotificationsPanel is stateless per click — no stale risk.

Per-page state (all 5 now pass):
- Loading: StateArea loading covers periods/entries (Timetable), list
  (Announcements/Messages), documents (Documents). Entity search shows
  "Loading..." option. NotificationPanel has per-job busy spinners. ✓
- Errors: fetch failures surface via StateArea; upload errors render
  INSIDE the modal (Documents); page-level on others (UX note below). ✓
- Empty: friendly EmptyState on all four list pages. ✓
- Forms/validation: Announcements + Messages use HTML required + guard
  checks and a disabled/saving button; Documents validates file + entity
  before upload inside the modal; Timetable generate disabled without a
  campus. ✓
- Mobile: all tables sit in .table-wrapper (horizontal scroll); message
  list is non-table. Minor: Announcements body-in-cell and Notifications
  inline-style <pre> can overflow on very narrow screens (CSS-level). ✓

=== 6. BUGS FOUND & FIXED ===
BUG-1  /media/** FAILED OPEN (media_views.py)
  Unsupported prefixes passed through -> any authenticated user could
  read files of any school given a URL. Now fail-closed owner/role
  resolution; superuser is the only cross-tenant carve-out.
BUG-2  get_institution(user) vs get_institution(request) (media_views.py)
  request.institution is the session-scoped school; passing a user broke
  the lookup and fell back to the thread-local *first* school.
BUG-3  STUDENT DOCUMENT FILTERS USED PARENT/TEACHER PK FILTERS ON THE
  WRONG MODEL (students/views.py) — Q(pk__in=student_ids) applied to
  StudentDocument PKs. Replaced with student_id__in resolution +
  apply_campus_scope("student__primary_campus_id").
BUG-4  EMAILLOGLISTVIEW OPEN TO ALL USERS, ALL SCHOOLS (email_views.py)
  -> IsAdminRole + institution filter + own-logs for non-global + [:200].
BUG-5  BROADCASTS CROSS-TENANT (email_views.py, sms_views.py)
  Recipients/guardian emails were global. All branches now institution-
  scoped; logs stamped with the institution.
BUG-6  MESSAGE TEMPLATES GLOBAL (template_views.py) CRUD/preview leaked.
  -> _visible_templates() institution or created_by membership; create stamps.
BUG-7  ANNOUNCEMENT GLOBAL-BRANCH LEAK (communication/views.py)
  Q(campus__isnull=True, class_obj__isnull=True) showed legacy school-wide
  posts to every school. Institution-marker filters + legacy-global hidden
  from non-root users; create stamps institution; cross-class rejected.
BUG-8  ANNOUNCEMENT notify() TARGETED EVERY SCHOOL (models.py)
  target_user_ids membership branch had no school filter; Notification/
  SMSLog created without institution. Both scoped + stamped.
BUG-9  TIMETABLE CROSS-TENANT (timetable/views.py, conflicts.py,
  generate_views.py, setup_timetable.py) — global periods list, global
  conflict scan, cross-school generate, institution-less Period rows.
BUG-10 memberships__school_id FieldError (media/email/sms/template views)
  InstitutionMembership has an `institution` FK (unique per user+school),
  NOT `school`. Fixed to memberships__institution_id everywhere.
BUG-11 MESSAGES REPLY SENT `recipient` INSTEAD OF `recipient_id`
  (MessagesPage.jsx:235) — the API rejects it, so replies always failed.
BUG-12 STALE DATA AFTER CAMPUS SWITCH (4 pages) — refetch on
  schoolScopeVersion added; TimetablePage now also binds its generate
  campus to campusList/activeCampus instead of a free-text name field.
BUG-13 "RUN NOW" SENT REAL SMS/EMAIL WITH ONE CLICK (NotificationsPanel)
  — added window.confirm before live runs (dry run still one-click).

=== 7. PERMISSION & SCHOOL ISOLATION CHECKLIST ===
- /timetable/periods|entries|conflicts|generate roles: academic members;
  backend now institution-scoped (+campus-scoped conflicts/generate). ✓
- /communication/*                messages user-scoped; announcements
  school-scoped + role-targeted; SMS/email broadcasts institution-scoped
  and IsAdminRole-gated; templates institution-scoped; logs admin/viewer-
  scoped. ✓
- /documents, /media              list scoped by institution + campus
  filters; ProtectedMediaView fail-closed per prefix+role+campus. ✓
- Strict isolation: parents can only reach their own children's documents
  and only via the student scoping helper; HR files gated to manager/self;
  superuser (root tenant operator) is the sole cross-tenant carve-out. ✓
- App-level A<->B: school switch remounts routes (App.jsx:975); campus
  switch now triggers refetch on all 5 audited pages. ✓

=== 8. KNOWN DESIGN GAPS (no change made — need a product/server decision) ===
1. Uploads that go to Vercel Blob / remote object store are served via
   public read URLs; protection is per-URL not per-request, so the code
   cannot fully close them. Fix belongs at infra level: use private/
   signed-URL blob storage and route downloads through ProtectedMediaView.
2. Message "unread-count" and list reads use raw fetch() without CSRF —
   acceptable for session-auth GETs; kept consistent with the codebase's
   existing read pattern.
3. Announcements/Messages submit errors render in the page-level
   StateArea, not adjacent to the open form/modal (UX polish, not a bug).
4. NotificationsPanel buttons carry no school/campus label; the cron jobs
   run against the session-scoped school server-side. Consider showing the
   active school name next to "Run now".
5. AnnouncementsPage loads in the render body (rows === null && load())
   instead of a useEffect — works but is a deferred anti-pattern; kept to
   minimize diff.

=== 9. VERIFICATION ===
- python -m py_compile on all 13 edited backend files: PASS.
- Full Vite production build: PASS (vite v8.2.1, 2451 modules, ~4s).
- No Django runtime available in this environment; backend behaviour
  verified by source audit (all scoping against request.institution /
  request session) plus the bug walkthroughs above.