from .base import *

DEBUG = True

CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Дополнительные приложения для разработки
DEV_APPS = [
    'drf_spectacular',
    'django_extensions',  # Полезно для разработки
]

INSTALLED_APPS += DEV_APPS

# Настройки DRF Spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'MyCloud API (Development)',
    'DESCRIPTION': 'API documentation for development environment',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
}

# Упрощенные настройки безопасности для разработки
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

# Логирование для разработки
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG' if DEBUG else 'INFO',
    },
}
