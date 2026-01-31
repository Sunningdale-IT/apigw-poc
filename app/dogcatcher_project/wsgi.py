"""
WSGI config for dogcatcher_project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dogcatcher_project.settings')

application = get_wsgi_application()
