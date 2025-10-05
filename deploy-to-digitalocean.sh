#!/bin/bash

# DigitalOcean Deployment Script
# This script automates the deployment process

set -e

echo "🚀 Reddit Bot - DigitalOcean Deployment Script"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on server
if [ ! -f "/etc/os-release" ]; then
    echo -e "${RED}❌ This script should be run on your DigitalOcean server${NC}"
    exit 1
fi

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_success "Docker installed"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo "Creating .env from template..."
    if [ -f ".env.prod.example" ]; then
        cp .env.prod.example .env
        print_warning "Please edit .env file with your actual values"
        echo "Run: nano .env"
        exit 1
    else
        print_error ".env.prod.example not found"
        exit 1
    fi
fi

print_success ".env file found"

# Ask for confirmation
echo ""
echo "This will:"
echo "  1. Stop existing containers"
echo "  2. Pull latest code (if git repo)"
echo "  3. Build Docker images"
echo "  4. Start all services"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Stop existing containers
echo ""
echo "📦 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true
print_success "Containers stopped"

# Pull latest code if git repo
if [ -d ".git" ]; then
    echo ""
    echo "📥 Pulling latest code..."
    git pull || print_warning "Could not pull latest code"
fi

# Build and start services
echo ""
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

# Check health
echo ""
echo "🏥 Health Checks:"

# Check backend
if curl -f http://localhost:8001/api/health &> /dev/null; then
    print_success "Backend is healthy"
else
    print_error "Backend health check failed"
fi

# Check frontend
if curl -f http://localhost:3000 &> /dev/null; then
    print_success "Frontend is healthy"
else
    print_error "Frontend health check failed"
fi

# Check nginx
if curl -f http://localhost &> /dev/null; then
    print_success "Nginx is healthy"
else
    print_error "Nginx health check failed"
fi

# Show logs
echo ""
echo "📋 Recent Logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20

echo ""
echo "=============================================="
print_success "Deployment Complete!"
echo ""
echo "Access your application at:"
echo "  - http://$(curl -s ifconfig.me)"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Check status: docker-compose -f docker-compose.prod.yml ps"
echo "  - Restart: docker-compose -f docker-compose.prod.yml restart"
echo "  - Stop: docker-compose -f docker-compose.prod.yml down"
echo ""
