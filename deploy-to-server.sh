#!/bin/bash

# Deployment script for Reddit Bot
# This script deploys the latest code to the DigitalOcean server

set -e  # Exit on any error

SERVER_IP="164.90.222.87"
SERVER_USER="root"
PROJECT_PATH="/home/deploy/apps/reddit-bot"

echo "🚀 Starting deployment to $SERVER_IP..."

# Step 1: Copy production .env file to server
echo "📋 Copying production environment file..."
scp .env.production $SERVER_USER@$SERVER_IP:$PROJECT_PATH/.env

# Step 2: Copy error fix script
echo "📋 Copying error fix script..."
scp fix-server-errors.sh $SERVER_USER@$SERVER_IP:$PROJECT_PATH/

# Step 3: SSH into server and run deployment commands
echo "🔧 Deploying on server..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home/deploy/apps/reddit-bot

echo "📥 Pulling latest code from GitHub..."
git pull origin main

echo "🛑 Stopping containers..."
docker-compose down

echo "🏗️  Building containers..."
docker-compose build --no-cache

echo "🚀 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 15

echo "🔍 Running error diagnostics..."
chmod +x fix-server-errors.sh
./fix-server-errors.sh

echo "📊 Final container status..."
docker-compose ps

echo "✅ Deployment complete!"
ENDSSH

echo ""
echo "✅ Deployment finished!"
echo ""
echo "🔍 To check logs, run:"
echo "   ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_PATH && docker-compose logs -f'"
echo ""
echo "🔧 To run diagnostics, run:"
echo "   ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_PATH && ./fix-server-errors.sh'"
echo ""
echo "🌐 Your app should be available at:"
echo "   http://$SERVER_IP:3000"
echo ""
