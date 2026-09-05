@echo off
set DJANGO_SETTINGS_MODULE=config.settings.test
python manage.py test accounts.tests.SchoolSwitchingTests --verbosity=2 %*