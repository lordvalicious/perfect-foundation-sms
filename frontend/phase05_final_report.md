=== DEVELOPER 2 — PHASE 05 FEES / ACCOUNTS: FINAL REPORT ===

Branch: developer2/phase-05-fees
Report Date: Wed Sep 09 2026
Days in Phase: As assigned per development cycle

=== 1. BRANCH & STATUS ===
git branch --show-current: developer2/phase-05-fees
Git modified files (relative to phase-04 base):
- backend/apps/finance/views.py          (bulk invoice/payment + campus scope fixes)
- backend/apps/finance/stripe_views.py   (online payment institution/numbering fix)
- backend/apps/finance/jazzcash_views.py (online payment institution/numbering fix)
- backend/apps/finance/easypaisa_views.py(online payment institution/numbering fix)
- backend/apps/dashboard/views.py        (finance dashboards now match invoice truth)
- src/App.jsx, src/App.css, src/App.jsx  (carryforward from phases 01-02, unchanged this phase)
- src/pages/FinancePage.jsx, src/pages/StudentFeesPage.jsx, src/pages/BulkFinancePage.jsx
- Plus all 66 phase-01/-02/-03 page modifications still present
- Plus 62 frontend pages repaired from a phase-04 automated-script corruption
  (duplicate imports + module-scope useSchool() + orphaned export/export default lines)

=== 2. FRONTEND CORRUPTION REPAIR (build was broken) ===
Homegrown analysis scripts in frontend/src detected and removed injected blocks:
- 62 pages had a duplicated import/const header injected with a module-scope
  `const { currentSchool, activeCampus, ... } = useSchool();` call.
- The destructured names were never referenced in any page, so the injection
  was pure corruption: it broke every page and Vite failed to build with
  "Cannot be redeclared here" duplicate-identifier errors.
- ReportsPage.jsx line 9 also had a bad import path `./schoolContext` (fixed to
  `../schoolContext`).
- Verified: zero module-scope useSchool() calls remain; zero bare export lines;
  zero duplicate import statements (the AuditLogsPage double `react"` import is
  a legal parse — it is a duplicate that the linter tolerates; no action taken).
- `npm run build` now succeeds (vite v8.2.1, 2451 modules, built in ~4.4s).
- All audit/repair helper scripts removed before commit (repo stays clean).

=== 3. FEES AUDIT — BACKEND TRUTH ===
The finance module is a single source of financial truth in the backend:

--- Invoice model (apps/finance/models.py:212) ---
- subtotal        = sum of invoice item amounts                      (line 346)
- total_amount    = max(subtotal - discount - approved concessions, 0) (line 353)
- paid_amount     = sum of completed payments net_amount             (line 366)
- balance         = max(total_amount - paid_amount, 0)               (line 377)
- Test math: Tuition 10000 + Transport 2000 = subtotal 12000;
  Discount 1000 -> total 11000;            Payment 5000 -> balance 6000. ✓

--- Payment model (apps/finance/models.py:504) ---
- save() -> full_clean() -> invoice.refresh_status() when completed (line 639) ✓
- net_amount = amount - completed reversals - completed refunds (line 654) ✓
- unique (institution, receipt_number) constraint enforced when institution set ✓
- Payment.clean() rejects amount > invoice.balance and installment overflow ✓

--- InvoiceSerializer (apps/finance/serializers.py:277) ---
- Exposes subtotal, discount, total_amount, paid_amount, balance —
  all backend-computed read-only properties. Frontend renders these via
  formatCurrency without recomputing. ✓

--- Single-record write paths (correct already) ---
- InvoiceCreateSerializer.create: institution + next_invoice_number(institution) ✓
- PaymentCreateSerializer.create: select_for_update on invoice, amount<=balance,
  institution + next_receipt_number(institution) ✓

=== 4. BUGS FOUND & FIXED ===

BUG-1 BULK INVOICE CREATION ALWAYS FAILED (apps/finance/views.py:844)
- Invoice.objects.create() did not set `institution` -> invoices landed with a
  NULL tenant (invisible to institution-scoped queries; tenant leak) and could
  bypass the unique (institution, invoice_number) constraint.
- next_invoice_number() was called without its required `institution` argument
  -> TypeError on every item, swallowed by the bare `except` so every
  enrollment was reported "skipped" without any error surfacing.
- Additionally the single chosen fee_structure.amount was always billed,
  ignoring StudentFeeOverride, even though FeeAssignmentPreviewView shows the
  overridden total -> preview promised a different total than the invoice.
FIX: pass request.institution to next_invoice_number(); set institution on the
Invoice; apply the active StudentFeeOverride amount (over the fee structure
amount) when creating the invoice item, mirroring FeeAssignmentPreviewView.

BUG-2 BULK PAYMENT CREATION ALWAYS FAILED (apps/finance/views.py:981)
- Payment.objects.create() did not set `institution` (or `campus`).
- next_receipt_number() called without its `institution` argument -> TypeError
  on every item, again swallowed -> bulk payments never worked.
FIX: pass request.institution to next_receipt_number(); set institution and
campus (locked_invoice.enrollment.campus) on the created Payment. Invoice
status refresh already happens inside Payment.save(). Amount<=balance is
checked against the select_for_update-locked invoice, cross-institution IDs
are rejected, and assert_campus_allowed() is respected. ✓

BUG-3 ONLINE PAYMENT FLOWS ALWAYS FAILED
- stripe_views.py:133, jazzcash_views.py:227, easypaisa_views.py:236 all called
  next_receipt_number() with no argument -> TypeError in the webhook/callback
  handler, so every completed Stripe / JazzCash / EasyPaisa payment died at the
  receipt-number step (payment never created, invoice status stale).
FIX: derive the institution from the invoice (invoice.academic_year.school),
pass it to next_receipt_number(), and set institution + campus on the Payment.

BUG-4 DASHBOARD FINANCE TOTALS OFF FROM INVOICE TRUTH
- dashboard_finance / dashboard_finance_breakdown aggregated
  billed = items_total - discount, ignoring approved concessions, and
  collected = gross payment amounts, ignoring reversals and refunds.
  So dashboard outstanding diverged from the sum of Invoice.balance when
  concessions/reversals/refunds existed.
FIX: both endpoints now annotate items, approved concessions, gross payments,
completed reversals and completed refunds, then compute net billed / net paid
per invoice exactly like the Invoice model, so:
  total_billed  == sum(total_amount)
  outstanding   == sum(balance)
  outstanding rows / campus billed / collected also use the same net math. ✓

BUG-5 STUDENT OUTSTANDING ENDPOINT MISSING CAMPUS SCOPE
- StudentOutstandingBalanceView allowed managers to read any student in the
  institution regardless of their campus scope.
FIX: apply apply_campus_scope(..., "enrollment__campus_id") — for parents and
students the scope resolves to their own campuses so identity-level access is
unchanged; manager campus isolation is now enforced. ✓

=== 5. AUDITED — NO ACTION NEEDED ===
- OutstandingBalanceView (views.py:1183): institution-verified student/campus/
  academic-year filters + campus scope + backend total/paid/balance. ✓
- Invoice / Payment list views: institution + apply_campus_scope filtering. ✓
- Reports (apps/reports/fee_views.py): FeeCollection, FeeStatus, FeeAnalytics,
  Finance, FeeDefaulters — all server-side aggregated, IsAccountantRole. ✓
- Receipt PDF (apps/finance/pdf.py payment_receipt_pdf) — server-side render. ✓
- IsAccountantRole / IsFinanceReaderRole (apps/accounts/permissions.py:116/251):
  role lists + institution-scoped has_any_role; parents/students get finance
  read via IsFinanceReaderRole but identity-scoped by the view. ✓
- Frontend route guards (App.jsx:1064-1080): /finance requires
  super_admin|admin|principal|academic|accountant; /finance/student-fees and
  /finance/bulk require super_admin|admin|accountant. Accountant cannot reach
  admin-only bulk pages; principal/academic cannot reach them either. ✓

=== 6. FRONTEND DISPLAYS BACKEND TRUTH ONLY ===
- FinancePage.jsx: renders backend total_amount/paid_amount/balance as-is. ✓
- StudentFeesPage.jsx: renders backend total_amount; invoice action calls the
  backend (no local recompute). ✓
- BulkFinancePage.jsx: the "total to collect" is only a UI sum of backend
  balance values (line 300); the POST sends amount: inv.balance and the backend
  re-validates amount <= balance with row locks — no financial truth is ever
  computed in the frontend. ✓

=== 7. SCHOOL SWITCHING — NO FINANCIAL CACHE LEAKAGE ===
- schoolContext.jsx guards every active-institution/(re)fetch and campus switch
  with abortRef + seqRef so stale responses are discarded (lines 167-211).
- setSchoolScopeVersion() bumps on school and campus change.
- App.jsx:975 renders <Routes key={currentSchool?.id ?? "none"}> so every page —
  including FinancePage, StudentFeesPage, BulkFinancePage — unmounts/remounts on
  school switch. Finance state cannot survive a School A -> B -> A round trip.
- The finance endpoints are computed fresh per request server-side; no financial
  cache exists on the backend dashboard endpoints. School A -> B -> A therefore
  always shows School A's own balances. ✓

=== 8. TEST VALUES / VERIFICATION STATUS ===
Test scenario used across the audit:
  Tuition 10,000 + Transport 2,000 = subtotal   12,000
  Discount                      1,000 = total    11,000
  Payment                       5,000 = balance   6,000  ✓ (Invoice.balance math)
- Backend runtime execution is not available in this workspace (django module
  not installed); the balance math was verified against the model property
  source. All logic changes are pure-or-simple ORM queries and compile cleanly
  (python -m py_compile on every edited file).
- Frontend production build passes end-to-end after all changes.

=== 9. NEXT STEPS / OPEN ITEMS ===
- Run `python manage.py test apps.finance` and a live smoke test of
  /api/finance/bulk-invoices/ and /api/finance/bulk-payments/ once a Django
  runtime is available.
- next_invoice_number/next_receipt_number use COUNT+1; the model unique
  constraints are the real guard against races. A sequence-based counter (or a
  SELECT FOR UPDATE on a school row) would remove the residual race — not fixed
  here to avoid over-engineering the audit.
- Dashboard finance views iterate the full invoice set per request; fine now,
  but a monthly-archived rollup would be the scale path later.