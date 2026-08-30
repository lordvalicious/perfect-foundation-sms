# DEVELOPER_2_INTEGRATION_CONTRACT.md

**Date:** 2026-08-30
**Owner:** Developer 1 (author), consumed by Developer 2.

This document tells Developer 2 **exactly what backend surface they may safely consume** while Developer 1 stabilizes core architecture.

---

## 1. Rules of the Road

- **API-first.** Developer 2 integrates through existing endpoints + serializers. Do not add migrations/columns.
- **Even if Developer 2 owns a module's UX**, schema changes proposal goes through Developer 1. Always propose a migration; never hand-write DB DDL.
- **Do not bypass scoping helpers.** Always pass the resolved `request`/`institution`/`campus` through — no `Model.objects.all()` from views without scope.
- **Never call `all_tenants()`/`all_campuses()`/`for_campus()`/`for_institution()`** in feature code (these are reserved bypass tools).
- **Read-only consumption is safest.** For writes, use the module's existing view endpoints; do not write raw ORM updates in frontend-facing code unless inside the module's own views.

---

## 2. SAFE to Consume (stable API today)

| Prefix | Notes |
|---|---|
| `/api/auth/*` | csrf, login, logout, me, password, 2FA (stable) |
| `/api/students/*` | students, guardians, enrollments, admissions (56 routes) |
| `/api/teachers/*` | teachers + assignments |
| `/api/attendance/*` | attendance + corrections |
| `/api/exams/*`, `/api/report-cards/*` | exams, results, report cards |
| `/api/finance/*` | fees, invoices, payments, accounting (64 routes) |
| `/api/hr/*`, `/api/payroll/*` | HR + payroll (read/write via existing views) |
| `/api/reports/*` | **167 report endpoints — read-only.** Consume, do not alter schema/columns for reports without sign-off. |
| `/api/events/*`, `/api/communication/*`, `/api/library/*`, `/api/transport/*`, `/api/inventory/*`, `/api/hostel/*`, `/api/lms/*`, `/api/homework/*`, `/api/discipline/*`, `/api/health-records/*`, `/api/alumni/*`, `/api/digital-ids/*`, `/api/helpdesk/*`, `/api/visitors/*`, `/api/workflow/*`, `/api/white-label/*` | module APIs (stable surface) |
| `/api/dashboard/*`, `/api/search/*`, `/api/portal/*`, `/api/documents/*` | aggregation APIs (no tables behind them) |

## 3. Backend invariants Developer 2 must respect

1. **Auth:** session cookie + CSRF (`X-CSRFToken`). No tokens/JWT. Carry `credentials: "include"`.
2. **Tenancy:** always send/resolve the active institution; data is scoped server-side. Do not trust client campus values for reads — send only the user's own context.
3. **Roles:** use existing role gates. **Do not write `is_superuser` shortcuts** into module features — that's a global bypass (Developer 1 reserved).
4. **Soft delete:** models with `deleted_at` — never hard-delete in views; use the soft-delete path.
5. **Pagination:** DRF default page size 20; filter lists with `?search=`, `?campus=`; don't page through hundreds of client requests.

## 4. Known landmines (avoid these right now)

| Landmine | Explanation | Workaround |
|---|---|---|
| `?campus=` query param can 500 today | middleware bug R-04 (fixing) | Until fixed, prefer `?campus_id=` or rely on server default campus; avoid `?campus=` in new frontend code |
| NULL-campus records are "school-wide" | visible to all in-scope campuses | Do not rely on NULL campus for access decisions |
| RBAC granular matrix unseeded | grants nothing until configured | Use legacy role classes (`IsAdminRole`, etc.) — they're the effective gate today |
| `librarian` role string broken | not a valid Role choice | Use `staff`+scope instead |
| reports endpoints heavy | slow on large data sets | Paginate + server-side search; no client-side full-list walks |

## 5. Change-request path (to Developer 1)

Any of these requires a Developer-1 review ticket: new DB column/table, changing a permission class used by another module, renaming an endpoint, changing tenant/campus serialization, adding to `report_definitions` datasets, changing `enabled_modules` behavior, or touching `config/settings`.

---

## 6. Definition of Done (integration)

- Works against the **deployed** API (or local via `vite.config.js` proxy -> Django :8000).
- No new migration without Developer 1 sign-off.
- No hard delete without soft-delete pattern.
- Passes the module's own tests (even if currently only smoke).
- Keeps `?campus=`/NULL-campus workarounds flagged in the PR description.