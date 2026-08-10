# Deployment Guide

The app is split in two:

- **Frontend** (React + Vite, in `frontend/`) -> **Vercel**
- **Backend** (Django, in `backend/`) -> **Render** (Docker + managed Postgres)

The frontend calls `/api/*` as a relative URL. On Vercel,
`frontend/vercel.json` rewrites `/api/*` to the Render backend, so cookies
stay **same-site** and the existing session/CSRF flow works unchanged.

## Before you start (checklist)

- [ ] Repo pushed to GitHub
- [ ] `backend/render.yaml` `repo:` points at your actual GitHub repo
      (already set to `lordvalicious/perfect-foundation-sms`)
- [ ] `backend/render.yaml` `DJANGO_CSRF_TRUSTED_ORIGINS` matches your Vercel URL
- [ ] After the backend deploys: copy its `https://*.onrender.com` URL into
      `frontend/vercel.json` (see step 3 below)

---

## 1. Prerequisites

- The repo pushed to GitHub (e.g. `github.com/you/perfect-foundation-sms`)
- A [Vercel](https://vercel.com) account
- A [Render](https://render.com) account

## 2. Deploy the backend on Render

1. Push your changes to GitHub.
2. In the Render dashboard: **New -> Blueprint -> New Blueprint Instance**,
   connect your repo and pick the blueprint. Render provisions:

   - `perfect-foundation-backend` (Docker web service)
   - `perfect-foundation-db` (managed Postgres)

   The blueprint runs `sh ./startup.sh` before every deploy, which applies
   migrations and collects static files.

4. After the first successful deploy, the service URL will look like
   `https://perfect-foundation-backend.onrender.com`. Verify it:
   `curl https://perfect-foundation-backend.onrender.com/api/health/`

### Backend environment

The blueprint sets most variables automatically:

| Variable | Source |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | auto-generated (set once) |
| `DJANGO_ALLOWED_HOSTS` | `*` (tighten after adding a custom domain) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | your Vercel origin, edit if you change it |
| `DATABASE_URL` | wired to the Render Postgres |

### Create an admin user

The production database starts empty. From the Render dashboard, open
**Shell** for the backend service and run:

```sh
python manage.py createsuperuser
```

### Optional: migrate your local data

To copy your local Postgres data to the production database:

```sh
docker compose exec db pg_dump -U school_admin perfect_foundation > dump.sql
# then in the Render shell:
cat dump.sql | python manage.py dbshell
```

(Simpler: use Render's dashboard DB import, or `pg_restore` from a
`pg_dump -Fc` archive.)

## 3. Deploy the frontend on Vercel

1. Vercel -> **Add New -> Project**, import the repo.
2. Project settings:
   - Framework preset: **Vite**
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
3. After deploy, edit `frontend/vercel.json` so `/api` rewrites point at your
   real Render URL, then redeploy:

   ```json
   {
     "rewrites": [
       { "source": "/api/:path*", "destination": "https://perfect-foundation-backend.onrender.com/api/:path*" },
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```

4. Visit your Vercel URL and sign in with the admin you created.

## 4. Custom domain (recommended)

- Vercel: add your domain to the frontend project.
- Render: add the same domain to the backend service (Settings -> Custom
  Domain), then update `DJANGO_ALLOWED_HOSTS` and
  `DJANGO_CSRF_TRUSTED_ORIGINS` to the real domains (they already include
  your Vercel origin).

## Notes / limitations

- **Render free Postgres** expires after 30 days. Use a paid plan or
  upgrade for production.
- **Media files** are stored on the container's local disk (ephemeral).
  There are currently no file/image uploads in the app, so this is fine;
  add S3 if you introduce uploads later.
- **Email** uses Django's console backend. Wire a real SMTP backend
  (e.g. SendGrid) in production settings before relying on password reset.
