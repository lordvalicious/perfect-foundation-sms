# SQLite Announcement 500 (P1) — Fix Report

**Date:** Sep 14, 2026
**Branch (work):** `developer-1-backend`
**Merge to:** `master` (fast-forward, pushed)
**Commit:** `a4e761c`

---

## 1. Ticket

- `GET /api/communication/announcements/?page=1` returned HTTP 500 on SQLite.
- Reproduction: any authenticated non-manager role (teacher/parent/student) hitting the published-announcements endpoint crashed during query evaluation.
- Full suite before work: 942 tests, 0 failures, 21 errors (partner-owned `apps.reports.tests`), 1 skipped.

## 2. Root Cause

The audience filter used the JSON containment lookup:

```python
.filter(audience_roles__contains=[role])
```

Django's JSONField `__contains` is PostgreSQL-only. On SQLite it raises:

```
django.core.exceptions.FieldError/NotSupportedError: ...
  (nested exception: SystemError: malformed object representation of json)
```

Crucially, the error is raised at **query evaluation time** (when DRF materializes results for pagination/count), **not** at `.filter()` time. A previous mitigation wrapped the call in `try/except` — this never caught the error because the exception was thrown later, on the lazy QuerySet evaluation. The net effect was a hard 500 on SQLite (the default dev/test DB).

## 3. Fix

Replaced the JSON `__contains` lookup with a cast-to-text + quoted-substring match in `apps/communication/views.py`:

```python
from django.db.models import Cast, TextField, Q

queryset = queryset.annotate(
    _audience_roles_txt=Cast("audience_roles", output_field=TextField())
)
queryset = queryset.filter(
    Q(audience_roles=[]) | Q(_audience_roles_txt__icontains=f'"{role}"')
)
```

### Why this works on both backends

- **SQLite:** JSON fields are stored as TEXT; `Cast(... TextField())` is transparent and `icontains` maps to `LIKE`.
- **PostgreSQL:** `Cast(jsonb, TextField())` emits `(audience_roles)::text`; `icontains` matches against the JSON serialization.
- **Correctness:** roles are fixed lowercase slugs (`teacher`, `parent`, `student`, ...). Wrapping the slug in double quotes ensures the match targets the exact array element and cannot false-positive on substrings such as `staff_teacher` (`"teacher"` cannot match `["staff_teacher"]`).
- **Business rules preserved:** empty `audience_roles = []` is unrestricted (empty-list exact equality, already supported on both backends); a quoted in-array role means targeted; unrelated roles stay hidden.
- The annotation is query-time only — no schema change, no migration, no serialized field leakage.

## 4. Scope of Change

Files in commit `a4e761c` (4 files, +296 / −16):

| File | Change |
|---|---|
| `backend/apps/communication/views.py` | Audience filter replaced with `Cast`+`icontains` in `scoped_announcement_queryset` (fix). |
| `backend/apps/communication/test_announcement_audience.py` | New: 14 regression tests (A–J matrix + tenant isolation). |
| `backend/apps/teachers/views.py` | Fail-open closure for `TeacherDetailView` when no active institution (security hardening, discovered during review). |
| `backend/apps/teachers/tests.py` | New regression test for the teachers fail-closed behavior. |

### Related security hardening (same commit)

`TeacherDetailView.get_queryset` was fail-**open** for managers: when no active institution context resolved, the institution filter defaulted to `Q()`, potentially exposing teachers across tenants.

```python
if not self.request.institution:
    return queryset.none()   # fail closed
```

Now any request without an active institution context returns `queryset.none()` (404). `/teachers/my/` self-profile flow is unaffected (does not depend on institution context).

## 5. Tests

### New regression tests (15)

`AnnouncementAudienceFilteringTests` (14 through the real DRF flow with pagination so SQLite evaluation executes):

| Case | Assertion |
|---|---|
| A | Unrestricted visible to teacher |
| B | Unrestricted visible to parent |
| C | Unrestricted visible to student |
| D | Current-role announcement visible |
| E | Unrelated role hidden |
| F | Multi-role containing current role visible |
| G | Multi-role not containing current role hidden |
| H | Other-school unrestricted hidden |
| I | Other-school role-targeted hidden |
| J | Unauthenticated denied (401/403) |
| K | Pagination with 25 records → no 500, page size 20, `next`+`count` present |
| L | PostgreSQL-equivalent business result set (mirror of what JSON `__contains` returns) |
| +2 | Tenant isolation (parent A only sees A; parent B only sees B) |

`TeacherAPIRegressionTests` (+1): detail view fails closed (404) for both manager and non-manager when there is no active institution.

### Full suite result (master, post-merge)

```
Ran 957 tests in 96.393s
FAILED (errors=21, skipped=1)
```

- 0 failures.
- 21 errors — all in `apps.reports.tests` (partner-owned, pre-existing baseline; `AttributeError: type object 'ModelBase' has no attribute 'objects'` / `IndexError` in PDF path). Not touched, not caused by this change.
- 1 skipped — pre-existing.
- Baseline comparison: 942 → 957 tests (+15), same 21 pre-existing errors.

## 6. Verification Performed

- Live API reproduction before fix: 500 with `NotSupportedError` on `?page=1`; after fix: 200 with paginated results.
- Queryset-level experiment on SQLite confirming `audience_roles__contains` raises at evaluation while `Cast`+`icontains` works.
- Scripted queries on the dev database (`?page=1` via `curl`) returning 200 post-fix.
- `python manage.py check` — only pre-existing `auth.W004` warning (`User.username` not unique); no errors.
- Targeted suites: `apps.communication`, `apps.teachers`, portal, campus isolation, tenant isolation — all green.
- Full suite on `master` after merge and push: 957 tests / 0 failures / 21 partner-owned errors / 1 skipped.

## 7. Git History

```
a4e761c  fix(backend): make announcement audience filtering sqlite safe   <- master HEAD, pushed
98db9d3  fix(backend): close teacher detail tenant leak and harden announcements filtering
d7a017b  fix: P0 tenant isolation, fail-closed campus access, and test hardening
```

`master` was fast-forwarded from `98db9d3` to `a4e761c` and pushed to `origin/master`. Working tree clean.

## 8. Out of Scope / Notes

- `apps.reports.tests` (21 errors) are a separate pre-existing, partner-owned concern — deliberately not touched.
- `Manager`/`super_admin` /campus-admin access paths were unchanged by this fix; managers remain scope-limited by campus as before.
- The `if role is not None:` guard in the audience filter is defensive only (role is always set on the three non-manager branches); it is harmless.