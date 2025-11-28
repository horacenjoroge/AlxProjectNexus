#!/bin/bash
set -e

# Change to backend directory
cd /app/backend

# Check SERVICE_TYPE environment variable to determine what to run
if [ "$SERVICE_TYPE" = "celery" ]; then
    echo "Starting Celery worker..."
    exec celery -A config worker --loglevel=info
elif [ "$SERVICE_TYPE" = "celery-beat" ]; then
    echo "Starting Celery Beat scheduler..."
    exec celery -A config beat --loglevel=info
else
    echo "Starting Gunicorn web server..."
    exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 4 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile - --log-level info config.wsgi:application
fi

