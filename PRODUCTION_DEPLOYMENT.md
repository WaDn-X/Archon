# Production Deployment Guide for Zippy-Archon

This guide covers the complete production deployment process for the Zippy-Archon platform.

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**: Latest versions installed
- **Domain/SSL Certificate**: For production HTTPS
- **Supabase Account**: For database and authentication
- **AI API Keys**: OpenAI, Anthropic, or Grok API keys
- **Redis**: For caching and rate limiting (optional but recommended)

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/your-org/zippy-archon.git
cd zippy-archon

# Set up environment
cp env.production.example .env.production
# Edit .env.production with your production values

# Deploy
ENVIRONMENT=production ./deploy-production.sh
```

## 📋 Pre-Deployment Checklist

### 🔐 Security Configuration

- [ ] **JWT Secret**: Generate a secure JWT secret key (256-bit recommended)
- [ ] **API Keys**: Configure AI provider API keys
- [ ] **CORS Origins**: Set allowed origins for your domain
- [ ] **SSL Certificate**: Obtain and configure SSL certificates
- [ ] **Firewall**: Configure firewall rules for required ports

### 🗄️ Database Setup

- [ ] **Supabase Project**: Create production Supabase project
- [ ] **Database URL**: Configure Supabase URL and service key
- [ ] **Row Level Security**: Enable RLS policies
- [ ] **Backups**: Configure automated database backups

### 🚀 Infrastructure Requirements

- [ ] **Server Specs**: Minimum 2GB RAM, 2 CPU cores
- [ ] **Storage**: 20GB free space for Docker images and data
- [ ] **Network**: Stable internet connection
- [ ] **Domain**: DNS configured for your domain

## 🔧 Environment Configuration

### Production Environment Variables

Create `.env.production` with the following configuration:

```bash
# Application Settings
ENVIRONMENT=production
RELEASE_VERSION=1.0.0
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-very-secure-jwt-secret-key-here
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key
SUPABASE_SCHEMA=public

# AI Providers (at least one required)
XAI_API_KEY=your-xai-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
ZIPPY_API_KEY=your-zippy-api-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
REDIS_URL=redis://redis:6379/0

# Services
ARCHON_SERVER_PORT=8181
ARCHON_MCP_PORT=8051
ARCHON_AGENTS_PORT=8052
ARCHON_UI_PORT=3737

# Nginx (if using reverse proxy)
NGINX_PORT=80
NGINX_SSL_PORT=443
```

### SSL Configuration

For HTTPS in production:

```bash
# Add to .env.production
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
SSL_PROTOCOLS=TLSv1.2 TLSv1.3
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Deploy all services
docker-compose -f docker-compose.prod.yml up -d

# View service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale services (if needed)
docker-compose -f docker-compose.prod.yml up -d --scale archon-server=3
```

### Manual Docker Commands

```bash
# Build images
docker build -t zippy-archon-server ./python --target server
docker build -t zippy-archon-frontend ./archon-ui-main

# Run services
docker run -d --name zippy-server -p 8181:8181 \
  --env-file .env.production \
  zippy-archon-server

docker run -d --name zippy-frontend -p 3737:3737 \
  --env-file .env.production \
  zippy-archon-frontend
```

## 🔍 Health Checks & Monitoring

### Health Check Endpoints

```bash
# API Health
curl http://localhost:8181/health

# Metrics
curl http://localhost:8181/metrics

# Frontend Health
curl http://localhost:3737
```

### Monitoring Stack

The production deployment includes:

- **Prometheus**: Metrics collection
- **Grafana**: Dashboard visualization
- **Sentry**: Error tracking and alerting
- **Health Checks**: Automated service monitoring

Access monitoring:

```bash
# Prometheus
open http://localhost:9090

# Grafana (default: admin/admin)
open http://localhost:3000
```

## 🔄 Database Management

### Initial Setup

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec archon-server python -c "
from database.supabase_client import create_supabase_manager
import asyncio

async def setup_db():
    db = create_supabase_manager()
    # Add any additional setup here
    print('Database setup complete')

asyncio.run(setup_db())
"
```

### Backup & Recovery

```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U zippy zippy_archon > backup.sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U zippy zippy_archon < backup.sql
```

## 🚀 Scaling & Performance

### Horizontal Scaling

```bash
# Scale API servers
docker-compose -f docker-compose.prod.yml up -d --scale archon-server=3

# Scale agents
docker-compose -f docker-compose.prod.yml up -d --scale archon-agents=2
```

### Performance Optimization

```bash
# Update resource limits
# Edit docker-compose.prod.yml and adjust deploy.resources

# Monitor performance
docker stats
docker-compose -f docker-compose.prod.yml logs | grep "response time"
```

## 🔒 Security Best Practices

### Network Security

```bash
# Use internal networks for service communication
# Configure firewall rules
# Enable SSL/TLS for all endpoints
# Use VPN for administrative access
```

### Application Security

```bash
# Keep dependencies updated
docker-compose -f docker-compose.prod.yml pull

# Regular security scans
docker run --rm -v $(pwd):/app aquasecurity/trivy fs /app

# Monitor for security vulnerabilities
# Enable rate limiting and DDoS protection
```

## 📊 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check resource usage
docker stats

# Verify environment variables
docker-compose -f docker-compose.prod.yml config
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec archon-server python -c "
from database.supabase_client import create_supabase_manager
import asyncio

async def test_db():
    db = create_supabase_manager()
    print('Database connection:', await db.test_connection())

asyncio.run(test_db())
"
```

#### AI Provider Issues
```bash
# Test AI providers
curl http://localhost:8181/health | jq .ai_providers

# Check API key validity
docker-compose -f docker-compose.prod.yml logs archon-agents
```

### Log Analysis

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Filter specific service
docker-compose -f docker-compose.prod.yml logs -f archon-server

# Search for errors
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

## 🔄 Updates & Maintenance

### Rolling Updates

```bash
# Update images
docker-compose -f docker-compose.prod.yml pull

# Rolling restart
docker-compose -f docker-compose.prod.yml up -d --no-deps archon-server
```

### Zero-Downtime Deployment

```bash
# Deploy new version
docker-compose -f docker-compose.prod.yml up -d --scale archon-server=2

# Wait for health checks
# Then scale down old version
docker-compose -f docker-compose.prod.yml up -d --scale archon-server=1
```

## 📞 Support & Monitoring

### Alert Configuration

Set up alerts for:
- Service downtime
- High error rates
- Resource exhaustion
- Security incidents

### Monitoring Dashboards

Access pre-configured dashboards:
- Application Performance
- Error Rates
- Resource Usage
- User Activity

## 🎯 Production Checklist

### Pre-Launch
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring alerts set up
- [ ] Load testing completed

### Post-Launch
- [ ] Health checks passing
- [ ] Monitoring dashboards active
- [ ] Backup verification
- [ ] Security scans clean
- [ ] Performance benchmarks met

### Ongoing Maintenance
- [ ] Weekly security updates
- [ ] Monthly performance reviews
- [ ] Regular backup testing
- [ ] Log rotation configured

---

## 📚 Additional Resources

- [API Documentation](http://localhost:8181/docs)
- [Monitoring Setup](./monitoring/README.md)
- [Security Guidelines](./SECURITY.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

For additional help, check the [GitHub Issues](https://github.com/your-org/zippy-archon/issues) or contact the development team.


