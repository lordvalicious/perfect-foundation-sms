@echo off
title Django Migration Fix - Auto Setup
cd C:\Users\Ryuk\Documents\perfect-foundation-sms\backend

:: Set up Python path to find all apps
set PYTHONPATH=C:\Users\Ryuk\Documents\perfect-foundation-sms\backend
set DJANGO_SETTINGS_MODULE=backend.config.settings

:: Disable output buffering for cleaner output
set PYTHONUNBUFFERED=1

echo.
echo ==========================================
echo Django Migration Fix
echo ==========================================
echo.
echo Current directory: %CD%
echo.
echo 1. Resetting teacher migrations to zero...
echo.

:: Step 1: Zero migrations
python -c "
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.config.settings'
import django
django.setup()
from django.db import connection
print('   Connected to database successfully')
" 2>&1

call python manage.py migrate teachers zero 2>&1

echo.
echo 2. Recreating teacher migrations...
call python manage.py makemigrations teachers 2>&1

echo.
echo 3. Applying teacher migrations...
call python manage.py migrate teachers 2>&1

echo.
echo 4. Applying all remaining migrations...
call python manage.py migrate --noinput 2>&1

echo.
echo 5. Collecting static files...
call python manage.py collectstatic --noinput 2>&1

echo.
echo.
echo ==========================================
echo ALL MIGRATIONS COMPLETE
echo ==========================================
echo.
echo 5. Migration fix complete!
echo.
echo Now redeploy to Vercel:
echo 1. Go to https://vercel.com/dashboard
echo 2. Select perfect-foundation-api project
echo 3. Settings -> Environment Variables
echo 4. Add these variables (Production = Yes):
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
echo 5. Click Deployments -> Latest -> Redeploy
echo.
pause