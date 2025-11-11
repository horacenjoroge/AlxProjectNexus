# Deployment Guide

## Production Deployment

### Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificate (Let's Encrypt recommended)

### Steps

1. **Set Environment Variables**

   Create `.env` file with production values:
   ```bash
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DB_NAME=provote_prod
   DB_USER=provote_user
   DB_PASSWORD=strong-password
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

2. **Build and Start Services**

   ```bash
   cd docker
   docker-compose -f docker-compose.yml up -d --build
   ```

3. **Run Migrations**

   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Collect Static Files**

   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

5. **Create Superuser**

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Configure Nginx for SSL**

   Update `docker/nginx.conf` to include SSL configuration.

7. **Set up Celery Beat**

   Celery Beat will automatically start with docker-compose.

## Environment-Specific Settings

### Development
- Uses `config.settings.development`
- Debug toolbar enabled
- Console email backend
- Less strict security

### Production
- Uses `config.settings.production`
- WhiteNoise for static files
- SMTP email backend
- Strict security headers
- SSL redirect enabled

### Testing
- Uses `config.settings.test`
- In-memory SQLite database
- Synchronous Celery tasks
- Disabled logging

## Monitoring

### Health Checks

All services include health checks:
- Database: `pg_isready`
- Redis: `redis-cli ping`
- Web: HTTP check on `/admin/`
- Nginx: HTTP check on `/`

### Logs

View logs:
```bash
docker-compose logs -f web
docker-compose logs -f celery
```

## Backup

### Database Backup

```bash
docker-compose exec db pg_dump -U provote_user provote_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U provote_user provote_db < backup.sql
```

## Scaling

### Horizontal Scaling

To scale web workers:
```bash
docker-compose up -d --scale web=3
```

### Load Balancing

Configure Nginx upstream for multiple web instances.

## Security Checklist

- [ ] Change default database passwords
- [ ] Set strong SECRET_KEY
- [ ] Enable SSL/TLS
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerts
- [ ] Regular security updates

