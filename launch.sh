#!/bin/bash

# 🚀 Zippy Archon Launch Script
# This script helps you get Zippy Archon running quickly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
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

log_header() {
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_header "🔍 Checking Prerequisites"

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        log_info "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log_success "Docker is running"

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed."
        exit 1
    fi
    log_success "docker-compose is available"

    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from template..."
        if [ -f "agentic-workflow/env.example" ]; then
            cp agentic-workflow/env.example .env
            log_warning "⚠️  IMPORTANT: Please edit .env file with your actual credentials!"
            log_warning "   Required: SUPABASE_URL, SUPABASE_SERVICE_KEY"
            log_warning "   Optional: OPENAI_API_KEY, XAI_API_KEY, ANTHROPIC_API_KEY"
            echo ""
            read -p "Press Enter after updating .env file..."
        else
            log_error "env.example not found. Please create .env manually."
            exit 1
        fi
    fi
    log_success ".env file exists"
}

# Setup database
setup_database() {
    log_header "🗄️  Database Setup"

    if [ ! -f "python/src/server/migrations/001_phase3_schema.sql" ]; then
        log_error "Database migration file not found!"
        exit 1
    fi

    log_info "Phase 3 database schema is ready to be applied."
    log_info "If using Supabase, run this SQL file in your Supabase SQL editor:"
    log_info "  python/src/server/migrations/001_phase3_schema.sql"
    log_info ""
    log_info "If using local PostgreSQL, the migration will run automatically."
    echo ""
}

# Start services
start_services() {
    log_header "🐳 Starting Services"

    log_info "Starting Docker services..."
    docker-compose up -d

    log_info "Waiting for services to start..."
    sleep 30
}

# Check service health
check_health() {
    log_header "🔍 Service Health Check"

    local services=(
        "archon-server:http://localhost:8181/health:Backend API"
        "archon-frontend:http://localhost:3737:Frontend UI"
        "archon-mcp:http://localhost:8051/health:MCP Server"
        "archon-agents:http://localhost:8052/health:AI Agents"
    )

    local all_healthy=true

    for service in "${services[@]}"; do
        IFS=':' read -r name url description <<< "$service"

        if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
            log_success "$description is healthy ($url)"
        else
            log_error "$description is not responding ($url)"
            all_healthy=false
        fi
    done

    return $([ "$all_healthy" = true ])
}

# Show status and next steps
show_status() {
    log_header "🎉 Zippy Archon is Running!"

    echo ""
    log_success "Services Status:"
    docker-compose ps

    echo ""
    log_success "Access URLs:"
    echo -e "  ${CYAN}📱 Frontend:${NC}       http://localhost:3737"
    echo -e "  ${CYAN}🔌 Backend API:${NC}   http://localhost:8181"
    echo -e "  ${CYAN}📚 API Docs:${NC}      http://localhost:8181/docs"
    echo -e "  ${CYAN}🔧 Logs:${NC}          docker-compose logs -f"

    echo ""
    log_info "Next Steps:"
    echo "  1. Open http://localhost:3737 in your browser"
    echo "  2. Create your first project"
    echo "  3. Try the AI-powered task prioritization"
    echo "  4. Test real-time collaboration features"

    echo ""
    log_info "To stop services: docker-compose down"
    log_info "To restart: docker-compose restart"
    log_info "To view logs: docker-compose logs -f"
}

# Show help
show_help() {
    echo "Zippy Archon Launch Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --no-health    Skip health checks"
    echo "  --logs         Show logs after startup"
    echo ""
    echo "Examples:"
    echo "  $0              # Normal launch"
    echo "  $0 --logs       # Launch and show logs"
    echo "  $0 --no-health  # Launch without health checks"
}

# Main script
main() {
    local skip_health=false
    local show_logs=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --no-health)
                skip_health=true
                shift
                ;;
            --logs)
                show_logs=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_header "🚀 ZIPPY ARCHON LAUNCH SEQUENCE"
    echo ""
    log_info "Welcome to Zippy Archon - Intelligent Project Management Platform"
    log_info "This script will help you get started quickly!"
    echo ""

    check_prerequisites
    setup_database
    start_services

    if [ "$skip_health" = false ]; then
        if check_health; then
            log_success "All services are healthy!"
        else
            log_warning "Some services may not be fully ready yet."
            log_info "Check logs with: docker-compose logs -f"
        fi
    fi

    show_status

    if [ "$show_logs" = true ]; then
        echo ""
        log_info "Showing service logs (Ctrl+C to exit)..."
        docker-compose logs -f
    fi
}

# Run main function
main "$@"
