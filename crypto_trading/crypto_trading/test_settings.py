"""
Configuración específica para testing.
Sobrescribe settings.py con opciones optimizadas para tests.
"""

from .settings import *
import sys

# Base de datos en memoria para tests rápidos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Email backend de prueba (almacena emails en memoria)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'test@cryptotrade.local'

# Password hasher más rápido para tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Desactivar debug en tests para simular producción
DEBUG = False
TEMPLATE_DEBUG = False

# Permitir todos los hosts en tests
ALLOWED_HOSTS = ['*', 'testserver']

# Secret key para tests
SECRET_KEY = 'test-secret-key-only-for-testing-do-not-use-in-production'

# Desactivar logging durante tests (opcional)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Configuración de caché en memoria para tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Desactivar migraciones para acelerar tests (opcional pero muy útil)
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None


# MIGRATION_MODULES = DisableMigrations()
