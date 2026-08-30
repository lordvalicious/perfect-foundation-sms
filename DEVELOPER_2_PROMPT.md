# Developer 2 Prompt — Phase 0 & 1 Work (Non-Overlapping with Developer 1)

---

## 🎯 CONTEXT

You are **Developer 2**. **Developer 1** is handling backend core/security/infrastructure tasks in parallel.  
**DO NOT** duplicate, recreate, or modify anything Developer 1 owns.

> **Golden Rule**: If it exists in the codebase — use it. If Developer 1 is doing it — don't touch it.  
> Check the repo first (`grep`, `find`, read files) before writing anything.

---

## 📋 YOUR WORK — PHASE 0 (Critical Security) — Days 1-3

### Your Phase 0 Tasks (5 tasks)

| Task | ID | What to Do | Files to Check First |
|------|----|------------|---------------------|
| **Fix duplicate SubjectOffering model** | P0-07 | `schools/models.py` has `SubjectOffering` defined **twice** (lines ~401-470 and ~736-819). Keep the first one, delete the second. Run `makemigrations` after. | `schools/models.py` (search "class SubjectOffering") |
| **Fix tuple fields in School model** | P0-08 | `School.logo`, `School.favicon`, `School.login_text_color` have trailing commas making them tuples. Remove commas. Also `School.__str__` defined twice. | `schools/models.py` lines 57-66, 82-86, 121-122, 140-141 |
| **Change Invoice.student FK to PROTECT** | P0-09 | In `finance/models.py`, find `Invoice.student` FK. Change `on_delete=models.CASCADE` → `models.PROTECT`. Create migration. | `finance/models.py` (search "class Invoice") |
| **Change Payment.invoice FK to PROTECT** | P0-09 | Same file, `Payment.invoice` FK: `CASCADE` → `PROTECT`. | `finance/models.py` (search "class Payment") |
| **Rate limiting on auth endpoints** | P0-10 | Add specific throttle classes to login, password-reset, 2FA views. Use DRF's `UserRateThrottle`/`AnonRateThrottle` with custom rates. | `apps/accounts/views.py`, `apps/accounts/urls.py` |

### What Developer 1 Is Doing (DO NOT TOUCH)
- P0-01: SECRET_KEY env enforcement
- P0-02: Secure cookies
- P0-03: Finance audit logging
- P0-04: Duplicate payment prevention (idempotency key)
- P0-05/06: DB/media backups
- P0-10: Rate limiting **infrastructure** (throttle classes config)

---

## 📋 YOUR WORK — PHASE 1 (Campus Isolation for ALL Modules) — Days 4-15

### Goal: Ensure every module's ViewSets enforce campus isolation using existing `CampusScopedManager` or `apply_campus_scope()`.

### Step 1: Audit Current State (Day 4)
Run this command to find all ViewSets:
```bash
grep -r "ViewSet\|APIView\|GenericAPIView" backend/apps/ --include="*.py" | grep -v test | grep -v migration
```

For each app, check:
1. Does the model have a `campus` FK (direct or nested)?
2. Does the ViewSet use `CampusScopedManager` or call `apply_campus_scope()`?
3. Is there a test in `test_campus_isolation.py` for it?

### Step 2: Modules You Own (12 modules — Developer 1 does NOT touch these)

| App | Model(s) with Campus FK | Campus Path | Action |
|-----|------------------------|-------------|--------|
| `library` | `BookCopy`, `Issue` | `book__campus` or `student__primary_campus` | Add `CampusScopedManager` to models; wrap ViewSet `get_queryset` |
| `transport` | `Vehicle`, `Route`, `StudentTransport` | `campus`, `route__campus`, `student__primary_campus` | Same |
| `hr` | `Employee`, `LeaveRequest` | `primary_campus`, `staff__primary_campus` | Same |
| `payroll` | `PayrollRun`, `Payslip` | `employee__primary_campus` | Same |
| `inventory` | `Stock`, `PurchaseOrder` | `campus`, `warehouse__campus` | Same |
| `assets` | `Asset`, `Maintenance` | `campus`, `assigned_to__primary_campus` | Same |
| `lms` | `Course`, `Enrollment` | `campus`, `student__primary_campus` | Same |
| `discipline` | `Incident` | `student__primary_campus` | Same |
| `health` | `MedicalIncident`, `Visit` | `student__primary_campus` | Same |
| `events` | `Event`, `Registration` | `campus`, `student__primary_campus` | Same |
| `sports` | `Team`, `Fixture` | `campus` | Same |
| `clubs` | `Club`, `Membership` | `campus`, `student__primary_campus` | Same |

### Step 3: Implementation Pattern (Copy This)

```python
# In each app's models.py — add CampusScopedManager to campus-scoped models
from apps.accounts.managers import CampusScopedManager

class BookCopy(models.Model):
    campus = models.ForeignKey('schools.Campus', ...)
    # ... existing fields ...
    
    objects = CampusScopedManager(campus_field="campus_id", institution_field="institution_id")
```

```python
# In each app's views.py — ensure ViewSet uses the manager (auto-scoped) OR explicitly scopes
from apps.accounts.access import apply_campus_scope

class BookCopyViewSet(ModelViewSet):
    queryset = BookCopy.objects.all()  # CampusScopedManager auto-filters
    
    # OR if not using CampusScopedManager:
    def get_queryset(self):
        qs = super().get_queryset()
        return apply_campus_scope(qs, self.request, campus_field="campus_id")
```

### Step 4: Verify (Day 15)
Add tests to `apps/accounts/test_campus_isolation.py` following the existing pattern for each module.

---

## 📋 YOUR WORK — PHASE 2 (Student & Academic) — Days 16-35

### Your Tasks (Developer 1 does NOT touch these)

| Task | ID | Description | Key Files |
|------|----|-------------|-----------|
| Bulk student import | P2-03 | CSV/Excel import with validation mapping, preview, error report. Use existing import framework if any. | `students/management/commands/`, `students/views.py` |
| Promotion engine | P2-05 | Rules-based promotion (pass/fail, age, attendance). Bulk promote with rollback. | `students/progression.py`, `students/views.py` |
| Timetable auto-generation | P2-07 | Constraint solver for timetable (no conflicts). | `timetable/management/commands/`, `timetable/views.py` |
| Subject allocation UI support | P2-08 | Backend APIs for conflict detection (teacher double-booked, room conflict). | `schools/views.py`, `schools/models.py` SubjectOffering |
| Curriculum mapping | P2-09 | SubjectGroup → Subject relationships, prerequisite chains. | `schools/models.py` SubjectGroup |

### What Developer 1 Owns (DO NOT TOUCH)
- P2-01: Student 360 dashboard (Frontend 1)
- P2-02: Admissions pipeline UI (Frontend 1)
- P2-04: Student transfer UI (Frontend 1)
- P2-06: Alumni dashboard (Frontend 2)
- P2-08: Subject allocation UI (Frontend 2)

---

## 📋 YOUR WORK — PHASE 3 (Attendance & Exams) — Days 36-50

### Your Tasks

| Task | ID | Description |
|------|----|-------------|
| Attendance correction workflow | P3-02 | Request → approve → audit trail. Extend `StaffAttendanceCorrection` for students. |
| Exam timetable conflict checker | P3-04 | Validate no teacher/room/student conflicts when creating exams. |
| Result approval workflow | P3-06 | Teacher → HOD → Principal. Use `apps.workflow` app. |
| GPA/Grade calculation engine | P3-07 | Configurable grading scale, weighted GPA, class rank. |
| Rechecking/remarking workflow | P3-08 | Student request → faculty assign → re-grade → audit. |

### What Developer 1 Owns
- P3-01: Student daily attendance UI (Frontend 1)
- P3-03: Student leave UI (Frontend 2)
- P3-05: Result entry UI (Frontend 1)
- P3-09: Grade config UI (Frontend 2)

---

## 📋 YOUR WORK — PHASE 4 (Finance Workflows) — Days 51-80

### Your Tasks (Backend Logic Only)

| Task | ID | Description | Key Files |
|------|----|-------------|-----------|
| Automated installment generation | P4-02 | From FeeStructure → create Invoices per installment schedule. | `finance/services.py`, `finance/models.py` |
| Payment gateway integration | P4-03 | Stripe, JazzCash, EasyPaisa webhooks. Verify signatures. | `finance/stripe_views.py`, `finance/jazzcash_views.py`, `finance/easypaisa_views.py` |
| Discount/concession workflow | P4-05 | Request → approve → apply to invoices. Audit trail. | `finance/views.py`, `finance/models.py` Concession |
| Bank reconciliation module | P4-07 | Import bank CSV/Excel → match payments → reconcile. New models needed. | `finance/models.py` (new), `finance/management/commands/` |
| Double-entry validation | P4-08 | JournalEntry save(): enforce Σdebits = Σcredits. | `finance/models.py` JournalEntry.save() |
| Financial reports backend | P4-09 | Trial balance, P&L, BS, cash flow querysets. | `reports/views.py`, `finance/services.py` |
| Expense approval workflow | P4-10 | Use `apps.workflow` for expense approval chain. | `finance/views.py`, `workflow/` |
| Budget vs actual | P4-11 | New models: Budget, BudgetLine. Compare to actuals. | `finance/models.py` (new) |

### What Developer 1 Owns (DO NOT TOUCH)
- P4-01: Fee structure builder UI (Frontend 1)
- P4-04: Duplicate payment prevention frontend (Frontend 1)
- P4-06: Refund workflow (Developer 1 does backend for this)

---

## 📋 YOUR WORK — PHASE 5 (HR & Payroll Core) — Days 81-110

### Your Tasks

| Task | ID | Description |
|------|----|-------------|
| Leave balance tracking & auto-accrual | P5-03 | Monthly/annual accrual based on LeaveType. Carry-forward rules. |
| Salary structure builder backend | P5-06 | Allowances, deductions, tax slabs, formulas. API for Frontend 1 UI. |
| Payroll run engine | P5-07 | Calculate gross → deductions → net. Generate Payslip records. Bulk process. |
| Advance/loan management | P5-08 | Loan application → approve → disburse → repayment schedule → auto-deduct from payroll. |
| Payslip generation | P5-09 | PDF generation (reportlab), email, portal access. |

### What Developer 1 Owns
- P5-01: Employee directory UI (Frontend 1)
- P5-02: Contract management UI (Frontend 1)
- P5-04: Recruitment pipeline (Backend 2 + Frontend 2 — you can collab on backend)
- P5-05: Performance reviews (Backend 2 + Frontend 2)

---

## 📋 YOUR WORK — PHASE 6-7 (Operations & LMS/Comm) — Days 111-150

### Your Tasks (Backend APIs)

| Phase | Task | ID | Description |
|-------|------|----|-------------|
| 6 | Purchase request → PO → Receive | P6-04 | Full procurement workflow. Stock update on receive. |
| 6 | Low stock alerts | P6-05 | Threshold-based alerts (email/in-app). Celery beat job. |
| 6 | Asset depreciation/disposal | P6-07 | Straight-line/declining balance. Disposal workflow. |
| 7 | Video lesson integration | P7-02 | YouTube/Vimeo embed + direct upload (signed URLs). |
| 7 | Grade sync to report cards | P7-04 | LMS assignment grades → Exam/Reportcard sync. |
| 7 | Scheduled notifications | P7-08 | Celery beat: fee reminders, absence alerts, birthday, etc. |

### What Developer 1 Owns
- All UI for these modules (Frontend 1 & 2)

---

## 📋 YOUR WORK — PHASE 8 (Portals API) — Days 151-190

### Your Tasks: Build API endpoints for each portal (Frontend 1/2 build UI)

| Portal | Endpoints You Build |
|--------|---------------------|
| Super Admin | `/api/super-admin/*` — tenant list, metrics, billing |
| Org Admin | `/api/org-admin/*` — multi-campus overview, settings |
| Campus Admin | `/api/campus-admin/*` — campus-scoped operations |
| Principal | `/api/principal/*` — academic overview, discipline, events |
| Teacher | `/api/teacher/*` — my classes, attendance, marks, timetable |
| Accountant | `/api/accountant/*` — fees, payments, reconciliation |
| HR | `/api/hr/*` — employees, leave, payroll |
| Parent | `/api/parent/*` — my children (360), fees, attendance, messages |
| Student | `/api/student/*` — my timetable, assignments, results, library |
| Employee | `/api/employee/*` — leave, payslip, profile, documents |

**Pattern**: Each portal gets a dedicated ViewSet with campus-scoped querysets (use `CampusScopedManager`).

---

## ✅ VERIFICATION CHECKLIST (Before Every PR)

- [ ] `grep -r "class.*Model"` — no duplicate model definitions
- [ ] `grep -r "CASCADE"` on financial FKs — should be PROTECT
- [ ] `grep -r "CampusScopedManager\|apply_campus_scope"` — every campus-scoped ViewSet uses it
- [ ] `python manage.py check` — no errors
- [ ] `python manage.py makemigrations --dry-run` — only your intended migrations
- [ ] Run `apps.accounts.test_campus_isolation` — all your modules pass

---

## 🚫 EXPLICITLY OFF-LIMITS (Developer 1 Territory)

| Area | Owner |
|------|-------|
| SECRET_KEY, secure cookies, session config | Dev 1 |
| Finance audit logging (`record_audit` calls) | Dev 1 |
| Idempotency key / duplicate payment prevention | Dev 1 |
| DB/media backup configuration | Dev 1 |
| Rate limiting infrastructure (throttle classes) | Dev 1 |
| Security headers middleware (CSP, HSTS) | Dev 1 |
| MFA enforcement policy | Dev 1 |
| File upload validation (MIME/size/virus) | Dev 1 |
| API versioning (`/api/v1/`) | Dev 1 |
| Object-level permission enforcement in views | Dev 1 |
| `created_by`/`updated_by` fields on models | Dev 1 |
| CI/CD, monitoring, health checks | Dev 1 |
| GDPR/FERPA/PCI compliance code | Dev 1 |
| All Frontend work (React components, pages, state) | Frontend 1 & 2 |

---

## 🔍 HOW TO CHECK IF SOMETHING EXISTS

Before writing ANY code:

```bash
# 1. Search for existing model/field
grep -r "class YourModel" backend/apps/ --include="*.py"

# 2. Search for existing ViewSet/endpoint
grep -r "YourModelViewSet\|your-model" backend/apps/ --include="*.py"

# 3. Search for existing manager/queryset method
grep -r "CampusScopedManager\|apply_campus_scope" backend/apps/ --include="*.py"

# 4. Check migrations
ls backend/apps/your_app/migrations/

# 5. Check tests
ls backend/apps/your_app/test*.py
```

If it exists → **use it, extend it, don't recreate**.

---

## 📁 FILES YOU WILL TOUCH (Primary)

```
backend/apps/library/models.py, views.py
backend/apps/transport/models.py, views.py
backend/apps/hr/models.py, views.py
backend/apps/payroll/models.py, views.py
backend/apps/inventory/models.py, views.py
backend/apps/assets/models.py, views.py
backend/apps/lms/models.py, views.py
backend/apps/discipline/models.py, views.py
backend/apps/health/models.py, views.py
backend/apps/events/models.py, views.py
backend/apps/sports/models.py, views.py
backend/apps/clubs/models.py, views.py
backend/apps/students/models.py, views.py, progression.py
backend/apps/exams/models.py, views.py
backend/apps/finance/models.py, views.py, services.py
backend/apps/workflow/ (use existing)
backend/apps/accounts/test_campus_isolation.py (add tests)
```

---

## 🎯 DEFINITION OF DONE (Per Task)

1. Code follows existing patterns in repo
2. Campus isolation enforced (tested)
3. No duplicate models/fields
4. Financial FKs are PROTECT
5. Migrations generated cleanly
6. Added to `test_campus_isolation.py` where applicable
7. No console.log/print/debug code
8. Type hints where practical

---

## 📞 SYNC POINTS WITH DEVELOPER 1

| When | What |
|------|------|
| End of Day 3 | Phase 0 complete — merge migrations |
| End of Day 15 | Phase 1 complete — all 12 modules campus-isolated |
| Weekly | Quick sync on shared models (User, School, Campus) |

---

**Start with Phase 0 — fix the 5 items above. They unblock everything else.**