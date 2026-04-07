from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# ---------------------------------------------------------------------------
# Logging overrides — development
# ---------------------------------------------------------------------------
# - Console uses human-readable coloured formatter (set in base)
# - SQL query logging enabled at DEBUG for performance tuning (opt-in)
# - All file handlers active (logs/ directory)

import os
os.makedirs(LOG_DIR, exist_ok=True)

# Enable SQL query logging in dev (opt-in via env var to avoid noise)
if env.bool("LOG_SQL", default=False):
    LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"
    LOGGING["loggers"]["django.db.backends"]["handlers"] = ["file_app", "console"]

