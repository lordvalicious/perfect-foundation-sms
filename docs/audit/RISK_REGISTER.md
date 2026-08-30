# RISK_REGISTER.md

**Date:** 2026-08-30
**Owner:** Developer 1
**Scale:** Critical / High / Medium / Low. Likelihood × Impact.

---

## Critical

| ID | Risk | Evidence | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | **Hardcoded superadmin creds in VCS + forced password reset on every migrate** | accounts/migrations/0014_create_frostfire_superadmin.py:12-31 (`FrostFire`/`ra2a1s345`) | Full platform takeover; any env redeploy re-injects known creds | Remove the migration; rotate password; add a secure bootstrap (env/secret) + stage-0 doc; revoke + recreate superadmin with random password |
| R-02 | **Unauthenticated schema-mutation endpoint** | config/urls.py:16 → `core.views.run_migrations_view` | Anyone can run migrations on the API → data loss/definition tamper | Gate behind auth + admin/CRON secret; disable in prod unless explicitly used |
| R-03 | **Tenant/campus isolation is opt-in, not guaranteed** | core scoping mixins & managers unused; `_model_has_path` silently skips models without FK | Cross-tenant/campus data exposure wherever a view forgets to scope | Phase-B default tenant/campus manager; enforce in new models; audit each view's queryset for scope |
| R-04 | **`CampusAccessMiddleware` NameError** | campus_middleware.py:66 `int(campus_id)` (undefined) | 500s on `?campus=` requests; middleware-level campus enforcement effectively dead | Fix to `int(campus_param)`; add middleware unit test |

## High

| ID | Risk | Evidence | Impact | Mitigation |
|---|---|---|---|---|
| R-05 | Committed secrets/artifacts at root (`/.env.production` w/ live `VERCEL_OIDC_TOKEN`, `cookie.txt`, `Neon Console.html`, dump files) | repo root | Credential exposure if repo is ever shared/leaked | Purge from history, rotate token, add `.gitignore`, secret scan in CI |
| R-06 | No object-level authorization; `has_permission` only | accounts/permissions.py & views across apps | IDOR risk on detail/update endpoints | Add object-scope helper + tests for detail views; prefer scoped querysets |
| R-07 | Two parallel RBAC gates; dead `librarian` role; permission mgmt endpoints gate on legacy role lists not codenames | accounts/permissions.py:153; views.py:1314-1516 | Confused privilege state; misconfiguration | Unify on codename matrix; seed defaults; kill dead role |
| R-08 | Login lockout bypassable by direct API (bad-password not recorded in login view) | accounts/views.py:136 vs 215-243 | Brute-force on login | Record failed attempts inside LoginView; keep LoginFailedView as belt+braces |
| R-09 | `accounts/0009_populate_institution_ids` giant cross-app backfill + `0014` referencing nonexistent `is_active` on School | DB-1 | Corrupt/partial backfills; fresh-DB crashes | Freeze these migrations; don't rerun; add guards; document irreversible nature |
| R-10 | Duplicate `SubjectOffering` classes; dup `SchoolSettings` (2 apps) | schools/models.py:364/699; schools:435 vs white_label:418 | Wrong model resolved in some import paths | Consolidate; deprecate one; add model resolution test |
| R-11 | No CI/CD, no test coverage in 12 apps | module inventory | Regressions ship silently; security bugs not caught | Add GH Actions (lint, test, migrate-check, secret scan) |

## Medium

| ID | Risk | Evidence | Impact | Mitigation |
|---|---|---|---|---|
| R-12 | Timestamp/soft-delete inconsistency (26 models lack both timestamps; soft-delete only on ~30 models) | DATABASE_AUDIT §3-4 | Audit/governance gaps; data lifecycle ambiguity | Adopt shared mixins in all new models; migrate existing incrementally |
| R-13 | CASCADE on 204 FKs in multi-tenant DB | DATABASE_AUDIT §5 | Accidental cascade deletion on tenant delete | Enforce PROTECT for critical FKs w/ explicit archive-then-delete flows |
| R-14 | Report endpoints heavy + Python-loop aggregations | staff_views.py:129-156; 167 routes | Slow lists, Vercel timeouts, N+1 | Optimize with annotations/select_related; perf workstream |
| R-15 | FileBasedCache in serverless; crons without queue; no APM | PERFORMANCE_AUDIT §2 | Unreliable throttling/cache; silent cron drops | Redis-backed cache; observability; cron → job queue when needed |
| R-16 | Global pagination 20; no code splitting; chatter API | PERFORMANCE_AUDIT §2.1-2.2 | Poor UX at scale | Route-split Vite; per-view pagination tuning; central data layer |
| R-17 | Multi-org not modeled; only `School` tenant | ARCHITECTURE §3 | Re-architecture needed later | Keep additive; plan `Organization` alias migration |
| R-18 | Lockout/TOTP plaintext secrets at rest; SSO unthrottled | SECURITY_AUDIT §1 | 2FA weaknesses | Encrypt TOTP seed; salted/hmac backup codes; throttle SSO |
| R-19 | `CSRF_TRUSTED_ORIGINS` triple-assigned in production.py | production.py:39-63 | Host changes need multiple edits → misconfig | Single-source constant |

## Low

| ID | Risk | Evidence | Impact | Mitigation |
|---|---|---|---|---|
| R-20 | No `Section` unique constraint | schools/models.py:223 | Duplicate section names | Add UniqueConstraint migration |
| R-21 | Hand-rolled polymorphic FKs (workflow) no referential integrity | workflow/models.py:107-108 | Orphan references | Hard FK or soft-verify on type |
| R-22 | `TenantHostMiddleware` dead code + subdomain bug | domain_middleware.py:9,39 | Confusion | Delete or fix + enable |
| R-23 | `IsLibrarianRole` dead (role string not a choice) | permissions.py:153 | Librarian module permission silently off | Fix role name or alias |
| R-24 | Empty `exams/admin.py` | exams/admin.py (0 bytes) | Maintenance confusion | Fill or delete |
| R-25 | Localization not per-tenant | base.py:173 | Future SaaS pain | Make configurable per School |

---

## Blocked Items (status)

- **Cannot verify Django check / migrate against production** — read-only mandate (needed: a scratch/staging clone + psql view to validate `0009`/`0014` state and column lists).
- **Cannot run query-plan profiling** without prod DB read rights.
- **Cannot run the test suite** without local DB (local Postgres is down).

---

## Next Phase Recommendation

Execute in order:
1. **Immediate (R-01, R-02, R-04, R-05):** security blockers — no schema impact, reversible.
2. **Phase B (R-03, R-06, R-12, R-13):** tenant/scoping + integrity foundation.
3. **Phase C (R-07, R-08, R-18):** RBAC/2FA hardening.
4. **Phase D (R-09, R-10, R-17, R-20, R-21):** schema hygiene + multi-org prep.
5. **Phase E (R-11, R-14, R-15, R-16):** delivery/performance.
Details in IMPLEMENTATION_ROADMAP.md.