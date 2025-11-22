#!/bin/bash
# Database restore script for Provote
# Usage: ./scripts/restore-database.sh <backup_file> [--confirm]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [--confirm]"
    echo ""
    echo "Available backups:"
    ls -lh "$PROJECT_ROOT/backups/database/"*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"
CONFIRM="${2:-}"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Set defaults
DB_NAME="${DB_NAME:-provote_production}"
DB_USER="${DB_USER:-provote_user}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.prod.yml}"

# Resolve backup file path
if [ ! -f "$BACKUP_FILE" ]; then
    # Try relative to backups directory
    if [ -f "$PROJECT_ROOT/backups/database/$BACKUP_FILE" ]; then
        BACKUP_FILE="$PROJECT_ROOT/backups/database/$BACKUP_FILE"
    else
        echo "Error: Backup file not found: $BACKUP_FILE"
        exit 1
    fi
fi

echo "=========================================="
echo "Database Restore"
echo "=========================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST"
echo "Backup file: $BACKUP_FILE"
echo ""
echo "⚠️  WARNING: This will overwrite the current database!"
echo ""

# Confirmation
if [ "$CONFIRM" != "--confirm" ]; then
    read -p "Are you sure you want to restore? Type 'yes' to continue: " response
    if [ "$response" != "yes" ]; then
        echo "Restore cancelled."
        exit 0
    fi
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if backup file is not empty
if [ ! -s "$BACKUP_FILE" ]; then
    echo "Error: Backup file is empty: $BACKUP_FILE"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found"
    exit 1
fi

# Check if database container is running
if ! docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" ps db | grep -q "Up"; then
    echo "Error: Database container is not running"
    exit 1
fi

# Stop application services (to prevent data corruption)
echo "Stopping application services..."
docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" stop web celery celery-beat || true
echo "✓ Services stopped"

# Create backup before restore (safety measure)
echo ""
echo "Creating safety backup before restore..."
SAFETY_BACKUP="$PROJECT_ROOT/backups/database/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T db \
    pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" | \
    gzip > "$SAFETY_BACKUP"
echo "✓ Safety backup created: $SAFETY_BACKUP"

# Restore database
echo ""
echo "Restoring database..."
if gunzip -c "$BACKUP_FILE" | \
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T db \
    psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME"; then
    echo "✓ Database restored successfully"
else
    echo "✗ Restore failed!"
    echo "You can restore the safety backup if needed:"
    echo "  $0 $SAFETY_BACKUP --confirm"
    exit 1
fi

# Verify restore
echo ""
echo "Verifying restore..."
RECORD_COUNT=$(docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T db \
    psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" "$DB_NAME" | tr -d ' ')
echo "Tables found: $RECORD_COUNT"

if [ "$RECORD_COUNT" -eq "0" ]; then
    echo "⚠️  Warning: No tables found after restore. Restore may have failed."
fi

# Restart application services
echo ""
echo "Restarting application services..."
docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" start web celery celery-beat
echo "✓ Services restarted"

echo ""
echo "=========================================="
echo "Restore completed!"
echo "Safety backup: $SAFETY_BACKUP"
echo "=========================================="

