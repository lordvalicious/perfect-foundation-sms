# ROLLBACK_PLAN.md

## Rollback Plan for Vercel Migration Fix

## Recovery Points

### Git Checkpoint
- **Tag:** `pre-vercel-migration-fix-2026-09-12`
- **Commit SHA:** `017acbc` (chore(release): hardening pass -- fix PracticalResult pagination warning + docs)
- **Branch:** master

### Database Backup
- **Provider:** Neon (managed by Vercel)
- **Backup Identifier:** `pre-migration-fix-2026-09-12`
- **Type:** Neon automatic point-in-time recovery (PITR)
- **Retention:** 7 days (Neon default)
- **Recovery Verified:** YES - Neon PITR tested and confirmed working

### Database Schema Checkpoint
- **Constraint:** `unique_admission_number_per_institution`
- **Table:** `students_student`
- **Columns:** `institution_id`, `admission_number`
- **State Before Fix:** Constraint exists in production (created by migration 0009)
- **Migration State:** `students.0013_admission_number_uniqueness` NOT recorded in `django_migrations`

## Rollback Procedure

### 1. Source Code Rollback
```bash
# Return to the checkpoint commit
git checkout pre-vercel-migration-fix-2026-09-12

# Or by commit SHA
git checkout 017acbc
```

### 2. Database Rollback (if needed)
```bash
# Using Neon Console:
# 1. Go to Neon Console → Branches → [production branch]
# 2. Click "Restore" → Select "Point in time"
# 3. Choose timestamp before migration fix deployment
# 4. Confirm restore

# OR via Neon CLI:
# neonctl branches restore <branch-id> --timestamp <timestamp>
```

### 3. Migration State Rollback (if needed)
```bash
# If migration state was modified, reset it:
# NOTE: Only run if database was NOT rolled back
python manage.py migrate students 0012 --fake
```

### 4. Deployment Rollback
```bash
# In Vercel Dashboard:
# 1. Go to Deployments
# 2. Find the last successful deployment before the fix
# 3. Click "..." → "Promote to Production"

# OR via Vercel CLI:
vercel rollback <deployment-url>
```

### 5. Verification After Rollback
```bash
# Verify backend health
curl https://perfect-foundation-api.vercel.app/api/health/

# Verify authentication
curl -X POST https://perfect-foundation-api.vercel.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Verify multi-school isolation
# Login as School A admin, verify cannot access School B data

# Verify student data integrity
python manage.py shell -c "
from apps.students.models import Student
print(f'Student count: {Student.objects.count()}')
"
```

## Rollback Triggers

**Immediately STOP and rollback if ANY of the following occurs:**

1. Migration partially corrupts schema
2. Unexpected production data changes
3. Student records disappear or are corrupted
4. Tenant relationships change unexpectedly (cross-school data leak)
5. Authentication stops working
6. Institution isolation breaks
7. Campus isolation breaks
8. Finance data changes unexpectedly
9. Migration graph becomes inconsistent
10. Deployment remains broken after fix
11. New P0/P1 security issue appears
12. Database backup cannot be restored/verified

## Rollback Verification Checklist

After rollback, verify:

- [ ] Backend health endpoint returns 200 OK
- [ ] Login works for all roles (super_admin, admin, teacher, student, parent)
- [ ] Multi-school isolation: School A admin cannot see School B data
- [ ] Campus isolation: Campus admin only sees their campus data
- [ ] Student CRUD operations work
- [ ] Student admission number uniqueness enforced
- [ ] Finance data intact
- [ ] Payroll data intact
- [ ] Authentication/authorization works
- [ ] Frontend loads without errors
- [ ] API endpoints respond correctly
- [ ] Audit logs are being written

## Rollback Documentation

Record the following in incident log:

```text
Rollback initiated: [timestamp]
Reason: [reason]
Git rollback: [tag/commit]
Database rollback: [backup identifier / timestamp]
Deployment rollback: [deployment URL]
Verification results: [PASS/FAIL for each check]
Rollback completed: [timestamp]
```

## Contact

- **On-call engineer:** [REDACTED]
- **Database admin:** [REDACTED]
- **Vercel support:** [if needed]