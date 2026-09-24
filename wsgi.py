"""Vercel entrypoint for Django application."""

import os
import sys

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Import the Django WSGI application
from backend.config.wsgi import application

# Vercel expects the application to be named 'application' or 'app'
application = application