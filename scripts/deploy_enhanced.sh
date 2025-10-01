#!/bin/bash

# Enhanced Reddit Bot System Deployment Script
# This script sets up the enhanced system with all new features

set -e

echo "🚀 Starting Enhanced Reddit Bot System Deployment"

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Checking system requirements..."

# Check available memory
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$MEMORY_GB" -lt 4 ]; then
    print_warning "System has less than 4GB RAM. Performance may be affected."
    print_warning "Recommended: 4GB+ RAM for optimal performance"
fi

# Check available disk space
DISK_SPACE_GB=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
if [ "$DISK_SPACE_GB" -lt 10 ]; then
    print_warning "Less than 10GB disk space available. Consider freeing up space."
fi

print_success "System requirements check completed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    
    # Generate a secure secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=change-this-in-production/SECRET_KEY=$SECRET_KEY/" .env
    
    # Generate Redis password
    REDIS_PASSWORD=$(openssl rand -hex 16)
    echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env
    
    print_success ".env file created with secure defaults"
    print_warning "Please edit .env file to add your API keys:"
    print_warning "  - OPENAI_API_KEY"
    print_warning "  - REDDIT_CLIENT_ID"
    print_warning "  - REDDIT_CLIENT_SECRET"
    print_warning "  - SERPAPI_API_KEY (optional)"
    print_warning "  - YOUTUBE_API_KEY (optional)"
    
    read -p "Press Enter to continue after updating .env file..."
else
    print_status ".env file already exists"
fi

# Validate required environment variables
print_status "Validating environment variables..."

source .env

REQUIRED_VARS=("SECRET_KEY" "OPENAI_API_KEY" "REDDIT_CLIENT_ID" "REDDIT_CLIENT_SECRET")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        print_error "  - $var"
    done
    print_error "Please update your .env file and run this script again"
    exit 1
fi

print_success "Environment variables validated"

# Build and start services
print_status "Building Docker images..."
docker-compose build --no-cache

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check if backend is responding
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    print_success "Backend service is healthy"
else
    print_error "Backend service is not responding"
    print_status "Checking logs..."
    docker-compose logs backend
    exit 1
fi

# Check if frontend is responding
if curl -f http://localhost > /dev/null 2>&1; then
    print_success "Frontend service is healthy"
else
    print_warning "Frontend service may still be starting up"
fi

# Check if Redis is responding
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis service is healthy"
else
    print_error "Redis service is not responding"
    exit 1
fi

# Check if PostgreSQL is responding
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL service is healthy"
else
    print_error "PostgreSQL service is not responding"
    exit 1
fi

# Create admin user
print_status "Creating admin user..."
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

docker-compose exec -T backend python -m app.scripts.create_admin

print_success "Admin user created"
print_status "Admin credentials:"
print_status "  Email: $ADMIN_EMAIL"
print_status "  Password: $ADMIN_PASSWORD"

# Run initial database setup
print_status "Setting up database..."
docker-compose exec -T backend python -c "
from app.db.base import Base
from app.db.session import engine
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

print_success "Database setup completed"

# Test API endpoints
print_status "Testing API endpoints..."

# Test health endpoint
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    print_success "Health endpoint working"
else
    print_error "Health endpoint not working"
fi

# Test WebSocket endpoint (basic check)
print_status "WebSocket endpoint available at: ws://localhost/api/ws"

# Display final status
print_success "🎉 Enhanced Reddit Bot System deployment completed!"
echo ""
print_status "Access your application:"
print_status "  Frontend: http://localhost"
print_status "  API Docs: http://localhost/api/docs"
print_status "  Admin Panel: http://localhost (login with admin credentials)"
echo ""
print_status "New Features Available:"
print_status "  ✅ Advanced Analytics & Reporting"
print_status "  ✅ AI Response Quality Scoring"
print_status "  ✅ Real-time Dashboard Updates (WebSockets)"
print_status "  ✅ Enhanced User Management"
print_status "  ✅ Performance Monitoring"
print_status "  ✅ Trend Analysis"
echo ""
print_status "Background Services:"
print_status "  ✅ Reddit Monitoring (every 5 minutes)"
print_status "  ✅ Performance Metrics (daily)"
print_status "  ✅ Trend Analysis (weekly)"
print_status "  ✅ Data Cleanup (weekly)"
echo ""
print_warning "Next Steps:"
print_warning "1. Login to the admin panel and create your first client"
print_warning "2. Configure Reddit monitoring keywords and subreddits"
print_warning "3. Set up brand voice and response preferences"
print_warning "4. Monitor the dashboard for real-time updates"
echo ""
print_status "For detailed documentation, see:"
print_status "  - README.md (basic setup)"
print_status "  - ENHANCED_FEATURES_GUIDE.md (new features)"
print_status "  - COMPLETE_SETUP_GUIDE.md (comprehensive guide)"
echo ""
print_status "To view logs: docker-compose logs -f [service_name]"
print_status "To stop services: docker-compose down"
print_status "To restart services: docker-compose restart"
echo ""
print_success "Deployment completed successfully! 🚀"