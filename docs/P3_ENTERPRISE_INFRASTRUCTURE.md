# P3 — Enterprise Infrastructure Enhancements

Status report and operational documentation for the P3 scope
(`dev1/p3-enterprise`).

Every item below follows the same rule set that governed design: only
safe, evidence-based changes; existing behavior preserved unless a bug
proved otherwise; tenant isolation is never relaxed; and every feature
ships with tests.

---

## Status Summary

| # | Requirement                    | Status          | Notes |
|---|--------------------------------|-----------------|-------|
| 1 | Feature flags                  | IMPLEMENTED     | Global + per-institution toggles, default-off, 300s cache, kill-switch safe. |
| 2 | Tenant provisioning improvements| IMPLEMENTED    | Platform tenant create/patch now reuses the transactional `provision_school_with_admin`; N+1 stats fixed. |
| 3 | SaaS administration            | IMPLEMENTED     | Platform overview, status, security, plans + subscription admin views. |
| 4 | Subscription foundations       | IMPLEMENTED     | `Plan`/`Subscription` state machine (foundation only — billing provider is out of scope). |
| 5 | Usage analytics                | IMPLEMENTED     | Cache-buffered counters flushed to `DailyUsageSnapshot` by `collect_usage`. |
| 6 | Monitoring                     | IMPLEMENTED     | `PlatformStatusView` (DB + cache liveness) and `/api/health/` DB probe. |
| 7 | Performance                    | IMPLEMENTED     | Tenants list now aggregates stats in 2 queries instead of 2 per school; throttle `user` rate raised. |
| 8 | API rate limiting              | IMPLEMENTED     | DRF scoped throttling already in place; verified + tuned (`user` 2000→10000/day). |
| 9 | Security monitoring            | IMPLEMENTED     | IP brute-force detection (10 failures/day) emits one `brute_force_detected` audit alert/day; security roll-up view. |
|10 | Infrastructure hardening       | PARTIAL         | Env-gated security headers added; HTTPS/HSTS/DB concurrency limits were pre-existing. Redis-backed cache / rate-limit backend not introduced (out of infra budget for this phase). |

### Pre-existing issues found (NOT part of P3 scope)
- `makemigrations --check` reports unrelated drift in `accounts` and
  `payroll` (field alterations that predate this branch, likely from the
  merged P2 work). Left untouched; flagged here for follow-up.
- Django emits `auth.W004` (non-unique `USERNAME_FIELD`, expected —
  usernames are unique *per institution* by design).

---

## 1. Feature Flags — `apps.saas`

Model `FeatureFlag` (`backend/apps/saas/models.py`):
- `institution = NULL` → global flag; `institution != NULL` → per-tenant
  override. Two DB constraints keep both namespaces clean.
- Default is **off** — a new flag can never silently ship a regression.

Resolution order in `services.feature_enabled(name, institution)`:
per-institution override wins (even when it is explicitly **off**), then
the global flag, then `False`. Results cached 300s; `set_feature_flag`
invalidates the affected cache key.

### API
| Method | Endpoint | Who | Notes |
|--------|----------|-----|-------|
| GET | `/api/saas/flags/current/` | any authenticated | Effective flags for the caller's active institution. |
| GET/POST | `/api/saas/flags/` | platform admin | List or create/update (global or `institution_id`-scoped). |
| DELETE | `/api/saas/flags/<id>/` | platform admin | Deletes flag + cache entry. |

Seeding: `python manage.py seed_feature_flags [--enable lms.grading_v2 ...]`.

---

## 2. Tenant Provisioning Improvements — `apps.schools.platform_views`

- `TenantListCreateView.post` now provisions the tenant **and** its admin
  through `accounts.services.provision_school_with_admin` (one
  transaction). A terminal admin failure (duplicate email, exhausted
  usernames, invalid… ) rolls back the school — no more orphaned tenants.
- `TenantDetailView.patch` can add a School Admin transactionally too.
- `TenantListCreateView.get` stats (campuses + active students) are now
  computed by `_school_stats_map()` in **2 queries total** instead of
  2 per school (N+1 eliminated).

---

## 3–5. SaaS Admin, Subscriptions, Usage — `apps/saas`

### Subscription foundation
- `Plan` (code/limits/price in integer cents/features JSON) and
  `Subscription` (one per school; `trial → active → past_due/canceled`).
- `get_subscription(school)` lazily attaches the default `free` plan on
  first access so every school always has a row for analytics.
- `TenantSubscriptionView` lets a platform admin set
  `plan_code`/`status`; every change writes a `subscription_changed`
  audit record.

### Usage analytics
- `record_usage(school_id, metric)` is a **cache-buffered** counter
  (`api_requests | logins | failed_logins`) — zero DB writes on the
  request path.
- `python manage.py collect_usage` flushes buffered counts into
  `DailyUsageSnapshot` (one row per school/day, upserted) and recomputes
  live dimensions (students/staff/payments) straight from the DB.
- `GET /api/saas/analytics/usage/?days=N` (N≤365) flushes then aggregates.

### Platform administration views (all platform-admin gated)
- `GET /api/saas/platform/overview/` — schools/users/students/subscriptions
  + auth activity roll-up.
- `GET /api/saas/platform/status/` — DB `SELECT 1` + cache liveness probe.
- `GET /api/saas/security/` — failed-login windows, top offending IPs,
  locked accounts, brute-force alert counts.
- `GET /api/saas/plans/` — active plans.

> **Tenant isolation:** SaaS models use plain managers (no
> `TenantManager`) because they are platform/ops data; per-tenant read
> surfaces (`flags/current/`, `subscription/`) scope themselves by
> `request.institution`, never by a client-supplied id.

---

## 6–8. Monitoring, Performance, Rate Limiting

- `/api/health/` now accepts `?probe=db` (`SELECT 1`); returns
  `503/degraded` (JSON, no stack traces) when the DB is unreachable.
- DRF throttling (already configured in `base.py`) was audited and the
  `user` scope raised from `2000/day` to `10000/day` to stop legitimate
  ERP dashboard usage being throttled. Other scopes unchanged.

---

## 9. Security Monitoring — `apps.audit`

- `ACTION_CHOICES` extended (`subscription_changed`, `feature_flag_changed`,
  `role_change`, `brute_force_detected`, `api_key_created`) — migration
  `audit.0008_alter_auditlog_action`.
- `LoginAttemptAuditMiddleware` now:
  - keeps recording `login_failed`;
  - flags an IP that crosses **10 failed logins/day** with exactly one
    `brute_force_detected` audit row per day (deduped via cache);
  - bumps the per-institution `logins` usage counter on success.

---

## 10. Infrastructure Hardening — `config/settings/production.py`

Env-gated, safe-by-default additions (HSTS/secure cookies/CSRF origins
were already present):
- `DJANGO_SECURE_REFERRER_POLICY` (default `same-origin`)
- `DJANGO_SECURE_CROSS_ORIGIN_OPENER_POLICY` (opt-in `same-origin`)
- `SECURE_CONTENT_TYPE_NOSNIFF` (default on, env-disableable)

Explicitly **not** introduced this phase: Redis-backed cache and a
custom rate-limit backend — both require an infrastructure commitment
outside this scope. The file-based cache keeps counters and brute-force
detection working today.

---

## Verification

Commands (Windows PowerShell):

```powershell
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --settings=config.settings.test   # (audit+saas clean)
python manage.py test apps.saas apps.audit apps.schools --settings=config.settings.test
npm run build                                   # frontend
```

Results at time of writing:
- `apps.saas` — 76 tests, all passing (new), including review-regression tests added for
  strict boolean coercion on flag/`is_paused` payloads and the tenant-patch all-or-nothing rollback.
- `apps.audit` — 25 tests, all passing.
- `apps.schools` — 14 tests, all passing.
- `apps.accounts` (provisioning, auth-hardening, school auth, role security) — 102 tests, all passing.
- `vite build` — success.

Review fixes landed in this phase:
- `FeatureFlagAdminView` / `set_feature_flag` now use strict bool coercion —
  `bool("false")` was silently enabling flags (`"false"` → `True`).
- `TenantSubscriptionView` rejects non-numeric / negative `seats_used` with a 400 instead of a 500.
- `TenantListCreateView.patch` applies pause/activate only after admin provisioning
  succeeds, so a failed admin payload cannot leave a partially-persisted edit
  (previously the pause toggle saved itself before the admin transaction).
- Removed a dead `export` throttle rate that no view referenced.

## Operations cheat-sheet

```powershell
python manage.py seed_feature_flags                                   # baseline flags
python manage.py seed_plans                                           # plan catalog
python manage.py collect_usage                                        # flush usage buffer (cron it daily)
python manage.py makemigrations saas audit                            # if models change
```