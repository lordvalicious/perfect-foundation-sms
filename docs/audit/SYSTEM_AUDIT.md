# SYSTEM_AUDIT.md

**System:** Perfect Foundation SMS (School ERP)
**Auditor Role:** Developer 1 (Core Architecture, Backend, Database, Security, APIs, Infrastructure, DevOps)
**Date:** 2026-08-30
**Branch:** R
**Scope:** Read-only audit. No production data modified, no database reset, no mock data created.

---

## 1. Executive Summary

The system is a mature, single-deploy Django 6.1 backend exposing a large DRF REST API to a React 19 SPA, deployed on Vercel (frontend + backend) with a Neon PostgreSQL database. It covers ~33 backend apps and ~45 frontend pages spanning SIS, finance, HR, payroll, exams, reports, LMS, library, transport, inventory, and platform/white-label tooling.

The architecture is **single-codebase, multi-tenant** (one Django project serving the platform and all schools). Tenant isolation is handled by per-view queryset scoping plus 3 middleware layers, NOT by centralized model managers. This is the single most important architectural risk: **isolation correctness depends on per-view discipline.**

### Health grades

| Area | Grade | Rationale |
|---|---|---|
| Feature breadth | A- | 33 apps, 167+ report routes, deep verticals |
| Multi-tenant isolation | C- | Ad-hoc scoping, unused scoping mixins/managers, known NULL-passthrough |
| Security | D+ | Hardcoded superadmin creds, insecure secret default, unauthenticated runtime migration endpoint |
| Authentication UX | B+ | Session+CSRF works; lockout is frontend-coordinated (bypassable) |
| Data integrity | B- | Soft-delete inconsistent, timestamps inconsistent, CASCADE-heavy |
| Performance | C+ | File-based cache, no DB-layer caching, no profiling baseline, heavyweight report views |
| Testing | D+ | 12/33 apps have zero tests; no CI pipeline |
| DevOps | C | Deploy targets inconsistent (Vercel backend vs docs' Render); no CI/CD; env hygiene issues |
| Maintainability | C | Multiple 1300+ line files, codebase still evolving rapidly |

---

## 2. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Backend framework | Django | 6.1 |
| API | Django REST Framework | 3.18.0 |
| Database driver | psycopg (v3) | 3.3.4 |
| Backend deploy | Vercel (Python serverless) | — |
| Alternative backend | Docker + Gunicorn (Render/VPS docs) | — |
| Database | Neon PostgreSQL | — |
| Frontend framework | React | 19.2.8 |
| Router | react-router-dom | 7.x |
| HTTP client | Native `fetch` (`apiFetch` in `src/api.js`) | — |
| State management | React Context (`AuthProvider`, `LanguageProvider`) | — |
| Charts | recharts | 3.x |
| Icons | lucide-react | 1.30.0 |
| Build | Vite | 8.2.0 |
| Background jobs | Vercel Cron endpoints (5 crons) | — |
| SMS | Twilio | 9.4.5 |
| Payments | Stripe (online) + JazzCash/Easypaisa (PK, env-only so far) | 11.3.0 |
| 2FA | pyotp + backup codes (unsalted SHA-256) | 2.10.0 |
| PDF | reportlab | 5.0.0 |
| Static | WhiteNoise (compressed manifest) | 6.9.0 |

---

## 3. Repository Layout (top-level)

- `backend/` — Django project (`config/` = Django project config; `apps/` = 33 apps)
- `frontend/` — React SPA (Vite)
- `docs/` — Engineering docs (deployment, white-label, audit)
- `vercel.json` (root, mirrors `backend/vercel.json`) — backend build/routing/crons
- `frontend/vercel.json` — frontend build + `/api` proxy to `perfect-foundation-api.vercel.app`
- `render.yaml` — alternative Render Blueprint (backend, Docker)
- `docker-compose.yml` — local Postgres 17
- `.env.production`, `Neon Console.html`, `cookie.txt`, many `*.bat`, `debug_room*.py`, `seed_*.py`, numbered files (e.g. `589`, `1010`…) — **repository hygiene issues** (see Risk Register R-13).

---

## 4. Backend Structure

- **Settings:** `config/settings/` → `base.py` + `production.py`. `DEBUG=False` everywhere; production hard-fails on missing `DJANGO_SECRET_KEY`.
- **Apps (33):** accounts, alumni, attendance, audit, communication, core, dashboard, digital_ids, discipline, documents, events, exams, finance, health, helpdesk, homework, hostel, hr, inventory, library, lms, payroll, portal, reportcards, reports, schools, search, students, teachers, timetable, transport, visitors, white_label, workflow.
- **Routing:** `config/urls.py` mounts 30+ `/api/<app>/` prefixes; protected media via `ProtectedMediaView`.
- **View style:** predominantly DRF `APIView`/`generics` CBVs; only `schools` uses ViewSets; `core`/`dashboard`/`portal` use function-based `@api_view`.
- **Background jobs:** Vercel cron → authenticated-by-`CRON_SECRET` endpoints (late-fees, email-weekly, absence-alerts, fee-reminders, process-notifications).

---

## 5. Frontend Structure

- `src/api.js` — `apiFetch()` wrapper, `credentials: "include"`, CSRF from cookie, relative `/api/...` paths.
- `src/auth.jsx` — auth flow (csrf → login → me → OTP).
- `src/App.jsx` — 52 routes, client-side `RequireRoles` guards; public routes: `/login`, `/apply`.
- `src/pages/` ~59 files; `src/components/` ~10 shared components.
- No dedicated UI kit, no dedicated state/store library (Context only).

---

## 6. Authentication Summary

- **Session-based only** (`SessionAuthentication`), CSRF cookie must be readable by JS (`CSRF_COOKIE_HTTPONLY=False`).
- Custom `User(AbstractUser)` with roles stored per-institution via `InstitutionMembership` → `RoleAssignment`.
- 14 Role types; 190+ Permission codenames; per-role and per-user (allow/deny) permission tables.
- Google SSO present (`google_sso.py`), account must pre-exist.
- **Gaps:** lockout depends on a separate `LoginFailedView` call rather than the login view itself; 2FA TOTP seed stored plaintext; backup codes unsalted SHA-256; hardcoded superadmin credentials in migration `accounts/0014`.

---

## 7. Multi-tenancy Summary

- Tenant = `schools.School` (docstring: "kept as School for API compatibility"). Sub-tenant = `schools.Campus`.
- Resolution: `ActiveInstitutionMiddleware` (host/domain → session → first membership).
- Enforcement: `CampusAccessMiddleware` + per-view `apply_campus_scope()` / `restrict_to_allowed_campuses()`.
- **Gap:** centralized `TenantManager` / `CampusScopedManager` exist in `accounts/managers.py` but are **not wired to any model**; scoping mixins (`InstitutionScopedMixin`, `CampusScopedMixin`, `TimeStampedMixin`, `AuditableMixin`) exist in `core/models.py` but **only `SoftDeleteMixin` is actually used**.
- **Gap:** records with NULL `campus`/`institution` are visible to everyone in scope (by design, documented in `access.py`, but a known cross-campus leak vector).
- **Gap:** `CampusAccessMiddleware` line 66 references undefined variable `campus_id` → 500 on any `?campus=` request (or worse, silent misbehavior).

---

## 8. Database Summary

- 182 model classes across 31 apps; 138 migration files.
- UniqueConstraints used well (~50+), no `unique_together` (modernized).
- on_delete: CASCADE 204 / PROTECT 149 / SET_NULL 170.
- JSONField used 40+ times; no ContentType/generic FK; one hand-rolled polymorphic pattern in `workflow`.
- Retrofit tenancy visible in migration history (many `add_institution_to_all_models` + a giant cross-app backfill `accounts/0009_populate_institution_ids`).

---

## 9. Deployment Summary

- **Live:** Frontend `perfect-foundation-sms.vercel.app`; Backend `perfect-foundation-api.vercel.app` (Vercel serverless, root/backend vercel.json identical).
- **Documented alternative:** Render `*.onrender.com` Docker + VPS/nginx path in `docs/`.
- Build command runs `migrate --noinput && collectstatic --noinput`.
- **No CI/CD** (no `.github/workflows`).
- **Env hygiene:** `/.env.production` contains a live `VERCEL_OIDC_TOKEN` in plaintext (R-13); hardcoded fallback secrets in `base.py` (R-02/R-03).

---

## 10. Existing Integrations

| Integration | Status |
|---|---|
| Twilio SMS | Config present, keys via env (possibly unused) |
| Stripe | Config + webhook secret env (payment endpoints exist in `finance`) |
| JazzCash / Easypaisa | Env template only (`*_ENV`), no live merchant keys |
| Google SSO | `GOOGLE_CLIENT_ID` env, account-pre-exist flow |
| Attendance/GPS devices | `ATTENDANCE_DEVICE_KEYS`, `GPS_DEVICE_KEYS` env only |
| Email | Console backend (default) → SMTP in production |

---

## 11. Technical Debt (headline list)

1. Multi-tenant scoping is per-view discipline, not enforced by managers/mixins.
2. Unknown-variable bug in `CampusAccessMiddleware` (campus_middleware.py:66).
3. Hardcoded superadmin credentials + forced re-set in migration `0014`.
4. Unauthenticated `POST /api/admin/run-migrations/` endpoint (config/urls.py:16 → `core.views.run_migrations_view`).
5. Duplicate class definitions: `SubjectOffering` (schools/models.py:364 & 699), `SchoolSettings` (schools + white_label apps).
6. Timestamp/soft-delete inconsistency across 182 models.
7. `TenantHostMiddleware` is dead code (not in MIDDLEWARE) and has a subdomain parsing bug.
8. Very large files (finance/models 1441, finance/views 1789, students/models 1682, hr/models 1710, reports/views 1534 + extended 1165).
9. Zero-test apps: alumni, audit, discipline, documents, health, homework, hostel, lms, payroll, reports, search, transport.
10. No CI pipeline; deploy target docs out of sync with live target.
11. `django_ratelimit` and `RatelimitMiddleware` disabled (commented out) pending Redis.
12. Repository hygiene: committed `.env.production` (with OIDC token), `cookie.txt`, debug scripts, dump files at root.