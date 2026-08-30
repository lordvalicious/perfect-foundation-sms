# ERP Remaining Work Roadmap - Master Branch

**Based on**: Complete audit of backend, frontend, database, security, and testing  
**Prioritization**: P0=Critical (security/data loss), P1=High (core ERP), P2=Medium (enterprise), P3=Low (nice-to-have)

---

## PHASE 0 — Critical Security & Data Issues (P0)
**Timeline**: 2-3 weeks | **Team**: 2 backend, 1 DevOps

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P0-01 | Remove hardcoded `SECRET_KEY` default; enforce env var | P0 | Backend 1 | None |
| P0-02 | Enable secure cookies (`CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_HTTPONLY`) in production | P0 | Backend 1 | P0-01 |
| P0-03 | Add audit logging to ALL finance write operations (invoice, payment, refund, concession, journal) | P0 | Backend 1 | `apps.audit` exists |
| P0-04 | Implement duplicate payment prevention (idempotency key + DB unique constraint) | P0 | Backend 1 | Finance models |
| P0-05 | Configure automated PostgreSQL backups with tested restore procedure | P0 | DevOps | Infrastructure |
| P0-06 | Configure media/static file backups | P0 | DevOps | Infrastructure |
| P0-07 | Fix duplicate `SubjectOffering` model in `schools/models.py` | P0 | Backend 1 | None |
| P0-08 | Fix tuple fields in `School` model (trailing commas on ImageField/CharField) | P0 | Backend 1 | None |
| P0-09 | Change `Invoice.student` and `Payment.invoice` FK to `PROTECT` (not CASCADE) | P0 | Backend 1 | Migration required |
| P0-10 | Add rate limiting on auth endpoints (login: 10/min, password_reset: 5/hr) | P0 | Backend 1 | DRF throttling |

---

## PHASE 1 — Core Foundation (P1)
**Timeline**: 4-6 weeks | **Team**: 2 backend, 1 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P1-01 | Complete campus isolation for ALL modules (Library, Transport, HR, Medical, Assets, LMS, Discipline, Events, Sports, Clubs, Trips) | P1 | Backend 2 | CampusAccessMiddleware |
| P1-02 | Add unique constraints: Student.admission_number, Invoice.invoice_number, Enrollment(student,year,active), Concession, Payslip | P1 | Backend 1 | Migration |
| P1-10 | Add missing indexes (see Database Audit) | P1 | Backend 1 | Migration |
| P1-03 | Implement refund approval workflow (request → approve → process → audit) | P1 | Backend 2 | Finance models, Workflow app |
| P1-04 | Add MFA enforcement policy for admin roles (org-level setting) | P1 | Backend 2 | Accounts models |
| P1-05 | Add file upload validation (MIME, size limit, virus scan integration) | P1 | Backend 2 | Documents, StudentDocument |
| P1-06 | Add API versioning (`/api/v1/`) with deprecation policy | P1 | Backend 1 | All API endpoints |
| P1-07 | Implement object-level permissions in all views (not just role-based) | P1 | Backend 2 | Permission system |
| P1-08 | Add security headers middleware (CSP, HSTS, X-Content-Type-Options, Referrer-Policy) | P1 | Backend 1 | None |
| P1-09 | Add `created_by`/`updated_by` FK to User on all financial, HR, student models | P1 | Backend 1 | Migration |

---

## PHASE 2 — Student & Academic (P1-P2)
**Timeline**: 6-8 weeks | **Team**: 1 backend, 2 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P2-01 | Student 360 dashboard (profile, enrollment, attendance, fees, exams, documents) | P1 | Frontend 1 | Student APIs |
| P2-02 | Admissions pipeline UI (enquiry → application → test → interview → merit → enrollment) | P1 | Frontend 1 | Students models |
| P2-03 | Bulk student import (CSV/Excel with validation mapping, preview, error report) | P1 | Backend 1, Frontend 2 | Import framework |
| P2-04 | Student transfer UI (request → approve → execute) | P2 | Frontend 1 | StudentTransfer model |
| P2-05 | Promotion engine (rules-based, bulk, with rollback) | P2 | Backend 2 | Progression model |
| P2-06 | Alumni engagement dashboard | P3 | Frontend 2 | Alumni model |
| P2-07 | Timetable auto-generation (constraint solver) | P2 | Backend 2 | Timetable models |
| P2-08 | Subject allocation UI with conflict detection | P2 | Frontend 2 | SubjectOffering |
| P2-09 | Curriculum mapping & sequence validation | P3 | Backend 2 | SubjectGroup |

---

## PHASE 3 — Attendance & Exams (P1-P2)
**Timeline**: 4-6 weeks | **Team**: 1 backend, 1 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P3-01 | Student daily attendance UI (bulk mark, quick mark, mobile-friendly) | P1 | Frontend 1 | Attendance APIs |
| P3-02 | Attendance correction workflow (request → approve → audit trail) | P1 | Backend 1 | StaffAttendanceCorrection |
| P3-03 | Student leave application (parent submit → teacher approve) | P2 | Frontend 2 | StaffLeave model |
| P3-04 | Exam timetable conflict checker | P1 | Backend 2 | Exam model |
| P3-05 | Result entry UI (marksheet, bulk entry, validation) | P1 | Frontend 1 | StudentResult |
| P3-06 | Result approval workflow (teacher → HOD → Principal) | P1 | Backend 2 | Workflow app |
| P3-07 | GPA/Grade calculation engine (configurable) | P1 | Backend 2 | ExamSubject passing marks |
| P3-08 | Rechecking/remarking workflow | P2 | Backend 2 | Workflow app |
| P3-09 | Grade configuration UI (letter grades, points, divisions) | P2 | Frontend 2 | ExamSubject |

---

## PHASE 4 — Finance & Accounting (P0-P1)
**Timeline**: 8-10 weeks | **Team**: 2 backend, 1 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P4-01 | Fee structure builder UI (categories, amounts, dependencies, installments) | P1 | Frontend 1 | FeeCategory, FeeStructure |
| P4-02 | Automated installment generation from fee structure | P1 | Backend 2 | Invoice model |
| P4-03 | Payment gateway integration (Stripe, JazzCash, EasyPaisa) with webhook handling | P1 | Backend 2 | Stripe/Twilio config |
| P4-04 | Duplicate payment detection & prevention (frontend + backend) | P0 | Backend 1, Frontend 1 | P0-04 |
| P4-05 | Discount/concession workflow (request → approve → apply → audit) | P1 | Backend 2 | Concession model |
| P4-06 | Refund workflow with approval chain | P0 | Backend 2 | P1-03 |
| P4-07 | Bank reconciliation module (import, match, reconcile) | P1 | Backend 2 | New models needed |
| P4-08 | Chart of accounts & double-entry validation (debit=credit) | P1 | Backend 1 | JournalEntry/Line |
| P4-09 | Financial reports (trial balance, P&L, balance sheet, cash flow) | P1 | Backend 1 | Reports app |
| P4-10 | Expense approval workflow | P2 | Backend 2 | Expense model |
| P4-11 | Budget vs actual tracking | P2 | Backend 2 | New models |

---

## PHASE 5 — HR & Payroll (P1-P2)
**Timeline**: 6-8 weeks | **Team**: 1 backend, 1 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P5-01 | Employee directory with org chart | P2 | Frontend 1 | HR models |
| P5-02 | Contract management with expiry alerts | P2 | Backend 1 | Contract model |
| P5-03 | Leave balance tracking & auto-accrual | P2 | Backend 1 | LeaveType, LeaveBalance |
| P5-04 | Recruitment pipeline (job post → applicant → offer → onboarding) | P3 | Backend 2, Frontend 2 | New models |
| P5-05 | Performance review cycle (self → manager → calibrate) | P3 | Backend 2 | New models |
| P5-06 | Salary structure builder (allowances, deductions, tax slabs) | P1 | Frontend 1 | PayrollStructure |
| P5-07 | End-to-end payroll run (calculate → approve → generate payslips) | P1 | Backend 2 | PayrollRun, Payslip |
| P5-08 | Advance/loan management with repayment schedule | P2 | Backend 2 | New models |
| P5-09 | Payslip generation (PDF, email, portal) | P1 | Backend 1 | P5-07 |

---

## PHASE 6 — Operations (P2-P3)
**Timeline**: 8-10 weeks | **Team**: 1 backend, 2 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P6-01 | Library: Book catalog search, issue/return UI, overdue fines, reservations | P2 | Frontend 1 | Library models |
| P6-02 | Transport: Route optimization, student assignment, fee calculation | P2 | Backend 2 | Transport models |
| P6-03 | Transport: GPS integration (vendor API) | P3 | Backend 2 | Vendor |
| P6-04 | Inventory: Purchase request → PO → Receive → Stock update | P2 | Frontend 2 | Inventory models |
| P6-05 | Inventory: Low stock alerts, reorder points | P2 | Backend 1 | Stock model |
| P6-06 | Assets: Register, assignment, depreciation, disposal | P2 | Frontend 2 | Asset models |
| P6-07 | Assets: Warranty tracking, maintenance scheduling | P3 | Backend 2 | Maintenance model |

---

## PHASE 7 — LMS & Communication (P2-P3)
**Timeline**: 6-8 weeks | **Team**: 1 backend, 2 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P7-01 | LMS: Course/lesson builder with rich content | P2 | Frontend 1 | LMS models |
| P7-02 | LMS: Video lesson integration (YouTube, Vimeo, direct upload) | P2 | Backend 2 | New storage |
| P7-03 | LMS: Assignment submission, grading, feedback loop | P2 | Frontend 2 | LMS models |
| P7-04 | LMS: Grade sync to report cards | P2 | Backend 2 | Exams, Reportcards |
| P7-05 | Communication: Parent-Teacher messaging (threaded, attachments, read receipts) | P1 | Frontend 1 | New models |
| P7-06 | Communication: Announcement targeting (campus, class, section, role) | P2 | Backend 1 | Announcement model |
| P7-07 | Communication: SMS/Email template builder with variables | P2 | Frontend 2 | Templates |
| P7-08 | Communication: Scheduled notifications, digest emails | P2 | Backend 2 | Celery/beat |

---

## PHASE 8 — Portals (P1-P2)
**Timeline**: 8-10 weeks | **Team**: 2 frontend, 1 backend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P8-01 | Super Admin portal (platform overview, tenant management, billing) | P1 | Frontend 1 | Schools, WhiteLabel |
| P8-02 | Organization Admin portal (multi-campus, settings, reports) | P1 | Frontend 1 | Campus isolation |
| P8-03 | Campus Admin portal (campus operations, staff, students) | P1 | Frontend 2 | Campus isolation |
| P8-08 | Principal portal (academic overview, discipline, events) | P2 | Frontend 2 | Dashboard |
| P8-04 | Teacher portal (attendance, marks, timetable, communication) | P1 | Frontend 1 | All teacher APIs |
| P8-05 | Accountant portal (fees, payments, reconciliation, reports) | P1 | Frontend 2 | Finance APIs |
| P8-06 | HR portal (employees, leave, payroll, recruitment) | P2 | Frontend 1 | HR/Payroll APIs |
| P8-07 | Parent portal (student 360, fees, attendance, communication, documents) | P1 | Frontend 2 | Student APIs |
| P8-09 | Student portal (timetable, assignments, results, library, transport) | P2 | Frontend 1 | LMS, Exams, Library |
| P8-10 | Employee self-service (leave, payslip, profile, documents) | P2 | Frontend 2 | HR APIs |

---

## PHASE 9 — UI/UX Polish (P2-P3)
**Timeline**: 4-6 weeks | **Team**: 2 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P9-01 | Responsive design audit & fix (mobile, tablet, desktop) | P2 | Frontend 1 | All portals |
| P9-02 | Dark mode support (CSS variables, theme context) | P2 | Frontend 1 | Design system |
| P9-03 | Loading/skeleton/empty/error states for ALL pages | P2 | Frontend 2 | Component library |
| P9-04 | Form validation (client + server sync) with inline errors | P2 | Frontend 1 | Forms |
| P9-05 | Confirmation dialogs for destructive actions | P2 | Frontend 2 | Components |
| P9-06 | Accessibility audit (WCAG 2.1 AA) | P3 | Frontend 1 | All UI |
| P9-07 | Keyboard navigation & focus management | P3 | Frontend 2 | Components |
| P9-08 | Breadcrumbs, search, filtering, sorting, pagination consistency | P2 | Frontend 1 | All lists |
| P9-09 | Bulk actions (select all, export, delete, status change) | P2 | Frontend 2 | Tables |

---

## PHASE 10 — White Label / SaaS Readiness (P2-P3)
**Timeline**: 6-8 weeks | **Team**: 1 backend, 1 frontend

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P10-01 | Per-tenant theming engine (logo, colors, login page, emails) | P2 | Frontend 1 | School branding fields |
| P10-02 | Custom domain/subdomain routing with SSL | P2 | Backend 1, DevOps | Domain middleware |
| P10-03 | Feature entitlements per plan (modules, users, campuses, storage) | P2 | Backend 2 | School.enabled_modules |
| P10-04 | Certificate/receipt/ID-card branding per tenant | P3 | Backend 1 | PDF generation |
| P10-05 | Tenant onboarding wizard (self-serve signup) | P3 | Frontend 2 | Schools, WhiteLabel |
| P10-06 | Usage metering & limits enforcement | P3 | Backend 2 | New models |

---

## PHASE 11 — Performance & DevOps (P1-P3)
**Timeline**: 4-6 weeks | **Team**: 1 backend, 1 DevOps

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P11-01 | N+1 query audit & fix (select_related/prefetch_related) | P1 | Backend 1 | All ViewSets |
| P11-02 | Slow query identification & indexing | P1 | Backend 1 | P1-10 |
| P11-03 | API response pagination optimization (cursor pagination for large sets) | P2 | Backend 1 | DRF |
| P11-04 | Dashboard query optimization (materialized views, caching) | P1 | Backend 2 | Dashboard app |
| P11-05 | Search optimization (PostgreSQL full-text or Elasticsearch) | P2 | Backend 2 | Search app |
| P11-06 | Large export async (Celery + download link) | P2 | Backend 2 | Export endpoints |
| P11-07 | CI/CD pipeline (test → build → staging → production) | P1 | DevOps | GitHub Actions |
| P11-08 | Health checks, monitoring (Prometheus/Grafana), error tracking (Sentry) | P1 | DevOps | Infrastructure |
| P11-09 | Database connection pooling (PgBouncer) | P2 | DevOps | Production |
| P11-10 | Automated dependency scanning (Dependabot, npm audit) | P2 | DevOps | CI/CD |

---

## PHASE 12 — Final Security & QA (P0-P2)
**Timeline**: 3-4 weeks | **Team**: 1 backend, 1 frontend, 1 QA

| ID | Task | Priority | Owner | Dependencies |
|----|------|----------|-------|--------------|
| P12-01 | Penetration testing (external) | P0 | QA | All phases |
| P12-02 | GDPR compliance (data export, deletion, consent) | P1 | Backend 1 | All models |
| P12-03 | FERPA compliance audit (student record access logging) | P1 | Backend 1 | Audit app |
| P12-04 | PCI DSS SAQ completion (Stripe handles card data) | P1 | Backend 2 | Finance |
| P12-05 | Load testing (1000 concurrent users) | P1 | QA | Staging |
| P12-06 | Chaos engineering (DB failover, cache failure) | P2 | DevOps | P11-08 |
| P12-07 | Security headers validation (securityheaders.com) | P2 | DevOps | P1-08 |
| P12-08 | Dependency vulnerability scan & remediation | P2 | DevOps | P11-10 |
| P12-09 | User acceptance testing (all portals) | P1 | QA | P8 |
| P12-10 | Documentation (API, deployment, operations, user guides) | P2 | All | All |

---

## Cross-Phase Dependencies

```
P0 (Security) ──────────────────────────────────────┐
                                                     ▼
P1 (Core) ←── P2 (Student/Academic) ←── P3 (Attendance/Exams)
    │                                                │
    └──────► P4 (Finance) ◄────── P5 (HR/Payroll) ───┘
                    │
                    ▼
P6 (Ops) ◄── P7 (LMS/Comm) ◄── P8 (Portals)
    │                          │
    └──────────► P9 (UI/UX) ◄──┘
                    │
                    ▼
P10 (SaaS) ◄────── P11 (Perf/DevOps)
                    │
                    ▼
               P12 (Sec/QA)
```

---

## Resource Allocation Summary

| Role | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 | Phase 8 | Phase 9 | Phase 10 | Phase 11 | Phase 12 |
|------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|----------|----------|----------|
| Backend 1 | 100% | 100% | 50% | 50% | 100% | 50% | 50% | 50% | 50% | - | 50% | 100% | 50% |
| Backend 2 | 50% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 50% | - | 100% | 50% | 50% |
| Frontend 1 | - | 50% | 100% | 100% | 100% | 50% | 100% | 100% | 100% | 100% | 100% | - | 50% |
| Frontend 2 | - | 50% | 100% | 100% | 50% | 100% | 100% | 100% | 100% | 100% | 100% | - | 50% |
| DevOps | 100% | 50% | - | - | - | - | - | - | - | - | - | 100% | 100% |
| QA | - | - | - | - | - | - | - | - | - | - | - | - | 100% |

---

## Estimated Total Effort

| Phase | Backend Days | Frontend Days | DevOps Days | QA Days | Total Days |
|-------|-------------|---------------|-------------|---------|------------|
| Phase 0 | 25 | 0 | 15 | 0 | 40 |
| Phase 1 | 40 | 10 | 0 | 0 | 50 |
| Phase 2 | 20 | 30 | 0 | 0 | 50 |
| Phase 3 | 15 | 15 | 0 | 0 | 30 |
| Phase 4 | 40 | 15 | 0 | 0 | 55 |
| Phase 5 | 25 | 15 | 0 | 0 | 40 |
| Phase 6 | 15 | 30 | 0 | 0 | 45 |
| Phase 7 | 15 | 30 | 0 | 0 | 45 |
| Phase 8 | 10 | 40 | 0 | 0 | 50 |
| Phase 9 | 0 | 30 | 0 | 0 | 30 |
| Phase 10 | 15 | 15 | 5 | 0 | 35 |
| Phase 11 | 10 | 0 | 20 | 0 | 30 |
| Phase 12 | 5 | 5 | 10 | 20 | 40 |
| **TOTAL** | **230** | **205** | **50** | **20** | **505 person-days** |

**At 2 backend + 2 frontend + 1 DevOps + 0.5 QA = 5.5 FTE: ~23 weeks (6 months) to production-ready enterprise ERP**