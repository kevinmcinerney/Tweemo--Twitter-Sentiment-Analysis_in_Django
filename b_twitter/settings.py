"""
Django settings for twitter project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-@9l82kym*r0f@%jc$e7=)&5x-ukh1z(#mjs4czl_(z41oam_s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tweemo',
    'bootstrap_toolkit',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'b_twitter.urls'

WSGI_APPLICATION = 'b_twitter.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases


DATABASES = {
    
    'default': {
	'ENGINE': 'django_mongodb_engine',
	'NAME': 'twitter',
	'USER': 'kevin',
	'PASSWORD': '6841734aa',
	'HOST': 'ds027489.mongolab.com',
	'PORT': 27489,
    }
}

SOUTH_DATABASE_ADAPTERS = {
    'default': "south.db.sqlite3"
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT = 'staticfiles'

STATIC_URL = "/static/"

STATICFILES_DIRS = (
	os.path.join(BASE_DIR, 'static'),
	('assets', '/app/b_twitter/static'),
)

print BASE_DIR
TEMPLATE_DIRS = (
	'/app/templates',
	'/app/tweemo/templates',
)

TEMPLATE_LOADERS = (

    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',

)

#Enter valid gmail + password below
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'myemail'
EMAIL_HOST_PASSWORD = 'mypassword'
EMAIL_PORT = 587
