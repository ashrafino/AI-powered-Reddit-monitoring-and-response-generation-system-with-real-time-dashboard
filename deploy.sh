#!/bin/bash

# Reddit Bot Deployment Script for Digital Ocean

set -e

echo "🚀 Starting Reddit Bot deployment..."

# Check if docker and docker-compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans || true

# Remove old images to ensure fresh build
echo "🧹 Cleaning up old images..."
docker system prune -f

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check if postgres is ready
echo "Checking PostgreSQL..."
docker-compose exec -T postgres pg_isready -U postgres || echo "⚠️  PostgreSQL not ready yet"

# Check if redis is ready
echo "Checking Redis..."
docker-compose exec -T redis redis-cli ping || echo "⚠️  Redis not ready yet"

# Check if backend is ready
echo "Checking Backend API..."
curl -f http://localhost/api/health || echo "⚠️  Backend API not ready yet"

# Show running containers
echo "📋 Running containers:"
docker-compose ps

echo "✅ Deployment complete!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost"
echo "   API Docs: http://localhost/api/docs"
echo "   Admin Login: admin@example.com / admin123"
echo ""
echo "📊 To check logs:"
echo "   docker-compose logs -f [service_name]"
echo ""
echo "🛠️  To test login:"
echo "   python3 test_login.py"