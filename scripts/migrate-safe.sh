#!/bin/bash
# Safe migration wrapper script
# Usage: ./scripts/migrate-safe.sh [app_name] [migration_name]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.prod.yml}"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

echo "=========================================="
echo "Safe Migration Process"
echo "=========================================="

# Step 1: Backup
echo ""
echo "Step 1: Creating backup..."
if ! "$SCRIPT_DIR/backup-database.sh" --pre-migration; then
    echo "✗ Backup failed! Aborting migration."
    exit 1
fi

# Step 2: Check migration safety
if [ $# -ge 2 ]; then
    APP_NAME="$1"
    MIGRATION_NAME="$2"
    
    echo ""
    echo "Step 2: Checking migration safety..."
    if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T web \
        python manage.py check_migration_safety "$APP_NAME" "$MIGRATION_NAME" \
        --settings=config.settings.production; then
        echo "✗ Migration is not safe! Review warnings above."
        read -p "Continue anyway? (yes/no): " continue_migration
        if [ "$continue_migration" != "yes" ]; then
            echo "Migration cancelled."
            exit 1
        fi
    fi
    
    # Step 3: Validate migration
    echo ""
    echo "Step 3: Validating migration..."
    if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T web \
        python manage.py validate_migration "$APP_NAME" "$MIGRATION_NAME" \
        --settings=config.settings.production; then
        echo "✗ Migration validation failed!"
        exit 1
    fi
    
    # Step 4: Apply migration
    echo ""
    echo "Step 4: Applying migration..."
    if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T web \
        python manage.py migrate "$APP_NAME" "$MIGRATION_NAME" \
        --settings=config.settings.production; then
        echo "✗ Migration failed!"
        echo "To rollback, run: ./scripts/restore-database.sh <backup_file>"
        exit 1
    fi
    
    # Step 5: Verify migration data
    echo ""
    echo "Step 5: Verifying migration data..."
    if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T web \
        python manage.py verify_migration_data "$APP_NAME" "$MIGRATION_NAME" \
        --settings=config.settings.production; then
        echo "⚠️  Data verification found issues. Review above."
    fi
else
    # Apply all pending migrations
    echo ""
    echo "Step 2: Applying all pending migrations..."
    if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T web \
        python manage.py migrate --settings=config.settings.production; then
        echo "✗ Migration failed!"
        echo "To rollback, run: ./scripts/restore-database.sh <backup_file>"
        exit 1
    fi
fi

# Step 6: Health check
echo ""
echo "Step 6: Verifying application health..."
if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T web \
    curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "⚠️  Health check failed. Application may be experiencing issues."
else
    echo "✓ Application health check passed"
fi

echo ""
echo "=========================================="
echo "Migration completed successfully!"
echo "=========================================="

