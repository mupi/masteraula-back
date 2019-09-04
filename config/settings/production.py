# -*- coding: utf-8 -*-
"""
Production Configurations

- Use Amazon's S3 for storing static files and uploaded media
- Use mailgun to send emails
- Use Redis for cache


"""
from __future__ import absolute_import, unicode_literals
from email.utils import parseaddr 

from boto.s3.connection import OrdinaryCallingFormat
from django.utils import six


from .common import *  # noqa

env.read_env()

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env('DJANGO_SECRET_KEY')


# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY CONFIGURATION
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/1.9/ref/middleware/#module-django.middleware.security
# and https://docs.djangoproject.com/ja/1.9/howto/deployment/checklist/#run-manage-py-check-deploy

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    'DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', default=True)
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = False
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = 'DENY'

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['mupi.me'])
# END SITE CONFIGURATION

INSTALLED_APPS += (
    'gunicorn',
    'djcelery_email',
)

# S3 CONFIGURATION
# ------------------------------------------------------------------------------
AWS_ACCESS_KEY_ID =  env('DJANGO_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('DJANGO_AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('DJANGO_AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'
STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'masteraula.questions.storage_backends.MediaStorage'

# Static Assets
# ------------------------

# STATIC_URL = 'https://s3.amazonaws.com/%s/static/' % AWS_STORAGE_BUCKET_NAME
# STATICFILES_STORAGE = 'config.settings.production.StaticRootS3BotoStorage'
# # See: https://github.com/antonagestam/collectfast
# # For Django 1.7+, 'collectfast' should come before
# # 'django.contrib.staticfiles'
# AWS_PRELOAD_METADATA = True
# INSTALLED_APPS = ('collectfast', ) + INSTALLED_APPS

# EMAIL
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env('DJANGO_DEFAULT_FROM_EMAIL',
                         default='Mupi Question Database <noreply@mupi.me>')
EMAIL_SUBJECT_PREFIX = env('DJANGO_EMAIL_SUBJECT_PREFIX', default='[Mupi Question Database] ')
SERVER_EMAIL = env('DJANGO_SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Anymail with Mailgun
# INSTALLED_APPS += ("anymail", )
# ANYMAIL = {
#     "MAILGUN_API_KEY": env('DJANGO_MAILGUN_API_KEY'),
#     "MAILGUN_SENDER_DOMAIN": env('MAILGUN_SENDER_DOMAIN')
# }
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('DJANGO_EMAIL_HOST')
EMAIL_HOST_USER = env('DJANGO_EMAIL_USER')
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_PASSWORD')
EMAIL_PORT = env('DJANGO_EMAIL_PORT')
EMAIL_USE_TLS = env.bool('DJANGO_EMAIL_USE_TLS')
EMAIL_USE_SSL = env.bool('DJANGO_EMAIL_USE_SSL')

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     ('django.template.loaders.cached.Loader', [
#         'django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader', ]),
# ]

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------

# Use the Heroku-style specification
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
# DATABASES['default'] = env.db('DATABASE_URL')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('POSTGRES_DB_NAME'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
    }
}


# CACHING
# ------------------------------------------------------------------------------

# REDIS_LOCATION = '{0}/{1}'.format(env('REDIS_URL', default='redis://127.0.0.1:6379'), 0)
# # Heroku URL does not pass the DB number, so we parse it in
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': REDIS_LOCATION,
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#             'IGNORE_EXCEPTIONS': True,  # mimics memcache behavior.
#                                         # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
#         }
#     }
# }


# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
ADMINS = tuple(parseaddr(email) for email in env('DJANGO_ADMINS').split(','))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True
        },
        'django.security.DisallowedHost': {
            'level': 'ERROR',
            'handlers': ['console', 'mail_admins'],
            'propagate': True
        }
    }
}

# Custom Admin URL, use {% url 'admin:index' %}
ADMIN_URL =  r'^admin/'

# Your production stuff: Below this line define 3rd party library settings
# ------------------------------------------------------------------------------

URL_FRONT = env('DJANGO_URL_FRONT')
CORS_ORIGIN_WHITELIST = env('DJANGO_CORS_ORIGIN_WHITELIST')
CORS_ORIGIN_ALLOW_ALL = env.bool('DJANGO_CORS_ALLOW_ALL')
HAYSTACK_CONNECTIONS = {
    'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
    'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
    'SILENTLY_FAIL' : False,
    # 'default': {
    #     'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
    #     'URL': env('DJANGO_HAYSTACK_URL'),
    #     'INDEX_NAME': env('DJANGO_HAYSTACK_INDEX_NAME'),
    #     'SILENTLY_FAIL' : env('DJANGO_HAYSTACK_SILENTLY_FAIL'),
    # },
}

# Celery
# -----------------------------------------------------------------------------
import urllib
env.read_env()
BROKER_URL = env('DJANGO_BROKER_URL') 
# BROKER_URL = 'sqs://{0}:{1}@'.format(
#     urllib.parse.quote(env('DJANGO_AWS_ACCESS_KEY_ID'), safe=''),
#     urllib.parse.quote(env('DJANGO_AWS_SECRET_ACCESS_KEY'), safe='')
# )
# CELERY_DEFAULT_QUEUE = env('DJANGO_AWS_CELERY_DEFAULT_QUEUE')
# broker_transport_options = {
#     'region': 'us-east-2',
#     'polling_interval': 20,
# }