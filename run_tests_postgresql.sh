#!/bin/bash
# Script to run all tests with PostgreSQL
# Usage: ./run_tests_postgresql.sh

set -e

echo "Starting PostgreSQL container..."
docker-compose -f docker/docker-compose.yml up -d db

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Creating test database..."
docker-compose -f docker/docker-compose.yml exec -T db psql -U provote_user -d postgres -c "CREATE DATABASE provote_test_db;" 2>&1 || echo "Database might already exist"

echo "Running tests with PostgreSQL..."
export DJANGO_SETTINGS_MODULE=config.settings.test_postgresql
export DB_HOST=localhost
export DB_PORT=5433
export DB_USER=provote_user
export DB_PASSWORD=provote_password

pytest backend/ --no-cov -v "$@"

