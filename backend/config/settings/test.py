"""
Test settings for Provote project.
"""
import tempfile
from pathlib import Path
from .base import *  # noqa: F403, F401

# Use temporary file-based database for tests
# This works better with Django's initialization and pytest-django
# pytest-django will automatically create tables and run migrations
TEST_DB = Path(tempfile.gettempdir()) / "provote_test.db"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(TEST_DB),
    }
}

# Note: Migrations are enabled for CI/CD
# For faster unit tests, use pytest with --nomigrations flag
# MIGRATION_MODULES = DisableMigrations()

# Password hashing for tests (faster)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable security features for tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery configuration for tests (synchronous execution)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable logging during tests
LOGGING_CONFIG = None

# Static directory will be created by the workflow
# This is handled in .github/workflows/test.yml

