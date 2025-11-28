#!/bin/bash
set -e

# Change to backend directory
cd /app/backend

# Check SERVICE_TYPE environment variable to determine what to run
if [ "$SERVICE_TYPE" = "celery" ]; then
    echo "Starting Celery worker..."
    # Celery doesn't need PORT, but Railway requires it - set a dummy value
    export PORT=${PORT:-8000}
    exec celery -A config worker --loglevel=info
elif [ "$SERVICE_TYPE" = "celery-beat" ]; then
    echo "Starting Celery Beat scheduler..."
    # Celery Beat doesn't need PORT, but Railway requires it - set a dummy value
    export PORT=${PORT:-8000}
    exec celery -A config beat --loglevel=info
else
    echo "Starting Gunicorn web server..."
    # Railway provides PORT env var, use it or default to 8000
    export PORT=${PORT:-8000}
    exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile - --log-level info config.wsgi:application
fi

