# PHASE 37 — CLIENT DEMO PLAN

**Only workflows verified as PASS in production are included below.**

---

## SUPER_ADMIN Demo Script

| Step | Action | Expected Result | Evidence |
|------|--------|-----------------|----------|
| 1 | Login as FrostFire | Dashboard loads with cross-tenant stats (5 students, 1 teacher, 3 staff) | SA-001 |
| 2 | Navigate to Students | List shows 5 students across tenants | SA-002 |
| 3 | Navigate to Teachers | List shows 1 teacher | SA-003 |
| 4 | Navigate to Staff | List shows 3 staff | SA-004 |
| 5 | Navigate to Finance → Invoices | Empty list (no data) | SA-008 |
| 5 | Navigate to Reports → Enrollment | Chart renders enrollment by campus | SA-013 |
| 6 | Navigate to Reports → Fees | Chart renders fee collection | SA-015 |
| 7 | Navigate to AI Assistant | Overview loads with capabilities | SA-018 |
| 8 | Logout | Returns to login page | - |

---

## ADMIN Demo Script

| Step | Action | Expected Result | Evidence |
|------|--------|-----------------|----------|
| 1 | Login as Flora | Dashboard loads (12.2s) | AD-003 |
| 2 | Navigate to Teachers | List shows 1 teacher | AD-003 |
| 3 | Navigate to Staff | List shows 3 staff | AD-004 |
| 4 | Navigate to Attendance | List renders (0 records) | AD-005 |
| 5 | Navigate to Exams | List renders (0 records) | AD-006 |
| 6 | Navigate to Report Cards | List renders (0 records) | AD-007 |
| 7 | Navigate to Finance → Invoices | List renders (0 records) | AD-008 |
| 8 | Navigate to Finance → Payments | List renders (0 records) | AD-009 |
| 9 | Navigate to Finance → Categories | List renders (0 records) | AD-009 |
| 10 | Navigate to HR → Employees | List renders (0 records) | AD-011 |
| 11 | Navigate to Payroll → Records | List renders (0 records) | AD-012 |
| 12 | Navigate to Reports → Enrollment | Chart renders | AD-013 |
| 13 | Navigate to Reports → Attendance | Chart renders | AD-014 |
| 13 | Navigate to Reports → Fees | Chart renders | AD-015 |
| 14 | Navigate to Schools → Campuses | List shows 2 campuses | AD-016 |
| 15 | Navigate to Schools → Classes | List renders | AD-016 |

---

## TEACHER Demo Script

| Step | Action | Expected Result | Evidence |
|------|--------|-----------------|----------|
| 1 | Login as SA-EMP-0001 | Teacher dashboard loads | TEA-001 |
| 2 | Navigate to Students | Empty list (no assigned students) | TEA-002 |
| 3 | Navigate to Attendance | Form loads, roster empty | TEA-003 |
| 4 | Navigate to Exams | List renders (0 records) | TEA-003 |
| 5 | Navigate to Report Cards | List renders (0 records) | TEA-004 |
| 6 | Navigate to Schools → Campuses | List renders | TEA-005 |
| 6 | Navigate to Schools → Classes | List renders | TEA-005 |

---

## STUDENT Demo Script

| Step | Action | Expected Result | Evidence |
|------|--------|-----------------|----------|
| 1 | Login as SA-ST-0001 | Student dashboard loads | STU-001 |
| 2 | Navigate to My Profile | Shows own data only | STU-002 |
| 3 | Navigate to Attendance | Loads own records (0) | STU-003 |
| 4 | Navigate to Exams | List renders (0 records) | STU-004 |
| 5 | Navigate to Report Cards | List renders (0 records) | STU-005 |
| 6 | Navigate to Schools → Campuses | List renders | STU-006 |

---

## STAFF Demo Script

| Step | Action | Expected Result | Evidence |
|------|--------|-----------------|----------|
| 1 | Login as DI-EMP-0001 | Staff directory loads (3 records) | STA-001 |
| 2 | Navigate to Attendance | List renders (0 records) | STA-002 |
| 3 | Navigate to HR → Employees | List renders (0 records) | STA-003 |
| 4 | Navigate to Schools → Campuses | List renders | STA-004 |

---

## Features NOT in Demo (Blocked/Untested)

| Feature | Reason |
|---------|--------|
| Create/Edit/Delete Student | BLOCKED — production mutation unsafe |
| Create/Edit/Delete Teacher | BLOCKED — production mutation unsafe |
| Create/Edit/Delete Staff | BLOCKED — production mutation unsafe |
| Mark Attendance | BLOCKED — production mutation unsafe |
| Record Payment | BLOCKED — real payment unsafe |
| Stripe Checkout | BLOCKED — real payment unsafe |
| Send SMS/Email | BLOCKED — real delivery unsafe |
| AI Chat | BLOCKED — external AI invocation unsafe |
| Payroll Processing | BLOCKED — real payroll mutation unsafe |
| Publish Exam Results | BLOCKED — production mutation unsafe |
| Generate Payslip | DOWNLOAD PATH VERIFIED (not generated) |

---

## Known Issues to Disclose

1. **ADMIN Dashboard Timeout** (12.2s avg) — Missing DB index on institution-scoped queries
2. **ADMIN Students List Timeout** (12.7s avg) — Missing DB index on institution-scoped queries
3. **Student Module Intermittent Timeouts** — Attendance/Exams/Report Cards occasionally >15s
4. **F14 Migration Hardening** — Not deployed to production
5. **20+ Endpoints Return 404** — Not implemented in backend
6. **STAFF Dashboard Timeout** (12.5s avg) — Missing campus assignment for staff user
7. **Dashboard Summary Endpoint** — Obsolete, returns 404
8. **STAFF User Has No Campus** — Cannot create StaffProfile due to DB constraint on soft-deleted records
9. **F14 Migration Hardening** — Not deployed to production
10. **20+ Endpoints Return 404** — Not implemented in backend