# PHASE 46 — Staff Campus Assignment / Staff Data Remediation Report

**Phase:** 46
**Verdict:** PASS
**Target account (STAFF_01):** `DI-EMP-0001` (user id 1157, "But Ali", Default Institution)
**Date:** 2026-09-22
**Production region/environment:** primary (deployed backend, Neon Postgres, ap-southeast-1)

---

## 1. Objective

Resolve the production data-assignment blocker where STAFF_01 had no usable campus
assignment (`/api/auth/active-campus/` → `{"campus": null, "campuses": []}`), the staff
dashboard was empty/zero, and earlier StaffProfile creation attempts were blocked by the
`unique_staff_employee_number_per_institution` constraint (which includes soft-deleted rows).

Target state achieved:

- STAFF_01 → correct institution (Default Institution / school 1) ✓
- Active StaffProfile with correct campus (campus 7 "SS", Default Institution) ✓
- Non-zero dashboard (students 6 active, 2 classes, 2 sections, 8 enrollments) ✓
- Cross-campus & cross-institution isolation intact ✓
- No arbitrary deletion, no employee-number change, no constraint bypass ✓

---

## 2. Investigation (read-only)

| Source | Finding |
|---|---|
| `GET /api/auth/me/` (DI session) | user 1157, role `staff`, membership 1157 → institution 1 "Default Institution" |
| `GET /api/staff/me/` | StaffProfile **id 97** returned: employee_number `DI-EMP-0001`, `primary_campus: null`, `membership: null` |
| `GET /api/auth/active-campus/` | `{"campus": null, "campuses": []}` |
| `GET /api/schools/campuses/` | Campus **7 "SS"** (Sialkot) belongs to school 1 "Default Institution" (active; 2 classes, 2 sections, 8 students). Pilot suggestion of campus 9 "Bloom" was **rejected as verified cross-institution**: campus 9 belongs to school 4 "Springfield Academy". |
| Read-only production DB (Django ORM, pulled prod env; no secrets printed) | StaffProfile **97 is SOFT-DELETED** (`deleted_at` set 2026-09-06T11:37:18Z, minutes after creation), `institution_id=NULL`, `membership_id=NULL`, `primary_campus_id=NULL`. It is the **only** row for user 1157 and for employee_number `DI-EMP-0001`. |

Root cause:

- The only StaffProfile row (id 97) was **soft-deleted** and unlinked (NULL institution /
  membership / primary campus).
- `StaffProfile.objects` uses `SoftDeleteManager` (excludes soft-deleted rows), so
  `GET /api/staff/<pk>/` and the staff list 404'd it; the reverse OneToOne accessor used by
  `/api/staff/me/` still surfaced it (base-manager semantics), which is why `/me` returned 200.
- With `primary_campus = NULL` and a `staff` role, `user_allowed_campus_ids()` (access.py)
  yields an empty set → `active-campus` empty and every dashboard scope collapsed to zero.

Why creation was previously blocked (Phase 40 evidence): attempts to create a new profile
under the same (institution, employee_number) collided via the unique constraint; the
correct resolution is to **restore and relink the existing record** rather than create a
duplicate or delete anything.

---

## 3. Remediation (user-approved, minimal)

Operation executed through the application's Django ORM (no raw SQL), on **one row**:

```python
p = StaffProfile.objects.all_with_deleted().get(id=97)   # only row for user 1157
p.institution_id  = 1      # Default Institution
p.membership_id   = 1157   # user 1157's active membership (institution 1)
p.primary_campus_id = 7    # "SS" campus (school 1, active)
p.restore()                # soft-delete mixin: clears deleted_at / deleted_by
p.save()
```

Pre-checks (all passed, read-only): no other row shares `(institution=1,
employee_number='DI-EMP-0001')`; membership 1157 → user 1157 / institution 1 / active;
campus 7 → school 1 / active; profile 97 is the only StaffProfile for user 1157.

Safety properties: no records deleted, no employee_number/name/phone/email changed, no
constraint bypassed, reversible (re-soft-delete clears the same row), transaction-wrapped.

---

## 4. Before → After (production API evidence)

| Endpoint | Before | After |
|---|---|---|
| `GET /api/auth/active-campus/` (DI session) | `{"campus": null, "campuses": []}` | `{"campus": {"id": 7, "name": "SS"}, "campuses": [{"id": 7, "name": "SS"}]}` |
| `GET /api/staff/me/` | profile 97, campus/membership null | profile 97, `primary_campus: 7`, `membership: 1157` |
| `GET /api/staff/?search=DI-EMP-0001` (own context) | count 0 | count 1 |
| `GET /api/dashboard/overview/` | empty/zero (0-scope) | `{"students":{"total":6,"active":6},"campuses":1,"classes":2,"sections":2,"enrollments":8}` |
| `GET /api/staff/97/` (super_admin, Default ctx) | 404 (soft-deleted filter) | HTTP 200, full profile |
| `GET /api/students/?campus=9` (DI session) | n/a | HTTP 403 — **cross-campus denied** (Springfield campus out of scope) |

---

## 5. Testing

- No application code was changed (data remediation only).
- Regression: `python manage.py test apps.accounts --settings=config.settings.test`
  → **Ran 291 tests … OK** (exit 0), including campus/isolation and role-security suites.
- Existing isolation invariants confirmed via API (cross-campus 403 above).

---

## 6. Authorization evidence

- Writes performed as user-approved operations on the production DB, restricted to
  `accounts_staffprofile` row 97 (3 fields + soft-delete markers).
- Campus assignment verified to be within the user's own school: campus 7 → school
  (institution) 1 = Default Institution = the user's active membership institution.
- Access control unchanged: `staff` role still resolves to own-campus-only scope
  (`IsAdminOrReadOnly` permissions untouched; no role/membership changes).

---

## 7. Observations (out of scope, not changed)

1. `/api/staff/me/` surfaces a **soft-deleted** profile via the reverse OneToOne accessor
   (base manager) while list/detail 404 it. Behavior is inconsistent but preserved; consider
   a follow-up to make `/me` honor soft-delete.
2. `SA-EMP-0001` (teacher, Springfield) has a teacher profile with `campus: null` and an
   empty campus list while `SA-EMP-0003/0004` resolve campus 9. Teacher remediation is
   outside Phase 46 (staff) scope — flagged for a future phase.
3. STAFF_01's `active_campus_id` session selection was null; it is now persisted to campus 7.

---

## 8. Deliverables

- `PHASE_46_STAFF_PRODUCTION_MATRIX.csv` — account-level before/after matrix.
- This report.

No credentials/tokens were written to or printed in any file.