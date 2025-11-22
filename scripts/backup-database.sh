#!/bin/bash
# Database backup script for Provote
# Usage: ./scripts/backup-database.sh [--pre-migration] [--output-dir DIR]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/database}"
PRE_MIGRATION="${PRE_MIGRATION:-false}"
OUTPUT_DIR="${OUTPUT_DIR:-$BACKUP_DIR}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --pre-migration)
            PRE_MIGRATION=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--pre-migration] [--output-dir DIR]"
            exit 1
            ;;
    esac
done

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

# Create backup directory
mkdir -p "$OUTPUT_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="backup"
if [ "$PRE_MIGRATION" = "true" ]; then
    BACKUP_PREFIX="pre_migration_backup"
fi
BACKUP_FILE="$OUTPUT_DIR/${BACKUP_PREFIX}_${TIMESTAMP}.sql.gz"

echo "=========================================="
echo "Database Backup"
echo "=========================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST"
echo "Backup file: $BACKUP_FILE"
echo ""

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

# Create backup
echo "Creating backup..."
if docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T db \
    pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" | \
    gzip > "$BACKUP_FILE"; then
    echo "✓ Backup created successfully: $BACKUP_FILE"
else
    echo "✗ Backup failed!"
    exit 1
fi

# Verify backup file exists and is not empty
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    echo "✗ Backup file is missing or empty!"
    exit 1
fi

# Get backup file size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Create symlink to latest backup
LATEST_LINK="$OUTPUT_DIR/latest_backup.sql.gz"
if [ "$PRE_MIGRATION" = "true" ]; then
    LATEST_LINK="$OUTPUT_DIR/latest_pre_migration_backup.sql.gz"
fi

rm -f "$LATEST_LINK"
ln -s "$(basename "$BACKUP_FILE")" "$LATEST_LINK"
echo "✓ Latest backup link created: $LATEST_LINK"

# Cleanup old backups (keep last 30 days)
echo ""
echo "Cleaning up old backups (keeping last 30 days)..."
find "$OUTPUT_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -mtime +30 -delete
echo "✓ Cleanup complete"

# Optional: Upload to cloud storage
if [ -n "${BACKUP_UPLOAD_COMMAND:-}" ]; then
    echo ""
    echo "Uploading backup to cloud storage..."
    eval "$BACKUP_UPLOAD_COMMAND" "$BACKUP_FILE"
    echo "✓ Upload complete"
fi

echo ""
echo "=========================================="
echo "Backup completed successfully!"
echo "Backup file: $BACKUP_FILE"
echo "=========================================="

