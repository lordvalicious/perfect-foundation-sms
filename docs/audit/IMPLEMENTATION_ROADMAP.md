# IMPLEMENTATION_ROADMAP.md

**Date:** 2026-08-30
**Owner:** Developer 1

Safest implementation sequence after audit. Each item is **additive, reversible, no production data deletion/reset**. No mock data. Every DB change = safe migration with a plan.

---

## Phase 0 — Immediate Security Blockers (no schema change)

| Order | Task | Ref | Effort |
|---|---|---|---|
| 0.1 | Remove/hard-gate `POST /api/admin/run-migrations/` (require auth + admin role + CRON secret; or remove) | R-02 | S |
| 0.2 | Remove `accounts/0014_create_frostfire_superadmin.py` migration content; create a **bootstrap process** via env-driven management command (random password from secret, never committed); rotate the current superadmin password off `ra2a1s345` | R-01 | S |
| 0.3 | Purge committed secrets/artifacts (`/.env.production`, `cookie.txt`, `Neon Console.html`, dumps); rotate `VERCEL_OIDC_TOKEN`; add `.gitignore` entries; scrub history | R-05 | M |
| 0.4 | Fix `campus_middleware.py:66` (`int(campus_param)`); add middleware unit test | R-04 | S |
| 0.5 | Eliminate triple `CSRF_TRUSTED_ORIGINS` assignment in production.py → single source | R-19 | S |

**Exit criteria:** security blockers closed; test for superadmin bootstrapping documented.

---

## Phase 1 — Tenant Scoping & Integrity Foundation

| Order | Task | Ref | Effort |
|---|---|---|---|
| 1.1 | Wire `TenantManager`/`CampusScopedManager` (or equivalent) as default `objects` on the most sensitive tables first (finance, students, accounts memberships, hr) — behind explicit opt-in, never silently | R-03 | M/L |
| 1.2 | Stand up a **prototype psql/staging clone** to validate `0009`/`0014` migration state and current column list (unblocks audit verification) | R-09 | M |
| 1.3 | Add object-level scoping guard + a test that asserts every detail/update view scopes its queryset | R-06 | M |
| 1.4 | Adopt `TimeStampedMixin`/`CampusScopedMixin`/`InstitutionScopedMixin`/`AuditableMixin` in **new models**; begin incremental migration of hand-rolled timestamps on core apps (schools, finance, students) | R-12 | L |
| 1.5 | Hardening session/lockout: record failed logins inside `LoginView` | R-08 | S/M |
| 1.6 | Review top CASCADE FKs → PROTECT chips at tenant boundary | R-13 | M |

**Exit criteria:** every module passes an automated cross-campus IDOR smoke test.

---

## Phase 2 — RBAC / AuthZ Consolidation

| Order | Task | Ref | Effort |
|---|---|---|---|
| 2.1 | Seed default role→permission matrix at institution provisioning; document `permission.assign` usage | R-07 | M |
| 2.2 | Fix dead roles (`librarian`), align permission-management endpoints to codenames | R-07 | M |
| 2.3 | 2FA: encrypt TOTP seed at rest; salted backup codes; throttle Google SSO + FBV dashboard/portal | R-18 | M/L |
| 2.4 | Re-check `UserProfileView` data exposure; tighten to self + role-required fields | SECURITY §3 | S |

**Exit criteria:** role→permission matrix coverage test passes per role; no role grants across institutions.

---

## Phase 3 — Schema Hygiene & Multi-Org Prep (additive)

| Order | Task | Ref | Effort |
|---|---|---|---|
| 3.1 | Resolve duplicate `SubjectOffering` (keep one, add deprecation) and duplicate `SchoolSettings` | R-10 | M |
| 3.2 | Add `Section` unique constraint (safe migration; dedupe check first) | R-20 | S |
| 3.3 | Add FK/validation hardening for `workflow` polymorphic refs | R-21 | M |
| 3.4 | Plan `Organization` alias (rename-safe, additive FK/migration) for multi-org SaaS | R-17 | L |
| 3.5 | Per-tenant timezone/currency/locale already partly present (School.timezone/currency) — formalize | R-25 | S |
| 3.6 | Delete dead `TenantHostMiddleware`, fill or remove empty `exams/admin.py` | R-22, R-24 | S |

**Exit criteria:** no duplicate model definitions; all tenant tables carry institution/campus keys + timestamps.

---

## Phase 4 — Delivery, Performance, Observability

| Order | Task | Ref | Effort |
|---|---|---|---|
| 4.1 | GitHub Actions CI: lint + `python -m compileall` + unit tests + migration check + secret scan; deploy on main | R-11 | M |
| 4.2 | Perf pass: `.select_related`/annotation optimization on hot report/dashboard/student-profile endpoints; query-count guard | R-14 | L |
| 4.3 | Redis-backed cache; re-enable `django_ratelimit`; retention policy for audit/notification logs | R-15 | M |
| 4.4 | Vite route-based code splitting; pagination tuning per endpoint | R-16 | M |
| 4.5 | App-level observability (Sentry/New Relic); reconcile deploy docs (Vercel backend vs Render) | R-15 | M |

**Exit criteria:** CI green; baseline perf report; deploy docs singular.

---

## Testing Discipline

- Every schema migration ships with a **migration-check step** and a **rollback plan**.
- New tests required on: `reports` (aggregation accuracy), `finance` (double-entry), `students` (profile deep fetch), middleware (campus param), RBAC matrix.
- Do not delete/mutate production data. Use staging clone for any destructive validation.

---

## Recommended Immediate Next Phase

**Phase 0** (security blockers) → then **Phase 1.1–1.3** (tenant scoping + IDOR guards). Both are safe, testable, non-destructive. Full implementation deferred until this roadmap is approved.