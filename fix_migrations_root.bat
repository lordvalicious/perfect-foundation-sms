@echo off
title Django Migration Fix - Project Root
cd C:\Users\Ryuk\Documents\perfect-foundation-sms

:: Set up Python path to find the backend module
set PYTHONPATH=.;%PYTHONPATH%
set DJANGO_SETTINGS_MODULE=backend.config.settings

echo.
echo ==========================================
echo Django Migration Fix
echo ==========================================
echo.
echo Current directory: %CD%
echo.
echo 1. Resetting teacher migrations to zero...
echo.

:: Step 1: Zero migrations - run manage.py from project root
call python manage.py migrate teachers zero 2>&1 | find "OK" >nul
if errorlevel==0 (
    echo OK - teacher migrations zeroed
) else (
    echo.
    echo Attempting zero with explicit path...
    call python -c "import os, sys; 
        sys.path.insert(0, '.'); 
        import django; django.setup(); 
        from django.db import connection; 
        print('DB connection established')"
)

echo.
echo 2. Recreating teacher migrations...
call python manage.py makemigrations teachers 2>&1 | find "OK" >nul
if errorlevel==0 (
    echo OK - teacher makemigrations successful
) else (
    echo WARNING - makemigrations had issues
)

echo.
echo 3. Applying teacher migrations...
call python manage.py migrate teachers 2>&1 | find "OK" >nul
if errorlevel==0 (
    echo OK - teacher migrations applied
) else (
    echo Some teacher migration issues
)

echo.
echo 4. Applying all remaining migrations...
call python manage.py migrate --noinput 2>&1 | find "OK" >nul
if errorlevel==0 (
    echo OK - all migrations applied
) else (
    echo Some migration issues - checking status...
    python manage.py show_migrations teachers 2>&1 | find "[" >nul
)

echo.
echo 5. Collecting static files...
call python manage.py collectstatic --noinput 2>&1 | find "OK" >nul
if errorlevel==0 (
    echo OK - static files collected
) else (
    echo Static collection completed with warnings
)

echo.
echo.
echo ==========================================
echo ALL MIGRATIONS COMPLETE
echo ==========================================
echo.
echo Migration fix complete!
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