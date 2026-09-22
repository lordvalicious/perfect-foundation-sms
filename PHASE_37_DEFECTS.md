# PHASE 37 — DEFECTS REPORT

## Critical Defects

| ID | Module | Endpoint | Severity | Description | Evidence |
|----|--------|----------|----------|-------------|----------|
| D001 | Dashboard | `/api/dashboard/overview/` | HIGH | ADMIN timeout >15s (12.2s avg); STAFF timeout >15s (12.5s avg) | AD-001, STA-001 |
| D002 | Dashboard | `/api/dashboard/summary/` | HIGH | Returns 404 for all roles | Multiple |
| D003 | Timetable | `/api/timetable/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D004 | LMS | `/api/lms/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D005 | Library | `/api/library/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D006 | Transport | `/api/transport/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D007 | Inventory | `/api/inventory/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D008 | Helpdesk | `/api/helpdesk/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D009 | Visitors | `/api/visitors/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D010 | Digital IDs | `/api/digital-ids/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D011 | Workflow | `/api/workflow/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D012 | Hostel | `/api/hostel/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D011 | Health Records | `/api/health-records/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D012 | LMS | `/api/lms/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D012 | Portal | `/api/portal/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D013 | Workflow | `/api/workflow/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D013 | Helpdesk | `/api/helpdesk/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D014 | Visitors | `/api/visitors/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D014 | Digital IDs | `/api/digital-ids/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D014 | SAAS | `/api/saas/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D015 | Audit Logs | `/api/audit-logs/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D015 | Settings | `/api/settings/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D016 | Branding | `/api/branding/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D016 | Health | `/api/health/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D017 | Audit Logs | `/api/audit-logs/` | HIGH | Endpoint returns 404 for all roles | Multiple |
| D017 | Reports Root | `/api/reports/` | HIGH | Returns 404 (child endpoints work) | E111 |
| D018 | Finance Root | `/api/finance/` | HIGH | Returns 404 (child endpoints work) | E070 |
| D019 | Accounts Me | `/api/accounts/me/` | MEDIUM | Returns 404 for all roles | E006 |
| D020 | Accounts Roles | `/api/accounts/roles/` | MEDIUM | Returns 404 for all roles | E007 |
| D019 | Accounts Me | `/api/accounts/me/` | MEDIUM | Returns 404 for all roles | E006 |
| D020 | Accounts Roles | `/api/accounts/roles/` | MEDIUM | Returns 404 for all roles | E007 |
| D020 | Dashboard Summary | `/api/dashboard/summary/` | HIGH | Returns 404 for all roles | Multiple |
| D021 | AI Ask | `/api/ai/ask/` | MEDIUM | Returns 405 (POST only) | E141 |
| D022 | AI Insights | `/api/ai/insights/*` | MEDIUM | Returns 403 for all tested | Multiple |
| D021 | Dashboard Finance | `/api/dashboard/finance/` | LOW | SUPER_ADMIN 6.6s; ADMIN 12.2s | E171 |
| D022 | Dashboard Finance Breakdown | `/api/dashboard/finance/breakdown/` | LOW | SUPER_ADMIN 6.6s; ADMIN 12.2s | E172 |
| D022 | ADMIN Dashboard | `/api/dashboard/overview/` | HIGH | ADMIN timeout 12.2s avg | AD-001 |
| D023 | STAFF Dashboard | `/api/dashboard/overview/` | HIGH | STAFF timeout 12.5s avg | STA-001 |
| D023 | ADMIN Students | `/api/students/` | HIGH | ADMIN timeout 12.7s avg | AD-002 |
| D024 | AI Ask | `/api/ai/ask/` | MEDIUM | Returns 405 (POST only) | E141 |
| D024 | AI Insights | `/api/ai/insights/*` | MEDIUM | Returns 403 for all tested | Multiple |
| D024 | Dashboard Finance Breakdown | `/api/dashboard/finance/breakdown/` | LOW | SUPER_ADMIN 6.6s; ADMIN 12.2s | E172 |
| D024 | ADMIN Dashboard | `/api/dashboard/overview/` | HIGH | ADMIN timeout 12.2s avg | AD-001 |
| D025 | STAFF Dashboard | `/api/dashboard/overview/` | HIGH | STAFF timeout 12.5s avg | STA-001 |
| D025 | ADMIN Students | `/api/students/` | HIGH | ADMIN timeout 12.7s avg | AD-002 |
| D025 | AI Ask | `/api/ai/ask/` | MEDIUM | Returns 405 (POST only) | E141 |
| D026 | AI Insights | `/api/ai/insights/*` | MEDIUM | Returns 403 for all tested | Multiple |

## Summary Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 20 |
| MEDIUM | 6 |
| LOW | 2 |
| **TOTAL** | **28** |

## Root Cause Analysis

| Category | Defects | Root Cause |
|----------|---------|------------|
| Missing Endpoints (404) | 20 | Endpoints not implemented in backend or URL routing missing |
| Dashboard Timeout | 3 | Slow queries in `_institution_overview_counts()` |
| Wrong HTTP Method | 2 | AI Ask expects POST, AI Ask endpoint 405 |
| Authorization Issues | 3 | AI Insights returns 403, Finance root 404 |
| Performance | 3 | Dashboard/Students/Reports slow for ADMIN |

## Recommendations

1. **Implement Missing Endpoints**: 20 endpoints return 404 - need backend implementation
2. **Fix Dashboard Timeouts**: Optimize `_institution_overview_counts()` with aggregation queries
3. **Fix AI Endpoints**: AI Ask should accept POST; AI Insights need proper role checks
4. **Fix Dashboard Summary**: Implement `/api/dashboard/summary/` endpoint
5. **Fix Finance Root**: Implement `/api/finance/` parent endpoint