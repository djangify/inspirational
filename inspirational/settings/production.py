import os
from .base import *  # noqa: F403


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS
ALLOWED_HOSTS = [
    "inspirationalguidance.com",
    "www.inspirationalguidance.com",
    "mail.inspirationalguidance.com",
    "65.108.89.200",
    "localhost",
    "127.0.0.1",
]

# Database in base.py is already set up to use environment variables
# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),  # noqa: F405
        "USER": env("DATABASE_USER"),  # noqa: F405
        "PASSWORD": env("DATABASE_PASSWORD"),  # noqa: F405
        "HOST": env("DATABASE_HOST", default="localhost"),  # noqa: F405
        "PORT": env("DATABASE_PORT", default="5432"),  # noqa: F405
    }
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "sessionid"  # Change back to standard name
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True  # Change back to True for security
SESSION_COOKIE_PATH = "/"

# Security settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True


SITE_URL = "https://inspirationalguidance.com"

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/django-error.log"),  # noqa: F405
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
# Ensure logs directory exists
log_dir = os.path.join(BASE_DIR, "logs")  # noqa: F405
os.makedirs(log_dir, exist_ok=True)


# Email verification settings
# EMAIL_VERIFICATION_URL = "https://corrison.corrisonapi.com/auth/verify-email"
EMAIL_VERIFICATION_TOKEN_EXPIRY = 36  # hours

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",  # Keep as fallback
]

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
