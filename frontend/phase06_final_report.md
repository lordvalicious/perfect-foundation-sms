=== DEVELOPER 2 — PHASE 06 PAYROLL + EXAMS / RESULTS: FINAL REPORT ===

Branch: developer2/phase-06-payroll-exams
Report Date: Wed Sep 09 2026
Days in Phase: As assigned per development cycle

=== 1. BRANCH & STATUS ===
git branch --show-current: developer2/phase-06-payroll-exams
Scope: payroll (Salary Structures, Payroll Records, Payslips, Bank File)
       and exams/results (Exams, Marks, Report Cards, PDF/print exports).
Phase-05 work is intentionally left UNCOMMITTED in the working tree per
directive ("Leave uncommitted"); this phase adds its own edits on top of it.

Git modified files introduced/edited this phase (relative to phase-05 tree):
- backend/apps/payroll/models.py              (STATUS "approved", timezone stamps,
                                               compute() running gross/net, is_taxable,
                                               SalaryStructure totals via calculate_amount)
- backend/apps/payroll/views.py               (PayslipGenerateView broken import fix)
- backend/apps/payroll/payslips_pdf.py        (IsAccountantRole permission + dict
                                               component_details formatting fix)
- backend/apps/payroll/bank_file.py           (IsAccountantRole permission + employee
                                               refactor for CSV rows)
- backend/apps/reportcards/views.py           (campus/institution scope on list, detail,
                                               batch PDF)
- backend/apps/reportcards/pdf.py             (summary now equals per-row table totals)
- frontend/src/pages/PayrollPage.jsx          (real draft->process->approve->pay UI)

=== 2. PAYROLL AUDIT — BACKEND TRUTH ===
The payroll model is the single calculation engine (payroll/views.py:
PayrollRecord.compute() runs inside save()):

--- PayrollRecord.compute() (models.py:323) ---
- allowances:  each SalaryStructureComponent.calculate_amount(basic, running_gross, 0)
- percent_gross allowances now use a RUNNING gross (basic + allowances so far)
  instead of `basic + self.gross_salary` (which was the previously persisted
  gross, 0 on first create -> wrong amounts for percentage-of-gross components).
- deductions:  each component.calculate_amount(basic, gross, running_net)
  percent_net deductions now use a RUNNING net (gross - deductions so far)
  instead of the pre-computed gross (previously percent_net acted on gross).
- gross_salary = basic + allowances; net_salary = gross - deductions;
  component_details.allowances/deductions store name, str(amount),
  calculation_type and is_taxable (deduction entries previously wrote a bogus
  "is_pre_tax": False key — SalaryStructureComponent has no is_pre_tax).
- Tax note (documented, not changed): DB net_salary is NET BEFORE WHT; both
  output paths (payslip PDF and bank file) subtract monthly_withholding() for
  display, so printed/exported net is consistent even though the stored field
  is pre-tax.

--- SalaryStructure (models.py:90) ---
- total_allowances / total_deductions_components now apply calculate_amount()
  (percent-based components are honored; previously ONLY the raw fixed `amount`
  field was summed, so structures with percentage components showed wrong
  Allowances/Gross in the UI and serializer).
- gross_salary = basic + total_allowances (unchanged property).

--- Status lifecycle ---
- "approved" was set by PayrollApproveView and approve() but was MISSING from
  STATUS_CHOICES and the inline choices -> admin/filters could not represent it.
  Added ("approved", "Approved") to both (models.py:173, 251).
- process()/approve()/pay() model methods assigned `models.DateTimeField(auto_now=True)`
  (a field descriptor, not a datetime) to processed_at/approved_at/paid_at —
  a latent crash path on save. Replaced with timezone.now().
- PayrollApproveView requires "processed"; PayrollPayView requires "approved" ✓.

--- Payslip PDF (payslips_pdf.py) ---
- permission_classes [IsAuthenticated] -> [IsAccountantRole] (was accessible to any
  logged-in user, incl. students/parents; now honour-based like the rest of payroll).
- component_details values are dicts ({"name","amount",...}); the code formatted
  the dict itself with `f"{value:,.2f}"` -> TypeError on any record with
  component_details. Now unwraps name/amount safely (also tolerates legacy
  scalar values from old seeds).
- Verified payroll_queryset scoping (employee__institution | primary_campus__school
  + apply_campus_scope over employee__primary_campus_id) is used to fetch the record.

--- Bank file CSV (bank_file.py) ---
- permission [IsAuthenticated] -> [IsAccountantRole].
- Migrated from the removed `teacher` FK to the Employee refactor: select_related
  employee/employee__primary_campus/employee__teacher; order_by
  employee__primary_campus__name; rows read employee.employee_number/full_name and
  bank fields through employee.teacher (nullable -> "Missing Bank Details" flagged).

--- Payslip generate (views.py:232) ---
- Import `.pdf_views` (module does not exist) -> `.payslips_pdf`
  (PayrollPayslipPdfView lives in payslips_pdf.py). This endpoint was 500ing.

=== 3. EXAMS / RESULTS AUDIT — BACKEND TRUTH ===

--- Marks entry & storage ---
- Teacher UI (MarksEntryPanel) POSTs theory via /api/exams/results/ and practical
  via /api/exams/practical/; the page never recomputes any total — it reloads
  backend state after each save.
- StudentResult.save() (exams/models.py:333) computes grade via
  GradeBand.band_for_percentage(percentage of subject maximum) and is_pass =
  obtained_marks >= exam_subject.passing_marks; is_absent forces 0/F/Fail. ✓

--- ReportCard aggregates (reportcards/models.py:147) ---
- total_marks    = sum of StudentResult.obtained_marks (THEORY ONLY), 2dp ROUND_HALF_UP
- maximum_marks  = sum of subject maxima
- percentage     = total/max*100, 2dp ROUND_HALF_UP
- grade          = GradeBand.band_for_percentage(percentage) on default scale
- is_pass        = every subject result passed
- Default scale (migration 0003): A+ [80,100), A [75,80), B+ [70,75), ... F [0,50).

--- TEST CASE: marks 80, 70, 90 (max 100 each) ---
- StudentResult per subject: 80->A+ pass, 70->B+ pass, 90->A+ pass.
- ReportCard: total_marks 240, maximum_marks 300, percentage 80.00, grade A+,
  overall_result Pass. Web UI (ReportCardsPage) renders the backend numbers only:
  "240 / 300", "80%", "A+", "Pass". ✓

=== 4. BUGS FOUND & FIXED ===

BUG-1 PAYSLIP / BANK-FILE PDF+CSV ACCESSIBLE TO ALL USERS
- payslips_pdf.py and bank_file.py used [IsAuthenticated]. Fixed to
  IsAccountantRole so only finance staff can download salary/bank data.

BUG-2 PAYSLIP PDF COMPONENT SECTIONS CRASHED (payslips_pdf.py:111)
- `f"{value:,.2f}"` on component_details dict (values are dicts). Fixed with a
  safe unwrap (name + Decimal(amount)), tolerant of legacy scalar values.

BUG-3 BANK FILE USED REMOVED teacher FIELD (bank_file.py)
- select_related("teacher"), record.teacher.* after the Employee refactor ->
  AttributeError on every export. Migrated to Employee + employee.teacher.

BUG-4 PAYSLIP GENERATE ENDPOINT IMPORTED NON-EXISTENT MODULE (views.py:248)
- from .pdf_views import PayrollPayslipPdfView -> .payslips_pdf. 500 -> works.

BUG-5 STATUS "approved" NOT A VALID CHOICE (models.py)
- Approver could set it, pay() required it, UI/admin couldn't represent it.
- Added to STATUS_CHOICES and the inline choices.

BUG-6 process/approve/pay SET A FIELD DESCRIPTOR AS A TIMESTAMP (models.py:394,412,431)
- `self.processed_at = models.DateTimeField(auto_now=True)` -> timezone.now().

BUG-7 PERCENTAGE-OF-GROSS / PERCENTAGE-OF-NET COMPONENTS WRONG BASE (compute())
- percent_gross used basic + (stale stored gross, 0 on create); percent_net used
  gross as net. Now running gross / running net. Serializer-visible structure
  totals (total_allowances) also corrected for percent-based components.

BUG-8 PAYROLL UI COULD NOT COMPLETE THE LIFECYCLE (PayrollPage.jsx)
- A single "Mark Paid" button POSTed .../process/ but no UI path existed for
  approve/pay, so records could never reach "paid" and payslips were unreachable.
- Reworked the Action cell to the real draft->process->approve->pay (+Payslip PDF),
  calling the existing /process/, /approve/, /pay/ endpoints.

BUG-9 REPORT CARD LIST/DETAIL + BATCH PDF NOT CAMPUS/INSTITUTION SCOPED
- ReportCardListView/DetailView only filtered by role/person (managers saw ALL
  schools), and ReportCardPdfBatchView(?exam=) had no scope at all. Added
  apply_campus_scope(campus_field="exam__campus_id",
  institution_field="exam__academic_year__school_id") to all three — closes the
  A->B school-isolation hole for report cards, mirroring ReportCardStatusView.

BUG-10 REPORT CARD PDF SUMMARY CONTRADICTED ITS OWN TABLE (pdf.py:116)
- The marks table summed theory + practical per subject, but the summary block
  printed theory-only report_card.total_marks/percentage/grade (the grade used
  theory-only %). Fixed: the loop accumulates combined
  total/maximum/pass, and the summary recomputes percentage (2dp ROUND_HALF_UP)
  and grade via GradeBand.band_for_percentage from the combined totals, and the
  Pass/Fail line from the table's per-row pass flags. The printed card is now
  internally consistent AND, for theory-only classes (the 80/70/90 case above),
  exactly equals the API numbers.

=== 5. PERMISSION & SCHOOL ISOLATION CHECKLIST ===
- /payroll            roles: super_admin, admin, principal, academic, accountant, hr
                       backend: IsAccountantRole everywhere; payroll_queryset scopes
                       employee__institution | primary_campus__school + campus scope;
                       Employee scope checked on structure/record create. ✓
- /exams, /report-cards roles: super_admin, admin, principal, academic, teacher
                       backend: IsAcademicMemberRole (+IsTeacherRole for status);
                       report-card list/detail/batch PDF now campus+institution scoped;
                       single PDF (_get_report_card) already role/person gate. ✓
- Strict isolation: parents/students never reach payroll; report cards restricted
  to own student/children or a teacher's students, published-only for parents.
- App-level A->B isolation: <Routes key={currentSchool?.id ?? "none"}> (App.jsx:975)
  remounts all pages when the active school changes; pages read
  currentSchool/activeCampus from context only (no cross-tenant state). ✓

=== 6. EXPORTS / PRINT / PDF CHECKLIST ===
- Payslip PDF      GET /api/payroll/records/<pk>/payslip.pdf   (accountant only) ✓
- Bank file CSV    GET /api/payroll/records/bank-file/?year=&month= (accountant only) ✓
- Payslip generate POST /api/payroll/records/<pk>/payslip/      (now functional) ✓
- Report card PDF  GET /api/report-cards/<pk>/pdf/   (role/person gated) ✓
- Report card ZIP  GET /api/report-cards/pdf/?exam=  (batch; now scoped) ✓
- All formats are generated server-side (ReportLab/CSV) from backend data —
  no client-side totals anywhere. Verified Vite production build passes.

=== 7. KNOWN DESIGN GAPS (no change made — need a product decision) ===
1. ReportCard.total_marks / percentage / grade / position are THEORY-ONLY.
   The printed PDF (BUG-10 fix) includes practical marks in its table/summary.
   For classes with practical results the web list number and printed card will
   differ; for theory-only classes they match exactly. Recommend deciding whether
   ReportCard aggregates should include practical marks (would affect ranking/
   positions) and apply consistently.
2. payroll/services.py + management/commands/seed_payroll.py still reference the
   pre-refactor teacher/structure/allowances API. They are NOT wired to any view
   (views use models/serializers directly); left as-is to avoid dead-code churn.
3. Stored net_salary is net-before-WHT by design; WHT is applied at print/export.
4. GradeBand.band_for_percentage honours its own _default_bands cache only until
   the default scale changes; acceptable for a rarely-changing lookup.

=== 8. VERIFICATION ===
- Full Vite production build: PASS (vite v8.2.1, 2451 modules, ~14s).
- python -m py_compile on all edited backend files: PASS.
- No Django runtime available in this environment, so model/view behaviour was
  verified by source audit + the numeric walkthrough above, not by running tests.