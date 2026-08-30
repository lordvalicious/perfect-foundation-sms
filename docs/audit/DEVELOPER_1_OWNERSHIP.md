# DEVELOPER_1_OWNERSHIP.md

**Role:** Developer 1 — Core Architecture, Backend, Database, Security, Authentication, Authorization, Multi-campus isolation, APIs, Infrastructure, DevOps, Performance, Data integrity.
**Date:** 2026-08-30

Developer 2 owns ERP modules, frontend, portals, and operational features. **Developer 1 does not overwrite Developer 2's work.**

---

## 1. Ownership Boundary

Developer 1 owns the backend/core files that guarantee the whole system is secure, isolated, and consistent. Specifically:

### Non-negotiable (Developer 1 only — no one else edits without explicit sign-off):

| Area | Files / Paths |
|---|---|
| Settings & project config | `backend/config/**` (settings, urls, wsgi, asgi) |
| Tenant & campus isolation | `backend/apps/accounts/access.py`, `managers.py`, `campus_middleware.py`, `middleware.py`, `scopes.py` |
| RBAC & authorization core | `backend/apps/accounts/permissions.py`, `permissions_new.py`, `permission models` |
| Authentication core | `backend/apps/accounts/authentication.py`, `google_sso.py`, `twofa_views.py`, `models.py` (User part) |
| Tenant/domain resolution | `backend/apps/schools/domain_middleware.py`, `middleware.py`, `branding_*.py`, `modules.py` |
| Shared model foundations | `backend/apps/core/models.py` (mixins/managers) |
| Media protection | `backend/apps/schools/media_views.py` |
| Deployment & infra | `vercel.json` (all), `render.yaml`, `Dockerfile`, `startup.sh`, `requirements.txt`, `docker-compose.yml`, `backend/deploy/**`, `.github/**` |
| Audit & security | `backend/apps/audit/**`, security docs |

### Shared (changes require Developer 1 review before merge):

| Area | Files |
|---|---|
| Data models & migrations | **all** `apps/*/models.py` + `apps/*/migrations/**` (Developer 2 may propose but Developer 1 signs off on schema) |
| API permission classes used cross-module | `accounts/permissions.py` (already reserved) + any new `BasePermission` in module apps that deviates from campus/tenant scoping |
| Serializers that set tenant/campus fields | any serializer that assigns `institution`/`campus`/`school` |

### Developer 2 owns (Developer 1 does not modify unless required for backend integration):

- `frontend/**` (all pages, components, routing, UX)
- Module operational features (fees UX, attendance UX, HR forms, etc.) — the *views/serializers* inside their module may be touched by Developer 1 only for scoping/perf fixes, with a note in PR.

---

## 2. Developer 1 Responsibilities (current audit phase)

1. Fix critical security blockers (R-01…R-05).
2. Add default tenant/campus manager + object-level guards.
3. Consolidate RBAC onto the codename matrix; seed defaults.
4. Own migration safety: every DB change ships with rollback + migration-check.
5. Own the live deploy configs and env hygiene.
6. Keep the audit/architecture docs in `docs/audit/**` current and do not let them drift.

## 3. Contract Invariants (Do Not Break)

- Never remove/rename tables, columns, or cause irreversible migrations on production.
- Never seed mock/production data outside seed scripts that are clearly demarcated and non-default.
- Never reduce isolation: new views MUST apply tenant/campus scoping.
- Never add a model without a **migration + tenant/campus key where applicable**.
- Never disable/mute security middleware to "make tests pass."

---

## 4. STOP Rules (Developer 1)

- Do **not** rebuild applications or replace working architecture without a documented, approved reason.
- Do **not** delete production data or reset the database.
- Do **not** create mock production data.
- Protect Developer 2's modules: no frontend/UX rewrites without explicit task scope.