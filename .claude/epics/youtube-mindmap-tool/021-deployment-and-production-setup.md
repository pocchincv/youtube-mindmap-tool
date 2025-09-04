---
id: 021-deployment-and-production-setup
title: Deployment and Production Environment Setup
epic: youtube-mindmap-tool
status: backlog
priority: medium
complexity: medium
estimated_days: 3
dependencies: [001-project-setup-and-infrastructure, 020-performance-optimization]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [deployment, production, devops, infrastructure, ci-cd]
---

# Deployment and Production Environment Setup

## Description
Set up production deployment infrastructure, CI/CD pipeline, monitoring, and scalable hosting solution for the YouTube Mind Map Tool with proper security, backup, and maintenance procedures.

## Acceptance Criteria
- [ ] Production-ready Docker containerization for both frontend and backend
- [ ] CI/CD pipeline with automated testing and deployment
- [ ] Production database setup with backups and migrations
- [ ] Environment configuration management for different deployment stages
- [ ] SSL/TLS certificates and security hardening
- [ ] Load balancing and horizontal scaling capabilities
- [ ] Monitoring and alerting system for production health
- [ ] Backup and disaster recovery procedures
- [ ] CDN setup for static asset delivery
- [ ] Domain configuration and DNS management
- [ ] Production secrets and API key management
- [ ] Log aggregation and analysis system

## Technical Requirements

### Docker Containerization:
```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for Development:
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000
    networks:
      - app-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - database
      - redis
    environment:
      - DATABASE_URL=postgresql://user:password@database:5432/mindmap_db
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=development
    volumes:
      - ./backend:/app
      - uploaded_files:/app/uploads
    networks:
      - app-network

  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=mindmap_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  uploaded_files:

networks:
  app-network:
    driver: bridge
```

### CI/CD Pipeline (GitHub Actions):
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run backend tests
        run: |
          cd backend
          pytest tests/ -v --cov=./ --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
          ENVIRONMENT: test
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm run test:ci
      
      - name: Build frontend
        run: |
          cd frontend
          npm run build

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Deploy to production
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/mindmap-app
            docker-compose pull
            docker-compose up -d
            docker system prune -f
```

### Production Environment Configuration:
```python
# config/production.py
import os
from typing import Optional

class ProductionConfig:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/mindmap_prod')
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '20'))
    DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '30'))
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    
    # API Keys (from secrets management)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    
    # File Storage
    UPLOAD_PATH = os.getenv('UPLOAD_PATH', '/var/app/uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '100000000'))  # 100MB
    
    # External Services
    CDN_URL = os.getenv('CDN_URL', '')
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    
    # Performance
    WORKER_PROCESSES = int(os.getenv('WORKER_PROCESSES', '4'))
    MAX_CONCURRENT_JOBS = int(os.getenv('MAX_CONCURRENT_JOBS', '10'))
    
    # Monitoring
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

config = ProductionConfig()
```

### Nginx Configuration:
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:80;
    }
    
    upstream backend {
        server backend:8000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=1r/s;
    
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
        
        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
        
        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # WebSocket routes
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400;
        }
        
        # Upload endpoint with specific limits
        location /api/upload {
            limit_req zone=upload burst=5 nodelay;
            client_max_body_size 100M;
            proxy_pass http://backend;
            proxy_request_buffering off;
        }
        
        # Static files with caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            proxy_pass http://frontend;
        }
    }
}
```

### Monitoring and Alerting:
```python
# monitoring/health_check.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis
import asyncio

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with dependencies"""
    checks = {}
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Redis check
    try:
        r = redis.from_url(config.REDIS_URL)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # External API checks
    try:
        # Check YouTube API
        response = await test_youtube_api()
        checks["youtube_api"] = "healthy" if response else "degraded"
    except:
        checks["youtube_api"] = "unhealthy"
    
    overall_status = "healthy" if all(
        status == "healthy" for status in checks.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

### Backup and Recovery:
```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/opt/backups/mindmap-$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting backup process..."

# Database backup
echo "Backing up database..."
pg_dump $DATABASE_URL > $BACKUP_DIR/database.sql

# Redis backup
echo "Backing up Redis..."
redis-cli --rdb $BACKUP_DIR/redis-dump.rdb

# User uploads backup
echo "Backing up uploads..."
tar -czf $BACKUP_DIR/uploads.tar.gz /var/app/uploads/

# Configuration backup
echo "Backing up configuration..."
cp -r /opt/mindmap-app/config $BACKUP_DIR/

# Compress final backup
echo "Compressing backup..."
cd /opt/backups
tar -czf mindmap-backup-$(date +%Y%m%d_%H%M%S).tar.gz mindmap-*

# Upload to cloud storage (if configured)
if [ -n "$S3_BACKUP_BUCKET" ]; then
    aws s3 cp mindmap-backup-*.tar.gz s3://$S3_BACKUP_BUCKET/
fi

# Cleanup old backups (keep last 7 days)
find /opt/backups -name "mindmap-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed successfully"
```

### Deployment APIs:
```
/**
* Health Check Endpoint
* Check application health and dependency status
* Input Parameters: detailed (boolean, optional)
* Return Parameters: HealthStatus with system status
* URL Address: /health or /health/detailed
* Request Method: GET
**/

/**
* Deployment Status
* Get current deployment version and status
* Input Parameters: None
* Return Parameters: DeploymentInfo with version and status
* URL Address: /api/deployment/status
* Request Method: GET
**/

/**
* System Metrics
* Get production system metrics for monitoring
* Input Parameters: metric_type (string, optional)
* Return Parameters: SystemMetrics with performance data
* URL Address: /api/monitoring/metrics
* Request Method: GET
**/
```

## Definition of Done
- Docker containers build and run successfully in production environment
- CI/CD pipeline automatically tests and deploys on successful builds
- Production database is configured with automated backups
- SSL certificates are properly configured and auto-renewing
- Load balancing distributes traffic across multiple instances
- Monitoring alerts notify team of production issues
- Backup and recovery procedures are tested and documented
- CDN serves static assets with appropriate caching headers
- All production secrets are securely managed and rotated
- Log aggregation captures and indexes application logs
- Health check endpoints provide accurate system status
- Deployment process has zero-downtime rollback capability