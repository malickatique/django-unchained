"""
Django settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import environ
from pathlib import Path

from common.logging.constants import LogCategory

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file from project root
environ.Env.read_env(BASE_DIR / '.env')

# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

AUTH_USER_MODEL = 'users.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',

    # Project Apps / Modules / Domain
    'common',
    'apps.users',
]

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Request logging — extracts/generates request_id, logs access events,
    # populates thread-local context for structured logging.
    # Must come AFTER AuthenticationMiddleware (needs request.user).
    'common.logging.middleware.RequestLoggingMiddleware',
    # Audit — auto-populates created_by/updated_by on AuditModel.
    # Must come AFTER AuthenticationMiddleware and RequestLoggingMiddleware.
    'common.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL')
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    # ── Response envelope ────────────────────────────────────────────
    # ApiRenderer wraps every response in {success, message, data, meta, errors}
    "DEFAULT_RENDERER_CLASSES": [
        "common.response.renderers.ApiRenderer",
    ],

    # ── Exception handling ───────────────────────────────────────────
    # Central handler — normalises all exceptions into the error envelope
    "EXCEPTION_HANDLER": "common.exceptions.handler.api_exception_handler",

    # ── Pagination ───────────────────────────────────────────────────
    "DEFAULT_PAGINATION_CLASS": "common.response.pagination.ApiPageNumberPagination",
    "PAGE_SIZE": 20,
}

# ---------------------------------------------------------------------------
# Application metadata (used by logging, health checks, etc.)
# ---------------------------------------------------------------------------

APP_ENVIRONMENT = env("DJANGO_ENV", default="development")

# APP_VERSION: set by CI/CD to git SHA or release tag (e.g. "v1.2.3" or "abc1234f").
# Locally, auto-detect from git. Falls back to "local" if git isn't available.
APP_VERSION = env("APP_VERSION", default="")
if not APP_VERSION:
    import subprocess
    try:
        APP_VERSION = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(BASE_DIR),
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()
    except Exception:
        APP_VERSION = "local"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Structured JSON logging with per-category handlers.
# See common/logging/ for formatters, filters, context, and middleware.

LOG_DIR = BASE_DIR / "logs"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    # ── Formatters ────────────────────────────────────────────────
    "formatters": {
        "json": {
            "()": "common.logging.formatters.JsonFormatter",
            "environment": APP_ENVIRONMENT,
            "version": APP_VERSION,
        },
        "console": {
            "()": "common.logging.formatters.ConsoleFormatter",
        },
    },

    # ── Filters ───────────────────────────────────────────────────
    "filters": {
        "request_context": {
            "()": "common.logging.filters.RequestContextFilter",
        },
    },

    # ── Handlers ──────────────────────────────────────────────────
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "filters": ["request_context"],
            "stream": "ext://sys.stdout",
        },
        "file_access": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "access.log"),
            "formatter": "json",
            "filters": ["request_context"],
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "file_app": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "formatter": "json",
            "filters": ["request_context"],
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "file_security": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "security.log"),
            "formatter": "json",
            "filters": ["request_context"],
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "error.log"),
            "formatter": "json",
            "filters": ["request_context"],
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },

    # ── Loggers ───────────────────────────────────────────────────
    # Keys use LogCategory constants so changing the prefix in
    # constants.py automatically updates here too.
    "loggers": {
        # Access logs — request received / response sent
        LogCategory.ACCESS: {
            "handlers": ["file_access", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # Application / domain logs — business events
        LogCategory.APP: {
            "handlers": ["file_app", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # Security logs — auth, permissions, sensitive actions
        LogCategory.SECURITY: {
            "handlers": ["file_security", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # Error logs — unhandled exceptions, integration failures
        LogCategory.ERROR: {
            "handlers": ["file_error", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Infrastructure logs — DB, cache, external APIs
        LogCategory.INFRA: {
            "handlers": ["file_app", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # App-level loggers — route domain logs to file_app
        "apps": {
            "handlers": ["file_app", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # Exception handler — route to error file
        "common.exceptions.handler": {
            "handlers": ["file_error", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        # Django internals
        "django.request": {
            "handlers": ["file_error", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["file_security", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file_app"],
            "level": "WARNING",
            "propagate": False,
        },
    },

    # Root logger — catch anything not handled above
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}