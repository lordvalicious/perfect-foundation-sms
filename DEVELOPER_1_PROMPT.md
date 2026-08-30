# Developer 1 Prompt — Phase 0 & 1 Work (Non-Overlapping with Developer 2)

---

## 🎯 CONTEXT

You are **Developer 1** (Backend Core / Security / Infrastructure).  
**Developer 2** handles module-specific backend logic (campus isolation per app, finance workflows, HR/payroll engine, operations, portals API).

**DO NOT** touch Developer 2's modules. If it exists → use it.

---

## 📋 YOUR WORK — PHASE 0 (Critical Security) — Days 1-3

### Your Phase 0 Tasks (5 tasks)

| Task | ID | What to Do | Files |
|------|----|------------|-------|
| **Remove hardcoded SECRET_KEY default** | P0-01 | `config/settings/base.py:22` — remove default, enforce `DJANGO_SECRET_KEY` env var. Fail fast if missing. | `config/settings/base.py` |
| **Enable secure cookies in production** | P0-02 | `config/settings/production.py`: `CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_HTTPONLY=True`, `CSRF_COOKIE_SAMESITE='Strict'`. | `config/settings/production.py` |
| **Add audit logging to ALL finance writes** | P0-03 | In every finance view that creates/updates: `Invoice`, `Payment`, `Concession`, `JournalEntry`, `FeeStructure` — call `record_audit(user, action, details)`. | `finance/views.py`, `apps/audit/models.py` |
| **Duplicate payment prevention** | P0-04 | 1) Add `idempotency_key` field to `Payment` model (UUID, unique). 2) Frontend sends key; backend rejects duplicate. 3) Add DB unique constraint on `(student, invoice, amount, payment_date, idempotency_key)`. | `finance/models.py`, `finance/views.py`, `finance/serializers.py` |
| **Configure DB + media backups** | P0-05/06 | With DevOps: pg_dump cron → S3/GCS, media rsync → S3/GCS. Document restore steps. Test restore. | `docker-compose.yml`, backup scripts, docs |

### What Developer 2 Is Doing (DO NOT TOUCH)
- P0-07: Fix duplicate SubjectOffering model
- P0-08: Fix tuple fields in School model
- P0-09: Change Invoice.student & Payment.invoice FK to PROTECT
- P0-10: Rate limiting on auth endpoints (views)

---

## 📋 YOUR WORK — PHASE 1 (Core Foundation) — Days 4-25

### Your Tasks (Infrastructure / Cross-Cutting)

| Task | ID | Description | Files |
|------|----|-------------|-------|
| **Security headers middleware** | P1-08 | Add `django-csp` or custom middleware: CSP, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. | `config/middleware.py` (new), `config/settings/base.py` |
| **MFA enforcement for admin roles** | P1-04 | Org-level setting `require_2fa_for_admins`. Check in `EmailOrUsernameBackend` or middleware. | `apps/accounts/authentication.py`, `apps/schools/models.py` (School settings) |
| **File upload validation** | P1-05 | MIME allowlist, size limit (per-field), virus scan hook (ClamAV/cloud). Apply to `StudentDocument`, `EmployeeDocument`, `Asset.document`. | `apps/documents/validators.py` (new), model `FileField` validators |
| **API versioning** | P1-06 | Wrap all routers in `/api/v1/`. Add `APIVersionMixin` for future v2. Deprecation header. | `config/urls.py`, `apps/*/urls.py` |
| **Object-level permissions in ALL views** | P1-07 | Create `ObjectPermissionMixin` using `user.has_permission(codename, institution)`. Apply to every ViewSet. | `apps/accounts/permissions.py` (new), all `views.py` |
| **Add created_by/updated_by to financial/HR/student models** | P1-09 | FK to User, `auto_now_add`/`auto_now` not enough — need actor. Migration + backfill script. | `finance/models.py`, `hr/models.py`, `students/models.py`, `payroll/models.py` |
| **Campus isolation test coverage for Dev 2's modules** | P1-01 (shared) | Add test cases to `test_campus_isolation.py` for Library, Transport, HR, Payroll, Inventory, Assets, LMS, Discipline, Health, Events, Sports, Clubs. | `apps/accounts/test_campus_isolation.py` |

### What Developer 2 Owns (DO NOT TOUCH)
- All 12 modules' `CampusScopedManager` implementation
- Finance workflows (installments, gateways, bank rec, double-entry)
- HR/Payroll engine (salary structure, payroll run, payslips, loans)
- Student/Academic (import, promotion, timetable, curriculum)
- Attendance/Exams (corrections, GPA, workflows)
- Operations (procurement, stock alerts, depreciation)
- LMS/Comm (video, grade sync, scheduled notifications)
- Portals API

---

## 📋 YOUR WORK — PHASE 4 (Finance Core Security) — Days 51-80

### Your Tasks (Security/Integrity Layer)

| Task | ID | Description |
|------|----|-------------|
| **Refund approval workflow backend** | P4-06 | RefundRequest model → workflow (request → approve → process). Audit every step. Integrate with `apps.workflow`. |
| **Payment gateway webhook signature verification** | P4-03 (shared) | Verify Stripe `stripe-signature`, JazzCash/EasyPaisa checksums. Reject invalid. |
| **PCI DSS SAQ compliance helpers** | P12-04 | Tokenize card data (Stripe handles), no PAN in logs, encryption at rest for any stored tokens. |

---

## 📋 YOUR WORK — PHASE 11 (Performance & DevOps) — Days 191-220

### Your Tasks

| Task | ID | Description |
|------|----|-------------|
| **N+1 query audit & fix** | P11-01 | Django Debug Toolbar / `django-querycount`. Add `select_related`/`prefetch_related` to all ViewSets. |
| **Slow query identification & indexing** | P11-02 | `pg_stat_statements` analysis. Add missing composite indexes (see Database Audit). |
| **Dashboard query optimization** | P11-04 | Materialized views for dashboard aggregates. Refresh via Celery beat. |
| **CI/CD pipeline** | P11-07 | GitHub Actions: test → build → staging → production. Docker multi-stage. |
| **Health checks, monitoring, error tracking** | P11-08 | `/health/` endpoint, Prometheus metrics, Sentry/Grafana. |
| **Database connection pooling** | P11-09 | PgBouncer config (transaction pooling). Update `DATABASES` config. |
| **Automated dependency scanning** | P11-10 | Dependabot (pip + npm), `pip-audit`, `npm audit` in CI. |

---

## 📋 YOUR WORK — PHASE 12 (Final Security & QA) — Days 221-250

### Your Tasks

| Task | ID | Description |
|------|----|-------------|
| **GDPR compliance** | P12-02 | Data export (all user data), right to deletion (anonymize), consent tracking. |
| **FERPA compliance** | P12-03 | Student record access logging, directory info opt-out. |
| **PCI DSS SAQ completion** | P12-04 | Document Stripe scope, no card storage, quarterly scans. |
| **Security headers validation** | P12-07 | `securityheaders.com` A+ grade. |
| **Dependency vulnerability remediation** | P12-08 | Fix all `pip-audit`/`npm audit` findings. |

---

## 🚫 EXPLICITLY OFF-LIMITS (Developer 2 Territory)

| Area | Owner |
|------|-------|
| Campus isolation per module (Library, Transport, HR, etc.) | Dev 2 |
| Finance workflows (installments, gateways, bank rec, double-entry) | Dev 2 |
| HR/Payroll engine (salary calc, payroll run, payslips, loans) | Dev 2 |
| Student/Academic logic (import, promotion, timetable, curriculum) | Dev 2 |
| Attendance/Exams logic (corrections, GPA, workflows) | Dev 2 |
| Operations logic (procurement, stock, assets) | Dev 2 |
| LMS/Comm logic (video, grade sync, notifications) | Dev 2 |
| Portals API endpoints | Dev 2 |
| All Frontend work | Frontend 1 & 2 |

---

## ✅ VERIFICATION CHECKLIST (Before Every PR)

- [ ] `config/settings/production.py` has all secure cookie flags
- [ ] `config/settings/base.py` has no hardcoded secrets
- [ ] `record_audit()` called in ALL finance write views
- [ ] `Payment.idempotency_key` unique constraint exists
- [ ] CSP/HSTS headers present in responses
- [ ] MFA enforcement setting works
- [ ] File upload validators on all `FileField`s
- [ ] API routes under `/api/v1/`
- [ ] `ObjectPermissionMixin` on all ViewSets
- [ ] `created_by`/`updated_by` on financial/HR/student models
- [ ] CI/CD passes (tests, lint, typecheck, security scan)
- [ ] No new N+1 queries in changed ViewSets

---

## 📁 FILES YOU WILL TOUCH (Primary)

```
config/settings/base.py, production.py, development.py
config/middleware.py (new)
config/urls.py
apps/accounts/authentication.py, permissions.py (new), views.py
apps/accounts/test_campus_isolation.py (add tests)
apps/audit/models.py, middleware.py
apps/finance/models.py, views.py, serializers.py
apps/hr/models.py
apps/students/models.py
apps/payroll/models.py
apps/documents/validators.py (new)
docker-compose.yml, Dockerfile
.github/workflows/ci.yml (new)
monitoring/ (new)
```

---

## 🎯 DEFINITION OF DONE (Per Task)

1. Follows existing patterns in repo
2. No hardcoded secrets
3. Security-first defaults
4. Migrations clean
4. Tests pass (including campus isolation)
5. CI/CD green
6. Documented in code (docstrings)

---

## 📞 SYNC POINTS WITH DEVELOPER 2

| When | What |
|------|------|
| End of Day 3 | Phase 0 complete — merge migrations |
| End of Day 25 | Phase 1 complete — infra ready for module work |
| Weekly | Quick sync on shared models (User, School, Campus, Permission) |

---

**Start with Phase 0 — your 5 items unblock Dev 2's FK changes and rate limiting.**