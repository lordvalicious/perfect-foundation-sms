# RBAC Documentation

## Role Model

`Role` is a `TextChoices` field with 18 distinct values, used for Role-Based Access Control across the system. Roles are hierarchical and scope-specific.

| Value | Description | Global Scope | Campus Scope |
|-------|-------------|:------------:|:------------:|
| `super_admin` | Platform-wide full access | Yes | No |
| `admin` | Institution-level administrator | Yes | No |
| `org_admin` | Organization administrator | No | Yes (own org) |
| `head_office` | Head office staff | No | Yes (cross-campus) |
| `academic` | Academic staff member | No | Yes (own campus) |
| `principal` | School principal | No | Yes (own school) |
| `vice_principal` | Vice principal | No | Yes (own school) |
| `campus_admin` | Campus administrator | No | Yes (own campus) |
| `teacher` | Teaching staff | No | Yes (own classes) |
| `accountant` | Finance/accounting role | No | Yes (own institution) |
| `hr` | HR / Staff Officer | No | Yes (own institution) |
| `receptionist` | Front desk / reception | No | Yes (own institution) |
| `librarian` | Library staff | No | Yes (own institution) |
| `guard` | Security guard | No | Yes (own institution) |
| `student` | Student self-access | No | Yes (own records) |
| `parent` | Parent/guardian access | No | Yes (own child records) |
| `staff` | General staff member | No | Yes (own institution) |
| `student` | Student basic access | No | Yes (own records) |

## Authorization Model

- **Global roles** (`super_admin`, `admin`): Bypass campus isolation, see all records across all institutions
- **Campus-bounded roles** (`org_admin`, `head_office`, `academic`, etc.): Scoped to the institution/campus assigned via `StaffProfile.primary_campus` or `StaffProfile.institution`
- **Authoritative backend**: `request.institution` is set by the middleware chain (`AuthenticationMiddleware → ActiveInstitutionMiddleware → CampusAccessMiddleware → ModuleAccessMiddleware`), not trust client-supplied values
- **ModuleAccessMiddleware**: Enforces that users can only access modules they are assigned to teach (for academic roles)

## Middleware Chain

```
AuthenticationMiddleware
→ ActiveInstitutionMiddleware
→ CampusAccessMiddleware
→ ModuleAccessMiddleware
```

Exempt paths: `CAMPUS_VALIDATION_EXEMPT_PATHS`

## Key Rules

1. Never trust client-supplied `campus_id` — always read from `request.institution`
2. `force_authenticate` alone leaves `request.institution` unset — tests must `client.login()` + `force_authenticate(user)`
3. RBAC decisions are made server-side based on user's role and institution assignment
4. `super_admin` and `admin` roles have global scope; all other roles are campus/institution bounded