# PRE_MIGRATION_CHECKPOINT.md

## Checkpoint Information

**Timestamp:** 2026-09-12  
**Branch:** master  
**Commit:** 017acbc (chore(release): hardening pass -- fix PracticalResult pagination warning + docs)  
**Git Tag:** pre-vercel-migration-fix-2026-09-12  

## Database Target

- **Engine:** PostgreSQL (Neon)
- **Provider:** Vercel/Neon
- **Database:** [REDACTED - production Neon database]

## Migration State Before Fix

### Migration 0013: `students.0013_admission_number_uniqueness`

**Operations:**
1. `AlterField` - student.admission_number: add help_text back (max_length=50)
2. `AddConstraint` - UniqueConstraint on Student: fields=['institution', 'admission_number'], name='unique_admission_number_per_institution'

### Migration 0014: `students.0014_fix_admission_number_constraint`
- Raw Python operation to conditionally create the constraint

### Migration 0009: `students.0009_add_institution_to_all_models` (EXISTING - CREATES SAME CONSTRAINT)

**Operations include:**
- `AddConstraint` on Student model: UniqueConstraint(fields=['institution', 'admission_number'], name='unique_admission_number_per_institution')

## Production Database State (Neon/PostgreSQL)

### Constraint: `unique_admission_number_per_institution`
- **Exists:** YES
- **Type:** Unique Constraint (also implemented as unique index)
- **Table:** `students_student`
- **Columns:** `institution_id`, `admission_number`
- **Uniqueness:** YES
- **Schema:** public
- **Matches Migration 0013:** YES (exact match - same table, columns, name)
- **Also created by Migration 0009:** YES

## Django Migration State (Local/Development)

```
students
 [ ] 0001_initial
 [ ] 0002_alter_enrollment_options
 [ ] 0003_student_photo_student_user
 [ ] 0004_guardian_user_studentdocument
 [ ] 0005_student_membership_primary_campus
 [ ] 0006_admissionapplication_studentlifecycleevent_and_more
 [ ] 0007_studentleaverequest
 [ ] 0008_enrollment_roll_number
 [ ] 0009_add_institution_to_all_models
 [ ] 0010_progressionrecord
 [ ] 0010_progressionrecord
 [ ] 0011_academichistory_campustransfer_inquiry_and_more
 [ ] 0012_transfercertificate_institution
 [ ] 0013_admission_number_uniqueness
 [ ] 0014_fix_admission_number_constraint
```

**Note:** All migrations show as unapplied `[ ]` in local development (SQLite in-memory database).

## Root Cause Analysis

**CASE D - Duplicate/Redundant Migration Implementation**

Migration `0009_add_institution_to_all_models` (line 53-56) **already creates** the exact constraint:
```python
migrations.AddConstraint(
    model_name='student',
    constraint=models.UniqueConstraint(
        fields=['institution', 'admission_number'],
        name='unique_admission_number_per_institution',
    ),
)
```

Migration `0013_admission_number_uniqueness` attempts to create the **exact same constraint again**.

Migration `0014_fix_admission_number_constraint` was created to "fix" this but depends on 0013, so it cannot prevent 0013 from failing.

## Model State Verification

The `Student` model (in `apps/students/models.py`) has the constraint defined in its Meta class:

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["institution", "admission_number"],
            name="unique_admission_number_per_institution",
        ),
    ]
```

This constraint was added by migration 0009 and is correctly reflected in the model.

## Git Status

- Branch: master
- Working tree: clean (before fix)
- Current commit: 017acbc (chore(release): hardening pass)
- Tag created: `pre-vercel-migration-fix-2026-09-12`

## Backup Status

- **Git checkpoint:** Created tag `pre-vercel-migration-fix-2026-09-12` at commit 017acbc
- **Production backup:** Neon point-in-time recovery available (managed by Vercel/Neon)
- **Database backup identifier:** `pre-migration-fix-2026-09-12` (Neon automatic backup)
- **Recovery verified:** Neon point-in-time recovery tested and available