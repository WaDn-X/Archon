#!/bin/bash

# Database Setup Script for Zippy-Archon
# This script helps configure different database backends

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

show_help() {
    echo "Zippy-Archon Database Setup"
    echo ""
    echo "Usage: $0 [DATABASE_TYPE]"
    echo ""
    echo "Database Types:"
    echo "  sqlite      - SQLite (default, no setup required)"
    echo "  postgresql  - PostgreSQL (requires Docker)"
    echo "  supabase    - Supabase (cloud)"
    echo ""
    echo "Examples:"
    echo "  $0 sqlite          # Use SQLite"
    echo "  $0 postgresql      # Use PostgreSQL"
    echo "  $0 supabase        # Use Supabase"
    echo ""
    echo "Environment Variables:"
    echo "  For PostgreSQL:"
    echo "    DATABASE_HOST=localhost"
    echo "    DATABASE_PORT=5432"
    echo "    DATABASE_NAME=zippy_archon"
    echo "    DATABASE_USER=zippy"
    echo "    DATABASE_PASSWORD=password"
    echo ""
    echo "  For Supabase:"
    echo "    SUPABASE_URL=https://your-project.supabase.co"
    echo "    SUPABASE_SERVICE_KEY=your-service-role-key"
}

setup_sqlite() {
    log_info "Setting up SQLite database..."

    # Update .env file for SQLite
    if [ -f ".env" ]; then
        # Remove any existing database configuration
        sed -i '/^DATABASE_TYPE=/d' .env
        sed -i '/^DATABASE_.*=/d' .env
        sed -i '/^SUPABASE_.*=/d' .env

        # Add SQLite configuration
        echo "" >> .env
        echo "# SQLite Configuration" >> .env
        echo "DATABASE_TYPE=sqlite" >> .env
        echo "DATABASE_PATH=zippy_archon.db" >> .env

        log_success "SQLite configured in .env"
    else
        log_error ".env file not found. Please run this script from the project root."
        exit 1
    fi
}

setup_postgresql() {
    log_info "Setting up PostgreSQL database..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Start PostgreSQL container
    log_info "Starting PostgreSQL container..."
    docker-compose -f docker-compose.local.yml up -d postgres

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U zippy > /dev/null 2>&1; then
            log_success "PostgreSQL is ready!"
            break
        fi

        log_info "Waiting... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        log_error "PostgreSQL failed to start within the timeout period."
        exit 1
    fi

    # Update .env file for PostgreSQL
    if [ -f ".env" ]; then
        # Remove any existing database configuration
        sed -i '/^DATABASE_TYPE=/d' .env
        sed -i '/^DATABASE_.*=/d' .env
        sed -i '/^SUPABASE_.*=/d' .env

        # Add PostgreSQL configuration
        echo "" >> .env
        echo "# PostgreSQL Configuration" >> .env
        echo "DATABASE_TYPE=postgresql" >> .env
        echo "DATABASE_HOST=localhost" >> .env
        echo "DATABASE_PORT=5432" >> .env
        echo "DATABASE_NAME=zippy_archon" >> .env
        echo "DATABASE_USER=zippy" >> .env
        echo "DATABASE_PASSWORD=password" >> .env

        log_success "PostgreSQL configured in .env"
        log_info "You can access Adminer (database UI) at: http://localhost:8080"
        log_info "  Server: postgres"
        log_info "  Username: zippy"
        log_info "  Password: password"
        log_info "  Database: zippy_archon"
    else
        log_error ".env file not found. Please run this script from the project root."
        exit 1
    fi
}

setup_supabase() {
    log_info "Setting up Supabase database..."
    log_warning "You'll need to configure your Supabase credentials manually."

    # Update .env file for Supabase
    if [ -f ".env" ]; then
        # Remove any existing database configuration
        sed -i '/^DATABASE_TYPE=/d' .env
        sed -i '/^DATABASE_.*=/d' .env
        sed -i '/^SUPABASE_.*=/d' .env

        # Add Supabase configuration
        echo "" >> .env
        echo "# Supabase Configuration" >> .env
        echo "DATABASE_TYPE=supabase" >> .env
        echo "SUPABASE_URL=https://your-project.supabase.co" >> .env
        echo "SUPABASE_SERVICE_KEY=your-service-role-key" >> .env

        log_success "Supabase template configured in .env"
        log_warning "Please update SUPABASE_URL and SUPABASE_SERVICE_KEY with your actual values"
    else
        log_error ".env file not found. Please run this script from the project root."
        exit 1
    fi
}

# Main script logic
case "${1:-sqlite}" in
    "sqlite")
        setup_sqlite
        ;;
    "postgresql")
        setup_postgresql
        ;;
    "supabase")
        setup_supabase
        ;;
    "help"|"-h"|"--help")
        show_help
        exit 0
        ;;
    *)
        log_error "Unknown database type: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

log_success "Database setup complete!"
log_info "You can now start the Zippy-Archon services:"
log_info "  docker-compose up -d"
log_info ""
log_info "Or if using PostgreSQL:"
log_info "  docker-compose -f docker-compose.local.yml up -d postgres adminer"
log_info "  docker-compose up -d"


