# White-Label Multi-Tenant Conversion Plan

## Architecture Decision

- **Tenant resolution**: Shared domain + session (existing `ActiveInstitutionMiddleware`)
- **Data isolation**: Shared PostgreSQL DB, every model gets `institution_id` FK column
- **Enforcement**: Django middleware + model manager + access helpers

## Current State (Problems to Fix)

### Models WITHOUT institution scoping (must add `institution_id`):
- `Subject` — global unique `code`
- `FeeCategory` — global unique `name`
- `GradeScale` / `GradeBand` — global unique `name`, single `is_default`
- `Period` — global unique `number`
- `Supplier` / `AssetCategory` — completely global
- `Guardian` — global (shared across tenants)
- `MessageTemplate` — global
- `Message` — no tenant scope
- `Announcement` — no School FK (leaks cross-tenant)
- `Book` / `Asset` / `Vehicle` / `Driver` / `Route` — nullable campus, no school FK

### Globally-unique identifiers that must become per-tenant:
- `admission_number` → unique (institution, admission_number)
- `invoice_number` → unique (institution, invoice_number)
- `receipt_number` → unique (institution, receipt_number)
- `employee_number` → unique (institution, employee_number)
- `isbn` → unique (institution, isbn) [library]
- `plate_number` → unique (institution, plate_number) [transport]
- `Subject.code` → unique (institution, code)

### Access control gaps:
- `campus_access()` never checks `request.institution`
- Many views use `apply_campus_scope()` which only filters by campus, not institution
- `Announcement.target_user_ids()` leaks cross-tenant
- `StaffAttendance`/`StaffLeave` have no `apply_campus_scope`

## Implementation Phases

### Phase 1: Tenant Infrastructure (Foundation)
**Goal**: Add `institution_id` to every model, create tenant middleware enforcement

1. **Create `TenantManager` base class** (`backend/apps/accounts/managers.py`)
   - Auto-filters queryset by `request.institution`
   - Applied globally via `Meta.manager_inheritance_from_factory`

2. **Create `TenantModelMixin`** (`backend/apps/accounts/models.py`)
   - Adds `institution` FK (nullable for migration safety, non-nullable after data migration)
   - Validates institution matches user's active institution

3. **Add `institution` FK to every model** missing it (migration per app):
   - schools: `Subject`, `SubjectOffering`
   - students: `Guardian`, `StudentGuardian`
   - finance: `FeeCategory`, `Invoice`, `Payment`
   - library: `Book`, `BookCopy`, `BookIssue`
   - inventory: `AssetCategory`, `Supplier`, `Asset`
   - transport: `Vehicle`, `Driver`, `Route`
   - communication: `Message`, `Announcement`, `MessageTemplate`
   - reportcards: `GradeScale`, `GradeBand`
   - timetable: `Period`
   - audit: `AuditLog`

4. **Create data migration to populate `institution_id`** for existing records
   - Derive from campus→school relationships where possible
   - Default to primary institution for orphaned records

5. **Make unique constraints per-tenant**:
   - `admission_number`, `invoice_number`, `receipt_number`, `employee_number`, `isbn`, `plate_number`, `Subject.code`
   - Change from `unique=True` to `unique_together = ("institution", "field")`

### Phase 2: Middleware & Access Control Enforcement
**Goal**: Every query is automatically scoped to the active institution

1. **Upgrade `ActiveInstitutionMiddleware`**
   - After setting `request.institution`, set thread-local for ORM access
   - Reject requests if user has no membership

2. **Upgrade `access.py`**
   - `campus_access()` → also check `request.institution`
   - `user_allowed_campus_ids()` → scope to `request.institution`
   - Add `institution_queryset(qs)` helper that auto-filters by `request.institution`

3. **Add `TenantQuerySet` to all models**
   - Every model's default manager filters by institution
   - Override `get_queryset()` in views (or rely on manager)

4. **Fix cross-tenant leaks**:
   - `Announcement.target_user_ids()` → add institution filter
   - `StaffAttendance`/`StaffLeave` → add `apply_campus_scope`
   - Audit log queries → filter by institution

5. **Per-tenant seed data isolation**
   - `GradeScale` defaults → per-tenant
   - `Period` definitions → per-tenant
   - Subject catalog → per-tenant

### Phase 3: Tenant Management UI
**Goal**: Super-admin can create/manage tenants, users can switch institutions

1. **Tenant Admin Panel** (new `backend/apps/tenants/` app)
   - `Tenant` model (extends `School` with status, plan, config)
   - CRUD for creating new school tenants
   - Tenant provisioning: seed default data (campus, classes, grade scale, periods, etc.)

2. **Institution Switch UI** (frontend)
   - Dropdown in header to switch between institutions (for users with multiple memberships)
   - Visual indicator of active institution (branded header)

3. **Tenant Onboarding Wizard**
   - Step 1: Create school + admin user
   - Step 2: Add campuses
   - Step 3: Configure branding
   - Step 4: Import/seed initial data

### Phase 4: Per-Tenant Configuration
**Goal**: Each tenant can customize all reference data

1. **Tenant Settings Model** (extends `SchoolSettings`)
   - Timezone, language, date format
   - Grading system, passing marks
   - SMS provider config (per-tenant Twilio credentials)
   - Email template customization

2. **Per-Tenant Reference Data**
   - Subjects are per-tenant (can add custom subjects)
   - Fee categories are per-tenant
   - Grade scales are per-tenant
   - Period/bell schedules are per-tenant

3. **Per-Tenant Branding** (enhance existing)
   - Already have: logo, colors, motto, contact info
   - Add: custom domain, login page branding, email templates

### Phase 5: Deployment & Operations
**Goal**: Production-ready white-label deployment

1. **Tenant Resolution** (for future subdomain support)
   - Middleware to detect tenant from subdomain
   - Fallback to session-based selection

2. **Tenant-Aware Admin**
   - Django admin shows only current tenant data
   - Super-admin can impersonate any tenant

3. **Billing & Plans** (optional future)
   - Free tier, Pro tier, Enterprise
   - Feature flags per tenant
   - Usage tracking per tenant

## File Changes Summary

### New Files
- `backend/apps/accounts/managers.py` — TenantManager
- `backend/apps/tenants/` — entire new app (models, views, serializers, urls)
- `backend/apps/accounts/tenant_middleware.py` — enhanced middleware

### Modified Files (Phase 1-2)
- Every `models.py` — add institution FK
- Every `views.py` — ensure institution scoping
- `backend/apps/accounts/access.py` — add institution checks
- `backend/apps/accounts/middleware.py` — enhance
- `backend/apps/accounts/models.py` — TenantModelMixin
- `backend/config/settings/base.py` — add tenants app
- `backend/config/urls.py` — add tenant routes
- Frontend `App.jsx` — institution switcher UI
- Frontend `auth.jsx` — institution state management

## Migration Strategy
1. Add `institution` FK as nullable to all models
2. Run data migration to populate existing records
3. Make `institution` non-nullable
4. Add unique_together constraints
5. Deploy with both old and new code paths during transition
