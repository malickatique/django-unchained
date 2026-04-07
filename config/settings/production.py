from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

# ---------------------------------------------------------------------------
# Logging overrides — production
# ---------------------------------------------------------------------------
# - JSON to stdout only (collected by ELK/Datadog/CloudWatch)
# - No file handlers (container stdout is the log transport)
# - Console handler uses JSON formatter (not coloured text)
# - Stricter levels — no DEBUG anywhere

# Switch console to JSON for machine consumption
LOGGING["handlers"]["console"]["formatter"] = "json"

# Remove all file handlers — stdout is the single log transport
_file_handlers = {"file_access", "file_app", "file_security", "file_error"}
for handler_name in _file_handlers:
    LOGGING["handlers"].pop(handler_name, None)

# Update all loggers to use console only
for logger_config in LOGGING["loggers"].values():
    logger_config["handlers"] = [
        h for h in logger_config.get("handlers", [])
        if h not in _file_handlers
    ]
    # Ensure at least console
    if not logger_config["handlers"]:
        logger_config["handlers"] = ["console"]