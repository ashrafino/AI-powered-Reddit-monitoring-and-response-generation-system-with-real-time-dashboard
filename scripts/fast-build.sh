#!/bin/bash

# Fast build script for Reddit Bot System
# This script optimizes Docker builds for faster development

set -e

echo "🚀 Reddit Bot System - Fast Build Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install it and try again."
    exit 1
fi

# Parse command line arguments
MODE="dev"
CLEAN=false
PULL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            MODE="prod"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --pull)
            PULL=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prod, --production    Build for production (default: development)"
            echo "  --clean                 Clean build (remove volumes and rebuild)"
            echo "  --pull                  Pull latest base images"
            echo "  --help, -h              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

print_status "Build mode: $MODE"

# Clean build if requested
if [ "$CLEAN" = true ]; then
    print_warning "Cleaning up existing containers and volumes..."
    if [ "$MODE" = "dev" ]; then
        docker-compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
    else
        docker-compose down -v --remove-orphans 2>/dev/null || true
    fi
    docker system prune -f
    print_success "Cleanup completed"
fi

# Pull latest images if requested
if [ "$PULL" = true ]; then
    print_status "Pulling latest base images..."
    docker pull python:3.11-slim
    docker pull postgres:16-alpine
    docker pull redis:7-alpine
    docker pull nginx:1.27-alpine
    docker pull node:18-alpine
    print_success "Base images updated"
fi

# Set up environment file if it doesn't exist
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
    else
        cat > .env << EOF
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres/redditbot

# Redis
REDIS_PASSWORD=redispass
REDIS_URL=redis://:redispass@redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:redispass@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redispass@redis:6379/1

# App
APP_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# Reddit API (add your credentials)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditBot/1.0

# OpenAI API (add your key)
OPENAI_API_KEY=your_openai_api_key
EOF
        print_success "Created default .env file"
        print_warning "Please update .env with your actual API credentials"
    fi
fi

# Build and start services
print_status "Building and starting services..."

if [ "$MODE" = "dev" ]; then
    print_status "Starting development environment..."
    print_status "This will be much faster as it skips Docker builds!"
    
    # Start core services first
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    print_status "Waiting for core services to be ready..."
    sleep 10
    
    # Start application services
    docker-compose -f docker-compose.dev.yml up -d backend-dev worker-dev beat-dev frontend-dev
    
    print_success "Development environment started!"
    print_status "Services:"
    print_status "  - Backend API: http://localhost:8001"
    print_status "  - Frontend: http://localhost:3000"
    print_status "  - PostgreSQL: localhost:5432"
    print_status "  - Redis: localhost:6379"
    
    print_status "To view logs: docker-compose -f docker-compose.dev.yml logs -f"
    print_status "To stop: docker-compose -f docker-compose.dev.yml down"
    
else
    print_status "Building production environment..."
    
    # Enable BuildKit for faster builds
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    # Build with parallel builds
    docker-compose build --parallel
    
    # Start services
    docker-compose up -d
    
    print_success "Production environment started!"
    print_status "Services:"
    print_status "  - Application: http://localhost:80"
    print_status "  - Backend API: http://localhost:8001"
    
    print_status "To view logs: docker-compose logs -f"
    print_status "To stop: docker-compose down"
fi

# Show running containers
print_status "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

print_success "Build completed successfully! 🎉"

# Health check
print_status "Performing health checks..."
sleep 5

if [ "$MODE" = "dev" ]; then
    if curl -f http://localhost:8001/api/health > /dev/null 2>&1; then
        print_success "Backend is healthy ✓"
    else
        print_warning "Backend health check failed - it may still be starting up"
    fi
    
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is healthy ✓"
    else
        print_warning "Frontend health check failed - it may still be starting up"
    fi
else
    if curl -f http://localhost:80 > /dev/null 2>&1; then
        print_success "Application is healthy ✓"
    else
        print_warning "Application health check failed - it may still be starting up"
    fi
fi

print_status "Setup complete! Check the logs if any services failed to start."