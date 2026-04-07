from .base import *

DEBUG = False

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use SQLite for speed in tests regardless of DATABASE_URL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ---------------------------------------------------------------------------
# Logging overrides — tests
# ---------------------------------------------------------------------------
# - Suppress all log output to keep test output clean
# - Only CRITICAL passes through (so truly broken things still show)
# - No file handlers (no logs/ directory needed in CI)

LOGGING["handlers"] = {
    "console": {
        "class": "logging.NullHandler",
    },
}

for logger_config in LOGGING["loggers"].values():
    logger_config["handlers"] = ["console"]
    logger_config["level"] = "CRITICAL"

LOGGING["root"]["level"] = "CRITICAL"