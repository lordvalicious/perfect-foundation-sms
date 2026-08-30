# DATABASE_AUDIT.md

**Date:** 2026-08-30
**Owner:** Developer 1
**Method:** Source-level audit (models.py, migrations). No migrate/check run against production — read-only.

---

## 1. Inventory (Source-Level)

- **Model classes declared:** 182 (across 31 apps with models.py)
- **No models.py:** `documents`, `portal`, `search` (aggregation/utility apps)
- **Migration files:** 138 numeric
- **Apps with no migrations:** `core`, `documents`, `portal`, `search`, `dashboard` (0 files)

Per-model-count: accounts 15, hr 26, finance 19, students 16, schools 14, communication 9, reports 8, inventory 7, lms 6, core 6 (mixins only), reportcards 5, payroll 5, exams 5, white_label 4, workflow 4, events 3, helpdesk 3, hostel 3, library 3, attendance 2, discipline 2, homework 2, teachers 2, timetable 2, alumni 1, audit 1, digital_ids 1, health 1, transport 6, visitors 1, dashboard 0.

---

## 2. Base / Abstract Models (core/models.py)

| Mixin | Purpose | Used by |
|---|---|---|
| `SoftDeleteMixin` | `deleted_at`, `deleted_by` FK(User, SET_NULL) | ✅ accounts(4), finance(16), students(9), teachers(1) |
| `SoftDeleteManager` | filters `deleted_at__isnull=True` | ✅ alongside above |
| `TimeStampedMixin` | `created_at`/`updated_at` | ❌ **unused** |
| `CampusScopedMixin` | campus FK PROTECT | ❌ **unused** |
| `InstitutionScopedMixin` | institution FK CASCADE | ❌ **unused** |
| `AuditableMixin` | = SoftDelete + TimeStamped | ❌ **unused** |

**Critical finding:** The 4 tenant/timestamp mixins designed to guarantee consistent integrity are dead code. Only `SoftDeleteMixin`/`SoftDeleteManager` are imported (in accounts, finance, students, teachers).

---

## 3. Soft-Delete Coverage

- **Soft-deleted models (~30):** Staff*, Finance (16), Students (9), Teacher.
- **Rest (~152):** plain `models.Model` with `status`/`is_active` lifecycle flags instead of true soft-delete.
- **Inconsistency risk:** `AuditLog` uses `timestamp`; `User` (AbstractUser) has only `date_joined`; `AcademicYear`/`Campus` have no soft-delete markers.

---

## 4. Timestamps

- **26 models lack BOTH `created_at` and `updated_at`:** User, StaffAttendanceCorrection, RolePermission, UserPermission, AttendanceCorrection, AuditLog (uses `timestamp`), Message, ExamSubject, JournalLine, Submission, Room, AssetAssignment, Lesson/LessonCompletion/Question/QuizAttempt, Payslip, ReportCardSubject, GradeBand, Period, RouteStop, VehicleLocationLog, and others.
- **36 models lack exactly one** of the two fields.
- No model uses `TimeStampedMixin`. All timestamps are hand-rolled → drift.

---

## 5. Relationships & Constraints

- **on_delete totals (≈523 FKs):** CASCADE=204, PROTECT=149, SET_NULL=170, others 0.
  - Tenant root `School` → `Campus` is CASCADE. Child records chain through. Deleting a tenant cascades broadly (data-loss risk), though in normal ops schools are `archived` not deleted.
- **db_table:** none set anywhere (all Django default names).
- **unique_together:** none (modernized to `UniqueConstraint`).
- **UniqueConstraints:** ~50+, including:
  - `InstitutionMembership.unique_membership_per_user_institution` (accounts:230-233)
  - `AcademicYear.unique_school_year` (schools:281-285)
  - `Subject.unique_subject_code_per_institution` (schools:354-358)
  - `SubjectOffering.unique_subject_offering_per_class_per_year` (schools:750-754)
- **Gap:** `Section` (schools:223) has **no unique constraint** → duplicate section names allowed per class.

---

## 6. Indexing

- Good coverage via `Meta.indexes` and `db_index=True` (audit:85-101 four indexes; workflow `object_type`+`object_id` index; `deleted_at`/`created_at` on SoftDeleteMixin).
- No obvious missing indexes on common filter paths; should verify with real query plans in the perf pass (not run here).

---

## 7. JSON / Polymorphism

- **JSONField:** 40+ fields (schools `enabled_modules`/`working_days`, reports config, white_label, workflow states/transitions, finance, lms answers).
- **No GenericForeignKey/ContentType.**
- `workflow.WorkflowInstance` hand-rolls polymorphism via `object_type` (CharField, indexed) + `object_id` (PositiveBigIntegerField, indexed) — no FK enforcement; referential integrity is soft.

---

## 8. Migration Health

- **RunPython:** 17 occurrences / 10 files — mostly seed/data backfills:
  - `accounts/0009_populate_institution_ids` (giant cross-app backfill: 25+ models across ~8 apps)
  - `accounts/0014_create_frostfire_superadmin`
  - `communication/0004`, `events/0002`, `inventory/0002`, `library/0002`, `reportcards/0003`, `schools/0008`, `students/0006`, `transport/0002`
- **`atomic=False`:** 0. **`SeparateDatabaseAndState`:** 0.
- **Operation counts:** AddField=290, AlterField=52, RemoveField=28 — schema churn concentrated in tenancy retrofit.
- **Retrofit churn:** many `add_institution_to_all_models` / `populate_institution_ids` migrations → tenancy bolted on after initial build.

---

## 9. Tenant Root Model — `schools.School`

- Docstring: "The institution/tenant model (kept as School for API compatibility)".
- Fields: `name`, `code` (SlugField, unique, auto-generated `PF-XXXXX`), `institution_type`, `timezone`, `currency` (default PKR), `status` (active/inactive/archived), `is_paused`/`paused_at`/`paused_by`, `custom_domain` (unique, used for host resolution), `enabled_modules` (JSONField), `created_at`/`updated_at`.
- `Campus` FK `school` → CASCADE (schools:143-147).

---

## 10. Data-Integrity Blockers Found

| # | Blocker | Location | Severity |
|---|---|---|---|
| DB-1 | `accounts/0014` calls `School.objects.create(..., is_active=True)` but `School` has **no `is_active` field** (it has `status`) → `TypeError` only when DB has zero schools (guarded by `if school is None`) | accounts/migrations/0014:39-45 | Medium — latent crash on fresh DB after `School` field rename |
| DB-2 | Duplicate class `SubjectOffering` (local def:lib/2nd definition overrides 1st) | schools/models.py:364 & 699 | High (dead/redefined model; real risk of confusion/bug) |
| DB-3 | Two `SchoolSettings` models (schools:435, white_label:418) | schools + white_label | Medium (naming ambiguity) |
| DB-4 | `InstScoped/CampusScoped/TimeStamped/Auditable` mixins unused → no guarantee of audit/timestamps/tenant keys on new models | core/models.py | High (foundation debt) |
| DB-5 | `Section` lacks unique constraint | schools/models.py:223 | Medium |
| DB-6 | Hand-rolled polymorphic FKs (`workflow`) have no referential integrity | workflow/models.py:107-108 | Low/Medium |
| DB-7 | CASCADE is the plurality (204) in a multi-tenant system → accidental cascade deletion surface | all models | Medium |

---

## 11. No Modifications Made

Per audit mandate: **no production data touched, no reindex, no backfill, no cleanup runs executed.** The above is a read-only assessment for planning safe, additive migrations.