# SECURITY_AUDIT.md

**Date:** 2026-08-30
**Owner:** Developer 1
**Assumptions:** Read-only audit; findings not yet remediated. Severity: Critical/High/Medium/Low with all data verified in source.

---

## 1. Authentication

**Model summary**
- Custom `User(AbstractUser)`; `email` unique; `phone`, `photo`, TOTP seed (`twofa_secret`, **stored plaintext base32**), `twofa_enabled`, lockout fields (`failed_login_attempts`, `locked_until`), `password_changed_at`, `must_change_password`.
- Login: `EmailOrUsernameBackend` (case-insensitive email, then username); rejects locked accounts.

**Findings**

| Severity | Finding | Location |
|---|---|---|
| Critical | **Hardcoded superadmin** `FrostFire` / `ra2a1s345` committed in VCS migration; email `lordvalicious@gmail.com`; **re-forces password on every migration run**. Any DB rebuilt/reset or any migration on the prod DB re-creates/overwrites the superuser with the known password → full account takeover of the entire platform. | accounts/migrations/0014_create_frostfire_superadmin.py:12-31 |
| High | **Session fixation / lockout bypass:** bad-password lockout is not recorded by the login view itself; it depends on a separate `LoginFailedView` (frontend-coordinated) or 2FA failure. A direct API attacker never triggers lockout. | accounts/views.py:136 vs 215-243 |
| High | **TOTP secret plaintext** at rest (`twofa_secret`); backup codes hashed with **unsalted SHA-256** (fast to brute force). | accounts/models.py:43; twofa_views.py:101 |
| Medium | Google SSO: no lockout check, no throttle applied to the SSO path. | accounts/google_sso.py:52-115 |
| Medium | Password history only; default PBKDF2 (acceptable) — no config to upgrade hasher scheme/params. | (defaults) |

---

## 2. Session & CSRF

- Session auth only (`SessionAuthentication`); **no JWT/token backend** → relies on cookie SameSite + Secure.
- `CSRF_COOKIE_HTTPONLY=False` (deliberate — frontend reads cookie to send `X-CSRFToken`). Acceptable pattern but widening of exposure.
- Production: `SESSION_COOKIE_SECURE=1` and `CSRF_COOKIE_SECURE=1` defaults.
- Hotfixes re-declare `CSRF_TRUSTED_ORIGINS` **three times** in `production.py` (lines 39-41, 50-53, 60-63) — the last assignment wins; the hardcoded list is `perfect-foundation-api` + `perfect-foundation-sms` only, meaning any other future Vercel host must be added twice. Maintenance hazard, not a vuln.

---

## 3. Authorization / RBAC

**Architecture (3 coexisting systems)**
1. Legacy role-list permission classes (`permissions.py`)
2. Granular codename RBAC (`Permission`/`RolePermission`/`UserPermission` + `permissions_new.py`) — **not seeded → grants nothing until runtime-configured**
3. Middleware: campus + module entitlement + login-audit

**Findings**

| Severity | Finding | Location |
|---|---|---|
| High | **No object-level permission checks** in any view — every class is `has_permission` only; no `get_object` scoping via permission classes. Views calling `get_object()` without first scoping their queryset are IDOR-prone. | all apps |
| High | **Two parallel RBAC gates** create bypass risk: permission-management endpoints (`RolePermissionCreateView` etc.) gate on ad-hoc role lists, not on `permission.assign`/`role.manage` codenames; `IsLibrarianRole` references non-existent role `librarian` (dead). | accounts/permissions.py:153; views.py:1314-1516 |
| High | `has_any_role(roles)` with `None` institution aggregates **across all memberships**; several helpers call it without an institution → cross-institution role aggregation. | accounts/models.py:65-75; scopes.py:32-53 |
| Medium | `UserProfileView` exposes phone/email of any same-institution user to any authenticated member. | accounts/views.py:356-363 |
| Medium | `ModuleAccessMiddleware` gates by URL prefix only; unmapped prefixes (students/attendance/exams/finance/reports) are always open (by design "core"), but there is no record-type check inside routes. | schools/modules.py:9-26 |
| Medium | Superuser bypass is everywhere (roles, permissions, campus global, module gate) — correct *per design* but amplifies the hardcoded-superuser issue. | models.py:81-82,178-179; access.py:65; middleware.py:40-41 |

---

## 4. Campus / Tenant Isolation (Security View)

| Severity | Finding | Location |
|---|---|---|
| **Critical** | `CampusAccessMiddleware` line 66: `campus_id = int(campus_id)` — **`campus_id` is undefined** (should be `campus_param`). Any request carrying `?campus=<n>` raises `NameError` → HTTP 500 on the request path the middleware was meant to protect. Middleware-level campus filter therefore fails. (Views using `apply_campus_scope` independently still protect themselves.) | campus_middleware.py:62-71 |
| High | NULL-`campus` / NULL-`institution` records are visible to everyone in scope (documented "school-wide" behavior) — implicit cross-campus and cross-tenant leakage for unstaffed records. | access.py:243-245,296-299,323-325 |
| High | Scoping is **opt-in per view**; no default manager injects tenant/campus filters. Models without the FK silently skip scoping (`_model_has_path` returns False → skip). | access.py:251-271,293-299 |
| Medium | Bypass helpers `all_tenants()`/`all_campuses()`/`for_campus()`/`for_institution()` exist though currently unused. | accounts/managers.py:35-41,137-143 |
| Medium | `/api/schools/` is exempt from campus-validation middleware → tenant/campus enumeration surface. | campus_middleware.py:22-28 |
| Low | `TenantHostMiddleware` dead code (not in MIDDLEWARE) with subdomain parse bug. | schools/domain_middleware.py:9,39 |

---

## 5. Exposure & Secrecy

| Severity | Finding | Location |
|---|---|---|
| Critical | **Unauthenticated `POST /api/admin/run-migrations/`** endpoint mounted in `config/urls.py` (`core.views.run_migrations_view`) — schema is mutable via a public route. Must be gated (DRF auth + admin role + CRON secret) or removed. | config/urls.py:16; apps/core/views.py |
| Critical | Root `/.env.production` committed with a **live `VERCEL_OIDC_TOKEN`** in plaintext. If the repo is/was shared or public, the token is compromised. | /.env.production |
| High | Fallback `DJANGO_SECRET_KEY` = `django-insecure-…` (base.py) and default DB password `school_password` (base.py) — production guards the secret key (hard fail), but dev/.env fallback posture is unsafe if ever leaked. | config/settings/base.py:20-23,135-138 |
| High | `cookie.txt`, `Neon Console.html`, `debug_room*.py`, `seed_*.py`, numbered dump files (e.g. `589`, `1010`) committed at repo root — credentials/session artifacts and tooling in version control. | repo root |
| Medium | `CSRF_COOKIE_HTTPONLY=False` is required by design for the SPA to read it. | production.py:56 |
| Medium | Media serving is protected (`ProtectedMediaView`) but relies on session/permission logic per-object; verify object-level check exists before granting files. | apps/schools/media_views.py |

---

## 6. Rate Limiting

- `django_ratelimit` + `RatelimitMiddleware` are **commented out** (require Redis) — `config/settings/base.py:67,83`.
- DRF throttles are configured (`anon 60/min`, `user 2000/day`, `login`/`password_reset`/`public_apply` scopes) — applied only where views specify `throttle_scope`. **Login throttle exists (60/hr).** Legacy FBVs (`core`, `dashboard`, `portal`) and Google SSO have no throttle.

---

## 7. Operational Security

- HTTPS enforced in production (`SECURE_SSL_REDIRECT` default 1), HSTS 31536000s + preload.
- No CI/CD → no SAST/dependency/secret scanning in the pipeline.
- Logging: console only; no audit trail for permission changes beyond `AuditLog` app (present) — verify granular.

---

## 8. Priority to Fix (see RISK_REGISTER for full treatment)

1. **SEC-01** Remove/hard-gate public `run-migrations` endpoint.
2. **SEC-02** Remove hardcoded superadmin migration; rotate password; document bootstrap credential flow.
3. **SEC-03** Remove committed `.env.production` + secrets + artifacts; rotate the OIDC token.
4. **SEC-04** Fix `campus_middleware.py:66` undefined-variable bug.
5. **SEC-05** Add dashboard/portal/SSO throttling; remove dead `librarian` role; unify RBAC gates.
6. **SEC-06** Add default tenant/campus manager + require `apply_campus_scope` testing for IDOR coverage.