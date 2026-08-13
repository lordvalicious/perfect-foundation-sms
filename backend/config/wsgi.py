"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    (
        'config.settings.production'
        if os.environ.get('VERCEL')
        else 'config.settings.development'
    ),
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

handler = application
