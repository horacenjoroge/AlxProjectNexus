# Environment Setup Guide

## Creating .env File

Since `.env` is gitignored for security, you need to create it manually.

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=provote_db
DB_USER=provote_user
DB_PASSWORD=provote_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Security (Production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# CORS (if needed)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Generating SECRET_KEY

You can generate a secure SECRET_KEY using:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Local Development

For local development without Docker:
- Set `DB_HOST=localhost`
- Set `REDIS_HOST=localhost`
- Ensure PostgreSQL and Redis are running locally

## Docker Development

For Docker development:
- Set `DB_HOST=db`
- Set `REDIS_HOST=redis`
- These match the service names in docker-compose.yml

