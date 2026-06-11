# Production settings — extends base.py with hardened configuration

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"] + MIDDLEWARE  # noqa: F405

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

# Send Django errors to stderr so they appear in `docker logs`
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
