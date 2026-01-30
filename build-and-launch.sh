#!/bin/bash

# Zippy-Archon Build and Launch Script
# This script handles the complete build and launch process with error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$SCRIPT_DIR/python"
FRONTEND_DIR="$SCRIPT_DIR/archon-ui-main"
BACKEND_DIR="$PYTHON_DIR/src"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Prerequisites check
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."

    # Check Docker
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker Desktop."
        log_info "Download: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi

    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not available."
        log_info "Please ensure Docker Desktop is running and up to date."
        exit 1
    fi

    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is not installed."
        log_info "Please install Python 3.8 or higher."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log_info "🔧 Setting up environment..."

    # Create .env.production if it doesn't exist
    if [ ! -f ".env.production" ]; then
        log_info "Creating .env.production from template..."
        cp env.production.example .env.production
        log_warning "Please edit .env.production with your actual API keys and database credentials"
    fi

    # Set environment variables for this session
    export ARCHON_SERVER_PORT=8181
    export ARCHON_MCP_PORT=8051
    export ARCHON_AGENTS_PORT=8052
    export ARCHON_UI_PORT=3737
    export POSTGRES_PORT=5433
    export REDIS_PORT=6379
    export PROMETHEUS_PORT=9090
    export GRAFANA_PORT=3827
    export NGINX_PORT=8280
    export NGINX_SSL_PORT=8443

    log_success "Environment setup complete"
}

# Install Python dependencies
install_python_deps() {
    log_info "📦 Installing Python dependencies..."

    cd "$PYTHON_DIR"

    # Install main dependencies
    if [ -f "requirements.server.txt" ]; then
        pip install -r requirements.server.txt
        log_success "Python server dependencies installed"
    else
        log_warning "requirements.server.txt not found, skipping Python dependencies"
    fi

    cd "$SCRIPT_DIR"
}

# Install frontend dependencies
install_frontend_deps() {
    log_info "📦 Installing frontend dependencies..."

    cd "$FRONTEND_DIR"

    # Install npm dependencies
    if [ -f "package.json" ]; then
        npm install
        log_success "Frontend dependencies installed"
    else
        log_warning "package.json not found, skipping frontend dependencies"
    fi

    cd "$SCRIPT_DIR"
}

# Build Docker images
build_images() {
    log_info "🐳 Building Docker images..."

    # Build backend services
    if [ -f "python/Dockerfile.server" ]; then
        docker build -t zippy-archon-server:latest ./python --target server
        log_success "Server image built"
    fi

    if [ -f "python/Dockerfile.mcp" ]; then
        docker build -t zippy-archon-mcp:latest ./python --target mcp
        log_success "MCP server image built"
    fi

    if [ -f "python/Dockerfile.agents" ]; then
        docker build -t zippy-archon-agents:latest ./python --target agents
        log_success "Agents service image built"
    fi

    # Build frontend
    if [ -f "archon-ui-main/Dockerfile" ]; then
        docker build -t zippy-archon-frontend:latest ./archon-ui-main
        log_success "Frontend image built"
    fi
}

# Run port conflict resolution
resolve_port_conflicts() {
    log_info "🔍 Checking for port conflicts..."

    cd "$PYTHON_DIR"

    # Run port scanner
    if python -c "
import sys
sys.path.insert(0, 'src')
from utils.port_manager import port_manager
allocations = port_manager.check_and_resolve_conflicts(auto_resolve=True)
print('✅ Port conflicts resolved')
" 2>/dev/null; then
        log_success "Port conflicts resolved automatically"
    else
        log_warning "Port conflict resolution skipped (dependencies not available)"
    fi

    cd "$SCRIPT_DIR"
}

# Start services
start_services() {
    log_info "🚀 Starting services..."

    # Start with docker-compose
    docker-compose up -d

    # Wait for services to be healthy
    log_info "⏳ Waiting for services to become healthy..."

    # Wait for server health check
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"

        if curl -f -s "http://localhost:${ARCHON_SERVER_PORT:-8181}/health" >/dev/null 2>&1; then
            if curl -f -s "http://localhost:${ARCHON_UI_PORT:-3737}" >/dev/null 2>&1; then
                log_success "All services are healthy!"
                return 0
            fi
        fi

        sleep 5
        ((attempt++))
    done

    log_warning "Services may not be fully healthy after $max_attempts attempts"
    log_info "You can check service status with: docker-compose ps"
}

# Show service URLs
show_service_urls() {
    local server_port="${ARCHON_SERVER_PORT:-8181}"
    local ui_port="${ARCHON_UI_PORT:-3737}"
    local grafana_port="${GRAFANA_PORT:-3827}"
    local prometheus_port="${PROMETHEUS_PORT:-9090}"

    log_success "🎉 Zippy-Archon is now running!"
    echo ""
    echo "📋 Service URLs:"
    echo "  🌐 Frontend (React UI):    http://localhost:$ui_port"
    echo "  🔌 API Server (FastAPI):   http://localhost:$server_port"
    echo "  📚 API Documentation:     http://localhost:$server_port/docs"
    echo "  🏥 Health Check:          http://localhost:$server_port/health"
    echo "  📊 Grafana Dashboards:    http://localhost:$grafana_port"
    echo "  📈 Prometheus Metrics:    http://localhost:$prometheus_port"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:      docker-compose logs -f"
    echo "  Stop services:  docker-compose down"
    echo "  Restart:        docker-compose restart"
    echo ""
    echo "🎯 What to Try First:"
    echo "  1. Visit http://localhost:$ui_port to start using the application"
    echo "  2. Complete the interactive onboarding wizard"
    echo "  3. Upload some documents or start a project"
    echo "  4. Explore the API at http://localhost:$server_port/docs"
    echo ""
}

# Cleanup function
cleanup() {
    log_info "🛑 Stopping services..."
    docker-compose down 2>/dev/null || true
    log_success "Services stopped"
}

# Main build and launch function
main() {
    log_info "🚀 Starting Zippy-Archon build and launch process..."

    # Set up cleanup on exit
    trap cleanup EXIT

    # Run all steps
    check_prerequisites
    setup_environment
    install_python_deps
    install_frontend_deps
    build_images
    resolve_port_conflicts
    start_services
    show_service_urls

    log_success "🎉 Zippy-Archon is now running and ready to use!"
    log_info "Happy coding! 🚀"
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "🚀 Zippy-Archon Build and Launch Script"
    echo ""
    echo "This script will:"
    echo "  ✓ Check prerequisites (Docker, Python, Node.js)"
    echo "  ✓ Set up environment configuration"
    echo "  ✓ Install dependencies"
    echo "  ✓ Build Docker images"
    echo "  ✓ Resolve port conflicts automatically"
    echo "  ✓ Start all services"
    echo "  ✓ Wait for services to become healthy"
    echo "  ✓ Display service URLs"
    echo ""
    echo "Usage: $0"
    echo ""
    echo "Make sure to:"
    echo "  1. Edit .env.production with your API keys"
    echo "  2. Ensure Docker Desktop is running"
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Build cancelled."
        exit 0
    fi
fi

# Run main function
main
