# PERFORMANCE_AUDIT.md

**Date:** 2026-08-30
**Owner:** Developer 1
**Method:** Static review. No load test or query-plan profiling run.

---

## 1. Configuration Baseline

- Backend: Vercel Python serverless (cold starts) or Docker+Gunicorn (3 workers, timeout 120s) per `docs/`.
- DB: Neon PostgreSQL. `CONN_MAX_AGE=600`, health checks on (`base.py:120-124`).
- Cache: **FileBasedCache** for default + ratelimit — single-instance, no Redis. `django_ratelimit` disabled pending Redis.
- Pagination: DRF `PageNumberPagination`, `PAGE_SIZE=20` globally.
- Static: WhiteNoise `CompressedManifestStaticFilesStorage`.

---

## 2. Findings

### 2.1 API / Queryset Performance

| Severity | Finding | Impact |
|---|---|---|
| High | **Report endpoints are heavyweight per-view classes** — reports app has 167 routes; `views.py` (1534) + `extended_views.py` (1165). Many compute aggregate rows in Python loops over entire querysets (see `TeacherMasterReportView.get_detail_rows`, staff_views.py:129-156). No `.select_related`/`.prefetch_related` discipline confirmed. | Slow lists on large campuses; Vercel timeout risk (max ~60s) on big orgs |
| High | **JSON large-file views** — `finance/views.py` (1789 lines), `students/views.py` (1306), `hr/views.py` (1113), `accounts/views.py` (1364) — patterns break local reasoning; hot-path serializations unindexed lookups likely. | Maintenance + perf bugs surface at scale |
| Medium | Global page size 20 with no per-view tuning; `?page=1` over large data sets implies **N requests for a full roll-up** on the frontend (e.g. report tables). | Chatty client for list-heavy modules |
| Medium | **No caching headers / ETag / DRF caching layer** configured; identical heavy requests re-execute. | Repeated dashboard/report calls hit DB each time |
| Medium | FileBasedCache is not viable for multi-instance serverless (each instance has its own cache dir on Vercel); repeated cache misses after restart. | Throttle/cache behavior unreliable serverless |
| Medium | `AuditLog`, `NotificationDispatch`, `SMSLog`, `EmailLog` grow unbounded; no retention policy observed. | Table bloat → indexes/full scans slow writes |

### 2.2 Frontend

| Severity | Finding | Impact |
|---|---|---|
| Medium | No route splitting; single Vite bundle (build warned "chunk size" earlier). 59 page files in one bundle. | First-load latency grows with surface |
| Medium | All data fetch via `apiFetch` with no cache/dedupe layer (no react-query); repeated dashboard calls on navigation. | Extra round-trips |
| Low | `useApiList` hook pattern is good; resides per page (no central API layer for tables). | Consistency |

### 2.3 Background Jobs

| Severity | Finding | Impact |
|---|---|---|
| Medium | 5 Vercel crons hit serverless endpoints; no job queue/retry semantics. | Missed crons silently drop work; late-fee/fee-reminder runs rely on cron reliability |

---

## 3. No-Go Actions (this audit)

- No load testing performed.
- No EXPLAIN plans captured.
- No index changes executed.

---

## 4. Recommended Performance Workstream (separate task)

1. Add `.select_related`/`.prefetch_related` passes to the hot report list endpoints; convert Python-loop aggregations to `annotate`/`aggregate` where feasible.
2. Introduce a lightweight query-count guard for report/summary endpoints (test gate).
3. Adopt Redis-backed cache (Upstash/Render Redis) before enabling `django_ratelimit`; move heavy cached payloads (dashboard roll-ups) to cache with short TTLs.
4. Add route-level code splitting in Vite for the ~20 heaviest pages.
5. Set retention/purge policies for audit + notification logs (archive tables / scheduled cleanup).
6. Add an APM/error tracker (e.g. New Relic, Sentry) for serverless visibility.
7. Re-run this performance audit after the data-integrity phase with real query plans.

---

## 5. Slowest Suspect Endpoints (to baseline first)

- `/api/reports/*` (167 routes; many aggregate roll-ups)
- `/api/dashboard/*` (aggregations across modules)
- `/api/finance/*` invoicing/payment lists
- `/api/students/?search=` + `/api/reports/students/profile/?student=` (per-student deep profile)
- `/api/search/` cross-module search