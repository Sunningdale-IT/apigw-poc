"""
WSGI config for goodbehaviour_project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goodbehaviour_project.settings')
application = get_wsgi_application()
