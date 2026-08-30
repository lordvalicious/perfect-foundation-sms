# ERP Database Audit Report - Master Branch

**Assessment**: Code-level inspection of Django models, migrations, and managers  
**Database**: PostgreSQL (via psycopg3)  
**ORM**: Django 6.1 built-in ORM

---

## Executive Summary

The database schema is **well-structured** with proper normalization, multi-tenancy support via institution FK, soft-delete patterns, and campus isolation at the model level. However, there are **critical gaps** in constraints, indexes, audit fields, and financial data integrity that pose risks for production use.

**Overall Database Maturity**: **Intermediate** - Production-ready with remediation.

---

## Existing Models / Tables Inventory

### Core & Tenancy (9 models)
| Model | App | Purpose | Key Fields |
|-------|-----|---------|------------|
| `School` | schools | Institution/tenant | name, code, timezone, currency, status, branding, custom_domain |
| `Campus` | schools | Physical campus | school (FK), name, address, status |
| `AcademicUnit` | schools | Division within campus | campus (FK), name, status |
| `Class` | schools | Grade level | unit (FK), name, level, status |
| `Section` | schools | Class section | class_obj (FK), name, capacity, status |
| `AcademicYear` | schools | School year | school (FK), name, start/end dates, status |
| `Term` | schools | Term/semester | academic_year (FK), name, start/end dates, status |
| `Subject` | schools | Course subject | institution (FK), name, code, type, status |
| `SubjectOffering` | schools | Subject per class/year | academic_year, class_obj, subject, teacher, status |

### Authentication & Authorization (11 models)
| Model | App | Purpose |
|-------|-----|---------|
| `User` | accounts | Custom AbstractUser with 2FA, lockout, password history |
| `InstitutionMembership` | accounts | User ↔ School with status |
| `RoleAssignment` | accounts | Membership ↔ Role |
| `StaffProfile` | accounts | Staff details with SoftDelete |
| `StaffAttendance` | accounts | Daily attendance with SoftDelete |
| `StaffAttendanceCorrection` | accounts | Audit trail for attendance changes |
| `StaffLeave` | accounts | Leave requests with workflow |
| `FailedLoginAttempt` | accounts | Brute-force tracking |
| `PasswordHistory` | accounts | Password reuse prevention |
| `UserSession` | accounts | Active session management |
| `TwoFABackupCode` | accounts | 2FA recovery codes |

### Students (8+ models)
| Model | App | Purpose |
|-------|-----|---------|
| `Student` | students | Core student record |
| `Enrollment` | students | Student ↔ Section per year |
| `Guardian` | students | Parent/guardian info |
| `StudentDocument` | students | Uploaded documents |
| `StudentTransfer` | accounts | Cross-campus transfer workflow |
| `Promotion` | students | Grade progression |
| `Alumni` | students | Graduate tracking |

### Finance (12+ models)
| Model | App | Purpose |
|-------|-----|---------|
| `FeeCategory` | finance | Fee type (tuition, transport, etc.) |
| `FeeStructure` | finance | Fee amount per class/year |
| `Invoice` | finance | Generated fee invoice |
| `InvoiceItem` | finance | Line items per invoice |
| `Payment` | finance | Payment received |
| `PaymentAllocation` | finance | Payment → Invoice allocation |
| `Concession` | finance | Discount/waiver |
| `Expense` | finance | School expenses |
| `ExpenseCategory` | finance | Expense classification |
| `JournalEntry` | finance | Double-entry accounting |
| `JournalLine` | finance | Debit/credit lines |
| `Account` | finance | Chart of accounts |

### HR & Payroll (10+ models)
| Model | App | Purpose |
|-------|-----|---------|
| `Employee` | hr | Employee record |
| `Department` | hr | Organizational unit |
| `Designation` | hr | Job title |
| `Contract` | hr | Employment contract |
| `EmployeeDocument` | hr | HR documents |
| `LeaveType` | hr | Leave categories |
| `LeaveBalance` | hr | Accrued leave |
| `LeaveRequest` | hr | Leave application |
| `PayrollStructure` | payroll | Salary components |
| `PayrollRun` | payroll | Processed payroll |
| `Payslip` | payroll | Individual payslip |

### Operations (15+ models)
| Module | Key Models |
|--------|------------|
| **Library** | Book, BookCopy, Issue, Return, Reservation, Fine |
| **Transport** | Vehicle, Driver, Route, Stop, StudentTransport |
| **Inventory** | Item, Category, Supplier, PurchaseOrder, Stock, StockMovement |
| **Assets** | Asset, AssetCategory, Maintenance, Disposal |
| **LMS** | Course, Lesson, Chapter, Assignment, Submission, Enrollment |
| **Communication** | Announcement, Message, SMSTemplate, Notification |
| **Helpdesk** | Ticket, Category, Comment, SLA |
| **Discipline** | Incident, Action, Witness |
| **Medical** | MedicalProfile, Incident, Medication, Visit |
| **Events** | Event, Registration, Attendance |
| **Sports** | Sport, Team, Coach, Player, Fixture, Result |
| **Clubs** | Club, Membership, Event |
| **FieldTrips** | Trip, Destination, Participant, Consent |
| **Documents** | Document, Version, AccessLog |
| **Visitors** | Visitor, Visit, Host |

---

## Relationships Analysis

### Strong Relationships (Proper FK + Constraints)
✅ `School → Campus` (CASCADE, related_name="campuses")  
✅ `Campus → AcademicUnit` (CASCADE, related_name="academic_units")  
✅ `AcademicUnit → Class` (CASCADE, related_name="classes")  
✅ `Class → Section` (CASCADE, related_name="sections")  
✅ `School → AcademicYear` (CASCADE, related_name="academic_years")  
✅ `AcademicYear → Term` (CASCADE, related_name="terms")  
✅ `School → Subject` (CASCADE, nullable, related_name="subjects")  
✅ `SubjectOffering` links: academic_year (PROTECT), class_obj (PROTECT), subject (PROTECT), teacher (PROTECT)  
✅ `User → InstitutionMembership` (CASCADE, related_name="memberships")  
✅ `InstitutionMembership → RoleAssignment` (CASCADE, related_name="role_assignments")  
✅ `User → StaffProfile` (OneToOne, SET_NULL)  
✅ `StaffProfile → InstitutionMembership` (OneToOne, SET_NULL)  

### Weak / Risky Relationships

| Relationship | Issue | Risk |
|--------------|-------|------|
| `School → Subject` | `institution` nullable (null=True, blank=True) | Orphan subjects possible |
| `SubjectOffering → teacher` | `teachers.Teacher` string ref, PROTECT | Teacher deletion blocked but no cascade cleanup |
| `Student → primary_campus` | Campus FK, SET_NULL | Student can exist without campus |
| `Enrollment → campus` | Campus FK but no unique constraint per student/year | Duplicate enrollments possible |
| `Invoice → student` | Student FK, CASCADE | Deleting student deletes invoices (financial data loss!) |
| `Payment → invoice` | Invoice FK, CASCADE | Same risk |
| `JournalEntry → user` | User FK, SET_NULL | Audit trail preserved but user reference lost |
| `FeeStructure → class_obj` | Class FK, CASCADE | Deleting class deletes fee structures |

### Missing Relationships
| Needed | Current State |
|--------|---------------|
| `FeeStructure ↔ FeeCategory` | Many-to-many via through model missing |
| `Concession → FeeStructure` | Only linked to student, not fee structure |
| `Payment → PaymentMethod` | No payment method model (cash, card, bank, wallet) |
| `Inventory Stock → Location` | No warehouse/bin location model |
| `Asset → AssignedTo` | No polymorphic assignment (staff/student/department) |

---

## Constraints Analysis

### Unique Constraints (Good Coverage)
✅ `School.code` (unique)  
✅ `InstitutionMembership` (user, institution)  
✅ `RoleAssignment` (membership, role)  
✅ `StaffProfile` (institution, employee_number)  
✅ `StaffAttendance` (staff, date)  
✅ `AcademicYear` (school, name)  
✅ `Subject` (institution, code)  
✅ `SubjectOffering` (academic_year, class_obj, subject)  
✅ `ClassTeacher` (section, academic_year)  
✅ `SubjectGroup` (institution, code)  
✅ `Permission.codename` (unique)  
✅ `RolePermission` (role, permission, institution)  
✅ `UserPermission` (user, permission, institution)  

### Missing Unique Constraints (Data Integrity Risks)
| Model | Missing Constraint | Risk |
|-------|-------------------|------|
| `Enrollment` | (student, academic_year, status="active") | Student in multiple sections same year |
| `Invoice` | (student, fee_category, academic_year, term) | Duplicate invoices |
| `Payment` | (invoice, amount, payment_date, reference) | Duplicate payments |
| `Concession` | (student, fee_category, academic_year) | Overlapping concessions |
| `LeaveRequest` | (staff, start_date, end_date) overlapping | Overlapping leave |
| `PayrollRun` | (payroll_structure, period_start, period_end) | Duplicate payroll runs |
| `Payslip` | (payroll_run, employee) | Duplicate payslips |

### Check Constraints (Missing)
| Model | Needed Check | Current |
|-------|--------------|---------|
| `Invoice` | `total_amount >= 0` | None |
| `Payment` | `amount > 0` | None |
| `JournalLine` | `debit >= 0 AND credit >= 0 AND (debit > 0 XOR credit > 0)` | None |
| `JournalEntry` | Sum(debits) = Sum(credits) | Application-level only |
| `Enrollment` | `end_date >= start_date` | None |
| `LeaveRequest` | `end_date >= start_date` | None |

---

## Indexes Analysis

### Existing Indexes (Good)
✅ `FailedLoginAttempt` (user, attempted_at), (ip_address, attempted_at)  
✅ `PasswordHistory` (user, created_at)  
✅ `UserSession` (user, is_current), (expires_at)  
✅ `TwoFABackupCode` (user, used_at)  
✅ `StaffAttendanceCorrection` (attendance, -corrected_at), (staff, corrected_by)  
✅ `StudentTransfer` (student, status), (status, requested_at)  
✅ `RolePermission` (role, institution)  
✅ `UserPermission` (user, institution)  
✅ `AcademicCalendar` (institution, start_date, end_date), (campus, start_date, end_date), (academic_year, start_date)  

### Missing Critical Indexes
| Model | Missing Index | Query Pattern |
|-------|---------------|---------------|
| `Invoice` | (student, status, issue_date) | Student portal invoice list |
| `Invoice` | (institution, status, due_date) | Overdue report |
| `Payment` | (invoice, status) | Payment allocation |
| `Payment` | (student, payment_date) | Student payment history |
| `Enrollment` | (student, academic_year, status) | Active enrollment lookup |
| `Enrollment` | (section, academic_year, status) | Class roster |
| `Student` | (institution, primary_campus, status) | Campus student list |
| `StaffProfile` | (institution, primary_campus, status) | Campus staff list |
| `JournalEntry` | (institution, entry_date, status) | Financial reports |
| `JournalLine` | (account, entry_date) | Account ledger |
| `Concession` | (student, fee_category, academic_year, status) | Concession validation |

---

## Soft Delete Pattern Analysis

### Models Using SoftDeleteMixin + SoftDeleteManager
✅ `StaffProfile`  
✅ `StaffAttendance`  
✅ `StaffAttendanceCorrection`  
✅ `StaffLeave`  

### Models NOT Using Soft Delete (Should Consider)
| Model | Reason |
|-------|--------|
| `Student` | Legal record retention |
| `Invoice` | Financial audit requirement |
| `Payment` | Financial audit requirement |
| `JournalEntry` | Accounting integrity |
| `Employee` | HR compliance |
| `PayrollRun` | Payroll audit |
| `Concession` | Audit trail |

### Soft Delete Implementation Issues
- `SoftDeleteMixin` uses `status` field ("active"/"inactive") not `deleted_at` timestamp
- `SoftDeleteManager` filters `status="active"` but **raw queries bypass this**
- No `deleted_at` timestamp = cannot query "deleted this week"
- No cascade soft-delete for related objects

---

## Audit Fields Coverage

### Models WITH Full Audit Fields (created_at, updated_at)
✅ Most models have both (auto_now_add, auto_now)

### Models WITHOUT Updated_At (Risk)
| Model | Missing |
|-------|---------|
| `FailedLoginAttempt` | Only `attempted_at` (auto_now_add) |
| `PasswordHistory` | Only `created_at` |
| `TwoFABackupCode` | Only `created_at`, `used_at` |
| `UserSession` | Has `last_activity_at` (auto_now) but no `updated_at` |

### Models WITHOUT Created_By / Updated_By (Accountability Gap)
| Critical Models Missing Actor Tracking |
|----------------------------------------|
| `Invoice` - who created/modified? |
| `Payment` - who recorded? |
| `JournalEntry` - who posted? |
| `Concession` - who approved? |
| `FeeStructure` - who set fees? |
| `PayrollRun` - who processed? |
| `StudentTransfer` - has `approved_by` but not `created_by` |

---

## Duplicate-Prone Fields

| Model | Field | Risk |
|-------|-------|------|
| `School` | `code` | Unique constraint exists ✅ |
| `User` | `email` | Unique constraint exists ✅ |
| `User` | `username` | Unique (from AbstractUser) ✅ |
| `Student` | `admission_number` | **NO unique constraint per institution!** |
| `StaffProfile` | `employee_number` | Unique per institution ✅ |
| `Subject` | `code` | Unique per institution ✅ |
| `Invoice` | `invoice_number` | **NO unique constraint per institution!** |
| `Payment` | `receipt_number` | No field exists |
| `PayrollRun` | `run_number` | No field exists |
| `Asset` | `asset_tag` | No field exists |

---

## Potential Scalability Problems

| Issue | Impact | Affected Tables |
|-------|--------|-----------------|
| **No partitioning** | Large tables (Attendance, Payment, JournalLine) will slow down | `StudentAttendance` (not seen but likely), `Payment`, `JournalLine` |
| **No read replicas configured** | All reads hit primary | All |
| **JSONField overuse** | `School.enabled_modules`, `SchoolSettings.working_days` - not queryable | `School`, `SchoolSettings` |
| **Missing composite indexes** | Multi-column filter queries slow | See Missing Indexes above |
| **No materialized views** | Complex reports (GPA, fee summary) run slow | Would need `Dashboard` aggregation tables |
| **Soft delete without partial index** | `status="active"` filter scans deleted rows | All soft-delete models |
| **No connection pooling in base config** | `CONN_MAX_AGE=600` but no PgBouncer | Production only |

---

## Migration History Risks

### Observed Migration Patterns
- Many apps have `management/commands` for data fixes
- `fix_migrations*.bat` scripts exist - indicates migration conflicts
- `phase18_audit.py`, `phase19_qa.py` suggest schema validation scripts
- Duplicate `SubjectOffering` model in `schools/models.py` (lines 401-470 and 736-819) - **CODE DUPLICATION IN MODELS**

### Specific Migration Risks
1. **Duplicate SubjectOffering** - Two identical model definitions in same file (lines 401-470 and 736-819). One will cause migration conflict.
2. **School model has duplicate `__str__`** (lines 121-122 and 140-141) and duplicate `logo/favicon` fields (lines 57-66 as tuples with trailing commas, and again in `SchoolSettings`).
3. **Tuple fields in School model** - `logo = models.ImageField(...),` (trailing comma makes it a tuple!) - this will cause migration errors.
4. **`SchoolSettings` duplicates branding fields** already on `School` model.

---

## Data Integrity Risks Summary

| Risk Level | Count | Examples |
|------------|-------|----------|
| **Critical** | 4 | Duplicate invoice numbers, duplicate admission numbers, missing journal balance constraint, CASCADE delete on financial data |
| **High** | 8 | Missing unique constraints on enrollments, concessions, payslips; nullable institution on Subject |
| **Medium** | 12 | Missing indexes, missing check constraints, soft delete pattern inconsistency |
| **Low** | 6 | Missing audit fields (created_by), JSONField queryability |

---

## Recommended Database Remediation (Do Not Implement - Audit Only)

### Immediate (Pre-Production)
1. **Fix duplicate `SubjectOffering` model definition** in `schools/models.py`
2. **Fix tuple fields** in `School` model (remove trailing commas on lines 57-66, 82-86)
3. **Add unique constraint** on `Student.admission_number` per institution
4. **Add unique constraint** on `Invoice.invoice_number` per institution
5. **Change `Invoice.student` and `Payment.invoice` to PROTECT** (not CASCADE)
6. **Add check constraint** `JournalEntry` balance validation

### Short-term
7. Add all missing indexes from table above
8. Add `created_by`/`updated_by` FK to User on all financial/HR models
9. Standardize soft delete to use `deleted_at` timestamp + partial index
10. Add composite unique constraints for enrollments, concessions, payslips

### Medium-term
11. Implement table partitioning for `Payment`, `JournalLine`, attendance tables
12. Add read replica configuration
13. Create materialized views for dashboard/reports
14. Add database-level audit triggers for financial tables

---

## Schema Diagram (Logical)

```
School (1) ─────< Campus (1) ─────< AcademicUnit (1) ─────< Class (1) ─────< Section
    │                                                      │
    ├────< AcademicYear ────< Term                        │
    │                                                      │
    ├────< Subject ────────────────────────────────────────┤
    │                     SubjectOffering <────────────────┘
    │
    ├────< User (via InstitutionMembership)
    │         │
    │         ├────< RoleAssignment
    │         ├────< StaffProfile ──< StaffAttendance
    │         │                            └──< StaffAttendanceCorrection
    │         │                            └──< StaffLeave
    │         ├────< TeacherProfile
    │         ├────< StudentProfile ──< Enrollment
    │         │                            └──< StudentDocument
    │         ├────< GuardianProfile ──< Student (via Guardian.students)
    │         └────< UserSession
    │
    ├────< FeeCategory
    ├────< FeeStructure ──< Invoice ──< InvoiceItem
    │                            └──< Payment ──< PaymentAllocation
    │                            └──< Concession
    │
    ├────< JournalEntry ──< JournalLine
    │         └──< Account (Chart of Accounts)
    │
    ├────< Employee ──< Contract
    │         └──< LeaveRequest
    │         └──< PayrollStructure ──< PayrollRun ──< Payslip
    │
    ├────< Book ──< BookCopy ──< Issue/Return
    ├────< Vehicle ──< Route ──< Stop
    ├────< Item ──< Stock ──< StockMovement
    ├────< Asset ──< Maintenance
    ├────< Course ──< Lesson ──< Assignment
    └────< Event/Ticket/Incident/Visit/etc.
```