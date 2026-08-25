# School Onboarding Runbook

Everything needed to take Perfect Foundation SMS from zero to a
school logging in on day one.

---

## 1. One-time platform setup (per deployment)

### 1.1 Environment variables — Vercel backend project

Set in **Vercel → perfect-foundation-api → Settings → Environment Variables**:

| Variable | Required | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ | Session signing |
| `DATABASE_URL` | ✅ | Postgres connection string |
| `DJANGO_ALLOWED_HOSTS` | ✅ | Your API domain(s) |
| `DJANGO_EMAIL_HOST/PORT/USER/PASSWORD` | recommended | Enables the Email tab + weekly reports |
| `DEFAULT_FROM_EMAIL` | recommended | Sender address |
| `CRON_SECRET` | recommended | Authenticates scheduled jobs |
| `LATE_FEE_PERCENT` / `LATE_FEE_GRACE_DAYS` | optional | Daily late-fee job tuning |
| `TWILIO_ACCOUNT_SID/AUTH_TOKEN/PHONE_NUMBER` | optional | SMS sending |
| `STRIPE_SECRET_KEY` + Stripe webhook | optional | Online card payments |
| `JAZZCASH_MERCHANT_ID/PASSWORD/INTEGRITY_SALT`, `JAZZCASH_ENV=live` | optional | JazzCash checkout |
| `EASYPAISA_STORE_ID/STORE_KEY`, `EASYPAISA_ENV=live` | optional | EasyPaisa checkout |
| `GOOGLE_CLIENT_ID` | optional | "Continue with Google" button |
| `ATTENDANCE_DEVICE_KEYS` | optional | Biometric/RFID device webhooks |
| `GPS_DEVICE_KEYS` | optional | Vehicle GPS trackers |

See `backend/.env.example` for a copy-paste reference of every variable.

### 1.2 Scheduled jobs (already wired in `backend/vercel.json`)

- **Daily 06:00 UTC** — late fees applied to overdue invoices
- **Mondays 07:00 UTC** — weekly summary email to every admin

Both activate automatically once `CRON_SECRET` (+ email config for the
digest) exists. No further action needed.

### 1.3 Frontend

The frontend project only needs its normal Vercel deploy; `/api/*`
rewrites to the backend via `vercel.json`.

---

## 2. Onboarding a NEW school (multi-tenant: repeat per school)

Run against the production database (Vercel CLI or a one-off worker):

```bash
# 2.1 Create the school record + branding
#     Admin → Campuses → add school, or via Django admin.

# 2.2 Academic structure (required before anything else)
#     Admin → Schools: Academic Year (mark active), Terms,
#     Campus(es), Units, Classes, Sections, Subjects, Subject Offerings.

# 2.3 Demo-free baseline data
python manage.py migrate                       # schema is shared
python manage.py seed_all --skip-users         # optional demo data ONLY
```

> ⚠️ `seed_*` commands create DEMO content. For a real school import
> real data instead (step 2.4).

### 2.4 Import real data (no typing required)

1. Log in as an admin → **Finance group → Data Import**
2. Download the **Students** and/or **Teachers** CSV template
3. Fill it (campus/class/section matched by name)
4. Validate → fix reported rows → Run import

Students arrive with guardians and active enrollments ready to go.

### 2.5 Staff accounts & roles

- **People → Teachers / Staff**: create profiles (this provisions login
  accounts) or bulk-import teachers then link.
- Assign each person's role (teacher, accountant, hr, …) and campus.
- Optional: staff enable their own 2FA under **Settings → Two-Factor
  Authentication**, or use **Google sign-in** when
  `GOOGLE_CLIENT_ID` is set (email must match an existing account).

### 2.6 Money configuration

1. **Finance → Fee Categories**: tuition, admission, transport, etc.
2. **Finance → Fee Structures**: per campus + class + academic year.
3. **Bulk Finance**: generate invoices for every enrollment in one click.
4. Gateways: set credentials (table above) → parents can pay online via
   Stripe/JazzCash/EasyPaisa buttons; manual cash/bank recording always
   available.

### 2.7 Transport / Library / Hostel (optional modules)

Each module page has an **Add** flow; no extra configuration needed:

- **Transport**: vehicles → drivers → routes (+stops) → student assignments.
- **Library**: books → copies are auto-bar-coded → issue/return with fines.
- **Hostel**: hostels → rooms → allocations (capacity enforced).

### 2.8 Hardware integrations (optional)

Point vendor devices/webhooks at:

```
POST https://<api-domain>/api/attendance/device-sync/
X-Device-Key: <any key in ATTENDANCE_DEVICE_KEYS>
{ "type": "student", "identifier": "<admission_number>",
  "date": "2026-09-01", "time": "07:55" }

POST https://<api-domain>/api/transport/gps/ping/
X-Device-Key: <any key in GPS_DEVICE_KEYS>
{ "vehicle": "<plate>", "lat": 33.68, "lng": 73.04, "speed": 40 }
```

---

## 3. Day-one smoke checklist (10 minutes)

Log in as the school's admin and confirm:

- [ ] Dashboard loads with this school's counts (charts render)
- [ ] Students list shows imported enrollments per campus/class
- [ ] Invoices exist; a test payment records and receipt PDF downloads
- [ ] Attendance bulk-mark saves for any class section
- [ ] Reports tab opens each report without error
- [ ] A teacher account can log in (and via Google if enabled)
- [ ] Parent portal shows a child's attendance/results/fees

## 4. Ongoing operations

| Task | How |
|---|---|
| Late fees | Automatic daily (`CRON_SECRET`); manual: `python manage.py apply_late_fees --percent 2` |
| Weekly summary email | Automatic Monday 07:00 UTC to all admins |
| Data backup | **Data Export → Full JSON backup** (also scriptable: `/api/reports/backup/`) |
| New academic year | Settings → Academic Years → add + activate, then promote students (Students → Promotion) |
| Audit trail | System → Audit Logs (logins, payments, exports) |

## 5. Troubleshooting quick reference

| Symptom | Likely cause / fix |
|---|---|
| Login works but every list is empty | User has no active membership in that school's institution — check role assignment |
| Email tab says "not configured" | Set `DJANGO_EMAIL_*` vars, redeploy |
| Gateway buttons absent | Credentials missing — endpoints return 503 by design |
| Cron returns 401 | `Authorization` header must equal `Bearer $CRON_SECRET` |
| Device sync 401 | Key not present in `ATTENDANCE_DEVICE_KEYS` |
