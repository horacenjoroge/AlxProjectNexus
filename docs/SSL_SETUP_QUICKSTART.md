# SSL Setup Quick Start Guide

This guide will walk you through setting up SSL/HTTPS access for your Provote deployment.

## Prerequisites

- Domain name pointing to your server's IP address
- Server with root/sudo access
- Ports 80 and 443 open in firewall
- Docker and Docker Compose installed

## Step-by-Step SSL Setup

### Step 1: Install Certbot

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**On CentOS/RHEL:**
```bash
sudo yum install certbot python3-certbot-nginx
```

**On macOS (using Homebrew):**
```bash
brew install certbot
```

### Step 2: Stop Nginx Temporarily

```bash
cd docker
docker-compose stop nginx
```

### Step 3: Obtain SSL Certificate

**For a single domain:**
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

**For multiple domains (including www):**
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

**What happens:**
- Certbot will start a temporary web server on port 80
- It will verify you own the domain
- Certificates will be saved to `/etc/letsencrypt/live/yourdomain.com/`

**Expected output:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/yourdomain.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Step 4: Copy Certificates to Docker Directory

```bash
# Create SSL directory in your project
mkdir -p docker/ssl

# Copy certificates (replace 'yourdomain.com' with your actual domain)
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/

# Set proper permissions
sudo chmod 644 docker/ssl/fullchain.pem
sudo chmod 600 docker/ssl/privkey.pem

# Change ownership (replace 'yourusername' with your actual username)
sudo chown $USER:$USER docker/ssl/fullchain.pem
sudo chown $USER:$USER docker/ssl/privkey.pem
```

### Step 5: Create Nginx SSL Configuration

Create `docker/nginx-ssl.conf`:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Let's Encrypt challenge (for renewal)
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

**Important:** Replace `yourdomain.com` and `www.yourdomain.com` with your actual domain names!

### Step 6: Update Docker Compose for SSL

Update your `docker/docker-compose.yml` or create `docker/docker-compose.prod.yml`:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
    - static_volume:/static:ro
    - media_volume:/media:ro
  depends_on:
    - web
  restart: unless-stopped
```

### Step 7: Update Environment Variables

Ensure your `.env` file has:

```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Step 8: Restart Services

```bash
cd docker
docker-compose up -d nginx
docker-compose restart web
```

### Step 9: Verify SSL Setup

**Test HTTPS access:**
```bash
# Test from command line
curl -I https://yourdomain.com/api/v1/

# Expected output:
# HTTP/2 200
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**Test in browser:**
1. Open `https://yourdomain.com/api/v1/`
2. Check for padlock icon in address bar
3. Click padlock to view certificate details

**Test HTTP redirect:**
```bash
curl -I http://yourdomain.com/api/v1/

# Expected output:
# HTTP/1.1 301 Moved Permanently
# Location: https://yourdomain.com/api/v1/
```

**Test SSL rating:**
Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

### Step 10: Set Up Auto-Renewal

Let's Encrypt certificates expire every 90 days. Set up automatic renewal:

**Create renewal script:** `scripts/renew-ssl.sh`

```bash
#!/bin/bash
# SSL Certificate Renewal Script

DOMAIN="yourdomain.com"
PROJECT_DIR="/path/to/AlxProjectNexus"

# Renew certificate
sudo certbot renew --quiet

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $PROJECT_DIR/docker/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $PROJECT_DIR/docker/ssl/

# Set permissions
sudo chmod 644 $PROJECT_DIR/docker/ssl/fullchain.pem
sudo chmod 600 $PROJECT_DIR/docker/ssl/privkey.pem
sudo chown $USER:$USER $PROJECT_DIR/docker/ssl/*.pem

# Reload Nginx
cd $PROJECT_DIR/docker
docker-compose exec nginx nginx -s reload

echo "SSL certificate renewed successfully"
```

**Make script executable:**
```bash
chmod +x scripts/renew-ssl.sh
```

**Add to crontab (runs twice daily):**
```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM and 2 PM daily):
0 2,14 * * * /path/to/AlxProjectNexus/scripts/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

## Troubleshooting

### Issue: "Failed to obtain certificate"

**Possible causes:**
- Domain not pointing to your server
- Port 80 blocked by firewall
- Another service using port 80

**Solutions:**
```bash
# Check DNS
nslookup yourdomain.com

# Check if port 80 is open
sudo netstat -tulpn | grep :80

# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Issue: "Certificate not found" after copying

**Solution:**
```bash
# Verify certificates exist
ls -la docker/ssl/

# Check permissions
ls -l docker/ssl/*.pem

# Verify Nginx can read them
docker-compose exec nginx ls -la /etc/nginx/ssl/
```

### Issue: "SSL certificate expired"

**Solution:**
```bash
# Manually renew
sudo certbot renew

# Copy certificates again
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem docker/ssl/

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Issue: "Mixed content" warnings

**Solution:**
- Ensure all API calls use `https://`
- Update `ALLOWED_HOSTS` in `.env`
- Set `SECURE_SSL_REDIRECT=True`

## Accessing Your Application via SSL

Once SSL is set up:

1. **API Access:**
   ```
   https://yourdomain.com/api/v1/
   https://yourdomain.com/api/docs/
   https://yourdomain.com/api/redoc/
   ```

2. **Admin Panel:**
   ```
   https://yourdomain.com/admin/
   ```

3. **All HTTP traffic automatically redirects to HTTPS**

## Security Checklist

- [x] SSL certificate obtained
- [x] Nginx configured for HTTPS
- [x] HTTP to HTTPS redirect working
- [x] Security headers configured
- [x] Auto-renewal set up
- [x] Environment variables updated
- [x] Firewall allows ports 80 and 443
- [x] SSL rating checked (A or A+)

## Quick Reference

```bash
# Check certificate expiration
openssl x509 -in docker/ssl/fullchain.pem -noout -dates

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# View Nginx SSL configuration
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf

# Test Nginx configuration
docker-compose exec nginx nginx -t

# Reload Nginx (after config changes)
docker-compose exec nginx nginx -s reload
```

## Next Steps

After SSL is set up:
1. Update your application URLs to use HTTPS
2. Test all API endpoints
3. Verify security headers
4. Set up monitoring for certificate expiration
5. Document your SSL setup for your team

---

**Need Help?** Check the full deployment guide: `docs/deployment-guide.md` (Section 5: SSL Setup)

