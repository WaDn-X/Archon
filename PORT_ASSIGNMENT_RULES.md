# Zippy-Archon Port Assignment Rules

## 🚨 CRITICAL RULE FOR ALL DEVELOPERS AND AGENTS

**For the Zippy-Archon project, ALWAYS use the designated ports listed below to avoid conflicts with other projects on this active development workstation.**

### 🎯 Port Assignment Pattern:
**Zippy-Archon uses ports ending in "827" pattern (inspired by the original UBR system) with specific service designations.**

### 📋 Official Port Assignments:

| Service | Port | Description | Status |
|---------|------|-------------|---------|
| **Backend API** | **8181** | FastAPI server with Socket.IO | ✅ Active |
| **MCP Server** | **8051** | Model Context Protocol server | ✅ Active |
| **AI Agents** | **8052** | AI/ML agents service | ✅ Active |
| **Frontend UI** | **3737** | React frontend application | ✅ Active |
| **PostgreSQL** | **5432** | Primary database | ✅ Active |
| **Redis Cache** | **6379** | Caching and sessions | ✅ Active |
| **Prometheus** | **9090** | Metrics collection | ✅ Active |
| **Grafana** | **3827** | Monitoring dashboards | ✅ Active |
| **Nginx HTTP** | **8280** | Reverse proxy (HTTP) | ✅ Active |
| **Nginx SSL** | **8443** | Reverse proxy (HTTPS) | ✅ Active |

### 🚫 PROHIBITED PORTS (NEVER USE):
**These ports are commonly used by other projects and MUST be avoided:**

- **3000** - **OCCUPIED** by OpenWebUI (your local Ollama interface) - DO NOT USE
- **4000** - Commonly used by development servers
- **5173** - Vite development server default
- **8080** - Commonly used by development servers
- **8000** - Commonly used by Python/Django servers
- **5000** - Commonly used by Flask/Node servers
- **9000** - Commonly used by various services
- **80** - System HTTP port (conflicts with Nginx)
- **443** - System HTTPS port (conflicts with Nginx)

## 🔗 External Service Integration

### Ollama Integration
- **Your Setup**: Ollama running in Docker Desktop + OpenWebUI on port 3000 ✅
- **Zippy-Archon Usage**: Can connect to your existing Ollama instance via API
- **No Port Conflict**: Zippy-Archon will use your external Ollama, not create its own

### Configuration for External Ollama:
```bash
# In your .env.production file, configure Ollama connection:
OLLAMA_BASE_URL=http://localhost:11434  # Default Ollama API port
OLLAMA_MODEL=llama2:7b                   # Your preferred model

# Or configure via database settings in RAG strategy:
# LLM_BASE_URL=http://localhost:11434/v1
# This allows Zippy-Archon to connect to your existing Ollama instance
```

### Your Specific Setup (Ollama + OpenWebUI):
- **Ollama API**: Available at `http://localhost:11434` ✅
- **OpenWebUI**: Running on port 3000 ✅
- **Zippy-Archon**: Will connect to your Ollama via API calls
- **No Conflicts**: Zippy-Archon doesn't need to bind to these ports

**Result**: You can use both OpenWebUI (port 3000) and Zippy-Archon simultaneously! 🎉

### 🔍 Before Starting Any Service:

#### **Windows (PowerShell):**
```powershell
# 1. Check if port is available
netstat -ano | findstr :PORT_NUMBER

# 2. If port is in use, find the process
netstat -ano | findstr :PORT_NUMBER | ForEach-Object { $_.Split()[-1] }

# 3. Kill the conflicting process
taskkill /PID PROCESS_ID /F

# 4. Only then start the service
```

#### **Linux/Mac (Bash):**
```bash
# 1. Check if port is available
netstat -tulpn | grep :PORT_NUMBER

# 2. If port is in use, find the process
lsof -i :PORT_NUMBER

# 3. Kill the conflicting process
kill -9 PROCESS_ID

# 4. Only then start the service
```

### 🛠️ Quick Port Checking Commands:

#### **Check All Zippy-Archon Ports:**
```bash
# Windows
@("8181","8051","8052","3737","5432","6379","9090","3827","8280","8443") | ForEach-Object { netstat -ano | findstr ":$_" | Out-Host }

# Linux/Mac
for port in 8181 8051 8052 3737 5432 6379 9090 3827 8280 8443; do echo "Port $port:"; netstat -tulpn | grep ":$port" || echo "  Available"; done
```

#### **Check Specific Service Port:**
```bash
# Windows - Check server port
netstat -ano | findstr :8181

# Linux/Mac - Check server port
netstat -tulpn | grep :8181
```

### 🚀 Launch with Port Management:

#### **Automatic Port Resolution (Recommended):**
```bash
# Linux/Mac
./launch-with-port-check.sh

# Windows
.\launch-with-port-check.ps1
```

#### **Manual Port Assignment:**
```bash
# Set specific ports before launching
export ARCHON_SERVER_PORT=8181
export ARCHON_UI_PORT=3737
export GRAFANA_PORT=3827
export NGINX_PORT=8280

# Then launch
./launch-with-port-check.sh
```

### 📊 Environment Variables for Port Management:

| Variable | Default | Description |
|----------|---------|-------------|
| `ARCHON_SERVER_PORT` | 8181 | Main FastAPI server |
| `ARCHON_MCP_PORT` | 8051 | MCP server |
| `ARCHON_AGENTS_PORT` | 8052 | AI agents service |
| `ARCHON_UI_PORT` | 3737 | React frontend |
| `POSTGRES_PORT` | 5432 | PostgreSQL database |
| `REDIS_PORT` | 6379 | Redis cache |
| `PROMETHEUS_PORT` | 9090 | Prometheus monitoring |
| `GRAFANA_PORT` | 3827 | Grafana dashboards |
| `NGINX_PORT` | 8280 | Nginx HTTP proxy |
| `NGINX_SSL_PORT` | 8443 | Nginx HTTPS proxy |

### ⚡ Quick Access URLs:

After successful launch, access your services at:

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | http://localhost:3737 | Main application interface |
| **API Docs** | http://localhost:8181/docs | Interactive API documentation |
| **Health Check** | http://localhost:8181/health | System health status |
| **Grafana** | http://localhost:3827 | Monitoring dashboards (admin/admin) |
| **Prometheus** | http://localhost:9090 | Metrics collection |

### 🚨 Troubleshooting Port Conflicts:

#### **If a port is in use:**
1. **Identify the process:** `netstat -ano | findstr :PORT`
2. **Kill the process:** `taskkill /PID PID /F`
3. **Verify port is free:** `netstat -ano | findstr :PORT`
4. **Restart the service**

#### **Common conflicts to watch for:**
- **Port 3000** - React/Vite dev servers
- **Port 5173** - Vite default
- **Port 8080** - Various dev servers
- **Port 80/443** - System web ports

### 🔧 Development Guidelines:

#### **For New Services:**
1. Choose a port ending in the 827 pattern (e.g., 4827, 5827, 6827)
2. Add to this rules document
3. Update port management scripts
4. Test for conflicts before committing

#### **For Existing Services:**
1. Use the assigned ports from this table
2. Never hardcode ports in configuration files
3. Always use environment variables for port configuration

### 📝 Adding New Port Assignments:

When adding new services to Zippy-Archon:

1. **Choose a port** that follows the 827 pattern and isn't in use
2. **Add to this document** in the port assignments table
3. **Update environment files** (env.production.example)
4. **Update Docker configurations** if needed
5. **Test the port** with the port checking commands above
6. **Document the service** in the quick access URLs table

### 🎯 This Rule Must Be Followed:

**ALL developers and agents working on Zippy-Archon MUST follow these port assignment rules to prevent conflicts and ensure smooth development workflows.**

**Failure to follow these rules may result in:**
- ❌ Service startup failures
- ❌ Port conflicts with other projects
- ❌ Development workflow disruptions
- ❌ Team productivity loss

## 🚨 Special Notice: Your Local Setup

**Your development environment has a specific configuration that these rules protect:**

- **Ollama** running in Docker Desktop
- **OpenWebUI** on port 3000 (your local interface)
- **Zippy-Archon** configured to connect to your existing Ollama

**This is the optimal setup** because:
- ✅ **No port conflicts** between services
- ✅ **Resource sharing** - Ollama serves both OpenWebUI and Zippy-Archon
- ✅ **Consistent experience** - Same models available in both interfaces
- ✅ **Efficient resource usage** - Single Ollama instance for multiple tools

---

*This document is maintained by the Zippy-Archon development team. Last updated: January 2025*
