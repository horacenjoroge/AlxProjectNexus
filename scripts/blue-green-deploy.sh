#!/bin/bash
# Blue-Green Deployment Script for Provote
# Usage: ./scripts/blue-green-deploy.sh [--rollback]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BLUE_COMPOSE="$PROJECT_ROOT/docker/docker-compose.prod.yml"
GREEN_COMPOSE="$PROJECT_ROOT/docker/docker-compose.prod-green.yml"
ROLLBACK="${ROLLBACK:-false}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--rollback]"
            exit 1
            ;;
    esac
done

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

echo "=========================================="
echo "Blue-Green Deployment"
echo "=========================================="

# Determine current active environment
CURRENT_ENV="blue"
if docker-compose -f "$GREEN_COMPOSE" ps web 2>/dev/null | grep -q "Up"; then
    CURRENT_ENV="green"
fi

echo "Current active environment: $CURRENT_ENV"

if [ "$ROLLBACK" = "true" ]; then
    # Rollback: switch back to previous environment
    if [ "$CURRENT_ENV" = "green" ]; then
        TARGET_ENV="blue"
        TARGET_COMPOSE="$BLUE_COMPOSE"
        OLD_COMPOSE="$GREEN_COMPOSE"
    else
        TARGET_ENV="green"
        TARGET_COMPOSE="$GREEN_COMPOSE"
        OLD_COMPOSE="$BLUE_COMPOSE"
    fi
    
    echo ""
    echo "Rolling back to $TARGET_ENV environment..."
else
    # Deploy: switch to new environment
    if [ "$CURRENT_ENV" = "blue" ]; then
        TARGET_ENV="green"
        TARGET_COMPOSE="$GREEN_COMPOSE"
        OLD_COMPOSE="$BLUE_COMPOSE"
    else
        TARGET_ENV="blue"
        TARGET_COMPOSE="$BLUE_COMPOSE"
        OLD_COMPOSE="$GREEN_COMPOSE"
    fi
    
    echo ""
    echo "Deploying to $TARGET_ENV environment..."
fi

# Step 1: Build new environment
echo ""
echo "Step 1: Building $TARGET_ENV environment..."
if ! docker-compose -f "$TARGET_COMPOSE" build; then
    echo "✗ Build failed!"
    exit 1
fi
echo "✓ Build complete"

# Step 2: Start new environment
echo ""
echo "Step 2: Starting $TARGET_ENV environment..."
if ! docker-compose -f "$TARGET_COMPOSE" up -d; then
    echo "✗ Failed to start $TARGET_ENV environment!"
    exit 1
fi
echo "✓ Services started"

# Step 3: Wait for health checks
echo ""
echo "Step 3: Waiting for health checks..."
MAX_WAIT=300
WAIT_TIME=0
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if docker-compose -f "$TARGET_COMPOSE" ps web | grep -q "healthy"; then
        echo "✓ $TARGET_ENV environment is healthy"
        break
    fi
    echo "  Waiting... ($WAIT_TIME/$MAX_WAIT seconds)"
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo "✗ Health check timeout!"
    echo "Rolling back..."
    docker-compose -f "$TARGET_COMPOSE" down
    exit 1
fi

# Step 4: Verify new environment
echo ""
echo "Step 4: Verifying $TARGET_ENV environment..."

# Check health endpoint
if [ "$TARGET_ENV" = "green" ]; then
    HEALTH_URL="http://localhost:8002/health/"
else
    HEALTH_URL="http://localhost:8000/health/"
fi

if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✓ Health endpoint responding"
else
    echo "✗ Health endpoint not responding!"
    echo "Rolling back..."
    docker-compose -f "$TARGET_COMPOSE" down
    exit 1
fi

# Step 5: Run smoke tests (if available)
if [ -f "$PROJECT_ROOT/backend/tests/test_smoke.py" ]; then
    echo ""
    echo "Step 5: Running smoke tests..."
    if docker-compose -f "$TARGET_COMPOSE" exec -T web \
        python manage.py test backend.tests.test_smoke --settings=config.settings.production; then
        echo "✓ Smoke tests passed"
    else
        echo "✗ Smoke tests failed!"
        echo "Rolling back..."
        docker-compose -f "$TARGET_COMPOSE" down
        exit 1
    fi
fi

# Step 6: Switch traffic (update load balancer/nginx)
echo ""
echo "Step 6: Switching traffic to $TARGET_ENV..."
echo "⚠️  Manual step required: Update load balancer/nginx configuration"
echo "   to point to $TARGET_ENV environment"
echo ""
read -p "Press Enter after traffic has been switched..."

# Step 7: Monitor new environment
echo ""
echo "Step 7: Monitoring $TARGET_ENV environment..."
echo "Monitor logs: docker-compose -f $TARGET_COMPOSE logs -f"
echo "Monitor health: curl $HEALTH_URL"
echo ""
read -p "Press Enter to continue after monitoring period..."

# Step 8: Stop old environment (optional)
echo ""
read -p "Stop old $CURRENT_ENV environment? (yes/no): " stop_old
if [ "$stop_old" = "yes" ]; then
    echo "Stopping $CURRENT_ENV environment..."
    docker-compose -f "$OLD_COMPOSE" stop
    echo "✓ Old environment stopped"
fi

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "Active environment: $TARGET_ENV"
echo "=========================================="

