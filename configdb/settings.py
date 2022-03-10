"""
Django settings for configdb project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
import os


def str2bool(value):
    '''Convert a string value to a boolean'''
    value = value.lower()

    if value in ('t', 'true', 'y', 'yes', '1', ):
        return True

    if value in ('f', 'false', 'n', 'no', '0', ):
        return False

    raise RuntimeError('Unable to parse {} as a boolean value'.format(value))


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = str2bool(os.getenv('DEBUG', 'false'))

ALLOWED_HOSTS = ['*', ]


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'ocs_authentication.auth_profile',
    'reversion',
    'rest_framework',
    'configdb.hardware',
    'corsheaders',
    'django_extensions',
)

MIDDLEWARE = (
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'ocs_authentication.backends.OAuthUsernamePasswordBackend',
]

ROOT_URLCONF = 'configdb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'configdb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'configdb'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASS', 'postgres'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': int(os.getenv('DB_PORT', 5432)),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/static/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 1000,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Allows authentication against DRF authtoken and then Oauth Server's api_token
        'ocs_authentication.backends.OCSTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

CORS_ORIGIN_ALLOW_ALL = True

# This project now requires connection to an OAuth server for authenticating users to make changes
# In the OCS, this would be the Observation Portal backend
OCS_AUTHENTICATION = {
    'OAUTH_TOKEN_URL': os.getenv('OAUTH_TOKEN_URL', 'http://127.0.0.1:8000/o/token/'),
    'OAUTH_PROFILE_URL': os.getenv('OAUTH_PROFILE_URL', 'http://127.0.0.1:8000/api/profile/'),
    'OAUTH_CLIENT_ID': os.getenv('OAUTH_CLIENT_ID', ''),
    'OAUTH_CLIENT_SECRET': os.getenv('OAUTH_CLIENT_SECRET', ''),
    'OAUTH_SERVER_KEY': os.getenv('OAUTH_SERVER_KEY', ''),
    'REQUESTS_TIMEOUT_SECONDS': 60
}


try:
    from local_settings import *  # noqa
except ImportError:
    pass
