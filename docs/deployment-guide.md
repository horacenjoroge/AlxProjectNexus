# Comprehensive Deployment Guide

**Version:** 1.0  
**Last Updated:** 2025-11-22  
**Project:** Provote - Professional Voting Platform

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Variable Setup](#2-environment-variable-setup)
3. [Docker Deployment](#3-docker-deployment)
4. [Database Migrations](#4-database-migrations)
5. [SSL Setup](#5-ssl-setup)
6. [Monitoring Setup](#6-monitoring-setup)
7. [Backup Strategy](#7-backup-strategy)
8. [Post-Deployment Verification](#8-post-deployment-verification)
9. [Troubleshooting](#9-troubleshooting)
10. [Test Verification](#10-test-verification)

---

## 1. Prerequisites

### 1.1 System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Disk Space**: Minimum 10GB free space
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **CPU**: 2+ cores recommended

### 1.2 Network Requirements

- **Ports Required**:
  - `80` (HTTP) - Nginx
  - `443` (HTTPS) - Nginx (after SSL setup)
  - `5432` (PostgreSQL) - Internal only
  - `6379` (Redis) - Internal only
- **Domain Name**: Configured with DNS pointing to your server
- **Firewall**: Allow incoming traffic on ports 80 and 443

### 1.3 Software Installation

**Verify Docker Installation:**
```bash
docker --version
docker-compose --version
```

**Expected Output:**
```
Docker version 20.10.x or higher
Docker Compose version 2.x.x or higher
```

---

## 2. Environment Variable Setup

### 2.1 Create .env File

Create a `.env` file in the project root directory:

```bash
cd /path/to/AlxProjectNexus
cp .env.example .env  # If .env.example exists
# Or create manually:
touch .env
```

### 2.2 Required Environment Variables

**Minimum Required Variables:**

```bash
# Django Core Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings.production

# Database Configuration
DB_NAME=provote_production
DB_USER=provote_user
DB_PASSWORD=your-strong-database-password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security Settings (Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Geographic Restrictions (Default: Kenya only)
# Leave empty or set to ["KE"] for Kenya-only access
GEOIP_ALLOWED_COUNTRIES=KE
```

### 2.3 Generate SECRET_KEY

**Generate a secure SECRET_KEY:**

```bash
# Method 1: Using Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Method 2: Using Django shell
docker-compose exec web python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Method 3: Using OpenSSL (alternative)
openssl rand -base64 50
```

**Add to .env:**
```bash
SECRET_KEY=<generated-key-here>
```

### 2.4 Environment Variable Validation

**Verify all required variables are set:**

```bash
# Check .env file exists and has required variables
grep -E "SECRET_KEY|DEBUG|ALLOWED_HOSTS|DB_NAME|DB_PASSWORD" .env

# Expected output should show all variables with values
```

**Code Reference:** `backend/config/settings/base.py` (lines 13-29)

---

## 3. Docker Deployment

### 3.1 Production Docker Compose Configuration

Create a production-specific `docker-compose.prod.yml`:

```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - provote_network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - provote_network

  web:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: sh -c "cd /app/backend && python manage.py migrate --noinput --settings=config.settings.production && gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 --max-requests 1000 --max-requests-jitter 100 config.wsgi:application"
    working_dir: /app/backend
    volumes:
      - static_volume:/app/backend/staticfiles
      - media_volume:/app/backend/media
    env_file:
      - ../.env
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - PYTHONPATH=/app/backend
      - DJANGO_SETTINGS_MODULE=config.settings.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/').read()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - provote_network

  celery:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: sh -c "cd /app/backend && celery -A config worker --loglevel=info --concurrency=4"
    working_dir: /app/backend
    volumes:
      - static_volume:/app/backend/staticfiles
      - media_volume:/app/backend/media
    env_file:
      - ../.env
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - PYTHONPATH=/app/backend
      - DJANGO_SETTINGS_MODULE=config.settings.production
    depends_on:
      - db
      - redis
      - web
    restart: unless-stopped
    networks:
      - provote_network

  celery-beat:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: sh -c "cd /app/backend && python manage.py migrate --noinput --settings=config.settings.production && celery -A config beat --loglevel=info"
    working_dir: /app/backend
    env_file:
      - ../.env
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - PYTHONPATH=/app/backend
      - DJANGO_SETTINGS_MODULE=config.settings.production
    depends_on:
      - db
      - redis
      - web
    restart: unless-stopped
    networks:
      - provote_network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_volume:/static:ro
      - media_volume:/media:ro
    depends_on:
      - web
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - provote_network

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:

networks:
  provote_network:
    driver: bridge
```

### 3.2 Build Docker Images

```bash
cd docker
docker-compose -f docker-compose.prod.yml build --no-cache
```

**Expected Output:**
```
Building web...
Step 1/10 : FROM python:3.11-slim
...
Successfully built <image-id>
```

### 3.3 Start Services

```bash
# Start all services in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker-compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME                STATUS          PORTS
docker-db-1         Up (healthy)    5432/tcp
docker-redis-1      Up (healthy)    6379/tcp
docker-web-1        Up (healthy)    8000/tcp
docker-celery-1     Up              ...
docker-celery-beat-1 Up             ...
docker-nginx-1      Up (healthy)    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 3.4 Verify Service Health

```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=50 web
docker-compose -f docker-compose.prod.yml logs --tail=50 db
docker-compose -f docker-compose.prod.yml logs --tail=50 redis
```

**Code Reference:** `docker/docker-compose.yml`

---

## 4. Database Migrations

### 4.1 Run Initial Migrations

```bash
# Run all pending migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --settings=config.settings.production

# Verify migrations applied
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations --settings=config.settings.production
```

**Expected Output:**
```
[X] 0001_initial
[X] 0002_...
...
```

### 4.2 Verify Database Connection

```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell --settings=config.settings.production

# In PostgreSQL shell, run:
# \dt  # List all tables
# \q   # Quit
```

### 4.3 Create Database Superuser

```bash
# Interactive superuser creation
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser --settings=config.settings.production

# Or non-interactive (for automation)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser --noinput --settings=config.settings.production \
  --username admin --email admin@yourdomain.com
# Then set password separately
docker-compose -f docker-compose.prod.yml exec web python manage.py shell --settings=config.settings.production
```

**In Django shell:**
```python
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.set_password('your-secure-password')
user.save()
exit()
```

### 4.4 Migration Best Practices

1. **Always backup before migrations:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec db pg_dump -U ${DB_USER} ${DB_NAME} > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test migrations on staging first**

3. **Run migrations during low-traffic periods**

4. **Monitor for errors during migration**

**Code Reference:** `backend/config/settings/production.py`

---

## 5. SSL Setup

### 5.1 Using Let's Encrypt (Recommended)

**Install Certbot:**

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# On CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### 5.2 Obtain SSL Certificate

```bash
# Stop Nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### 5.3 Configure Nginx for SSL

Create `docker/nginx-ssl.conf`:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Static files
    location /static/ {
        alias /static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Django
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5.4 Copy SSL Certificates to Docker Volume

```bash
# Create SSL directory
mkdir -p docker/ssl

# Copy certificates (adjust paths as needed)
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/

# Set proper permissions
sudo chmod 644 docker/ssl/fullchain.pem
sudo chmod 600 docker/ssl/privkey.pem
```

### 5.5 Update Docker Compose for SSL

Update `docker-compose.prod.yml` nginx service:

```yaml
nginx:
  volumes:
    - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
```

### 5.6 Restart Nginx

```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

### 5.7 Auto-Renewal Setup

**Create renewal script:** `scripts/renew-ssl.sh`

```bash
#!/bin/bash
# Renew SSL certificates and reload Nginx

certbot renew --quiet

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/

# Reload Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

**Add to crontab (runs twice daily):**

```bash
# Edit crontab
crontab -e

# Add line:
0 0,12 * * * /path/to/scripts/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

**Code Reference:** `docker/nginx.conf`

---

## 6. Monitoring Setup

### 6.1 Health Check Endpoints

**Built-in Health Checks:**

- **API Root**: `http://yourdomain.com/api/v1/` (200 OK)
- **Admin**: `http://yourdomain.com/admin/` (302 redirect or 200 OK)
- **Schema**: `http://yourdomain.com/api/schema/` (200 OK)

**Test Health Checks:**

```bash
# API Root
curl -I https://yourdomain.com/api/v1/

# Expected: HTTP/2 200

# Admin (should redirect if not authenticated)
curl -I https://yourdomain.com/admin/

# Expected: HTTP/2 302 or 200
```

### 6.2 Docker Health Monitoring

**Monitor Container Health:**

```bash
# Check all container statuses
docker-compose -f docker-compose.prod.yml ps

# Monitor resource usage
docker stats

# Check specific service logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100 web
```

### 6.3 Application Logging

**View Application Logs:**

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f nginx

# Last 100 lines with timestamps
docker-compose -f docker-compose.prod.yml logs --tail=100 -t web
```

**Log Locations:**
- **Application Logs**: Docker container stdout/stderr
- **Nginx Logs**: `/var/log/nginx/` (inside container)
- **Database Logs**: PostgreSQL logs (if configured)

### 6.4 Database Monitoring

**Monitor Database:**

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U ${DB_USER} -d ${DB_NAME}

# Check database size
SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));

# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 6.5 Redis Monitoring

**Monitor Redis:**

```bash
# Connect to Redis CLI
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Check Redis info
INFO

# Check memory usage
INFO memory

# Monitor commands in real-time
MONITOR
```

### 6.6 External Monitoring Tools

**Recommended Tools:**

1. **Prometheus + Grafana**
   - Metrics collection and visualization
   - Set up exporters for PostgreSQL, Redis, Nginx

2. **Sentry** (Error Tracking)
   - Add to `requirements/production.txt`:
     ```
     sentry-sdk==1.40.0
     ```
   - Configure in `settings/production.py`:
     ```python
     import sentry_sdk
     from sentry_sdk.integrations.django import DjangoIntegration
     
     sentry_sdk.init(
         dsn="your-sentry-dsn",
         integrations=[DjangoIntegration()],
         traces_sample_rate=0.1,
     )
     ```

3. **Uptime Monitoring**
   - UptimeRobot
   - Pingdom
   - StatusCake

**Code Reference:** `backend/config/settings/production.py` (LOGGING configuration)

---

## 7. Backup Strategy

### 7.1 Database Backup

#### **Automated Daily Backup**

**Create backup script:** `scripts/backup-database.sh`

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME=${DB_NAME:-provote_production}
DB_USER=${DB_USER:-provote_user}

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Verify backup
if [ -f "$BACKUP_DIR/backup_$DATE.sql.gz" ]; then
    echo "Backup successful: backup_$DATE.sql.gz"
    # Optional: Upload to S3, Google Cloud Storage, etc.
else
    echo "Backup failed!" >&2
    exit 1
fi
```

**Schedule with cron:**

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup-database.sh >> /var/log/backup.log 2>&1
```

#### **Manual Backup**

```bash
# Full database backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U ${DB_USER} ${DB_NAME} > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U ${DB_USER} ${DB_NAME} | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 7.2 Redis Backup

**Redis Persistence (AOF):**

Redis is configured with `--appendonly yes` in docker-compose, which persists data to disk.

**Manual Redis Backup:**

```bash
# Create Redis backup
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# Copy Redis data file
docker cp $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 7.3 Media Files Backup

**Backup Media Files:**

```bash
# Backup media directory
docker-compose -f docker-compose.prod.yml exec web tar -czf - /app/backend/media | cat > media_backup_$(date +%Y%m%d_%H%M%S).tar.gz

# Or copy from volume
docker run --rm -v provote_media_volume:/data -v $(pwd):/backup alpine tar czf /backup/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### 7.4 Static Files Backup

Static files are generated from code, so they don't need backup. However, if you have custom static files:

```bash
docker run --rm -v provote_static_volume:/data -v $(pwd):/backup alpine tar czf /backup/static_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### 7.5 Restore Procedures

#### **Restore Database**

```bash
# Stop web service
docker-compose -f docker-compose.prod.yml stop web celery celery-beat

# Restore from backup
gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz | docker-compose -f docker-compose.prod.yml exec -T db psql -U ${DB_USER} ${DB_NAME}

# Or from uncompressed backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U ${DB_USER} ${DB_NAME} < backup_YYYYMMDD_HHMMSS.sql

# Restart services
docker-compose -f docker-compose.prod.yml start web celery celery-beat
```

#### **Restore Redis**

```bash
# Stop Redis
docker-compose -f docker-compose.prod.yml stop redis

# Restore Redis data
docker cp redis_backup_YYYYMMDD_HHMMSS.rdb $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb

# Start Redis
docker-compose -f docker-compose.prod.yml start redis
```

#### **Restore Media Files**

```bash
# Extract media backup
tar -xzf media_backup_YYYYMMDD_HHMMSS.tar.gz

# Copy to volume
docker run --rm -v provote_media_volume:/data -v $(pwd):/backup alpine sh -c "cp -r /backup/media/* /data/"
```

### 7.6 Backup Storage Recommendations

1. **Local Storage**: Keep last 7 days locally
2. **Cloud Storage**: Upload to S3, Google Cloud Storage, or Azure Blob
3. **Offsite Backup**: Weekly backups to different location
4. **Backup Verification**: Regularly test restore procedures

**Code Reference:** Database backup commands use PostgreSQL's `pg_dump` utility

---

## 8. Post-Deployment Verification

### 8.1 Service Health Checks

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Expected: All services show "Up (healthy)" or "Up"

# Test API endpoint
curl -I https://yourdomain.com/api/v1/

# Expected: HTTP/2 200

# Test admin panel
curl -I https://yourdomain.com/admin/

# Expected: HTTP/2 302 (redirect to login) or 200
```

### 8.2 Database Verification

```bash
# Verify database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell --settings=config.settings.production

# In PostgreSQL:
# SELECT COUNT(*) FROM polls_poll;
# SELECT COUNT(*) FROM votes_vote;
# \q
```

### 8.3 Static Files Verification

```bash
# Verify static files collected
docker-compose -f docker-compose.prod.yml exec web ls -la /app/backend/staticfiles/

# Test static file serving
curl -I https://yourdomain.com/static/admin/css/base.css

# Expected: HTTP/2 200
```

### 8.4 Celery Verification

```bash
# Check Celery worker is running
docker-compose -f docker-compose.prod.yml exec celery celery -A config inspect active

# Check Celery Beat is running
docker-compose -f docker-compose.prod.yml logs celery-beat | grep "beat: Starting"

# Test Celery task
docker-compose -f docker-compose.prod.yml exec web python manage.py shell --settings=config.settings.production
```

**In Django shell:**
```python
from apps.analytics.tasks import update_poll_analytics
result = update_poll_analytics.delay(1)  # Replace 1 with actual poll ID
print(result.get(timeout=10))
```

### 8.5 SSL Verification

```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check SSL rating
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# Verify HTTPS redirect
curl -I http://yourdomain.com/

# Expected: HTTP/1.1 301 Moved Permanently
# Location: https://yourdomain.com/
```

### 8.6 Security Verification

```bash
# Test security headers
curl -I https://yourdomain.com/api/v1/

# Should include:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
```

### 8.7 Performance Verification

```bash
# Test API response time
time curl -s https://yourdomain.com/api/v1/ > /dev/null

# Expected: < 200ms

# Load test (if Apache Bench installed)
ab -n 100 -c 10 https://yourdomain.com/api/v1/
```

---

## 9. Troubleshooting

### 9.1 Common Issues

#### **Issue: Services won't start**

**Symptoms:**
- `docker-compose ps` shows services as "Restarting" or "Exited"

**Solutions:**
```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs db

# Check environment variables
docker-compose -f docker-compose.prod.yml config

# Verify .env file exists and has correct values
cat .env | grep -E "SECRET_KEY|DB_PASSWORD"
```

#### **Issue: Database connection errors**

**Symptoms:**
- `OperationalError: could not connect to server`
- `FATAL: password authentication failed`

**Solutions:**
```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database credentials in .env
grep -E "DB_NAME|DB_USER|DB_PASSWORD" .env

# Test database connection
docker-compose -f docker-compose.prod.yml exec db psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT 1;"
```

#### **Issue: Migration errors**

**Symptoms:**
- `django.db.utils.OperationalError` during migrations
- `Migration ... is applied but missing`

**Solutions:**
```bash
# Check migration status
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations --settings=config.settings.production

# Fake migration (if needed, be careful!)
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --fake app_name migration_name --settings=config.settings.production

# Reset migrations (DESTRUCTIVE - backup first!)
# Only use in development
```

#### **Issue: Static files not loading**

**Symptoms:**
- 404 errors for `/static/` URLs
- CSS/JS not loading

**Solutions:**
```bash
# Recollect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --settings=config.settings.production

# Verify static files directory
docker-compose -f docker-compose.prod.yml exec web ls -la /app/backend/staticfiles/

# Check Nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

#### **Issue: SSL certificate errors**

**Symptoms:**
- Browser shows "Not Secure" warning
- Certificate expired

**Solutions:**
```bash
# Check certificate expiration
openssl x509 -in docker/ssl/fullchain.pem -noout -dates

# Renew certificate
sudo certbot renew

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem docker/ssl/

# Reload Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 9.2 Debugging Commands

```bash
# Enter web container shell
docker-compose -f docker-compose.prod.yml exec web sh

# Check Django settings
docker-compose -f docker-compose.prod.yml exec web python manage.py diffsettings --settings=config.settings.production

# Check for configuration errors
docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy --settings=config.settings.production

# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

---

## 10. Test Verification

### 10.1 Deployment Guide Tests

**Test File:** `backend/tests/test_deployment_guide.py`

**Purpose:** Verify that all deployment steps are documented and can be executed.

### 10.2 Fresh System Deployment Test

**Manual Test Procedure:**

1. **Set up fresh Ubuntu server** (or use VM)
2. **Follow deployment guide step-by-step**
3. **Verify each step completes successfully**
4. **Document any issues or missing steps**

**Automated Test Checklist:**

```bash
# Test 1: Verify Docker is installed
docker --version && docker-compose --version
# Expected: Both commands succeed

# Test 2: Verify .env file structure
grep -E "SECRET_KEY|DEBUG|ALLOWED_HOSTS|DB_NAME" .env
# Expected: All variables present

# Test 3: Verify Docker Compose file syntax
docker-compose -f docker-compose.prod.yml config
# Expected: No syntax errors

# Test 4: Verify services can start
docker-compose -f docker-compose.prod.yml up -d
sleep 30
docker-compose -f docker-compose.prod.yml ps
# Expected: All services healthy

# Test 5: Verify database migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations --settings=config.settings.production | grep "\[ \]"
# Expected: No unapplied migrations

# Test 6: Verify API is accessible
curl -f https://yourdomain.com/api/v1/ || curl -f http://localhost:8001/api/v1/
# Expected: HTTP 200

# Test 7: Verify SSL (if configured)
curl -I https://yourdomain.com/api/v1/ 2>&1 | grep "HTTP/2 200"
# Expected: HTTP/2 200
```

### 10.3 Documentation Completeness Test

**Verify all sections are documented:**

```bash
# Check deployment guide exists
test -f docs/deployment-guide.md && echo "✓ Deployment guide exists"

# Check all required sections
grep -E "^## [0-9]+\." docs/deployment-guide.md
# Expected: All 10 sections present

# Check code references exist
grep -o "`[^`]*`" docs/deployment-guide.md | grep -E "docker/|backend/" | while read ref; do
    file=$(echo $ref | sed 's/`//g' | cut -d: -f1)
    test -f "$file" || echo "Missing: $file"
done
# Expected: No missing files
```

### 10.4 Step-by-Step Verification

**Create test script:** `scripts/test-deployment.sh`

```bash
#!/bin/bash
# Test deployment guide completeness

set -e

echo "Testing deployment guide..."

# Test 1: Prerequisites
echo "✓ Testing prerequisites..."
docker --version > /dev/null
docker-compose --version > /dev/null

# Test 2: Environment variables
echo "✓ Testing environment variables..."
test -f .env || (echo "✗ .env file missing" && exit 1)
grep -q "SECRET_KEY" .env || (echo "✗ SECRET_KEY missing" && exit 1)
grep -q "DB_NAME" .env || (echo "✗ DB_NAME missing" && exit 1)

# Test 3: Docker Compose
echo "✓ Testing Docker Compose..."
docker-compose -f docker/docker-compose.prod.yml config > /dev/null

# Test 4: Services can build
echo "✓ Testing Docker build..."
docker-compose -f docker/docker-compose.prod.yml build --quiet

echo "✓ All deployment tests passed!"
```

**Run test:**
```bash
chmod +x scripts/test-deployment.sh
./scripts/test-deployment.sh
```

---

## Appendix

### A. Quick Reference Commands

```bash
# Start services
docker-compose -f docker/docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker/docker-compose.prod.yml down

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Run migrations
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py migrate --settings=config.settings.production

# Create superuser
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser --settings=config.settings.production

# Backup database
docker-compose -f docker/docker-compose.prod.yml exec -T db pg_dump -U ${DB_USER} ${DB_NAME} > backup.sql

# Restore database
docker-compose -f docker/docker-compose.prod.yml exec -T db psql -U ${DB_USER} ${DB_NAME} < backup.sql
```

### B. Production Checklist

- [ ] All environment variables set in `.env`
- [ ] `SECRET_KEY` is strong and unique
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] Database credentials are secure
- [ ] SSL certificate installed and configured
- [ ] Nginx SSL configuration tested
- [ ] All migrations applied
- [ ] Superuser created
- [ ] Static files collected
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Firewall rules configured
- [ ] Rate limiting enabled (remove `DISABLE_RATE_LIMITING`)
- [ ] Geographic restrictions configured (Kenya only)
- [ ] Email configuration tested
- [ ] Logging configured
- [ ] Documentation reviewed

### C. Security Hardening

1. **Change default passwords**
2. **Use strong SECRET_KEY**
3. **Enable SSL/TLS**
4. **Configure firewall** (UFW, iptables)
5. **Regular security updates**
6. **Monitor for vulnerabilities**
7. **Use secrets management** (Docker secrets, AWS Secrets Manager, etc.)

### D. Scaling Considerations

- **Horizontal Scaling**: Add more web containers
- **Database**: Consider read replicas for high traffic
- **Redis**: Use Redis Cluster for high availability
- **Load Balancer**: Configure Nginx upstream for multiple instances
- **CDN**: Use CloudFlare or similar for static assets

---

**Document Maintained By:** DevOps Team  
**Last Review Date:** 2025-11-22  
**Next Review Date:** 2026-02-22

