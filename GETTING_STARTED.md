# 🚀 Getting Started with Zippy-Archon

## 🎯 Quick Start Guide

This guide will get you up and running with Zippy-Archon in **under 10 minutes** with automatic port conflict resolution!

---

## ✅ Prerequisites

- **Docker Desktop** (Latest version)
- **Python 3.8+** (for port management utilities)
- **Git** (for cloning the repository)

---

## 🔧 Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/ZippyNetworks/Zippy-Archon.git
cd Zippy-Archon

# Make launch scripts executable (Linux/Mac)
chmod +x launch-with-port-check.sh deploy-production.sh

# Or use PowerShell version (Windows)
# .\launch-with-port-check.ps1
```

---

## 🔑 Step 2: Configure Environment

### Option A: Quick Setup (Recommended)
```bash
# Copy and edit the environment file
cp env.production.example .env.production

# Edit with your preferred editor
nano .env.production  # or code .env.production, or notepad .env.production
```

### Option B: Interactive Setup (Coming Soon)
```bash
# Run the setup wizard (when available)
python python/src/utils/setup_wizard.py
```

### Required Settings in `.env.production`:

```bash
# Database (Choose one option below)

# Option 1: Supabase (Recommended)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key-here

# Option 2: Local PostgreSQL (Advanced)
# DATABASE_URL=postgresql://zippy_user:password@localhost:5432/zippy_archon

# AI Provider (At least one required)
OPENAI_API_KEY=sk-your-openai-api-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key-here
# OR
XAI_API_KEY=your-xai-api-key-here

# Security (Generate a secure random key)
JWT_SECRET_KEY=your-very-secure-jwt-secret-key-min-32-chars

# External Ollama (Optional - connects to your existing Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b

# Monitoring (Optional but recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

---

## 🚀 Step 3: Launch with Port Management

### Automatic Port Conflict Resolution
The system will automatically detect and resolve port conflicts!

```bash
# Linux/Mac - Launch with automatic port resolution
./launch-with-port-check.sh

# Windows PowerShell - Launch with automatic port resolution
.\launch-with-port-check.ps1

# Or launch specific service stacks
./launch-with-port-check.sh --mode backend    # Backend only
./launch-with-port-check.sh --mode frontend   # Frontend only
./launch-with-port-check.sh --mode monitoring # Monitoring only
```

### What Happens During Launch:
1. **🔍 Port Scanning**: Detects conflicts with existing services
2. **🔧 Auto-Resolution**: Automatically allocates new ports if conflicts exist
3. **🐳 Service Startup**: Starts all Docker containers
4. **🏥 Health Checks**: Waits for services to become healthy
5. **📋 URL Display**: Shows you where to access each service

---

## 🌐 Step 4: Access Your Application

After successful launch, you'll see output like:

```
🎉 Services are running!

📋 Service URLs:
  🌐 Frontend (React UI):    http://localhost:3737
  🔌 API Server (FastAPI):   http://localhost:8181
  📚 API Documentation:     http://localhost:8181/docs
  🏥 Health Check:          http://localhost:8181/health
  📊 Grafana Dashboards:    http://localhost:3827
  📈 Prometheus Metrics:    http://localhost:9090

🔧 Management Commands:
  View logs:      docker-compose logs -f
  Stop services:  docker-compose down
  Restart:        docker-compose restart
```

### 🎯 What to Try First:

1. **🌐 Visit the Frontend**: http://localhost:3737
   - Interactive onboarding wizard
   - Knowledge base interface
   - Project management tools

2. **📚 Check API Docs**: http://localhost:8181/docs
   - Complete API documentation
   - Interactive testing interface

3. **🏥 Verify Health**: http://localhost:8181/health
   - System health status

4. **📊 View Monitoring**: http://localhost:3827 (admin/admin)
   - Real-time performance metrics
   - System health dashboards

---

## 🔧 Troubleshooting Common Issues

### Port Conflicts
```bash
# Check what services are using your ports
python python/src/utils/port_manager.py --report

# Force resolve all conflicts
python python/src/utils/port_manager.py --resolve
```

### Service Won't Start
```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs -f archon-server

# Restart specific service
docker-compose restart archon-server
```

### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec postgres pg_isready -U zippy_user

# View database logs
docker-compose logs postgres
```

### Environment Variable Issues
```bash
# Validate your .env.production file
python python/src/utils/port_manager.py --check

# Check all environment variables
python -c "import os; [print(f'{k}={v}') for k,v in sorted(os.environ.items()) if 'ARCHON' in k or 'SUPABASE' in k or 'API_KEY' in k]"
```

---

## 🛠️ Development Mode

### Quick Development Setup
```bash
# Start only backend services for development
./launch-with-port-check.sh --mode backend

# Or use Docker Compose directly
docker-compose up -d archon-server archon-mcp archon-agents

# Frontend development (requires Node.js)
cd archon-ui-main
npm install
npm run dev
```

### VS Code Extension Development
```bash
# Install extension dependencies
cd VoidSpec
npm install

# Build and test extension
npm run compile
npm run test
```

---

## 📊 Monitoring and Health Checks

### Real-time Monitoring
- **Grafana**: http://localhost:3827 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Application Logs**: `docker-compose logs -f`

### Health Endpoints
- **API Health**: http://localhost:8181/health
- **Frontend Health**: http://localhost:3737
- **Database Health**: `docker-compose exec postgres pg_isready`

---

## 🔒 Security Considerations

### Production Deployment
1. **SSL/TLS**: Configure nginx with your SSL certificates
2. **Firewall**: Restrict access to necessary ports only
3. **Secrets**: Use proper secret management (not environment variables)
4. **Updates**: Keep Docker images updated regularly

### Development Security
1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files and add to `.gitignore`
3. **Network**: Use `127.0.0.1` instead of `0.0.0.0` for local development

---

## 📚 Advanced Configuration

### Custom Port Configuration
```bash
# Set custom ports before launching
export ARCHON_SERVER_PORT=9000
export ARCHON_UI_PORT=4000
export GRAFANA_PORT=3500

# Then launch normally
./launch-with-port-check.sh
```

### Database Migration
```bash
# Run database migrations
docker-compose exec archon-server python -c "
import asyncio
from database.supabase_client import create_supabase_manager

async def migrate():
    db = create_supabase_manager()
    # Migration logic here
    print('Migrations completed')

asyncio.run(migrate())
"
```

---

## 🆘 Getting Help

### Documentation
- **API Reference**: http://localhost:8181/docs
- **User Guide**: `/docs/docs/user-guide.mdx`
- **Architecture**: `/docs/docs/architecture.mdx`

### Community Support
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Documentation**: Contribute improvements to `/docs/`

### Logs and Debugging
```bash
# Comprehensive logging
docker-compose logs -f --tail=100

# Specific service logs
docker-compose logs -f archon-server

# Database logs
docker-compose logs postgres

# Performance monitoring
curl http://localhost:8181/metrics
```

---

## 🎉 You're Ready!

Your Zippy-Archon instance is now running with:
- ✅ **Automatic port conflict resolution**
- ✅ **Production-ready architecture**
- ✅ **Real-time monitoring and alerting**
- ✅ **Interactive web interface**
- ✅ **Complete API documentation**

**Next Steps:**
1. Visit http://localhost:3737 to start using the application
2. Complete the interactive onboarding wizard
3. Upload some documents or start a project
4. Explore the API at http://localhost:8181/docs

**Happy coding with Zippy-Archon! 🚀**
