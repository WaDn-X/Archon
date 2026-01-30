#!/bin/bash

# Zippy-Archon Launch Script with Port Conflict Resolution
# This script checks for port conflicts and resolves them before launching

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
PYTHON_SRC_DIR="$SCRIPT_DIR/python/src"
PORT_MANAGER_SCRIPT="$PYTHON_SRC_DIR/utils/port_manager.py"
PORT_CONFIG_FILE="$SCRIPT_DIR/.zippy-archon-ports.json"

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    log_success "Python 3 is available"
}

# Check for port conflicts and resolve them
check_and_resolve_ports() {
    log_info "🔍 Checking for port conflicts..."

    # Run port scanner
    if python3 "$PORT_MANAGER_SCRIPT" --check --resolve; then
        log_success "Port conflicts resolved successfully"
        return 0
    else
        log_error "Failed to resolve port conflicts"
        return 1
    fi
}

# Load port configuration if available
load_port_config() {
    if [ -f "$PORT_CONFIG_FILE" ]; then
        log_info "Loading port configuration from $PORT_CONFIG_FILE"

        # Load port mappings into environment variables
        python3 -c "
import json
import os

try:
    with open('$PORT_CONFIG_FILE', 'r') as f:
        config = json.load(f)

    allocations = config.get('allocations', {})
    for env_var, allocation in allocations.items():
        port = allocation.get('allocated_port')
        if port:
            os.environ[env_var] = str(port)
            print(f'export {env_var}={port}')

except Exception as e:
    print(f'Warning: Could not load port config: {e}')
"
    fi
}

# Validate environment
validate_environment() {
    log_info "🔍 Validating environment..."

    # Check for required environment variables
    required_vars=("SUPABASE_URL" "SUPABASE_SERVICE_KEY")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            log_info "Please set it in your .env file or export it"
            exit 1
        fi
    done

    log_success "Environment validation passed"
}

# Start services based on mode
start_services() {
    local mode="${1:-full}"

    case "$mode" in
        "full")
            log_info "🚀 Starting all services..."
            docker-compose up -d
            ;;
        "backend")
            log_info "🚀 Starting backend services only..."
            docker-compose --profile backend up -d
            ;;
        "frontend")
            log_info "🚀 Starting frontend only..."
            docker-compose --profile frontend up -d
            ;;
        "monitoring")
            log_info "🚀 Starting monitoring stack..."
            docker-compose --profile monitoring up -d
            ;;
        *)
            log_error "Unknown mode: $mode"
            log_info "Available modes: full, backend, frontend, monitoring"
            exit 1
            ;;
    esac
}

# Wait for services to be healthy
wait_for_health() {
    log_info "⏳ Waiting for services to become healthy..."

    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"

        # Check main services
        if curl -f -s http://localhost:${ARCHON_SERVER_PORT:-8181}/health > /dev/null 2>&1; then
            if curl -f -s http://localhost:${ARCHON_UI_PORT:-3737} > /dev/null 2>&1; then
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
    local grafana_port="${GRAFANA_PORT:-3000}"
    local prometheus_port="${PROMETHEUS_PORT:-9090}"

    log_success "🎉 Services are running!"
    echo ""
    echo "📋 Service URLs:"
    echo "  🌐 Frontend (React UI):    http://localhost:${ARCHON_UI_PORT:-3737}"
    echo "  🔌 API Server (FastAPI):   http://localhost:${ARCHON_SERVER_PORT:-8181}"
    echo "  📚 API Documentation:     http://localhost:${ARCHON_SERVER_PORT:-8181}/docs"
    echo "  🏥 Health Check:          http://localhost:${ARCHON_SERVER_PORT:-8181}/health"
    echo "  📊 Grafana Dashboards:    http://localhost:${GRAFANA_PORT:-3827}"
    echo "  📈 Prometheus Metrics:    http://localhost:${PROMETHEUS_PORT:-9090}"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:      docker-compose logs -f"
    echo "  Stop services:  docker-compose down"
    echo "  Restart:        docker-compose restart"
    echo ""
}

# Main launch function
main() {
    log_info "🚀 Starting Zippy-Archon with port conflict resolution..."

    # Parse command line arguments
    MODE="full"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--mode <full|backend|frontend|monitoring>] [--help]"
                echo ""
                echo "Modes:"
                echo "  full       - Start all services (default)"
                echo "  backend    - Start only backend services"
                echo "  frontend   - Start only frontend"
                echo "  monitoring - Start only monitoring stack"
                echo ""
                echo "This script will:"
                echo "  1. Check for port conflicts and resolve them"
                echo "  2. Validate environment variables"
                echo "  3. Start the specified services"
                echo "  4. Wait for services to become healthy"
                echo "  5. Display service URLs"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run checks and setup
    check_python
    load_port_config
    check_and_resolve_ports
    validate_environment

    # Start services
    start_services "$MODE"
    wait_for_health
    show_service_urls

    log_success "✅ Zippy-Archon is now running successfully!"
}

# Show usage if no arguments and no environment suggests running
if [ $# -eq 0 ] && [ -z "$ARCHON_SERVER_PORT" ]; then
    echo "🚀 Zippy-Archon Launch Script"
    echo ""
    echo "This script will automatically:"
    echo "  ✓ Check for port conflicts and resolve them"
    echo "  ✓ Validate environment configuration"
    echo "  ✓ Start all services safely"
    echo "  ✓ Wait for services to become healthy"
    echo ""
    echo "Usage: $0 [--mode <full|backend|frontend|monitoring>]"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start all services"
    echo "  $0 --mode backend     # Start only backend services"
    echo "  $0 --mode monitoring  # Start only monitoring"
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Launch cancelled."
        exit 0
    fi
fi

# Run main function
main "$@"
