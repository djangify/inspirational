"""
Settings module initializer.
This allows for importing from corrison.settings directly
"""
import os
import sys

# Default to local settings if DJANGO_SETTINGS_MODULE is not set
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    if 'runserver' in sys.argv or 'manage.py' in sys.argv:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corrison.settings.local')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corrison.settings.production')
        