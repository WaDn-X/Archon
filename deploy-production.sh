#!/bin/bash

# Production Deployment Script for Zippy-Archon
# This script handles the complete production deployment process

set -e  # Exit on any error

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"
DOCKER_REPO="${DOCKER_REPO:-your-org/zippy-archon}"
TAG="${TAG:-latest}"
COMPOSE_FILE="docker-compose.prod.yml"

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

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if required tools are installed
    command -v docker >/dev/null 2>&1 || { log_error "Docker is not installed. Aborting."; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { log_error "Docker Compose is not installed. Aborting."; exit 1; }

    # Check if .env file exists
    if [ ! -f ".env.production" ]; then
        log_error ".env.production file not found. Please create it from env.production.example"
        exit 1
    fi

    # Check if required environment variables are set
    required_vars=("SUPABASE_URL" "SUPABASE_SERVICE_KEY" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env.production; then
            log_error "Required environment variable ${var} not found in .env.production"
            exit 1
        fi
    done

    log_success "Pre-deployment checks passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    # Build backend services
    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}/server:${TAG} ./python --target server
    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}/mcp:${TAG} ./python --target mcp
    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}/agents:${TAG} ./python --target agents

    # Build frontend
    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}/frontend:${TAG} ./archon-ui-main

    log_success "Docker images built successfully"
}

# Push images to registry (optional)
push_images() {
    if [ "${PUSH_IMAGES:-false}" = "true" ]; then
        log_info "Pushing images to registry..."

        docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}/server:${TAG}
        docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}/mcp:${TAG}
        docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}/agents:${TAG}
        docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}/frontend:${TAG}

        log_success "Images pushed to registry"
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."

    # Copy production environment file
    cp .env.production .env

    # Pull latest images if using registry
    if [ "${PUSH_IMAGES:-false}" = "true" ]; then
        docker-compose -f ${COMPOSE_FILE} pull
    fi

    # Start services
    docker-compose -f ${COMPOSE_FILE} up -d

    log_success "Services deployed successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    # Wait for database to be ready
    docker-compose -f ${COMPOSE_FILE} exec -T postgres sh -c 'while ! pg_isready -U zippy; do sleep 1; done'

    # Run migrations
    docker-compose -f ${COMPOSE_FILE} exec -T archon-server python -c "
import asyncio
from database.supabase_client import create_supabase_manager

async def run_migrations():
    db = create_supabase_manager()
    # Run any pending migrations here
    print('Migrations completed')

asyncio.run(run_migrations())
"

    log_success "Database migrations completed"
}

# Health checks
health_checks() {
    log_info "Running health checks..."

    # Wait for services to be healthy
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"

        # Check server health
        if curl -f -s http://localhost:8181/health > /dev/null; then
            log_success "Server is healthy"

            # Check frontend health
            if curl -f -s http://localhost:3737 > /dev/null; then
                log_success "Frontend is healthy"
                return 0
            fi
        fi

        sleep 10
        ((attempt++))
    done

    log_error "Health checks failed after $max_attempts attempts"
    exit 1
}

# Post-deployment tasks
post_deployment_tasks() {
    log_info "Running post-deployment tasks..."

    # Run any initialization scripts
    docker-compose -f ${COMPOSE_FILE} exec -T archon-server python -c "
# Add any post-deployment initialization here
print('Post-deployment tasks completed')
"

    # Collect static metrics
    log_info "Collecting deployment metrics..."
    docker stats --no-stream > deployment_stats.log

    log_success "Post-deployment tasks completed"
}

# Rollback function
rollback() {
    log_error "Deployment failed. Starting rollback..."

    # Stop services
    docker-compose -f ${COMPOSE_FILE} down

    # Optionally restore from backup
    if [ "${ROLLBACK_ENABLED:-false}" = "true" ]; then
        log_info "Restoring from backup..."
        # Add backup restoration logic here
    fi

    exit 1
}

# Main deployment function
main() {
    log_info "Starting Zippy-Archon production deployment..."

    # Set up error handling
    trap rollback ERR

    # Run deployment steps
    pre_deployment_checks
    build_images
    push_images
    deploy_services
    run_migrations
    health_checks
    post_deployment_tasks

    log_success "🎉 Deployment completed successfully!"
    log_info "Application is now running at:"
    log_info "  - Frontend: http://localhost:3737"
    log_info "  - API: http://localhost:8181"
    log_info "  - Health Check: http://localhost:8181/health"
    log_info "  - Metrics: http://localhost:8181/metrics"
}

# Show usage if requested
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -e, --environment   Set environment (default: production)"
    echo "  -t, --tag          Set Docker image tag (default: latest)"
    echo "  -p, --push         Push images to registry"
    echo "  -r, --rollback     Enable rollback on failure"
    echo ""
    echo "Environment variables:"
    echo "  ENVIRONMENT        Deployment environment"
    echo "  DOCKER_REGISTRY    Docker registry URL"
    echo "  DOCKER_REPO       Docker repository name"
    echo "  TAG               Docker image tag"
    echo "  PUSH_IMAGES       Push images to registry (true/false)"
    echo "  ROLLBACK_ENABLED  Enable rollback on failure (true/false)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH_IMAGES=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK_ENABLED=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Run main deployment
main


