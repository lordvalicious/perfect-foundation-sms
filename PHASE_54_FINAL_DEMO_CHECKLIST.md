# PHASE 54 — FINAL DEMO CHECKLIST

## Pre-Demo Verification

### Production Health
- [x] Frontend loads at https://perfect-foundation-sms.vercel.app/
- [x] Backend API responds at https://perfect-foundation-api.vercel.app/
- [x] Database connectivity verified (Neon PostgreSQL)
- [x] No obvious 500 errors
- [x] F14 migration endpoint secured (MIGRATION_SECRET active)

### Authentication
- [x] SUPER_ADMIN login (sa_frostfire.txt) → /api/auth/me/ → 200
- [x] ADMIN login (sa_flora.txt) → /api/auth/me/ → 200
- [x] TEACHER login (sa_SA-EMP-0001.txt) → /api/auth/me/ → 200
- [x] STAFF login (sa_DI-staff.txt) → /api/auth/me/ → 200
- [x] STUDENT login (sa_SA-ST-0001.txt) → /api/auth/me/ → 200
- [x] ACCOUNTANT role verified through existing accounts

---

## Client Demonstration Script

### 1. Login Flow (5 minutes)
- [ ] SUPER_ADMIN: Login as FrostFire → show global dashboard
- [ ] ADMIN: Login as Flora → show institution-bound dashboard
- [ ] TEACHER: Login as SA-EMP-0001 → show classroom-scoped dashboard
- [ ] STAFF: Login as DI-EMP-0001 → show campus 7 dashboard (mention Phase 46 repair)
- [ ] STUDENT: Login as SA-ST-0001 → show student self-service dashboard

### 2. Dashboard Tour (10 minutes)
- [ ] SUPER_ADMIN: Global institution switch, tenant management
- [ ] ADMIN: Institution overview, student/teacher/staff management
- [ ] TEACHER: Assigned classes, students, attendance, grades
- [ ] STAFF: Campus 7 scoped view (mention cross-campus isolation)
- [ ] STUDENT: Own profile, classes, attendance, exams, finances
- [ ] ACCOUNTANT: Finance-focused dashboard with full reports

### 3. Core Module Walkthroughs (15 minutes)

#### Students Module
- [ ] List students with search/filter
- [ ] Student profile view
- [ ] Enrollment details
- [ ] Parent portal (if applicable)

#### Finance Module (KEY DEMO)
- [ ] Finance Dashboard (`/api/dashboard/finance/`) — all roles
- [ ] Trial Balance Report — SUPER_ADMIN/ADMIN/ACCOUNTANT only
- [ ] Income/Expense Report — SUPER_ADMIN/ADMIN/ACCOUNTANT only
- [ ] Receivables Report — SUPER_ADMIN/ADMIN/ACCOUNTANT only
- [ ] Show role-based access: 403 for non-accountant roles
- [ ] Mention: `/api/students/finance/` → 404 (documented); use `/api/dashboard/finance/`

#### Attendance Module
- [ ] Attendance records view
- [ ] Filtering by date/class/student
- [ ] Note: Marking attendance NOT CERTIFIED (production mutation blocked)

#### Exams/Report Cards
- [ ] Exam schedule and results view
- [ ] Report card generation/visibility
- [ ] Note: Marks entry and publishing NOT CERTIFIED

#### HR/Payroll
- [ ] Staff/employee records (read-only)
- [ ] Payroll dashboard (read-only)
- [ ] Note: Payroll processing NOT CERTIFIED

### 4. Responsive UI Check (5 minutes)
- [ ] Desktop (1440×900): Full navigation, tables render
- [ ] Tablet (768×1024): Drawer menu, table reflow
- [ ] Mobile (390×844): Hamburger menu, single-column layout

### 5. Security/Authorization (5 minutes)
- [ ] Student tries admin endpoint → 403
- [ ] Student tries another student's data → 403
- [ ] Staff tries finance report → 403 (no accountant role)
- [ ] Staff tries cross-campus (campus 9) → 403
- [ ] Unauthenticated protected endpoint → 401/403

### 6. F14 Migration Endpoint (2 minutes)
- [ ] GET /api/migrate/ → 405 (method not allowed)
- [ ] POST /api/migrate/ (unauth) → 401 (MIGRATION_SECRET active)
- [ ] POST /api/migrate/ (invalid bearer) → 401
- [ ] Rate limit → 429 (10/min)

---

## Demo Limitations — MUST COMMUNICATE

### NOT CERTIFIED — DO NOT DEMONSTRATE AS WORKING
- [ ] Real payment transactions (Stripe would charge real money)
- [ ] Payroll processing (would issue employee compensation)
- [ ] Real attendance marking (would alter student records)
- [ ] Real marks entry (would alter academic records)
- [ ] Real SMS/email delivery (would send to real recipients)
- [ ] Destructive CRUD (student/teacher/staff create/delete)
- [ ] Accountant auto-creation via API (CSRF/ORM blockers)

### KNOWN LIMITATIONS
- [ ] `/api/students/finance/` → 404 (documented routing design)
- [ ] Accountant test account not auto-created (CSRF/ORM blockers)
- [ ] Consequential mutations intentionally not tested

---

## Post-Demo Actions
- [ ] Document any issues observed during demo
- [ ] Update defect register if new issues found
- [ ] Confirm no production data was mutated
- [ ] Verify all test accounts still functional

---

## Sign-Off

**Demo Conducted By:** _________________________
**Date:** _________________________
**Client Representative:** _________________________
**Status:** [ ] DEMO COMPLETE — READY FOR PRODUCTION