"""
Django settings for citizen_project (Model Citizen).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'citizen-secret-key-change-in-production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# API Gateway URL - points to Kong which proxies to Dogcatcher
# Use /public route for unauthenticated access, /apikey for authenticated
API_GATEWAY_URL = os.environ.get('API_GATEWAY_URL', 'http://kong:8000/public')
DOGCATCHER_PUBLIC_URL = os.environ.get('DOGCATCHER_PUBLIC_URL', 'http://localhost:8000')
DOGCATCHER_API_KEY = os.environ.get('DOGCATCHER_API_KEY', '')

# Mock citizen database
MOCK_CITIZENS = {
    'CIT001': {'name': 'John Smith', 'email': 'john.smith@email.com', 'address': '123 Main Street, Springfield'},
    'CIT002': {'name': 'Jane Doe', 'email': 'jane.doe@email.com', 'address': '456 Oak Avenue, Riverside'},
    'CIT003': {'name': 'Bob Wilson', 'email': 'bob.wilson@email.com', 'address': '789 Pine Road, Lakeside'},
    'DEMO': {'name': 'Demo User', 'email': 'demo@example.com', 'address': '1 Demo Lane, Test City'},
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'services',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'citizen_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'citizen_project.wsgi.application'

# No database needed for this app (uses mock data)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_AGE = 3600  # 1 hour
