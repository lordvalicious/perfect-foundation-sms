# ARCHITECTURE.md

**Status:** Current + Target
**Owner:** Developer 1
**Date:** 2026-08-30

---

## 1. Architecture Goals

The system must hold one deployment that serves:

- The **Platform** (multi-tenant operator tooling: school onboarding, white-label, module toggles, platform analytics)
- Many **Organizations** (schools/colleges/universities) — currently one tenant type: `schools.School`
- Many **Campuses** per organization — `schools.Campus`
- **Academic Sessions** (`AcademicYear`, `Term`)
- **Users** with **Roles** (14 types) and granular **Permissions** (190+ codenames)
- All module **Data** (students, finance, HR, exams, …)

Target shape:

```
Platform
  └─ Organization (School)
       ├─ Campus
       │    ├─ AcademicUnit → Class → Section
       │    └─ Enrollment → Student
       ├─ AcademicYear → Term
       ├─ Users
       │    ├─ Institutional Membership
       │    ├─ RoleAssignment (Role per membership)
       │    └─ UserPermission / RolePermission (grant/deny)
       ├─ Modules (entitlement: enabled/disabled per school)
       ├─ White-label (branding/domains)
       └─ Data (finance, HR, exams, reports, …)
```

This prepares for: multi-organization, white-label SaaS, feature entitlements, and localization — **incrementally**, without rebuilding.

---

## 2. Current Architecture (as-is)

- **One-Django-project monolith**, mounted as one serverless app on Vercel.
- Middleware chain (in order, `config/settings/base.py:80-94`):
  1. `corsheaders`
  2. `SecurityMiddleware`
  3. `SessionMiddleware`
  4. `CommonMiddleware`
  5. `CsrfViewMiddleware`
  6. `AuthenticationMiddleware`
  7. `ActiveInstitutionMiddleware` (accounts) — resolves tenant
  8. `CampusAccessMiddleware` (accounts) — validates campus scope
  9. `ModuleAccessMiddleware` (schools) — entitlement gating
  10. `MessageMiddleware`, `XFrameOptionsMiddleware`
  11. `LoginAttemptAuditMiddleware` (audit)
- In production: `WhitenoiseMiddleware` prepended.

**Tenancy resolution (ActiveInstitutionMiddleware):**
1. Host header → white-label `custom_domain` / subdomain
2. Session key `active_institution_id`
3. First active membership

**Isolation model:** per-view opt-in scoping via `apply_campus_scope(queryset, request)` (accounts/access.py:274) and `restrict_to_allowed_campuses`. Roots:
- `super_admin` | `admin` | `academic` → GLOBAL (all campuses)
- Everyone else → own campuses (profile + assignments/enrollments)
- NULL campus/institution records → visible to all in-scope (documented leakage)

**AuthN:** session only; `EmailOrUsernameBackend`; CSRF via readable cookie; optional TOTP + backup codes; Google SSO (pre-existing account).

**AuthZ:** three parallel systems coexist:
1. **Legacy role-list permission classes** (`permissions.py`) — `IsAdminRole`, `IsAccountantRole`, `IsTeacherRole`, `IsLibrarianRole` (broken: references non-existent role `librarian`), etc.
2. **Granular codename system** (`permissions_new.py`, `Permission`/`RolePermission`/`UserPermission`) — **not seeded**, so grants nothing until runtime-configured; RBAC management endpoints gate on legacy roles only.
3. **Middleware gating** — module entitlement (URL-prefix based) + campus + login audit.

**Data model spine:**
- `School` → `Campus` (CASCADE) → `AcademicUnit` → `Class` → `Section`
- `School` → `AcademicYear` (unique per school) → `Term`
- `School` → `InstitutionMembership` → `User` + `RoleAssignment`
- `User` → `StaffProfile` / `Teacher` / `Student` / guardian relations
- Multi-tenant FKs (`institution` / `school_id`) retrofit onto most tables.

---

## 3. Gaps Between Current and Target

| Gap | Current | Target | Priority |
|---|---|---|---|
| Tenant scoping not centralized | Mixins/managers unused; views must call scope helpers | Managers (or enforced mixin + query machinery) that guarantee scoping on every model by default | **Critical** |
| Multi-organization | Only `School` tenant; assumes 1 org per deployment | Generic `Organization` model (or rename/alias `School`), Campus under it | High (contract-friendly, additive) |
| White-label | `white_label` app exists (`WhiteLabelBranding`, `DomainMapping`); host resolution works | Formalize SaaS tenant plan (per-org branding, domains, module toggles) | Medium |
| Feature entitlements | `ModuleAccessMiddleware` + `enabled_modules` JSON | Tie entitlements to plans; audit usage | Medium |
| Localization | `USE_I18N=True`, no translations | `LANGUAGE_CODE` configurable per tenant | Low |
| RBAC coherence | Two parallel gates; librarian dead role; admin/unpriv users bypass | Single source of truth for role→permission mapping; seed defaults; keep superuser bypass explicit | **Critical** |
| Background jobs | Vercel crons hitting endpoints | Task queue w/ durability (Celery/Beat or similar) if VPS; keep crons serverless | Medium |
| Observability | Console logging only | Structured logging; APM/traces; error tracking | Medium |
| CI/CD | None | GitHub Actions: lint + test + migrate-check on PR; deploy on main | High |

---

## 4. Recommended Architecture Principles (for future work)

1. **Do not rebuild.** Keep the current Django+DRF+React structure. 
2. **Add a default tenant-proof manager layer** progressively: introduce default `objects` on key tenant tables that always inject `institution` (via request/thread-local when available) — behind a feature flag, one app/module at a time.
3. **Enforce isolation centrally**, keep per-view helpers as defense-in-depth.
4. **Consolidate AuthZ**: keep legacy role helpers as compatibility wrappers over the granular codename system; seed a default role→permission matrix at institution-provisioning.
5. **Superuser bypass stays** (documented admin behavior) but is not a substitute for per-view scoping.
6. **All new models** must use shared abstract mixins (fix `TimeStampedMixin`, `CampusScopedMixin`, `InstitutionScopedMixin`, `AuditableMixin`, `SoftDeleteMixin`) — stop hand-rolling timestamps/soft-delete.
7. **Migrations** must be additive; never destructive on production data without approval.

---

## 5. Incremental Rollout Path

1. **Phase A (stability/security):** fix critical bugs and security blockers (see RISK_REGISTER) — no schema changes.
2. **Phase B (data-integrity foundation):** normalize timestamps/soft-delete/timestamps on core apps; wire managers on the most sensitive tables first (finance, students, accounts, schools).
3. **Phase C (RBAC consolidation):** seed role→permission matrix; fix dead roles; align permission-management endpoints to codenames.
4. **Phase D (SaaS readiness):** contract for multi-organization, entitlement tiers, white-label per-org, localization.
5. **Phase E (delivery):** CI/CD, tests on the 12 untested apps (start with reports/finance core), observability, deploy-target consistency.

Each phase is additive and reversible via migrations; no production data is deleted or reset.