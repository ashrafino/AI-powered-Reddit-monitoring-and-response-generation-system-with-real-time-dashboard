#!/bin/bash

# Fix PostgreSQL password mismatch issue
echo "Fixing PostgreSQL password configuration..."

# Stop all containers
echo "Stopping containers..."
docker-compose -f docker-compose.prod.yml down -v

# Backup current .env
cp .env .env.backup

# Use .env.production as the main .env file
echo "Using .env.production configuration..."
cp .env.production .env

# Rebuild and start services
echo "Starting services with correct configuration..."
docker-compose -f docker-compose.prod.yml up -d

# Wait a bit for services to start
sleep 10

# Check status
echo ""
echo "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "Checking backend logs..."
docker-compose -f docker-compose.prod.yml logs backend --tail=20

echo ""
echo "Done! If you see errors, run: docker-compose -f docker-compose.prod.yml logs backend"
