@echo off
title Django Migration Fix
cd C:\Users\Ryuk\Documents\perfect-foundation-sms\backend
set DJANGO_SETTINGS_MODULE=backend.config.settings
echo.
echo ==========================================
echo Django Migration Fix Tool
echo ==========================================
echo.
echo This will reset and reapply all teacher migrations
echo to fix the "column teacher_id does not exist" error.
echo.
echo.
set /p confirm="Do you want to proceed? (y/n): "
if /i "%confirm%" equ "y" (
    echo.
    echo 1. Resetting teacher migrations to zero...
    python manage.py migrate teachers zero
    echo.
    echo 2. Recreating teacher migrations...
    python manage.py makemigrations teachers
    echo.
    echo 3. Applying all teacher migrations...
    python manage.py migrate teachers
    echo.
    echo 4. Applying all remaining migrations...
    python manage.py migrate --noinput
    echo.
    echo 5. Collecting static files...
    python manage.py collectstatic --noinput
    echo.
    echo ==========================================
    echo SUCCESS! All migrations reset and applied.
    echo ==========================================
    pause
) else (
    echo.
    echo Cancelled by user.
    pause
)