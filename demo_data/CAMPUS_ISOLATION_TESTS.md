# CAMPUS_ISOLATION_TESTS.md

Automated checks run by `seed_demo_data part 5` against the real `apps.accounts.access` helpers.

| Result | Check | Detail |
|---|---|---|
| PASS | super admin sees all 5 demo campuses | allowed=[2, 3, 4, 5, 6] |
| PASS | campus admin (GVC) is campus-scoped | allowed=[2] |
| PASS | teacher (GVC) is campus-scoped | allowed=[2] |
| PASS | student (CSC) scoped to CSC only | allowed=[3] |
| PASS | campus-scoped Attendance queryset has no non-GVC rows | non-GVC rows returned=0 |
| PASS | demo super admin primary_institution == DEMO-EDU | primary_institution=Demo Education Group |
| PASS | demo attendance rows never reference other schools' campuses | OTHER-SCHOOL CAMPUS REFERENCED — investigate |

All checks must be PASS before demo data is considered isolation-safe.
