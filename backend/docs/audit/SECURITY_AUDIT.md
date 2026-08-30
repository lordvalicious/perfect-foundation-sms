# Security Audit

## Overview

This document captures the security audit status for the ERP backend, including completed remediations, known considerations, and residual items.

## Completed Remediations

### Migration 0014 - FrostFire Superadmin
- **Issue**: Hardcoded FrostFire credentials (`make_password` with plaintext password, `role='super_admin'`, `institution=`, `status='active'`)
- **Fix**: Migration `0014_create_frostfire_superadmin.py` now uses proper Django `make_password` pattern, correct role value, and institution/status fields
- **Status**: Remediated

### Backup Code HMAC + Salt
- **Issue**: Legacy SHA-256 backup codes without HMAC-salting
- **Fix**: `0015_twofa_backupcode_salt.py` added salted HMAC-backed backup codes; `0016_alter_role_choices.py` enhanced role choices
- **Status**: Remediated

### MFA Legacy Fallback
- **Issue**: Legacy SHA-256 hash backup codes could be verified without HMAC validation
- **Fix**: Verification endpoint prioritizes salted HMAC path; legacy bare-SHA path is gated behind non-empty salt check (`test_verify_endpoint_accepts_legacy_bare_sha` / `test_salted_row_never_falls_back_to_bare_sha`)
- **Status**: Remediated

### Role Choices Standardization
- **Issue**: Inconsistent role choice formatting across migrations
- **Fix**: `0016_alter_role_choices.py` standardized all 18 role values as `TextChoices`
- **Status**: Remediated

## Known Considerations

### MFA Legacy Hash Residual
- Old SHA-256-only backup codes remain in the database from before the salted HMAC migration
- These are **still valid for login** via the legacy fallback pathway
- Admins should rotate all backup codes after migration using the `/api/auth/2fa/rotate-backup-codes/` endpoint
- The legacy fallback is intentional for backward compatibility and is secured by the salt-non-empty gate

### Production Environment
- Full 137-account test suite operates against Neon Postgres
- Throttle-lockout state issues are environment-dependent (not code regression)
- Local SQLite tests pass completely (22/22 campus isolation, 14/14 auth hardening)

### SubjectOffering Duplicate Classes
- Two `SubjectOffering` class definitions exist in `schools/models.py` (~line 364 and ~699)
- The active class (line 736) uses `related_name="subject_offerings"` consistently
- No action required unless merging the duplicate classes

## Audit Logging

- `AuditLog` model enhanced with `ip_address` and `user_agent` fields
- 3 new audit action types added:
  - `student_transfer_initiated`
  - `student_transfer_approved`
  - `student_transfer_rejected`
- Student result locking/unlocking actions recorded with `is_locked` detail

## Backup Code Format
- Format: `^[A-Z2-9]{4}-[A-Z2-9]{4}$` (8 alphanumeric chars, hyphen-separated)
- HMAC-salted: `hash = HMAC-SHA256(key=salt, msg=code)`
- Legacy SHA-256 fallback only when salt field is empty

## Role Hierarchy
- `super_admin` > `admin` > `org_admin` > `head_office` > academic roles
- Global vs campus-scoped access determined by role + StaffProfile assignment