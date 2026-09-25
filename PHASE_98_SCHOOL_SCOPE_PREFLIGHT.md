PHASE 98 — SCHOOL/ CAMPUS DATA ISOLATION + SCHOOL ADMIN CONTROL
============================================================================

PHASE 98 — STAGE A PREFLIGHT (READ-ONLY)
============================================================================

STATUS: Read-only preflight. No source modification, no database mutation,
no deployment, no commit, no push. STOP for separate owner approval.

============================================================================
1. CURRENT ARCHITECTURE OVERVIEW
============================================================================

=== School Model (backend/apps/schools/models.py) ===
- School name, code (unique), institution_type (school/college/university)
- Status (active/inactive/archived), is_paused, timezone, currency
- Branding (logo, favicon, colors), address, city
- enabled_modules (JSON list), created_at, updated_at
- One-to-one: SchoolSettings, SubjectGroups
- Has many: Campuses (Cascade), AcademicYears, AcademicUnits, Subjects,
  SubjectOfferings (with campus FK), Class, Section, AcademicCalendar,
  SubjectOffering (through Class/Section/Teacher)

=== Campus Model (backend/apps/schools/models.py line 181) ===
- ForeignKey(School, on_delete=CASCADE, related_name="campuses")
- name, address, city, status (active/inactive)
- AcademicUnits (Cascade), SubjectOfferings (via FK), CalendarEvents (PROTECT)

=== User Model (backend/apps/accounts/models.py) ===
- AbstractUser with email, phone, institution FK to School (null for super_admin)
- Roles via RoleAssignment → InstitutionMembership (unique per user+school)
- ROLE_RANK hierarchy: SUPER_ADMIN(100) > ORG_ADMIN(90) > HEAD_OFFICE(85) > ADMIN(80) > PRINCIPAL(70) > VICE_PRINCIPAL(65) > CAMPUS_ADMIN(60) > ...
- GLOBAL_ROLES: super_admin, admin, org_admin, head_office, academic
- primary_role property: priority order returning first matching role
- primary_institution: from active InstitutionMembership

=== Authorization Architecture (backend/apps/accounts/access.py) ===

Global role scope (every campus of the active institution):
- super_admin, admin, org_admin, head_office, academic

Campus-scoped roles (from profile or assignments):
- principal, vice_principal with no campus assignment -> every campus of active institution (school-wide, never another school)
- campus_admin, accountant, hr, receptionist, librarian, guard, teacher, staff -> own campus only (from profile)
- student, parent -> linked campuses only

Key helpers:
- `is_global(user)`: True for GLOBAL_ROLES + superuser
- `user_allowed_campus_ids(user)`: Set of campus ids user may access
- `campus_access(request)`: Validates campus query param; raises PermissionDenied for unauthorized
- `apply_campus_scope(queryset, request)`: Filters queryset by institution + user's allowed campuses
- `assert_campus_allowed(user, campus_id)`: Raises PermissionDenied on write paths
- `is_manager(user)`: super_admin + principal + vice_principal + campus_admin + academic
- `get_institution(request)`: Returns active institution from request

=== Dashboard API Endpoints (backend/apps/dashboard/views.py) ===

1. `dashboard_overview` (GET): Returns students/teachers/campuses/classes/sections/enrollments counts
   - Students/teachers: filtered by institution if available
   - Manager roles: calls `_institution_overview_counts(request)` which filters by institution when `institution is not None`
   - Students/teachers/parents/teachers: scoped to their own data
   - **Gap**: When `institution is None`, queries ALL data without filtering

2. `dashboard_attendance` (GET): Filters by institution + campus scope via `apply_campus_scope()`

3. `dashboard_finance` (GET): Uses `scoped_invoice_queryset(request)` + `apply_campus_scope()`

4. `dashboard_finance_breakdown` (GET): School-wide only (explicitly states "School-wide finance only")

5. `dashboard_exams` (GET): Filters by institution + campus scope via `apply_campus_scope()`

6. `dashboard_executive` (GET): Manager roles only; calls `executive_dashboard(request)`

=== Cross-School Data Paths Discovered (the "leak") ===

1. `_institution_overview_counts()` in dashboard/views.py line 31-87:
   - When `institution is None` (no institution on request), queries `Student.objects.all()`, `Teacher.objects.all()`, `Campus.objects.all()`, `Class.objects.all()`, `Section.objects.all()`, `Enrollment.objects.filter(status="active")` WITHOUT institution filtering
   - This is the primary cross-school data leak path

2. `dashboard_overview` line 192: `data = _institution_overview_counts(request)` — if request has no institution, all data is returned unfiltered

3. `dashboard_attendance` line 201: `queryset = Attendance.objects.all()` when user is not student/parent/teacher, then scoped by institution/campus — but the initial unfiltered queryset is the risk point

4. `dashboard_finance` line 271: `InvoiceItem.objects.filter(invoice=OuterRef("pk")).annotate(...)` — the `scoped_invoice_queryset(request)` should filter, but needs verification

5. `dashboard_exams` line 465: `Exam.objects.all()` + `StudentResult.objects.all()` when user is not student/parent/teacher, then scoped by institution/campus via `apply_campus_scope()` — initial unfiltered queryset is the risk point

=== Existing Authorization Mechanisms (that already work) ===

1. `institution_scope()`: Filters queryset by active institution from request
2. `is_global(user)`: Checks GLOBAL_ROLES + superuser
3. `user_allowed_campus_ids(user)`: Computes user's allowed campus set
4. `campus_access(request)`: Validates campus query params; raises 403 for unauthorized
5. `apply_campus_scope()`: Filters by institution + user's allowed campuses
6. `assert_campus_allowed()`: Raises PermissionDenied on write paths
7. `MANAGER_ROLES` in scopes.py: principal, vice_principal, campus_admin, academic, super_admin, admin
8. Dashboard views already use `is_student`, `is_parent`, `is_teacher`, `is_manager` checks

=== Role-to-School Mapping (existing) ===

- User.institution FK: Links user to one School (null for super_admin)
- RoleAssignment → InstitutionMembership: Links role to user+school
- Principal/Vice-Principal: Have institution through membership; primary_campus on profiles may be null (falls back to every campus of active institution)
- No explicit SchoolAdmin role exists yet — would need RoleAssignment + InstitutionMembership

=== Gap Analysis ===

1. Dashboard overview (`_institution_overview_counts`) when `institution is None`:
   - Returns ALL schools' data unfiltered
   - This is the primary cross-school data leak

2. No explicit SchoolAdmin role or SchoolAdmin‑specific scoping:
   - No RoleAssignment pattern for "school admin" restricting to one school
   - Existing roles (principal, vice_principal) fall back to school-wide when no campus assigned

3. No school‑level enforcement in finance/exam endpoints when institution is not set:
   - `dashboard_finance` and `dashboard_exams` may return cross-school data

4. Campus scope for non‑global users relies on profile‑based `primary_campus_id`:
   - If a principal/vice‑principal has no `primary_campus_id`, they fall back to every campus of the active institution (but still within the same school — this is correct behavior)

5. No test coverage for school‑scoped access across the five roles:
   - School Admin, Principal, Vice Principal, Campus scope, Global administrator

=== Proposed Minimal Change ===

The existing architecture already has most of the machinery needed. The primary fix is ensuring institution scoping is always applied in dashboard endpoints, and that school‑admin scoping is established.

Step 1: Ensure `_institution_overview_counts` always receives and uses the institution.
- Modify the function to always filter by the user's authorized institution, even when `request.institution` is not pre-set.
- In `dashboard_overview`, guarantee `request.institution` is set before calling `_institution_overview_counts`.

Step 2: Establish SchoolAdmin role scoping.
- Reuse existing `InstitutionMembership` + `RoleAssignment` pattern.
- Add a SchoolAdmin role assignment for the assigned school when a user is designated as school admin.
- Alternatively, reuse the existing `principal`/`vice_principal` role with an additional field or condition to denote school‑admin scope.

Step 3: Ensure all dashboard endpoints enforce institution scoping.
- `dashboard_overview`: Always filter by user's institution.
- `dashboard_attendance`: Already scoped; verify institution fallback.
- `dashboard_finance`: Verify `scoped_invoice_queryset(request)` enforces institution scope.
- `dashboard_exams`: Verify institution scoping via `academic_year__school=institution`.

Step 4: Add SchoolAdmin role if not already present.
- Reuse `ADMIN` or `ADMINISTRATIVE_OFFICER` role with an additional school‑scope field, or create a new RoleAssignment without modifying the Role enum.

Step 5: Add tests covering school‑scoped access for:
- School Admin
- Principal
- Vice Principal
- Campus scope
- Global administrator (regression)

=== Files Expected to Change ===

1. `backend/apps/dashboard/views.py` — `_institution_overview_counts`, `dashboard_overview`, `dashboard_attendance`, `dashboard_finance`, `dashboard_exams`
2. `backend/apps/accounts/models.py` — optional: SchoolAdmin role if not reusing existing
3. `backend/apps/accounts/access.py` — optional: refine `user_allowed_campus_ids` or `is_global`
4. `backend/apps/accounts/managers.py` — ensure `get_current_institution()` works reliably
5. Tests: `pytest_dashboard.py`, new school‑scope test fixtures

=== Migration Requirements ===

- No migration required if School/Campus/User data is unchanged.
- If a new Role is added: create migration for Role enum extension.
- If SchoolAdmin role is new: migration for RoleAssignment seeding.
- Otherwise: zero‑data migration needed.

=== Test Plan ===

A. School Admin
   - Can access own school
   - Can see own school's dashboard
   - Cannot access another school's dashboard
   - Cannot access another school's students/staff/campus
   - Cannot bypass restriction through API parameters

B. Principal
   - Can access own school
   - Cannot access another school

C. Vice Principal
   - Can access own school
   - Cannot access another school

D. Campus scope
   - Can access authorized campus
   - Cannot access unrelated campus
   - Cannot use another campus ID to bypass authorization

D. Global administrator
   - Existing legitimate multi‑school access continues to work

=== Risks/Gaps ===

1. The `_institution_overview_counts` function is the primary leak point; fixing it requires ensuring `institution` is always set on the request for dashboard calls.

2. Existing principals/vice‑principals with no `primary_campus_id` already have school‑wide scope within their own school — the fix must not accidentally restrict this legitimate behavior.

3. Finance and exam endpoints may already have scoped querysets, but the initial `.objects.all()` before scoping is a risk if the scoping logic fails.

4. Adding a new Role enum value requires a database migration and RoleAssignment seeding — must not disrupt existing users.

5. Cross‑school data may also exist in non‑dashboard APIs (attendance, finance, exams); each must be verified.

=== STOP Conditions ===

Do NOT:
- Deploy
- Commit
- Push
- Run migrations (unless required for new Role enum)
- Modify production data
- Create production users
- Change production permissions

Do:
- Inspect the exact data‑leak paths identified
- Propose the minimal changes listed above
- Wait for owner approval before any source change

============================================================================
PREFLIGHT DELIVERABLE
============================================================================

PHASE_98_SCHOOL_SCOPE_PREFLIGHT.md

This single deliverable captures the full preflight analysis and must be
reviewed and approved by the owner before any implementation phase begins.

STOP: Do not modify source code, deploy, commit, or push until owner approval.