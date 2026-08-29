@echo off
title Django Migration & Deploy Fix
echo.
echo ==========================================
echo Django Migration & Deploy Fix
echo ==========================================
echo.
echo This script will:
echo 1. Reset and reapply teacher migrations
echo 2. Fix the "column teacher_id does not exist" error
echo 3. Collect static files
echo 4. Provide Vercel deployment instructions
echo.
echo.
set /p confirm="Do you want to proceed? (y/n): "
if /i "%confirm%" neq "y" exit /b
cd C:\Users\Ryuk\Documents\perfect-foundation-sms\backend
set DJANGO_SETTINGS_MODULE=backend.config.settings
echo.
echo 1. Resetting teacher migrations to zero...
call python manage.py migrate teachers zero
echo.
echo 2. Creating new teacher migrations...
call python manage.py makemigrations teachers
echo.
echo 3. Applying teacher migrations...
call python manage.py migrate teachers
echo.
echo 4. Applying all remaining migrations...
call python manage.py migrate --noinput
echo.
echo 5. Collecting static files...
call python manage.py collectstatic --noinput
echo.
echo.
echo ==========================================
echo ALL MIGRATIONS COMPLETE
echo ==========================================
echo.
echo Now redeploy to Vercel:
echo 1. Go to https://vercel.com/dashboard
echo 2. Select perfect-foundation-api project
echo 4. Settings → Environment Variables
echo 5. Add these variables (Production = Yes):
echo.
echo DJANGO_SECRET_KEY=your-generated-key
echo DB_ENGINE=django.db.backends.postgresql
echo DB_NAME=perfect_foundation
echo DB_USER=school_admin
echo DB_PASSWORD=your_db_password
echo DB_HOST=localhost
echo DB_PORT=5432
echo DJANGO_ALLOWED_HOSTS=perfect-foundation-api.vercel.app
echo DJANGO_SESSION_COOKIE_SECURE=1
echo DJANGO_CSRF_COOKIE_SECURE=1
echo DJANGO_SECURE_SSL_REDIRECT=1
echo.
echo 6. Click Deployments → Latest → ⋯ → Redeploy
echo.
pause