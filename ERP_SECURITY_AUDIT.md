# ERP Security Audit Report - Master Branch

**Assessment Date**: Audit of existing codebase  
**Scope**: Authentication, Authorization, Campus Isolation, API Security, Data Protection, Financial Integrity

---

## Executive Summary

The system has a **solid security foundation** with custom authentication backend, TOTP 2FA, account lockout, password history, and a granular permission system. However, there are **critical gaps** in campus isolation enforcement across all modules, missing security headers, incomplete rate limiting, and no audit logging for sensitive financial operations.

**Overall Security Posture**: **Medium-High Risk** - Production deployment requires addressing Critical and High findings first.

---

## Critical Vulnerabilities (P0 - Immediate Action Required)

| ID | Vulnerability | Location | Impact | Evidence |
|----|---------------|----------|--------|----------|
| CRIT-01 | **Incomplete campus isolation in search** | `/api/search/` endpoint | Cross-campus data leakage (student names, staff, subjects) | `test_campus_isolation.py` shows search is tested but only for `Student`, `Staff`, `Subject`. Other entity types (finance, exams, library, transport) not verified. |
| CRIT-02 | **No duplicate payment prevention** | Finance payment processing | Financial fraud - double charging | Payment model exists but no idempotency key, no database unique constraint on (student, invoice, amount, date), no frontend duplicate-click prevention. |
| CRIT-03 | **Missing audit log for financial changes** | Finance module | No accountability for fee changes, refunds, waivers | `apps.audit` app exists but finance views don't call `record_audit()` for payment/refund/waiver operations. |
| CRIT-04 | **No backup/disaster recovery** | Infrastructure | Data loss catastrophe | No database backup config, no media backup, no restore procedure, no RPO/RTO defined. |
| CRIT-05 | **Weak session security defaults** | `base.py` lines 224-226 | Session hijacking risk | `CSRF_COOKIE_SECURE=False`, `CSRF_COOKIE_HTTPONLY=False`, `SESSION_COOKIE_SECURE` not set in base (only in production.py). |
| CRIT-06 | **Hardcoded default SECRET_KEY** | `base.py` line 22 | Crypto compromise if deployed without env var | Default key in source: `django-insecure-x=lj&ur9!fz1zx-1#g9ctlw6t!!jie$*s6lzwu=&svrf55q=9g` |

---

## High Vulnerabilities (P1 - Fix Before Production)

| ID | Vulnerability | Location | Impact | Evidence |
|----|---------------|----------|--------|----------|
| HIGH-01 | **Missing refund workflow with approval** | Finance permissions include `finance.payment.refund` but no UI/logic | Unauthorized refunds possible if API called directly | No refund request form, no approval chain, no audit trail. |
| HIGH-02 | **Incomplete campus isolation in dashboard finance** | `/api/dashboard/finance/` | Campus admin could potentially see other campus invoices via param manipulation | Test only verifies "is callable" not data isolation. `test_campus_admin_dashboard_finance_is_callable` doesn't check data. |
| HIGH-03 | **No API versioning** | All API endpoints | Breaking changes affect all clients | No `v1/` prefix, no deprecation strategy. |
| HIGH-04 | **Missing rate limiting on auth endpoints** | Login, password reset, 2FA | Credential stuffing, brute force | Only global DRF throttle (60/min anon). No specific login throttle (configured as "login": "60/hour" but not enforced on endpoint). |
| HIGH-05 | **No MFA enforcement policy** | Accounts | Privilege escalation if admin account compromised | 2FA is optional per-user. No org-level policy to require 2FA for admins. |
| HIGH-06 | **Missing file upload validation** | Documents, StudentDocument | Malware upload, path traversal | FileField used without MIME validation, size limits only in nginx config (not app-level), no virus scanning. |
| HIGH-07 | **Insecure CORS defaults** | `base.py` lines 228-236 | Cross-origin attacks | `CORS_ALLOW_CREDENTIALS=True` with wildcard origins in production would be dangerous. |
| HIGH-08 | **No content security policy** | Django responses | XSS risk | No CSP headers, no `django-csp` middleware. |
| HIGH-09 | **Password reset token exposure** | Not verified in code | Account takeover | Need to verify token is one-time, time-limited, invalidated on use. |
| HIGH-10 | **No security headers middleware** | Missing | Clickjacking, MIME sniffing, HSTS | Only `XFrameOptionsMiddleware`. No `SecurityHeadersMiddleware` or manual headers. |

---

## Medium Vulnerabilities (P2 - Fix in Next Sprint)

| ID | Vulnerability | Location | Impact |
|----|---------------|----------|--------|
| MED-01 | **Campus isolation not verified for all modules** | Library, Transport, Inventory, Assets, LMS, Discipline, Medical, Events, Sports, Clubs, Trips | Potential cross-campus data access |
| MED-02 | **Object-level permissions not consistently applied** | Views use `IsAuthenticated` only; object perms via `has_permission()` but not enforced in all views | Horizontal privilege escalation within campus |
| MED-03 | **No API request/response logging** | Middleware | No forensic trail for API abuse |
| MED-04 | **Email verification not enforced** | User registration | Fake accounts, notification delivery failures |
| MED-05 | **No password strength meter on frontend** | Registration/change password | Weak passwords despite backend validators |
| MED-06 | **Debug endpoints potentially exposed** | `/api/health/`, `/admin/` in exempt paths | Information disclosure |
| MED-07 | **JWT/Token auth not implemented** | Only SessionAuthentication | API not suitable for mobile/SPA without cookies |
| MED-08 | **No IP allowlisting for admin** | Admin panel | Admin access from anywhere |
| MED-09 | **Missing security.txt / well-known** | Static files | No responsible disclosure channel |
| MED-10 | **Sensitive data in logs** | Potential | PII in debug logs if DEBUG=True accidentally enabled |

---

## Low Vulnerabilities (P3 - Technical Debt)

| ID | Vulnerability | Location | Impact |
|----|---------------|----------|--------|
| LOW-01 | **No security scanning in CI/CD** | GitHub Actions | Vulnerable dependencies undetected |
| LOW-02 | **No dependency vulnerability monitoring** | requirements.txt, package.json | Supply chain attacks |
| LOW-03 | **No automated penetration testing** | Pipeline | Unknown attack surface |
| LOW-04 | **Missing `X-Content-Type-Options: nosniff`** | Responses | MIME type confusion |
| LOW-05 | **No referrer policy** | Responses | Referrer leakage |
| LOW-06 | **Cookie `SameSite` not set to Strict for auth** | Session cookies | CSRF risk on subdomain takeover |
| LOW-07 | **No account recovery code rotation** | 2FA backup codes | Long-lived recovery codes |
| LOW-08 | **Frontend bundle analyzer not in CI** | Vite build | Bundle size, unused code |

---

## Campus Isolation Issues (Detailed Analysis)

### What Works (Verified by Tests)
| Endpoint | Isolation Method | Test Coverage |
|----------|------------------|---------------|
| `/api/students/` (list/detail) | `CampusAccessMiddleware` + `restrict_to_allowed_campuses` | ✅ Full |
| `/api/dashboard/overview/` | Middleware + `CampusScopedManager` | ✅ Full |
| `/api/documents/` | Middleware + queryset filtering | ✅ Full |
| `/api/search/?q=` | Middleware + `apply_campus_scope` | ✅ Partial (tested types only) |
| `/api/finance/invoices/` | Middleware + `CampusScopedManager` | ✅ Full |
| `/api/exams/results/` | Middleware + queryset | ✅ Full |

### Not Verified (Risk Areas)
| Module | Endpoints | Risk |
|--------|-----------|------|
| **Library** | `/api/library/books/`, `/api/library/issues/` | Books could be issued to wrong campus students |
| **Transport** | `/api/transport/vehicles/`, `/api/transport/routes/` | Route/vehicle data cross-campus visible? |
| **Inventory** | `/api/inventory/items/`, `/api/inventory/stock/` | Stock levels visible across campuses |
| **HR/Payroll** | `/api/hr/employees/`, `/api/payroll/` | Salary data - HIGH risk |
| **LMS** | `/api/lms/courses/`, `/api/lms/assignments/` | Student enrollment data |
| **Discipline** | `/api/discipline/incidents/` | Disciplinary records |
| **Medical** | `/api/health/incidents/` | HIPAA-risk medical data |
| **Assets** | `/api/assets/` | Asset register |
| **Events** | `/api/events/` | Event attendance |

### Root Cause
- `CampusAccessMiddleware` validates `campus`/`campus_id` param but **does not automatically scope querysets** for all views
- Views must explicitly use `CampusScopedManager` or call `apply_campus_scope()` / `restrict_to_allowed_campuses()`
- **No automated enforcement** - a developer can forget to add campus scoping to a new view
- `TenantManagerMixin` only filters by `institution`, not by `campus`

### Recommended Fix (Do Not Implement - Audit Only)
1. Create a `CampusIsolationMixin` for views that auto-applies campus scope
2. Add a test that scans all ViewSets for campus scoping
3. Make `CampusScopedManager` the default for all campus-FK models

---

## RBAC / Permission Issues

### Strengths
- Granular permission codenames (`resource.action`)
- RolePermission per institution
- UserPermission allow/deny overrides with expiry
- Superuser bypass works correctly
- Permissions cover 100+ actions across 17 categories

### Gaps
| Issue | Description |
|-------|-------------|
| **No permission groups/presets** | Creating roles requires manually assigning 50+ permissions |
| **No permission inheritance** | Campus admin doesn't inherit from teacher permissions |
| **Frontend permission checks missing** | Buttons/menus shown based on role string, not actual permissions |
| **No permission audit trail** | Who granted what to whom not logged |
| **Permission cache not invalidated** | Changes take effect only on new request (thread-local) |

---

## Authentication Issues

### Strengths
- Email or username login
- TOTP 2FA with HMAC-SHA256 + salt backup codes
- Account lockout after 5 failures (15-min window dedup)
- Password history (prevents reuse)
- Failed login tracking with IP/user-agent
- Session tracking with revocation

### Gaps
| Issue | Description |
|-------|-------------|
| **No passwordless login / magic links** | Only password + 2FA |
| **No social login besides Google** | No Microsoft, Apple, SAML |
| **No device fingerprinting** | Session tracking only |
| **No geo-IP anomaly detection** | Login from new country not flagged |
| **No concurrent session limit** | Unlimited sessions per user |

---

## API Security Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| No request validation middleware | Medium | DRF serializers validate but no global input sanitization |
| No API gateway / WAF | Medium | Direct Django exposure |
| No GraphQL (if used) depth limiting | N/A | REST only |
| No API key management | Low | Only session auth |
| No webhook signature verification | Medium | Stripe/Twilio webhooks need verification |

---

## Data Protection Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| No field-level encryption | Medium | PII (phone, address, medical) stored plaintext |
| No data retention policy | Medium | No automated purge of old data |
| No GDPR/PDPA compliance module | High | No right-to-be-forgotten, no data export |
| Media files served directly | Medium | No signed URLs for private documents |
| No database encryption at rest | Low | Depends on PostgreSQL/host config |

---

## Financial Security Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| No double-entry bookkeeping validation | Critical | Journal entries not validated for balance |
| No segregation of duties | High | Same user can create invoice + record payment + approve refund |
| No positive pay / check verification | Medium | Not applicable (digital) but no payment verification |
| No audit trail for fee structure changes | High | FeeCategory changes not logged |
| No reconciliation reports | High | Bank reconciliation missing |

---

## File / Document Security

| Issue | Severity | Description |
|-------|----------|-------------|
| No MIME type validation on upload | High | `StudentDocument.file` uses `FileField` only |
| No file size limit in model | Medium | Relies on nginx `client_max_body_size` |
| No virus scanning | High | No ClamAV or cloud scanning integration |
| No signed URLs for private docs | Medium | Direct media URL access |
| No document access logging | Medium | `StudentDocument` has no view/download audit |

---

## Compliance Gaps

| Standard | Status | Gaps |
|----------|--------|------|
| **GDPR** | ❌ Non-compliant | No data portability, no deletion, no consent tracking |
| **FERPA** (Student records) | ⚠️ Partial | Campus isolation helps but no access logging |
| **HIPAA** (Medical) | ❌ Non-compliant | No encryption, no audit logs, no BAA |
| **PCI DSS** (Payments) | ⚠️ Partial | Stripe handles card data but no internal controls |
| **SOC 2** | ❌ Non-compliant | No logging, no monitoring, no incident response |

---

## Security Testing Coverage

| Test Type | Coverage | Notes |
|-----------|----------|-------|
| Unit tests (auth) | Good | `test_auth_hardening.py` covers lockout, password reuse, 2FA |
| Campus isolation tests | Good | `test_campus_isolation.py` covers 6 modules |
| Permission tests | Partial | `test_access.py` exists |
| API security tests | ❌ None | No IDOR, no injection, no auth bypass tests |
| Penetration tests | ❌ None | Never performed |
| Dependency scanning | ❌ None | Not in CI |
| SAST/DAST | ❌ None | Not configured |

---

## Recommended Remediation Priority

### Week 1-2 (Critical)
1. Set `SECRET_KEY` from env only (remove default)
2. Enable secure cookies in production
3. Add audit logging to all finance write operations
4. Implement duplicate payment prevention (idempotency key + unique constraint)
5. Configure database backups with test restore

### Week 3-4 (High)
6. Complete campus isolation for all modules (Library, Transport, HR, Medical, etc.)
7. Implement refund approval workflow with audit
8. Add rate limiting on auth endpoints
9. Add MFA enforcement for admin roles
10. Add file upload validation (MIME, size, virus scan)

### Month 2 (Medium)
11. Implement object-level permissions in all views
12. Add API versioning
13. Add security headers (CSP, HSTS, etc.)
14. Add permission groups/presets
15. Implement GDPR data export/deletion

### Month 3 (Low/Technical Debt)
16. Add CI security scanning
17. Implement device fingerprinting
18. Add account recovery code rotation
19. Add penetration testing to pipeline
20. Document incident response procedure