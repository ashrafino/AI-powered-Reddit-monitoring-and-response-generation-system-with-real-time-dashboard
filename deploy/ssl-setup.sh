#!/bin/bash

# SSL Certificate Setup Script for Reddit Bot System
# This script sets up SSL certificates using Let's Encrypt

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if domain is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <domain-name> [email]"
    print_error "Example: $0 example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-admin@$DOMAIN}

print_status "🔒 Setting up SSL certificates for $DOMAIN"
print_status "============================================="

# Validate domain format
if [[ ! $DOMAIN =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
    print_error "Invalid domain format: $DOMAIN"
    exit 1
fi

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root or with sudo"
    exit 1
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    print_status "Installing Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create SSL directory
mkdir -p /opt/reddit-bot/nginx/ssl

# Stop nginx if running
print_status "Stopping nginx temporarily..."
systemctl stop nginx 2>/dev/null || true

# Generate certificate using standalone mode
print_status "Generating SSL certificate for $DOMAIN..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN \
    --domains www.$DOMAIN

# Copy certificates to nginx directory
print_status "Copying certificates to nginx directory..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/reddit-bot/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/reddit-bot/nginx/ssl/

# Set proper permissions
chown -R deploy:deploy /opt/reddit-bot/nginx/ssl/
chmod 600 /opt/reddit-bot/nginx/ssl/privkey.pem
chmod 644 /opt/reddit-bot/nginx/ssl/fullchain.pem

# Update nginx configuration with actual domain
print_status "Updating nginx configuration..."
sed -i "s/your-domain.com/$DOMAIN/g" /opt/reddit-bot/nginx/nginx.prod.conf

# Create certificate renewal script
print_status "Setting up automatic certificate renewal..."
tee /opt/reddit-bot/renew-ssl.sh > /dev/null <<EOF
#!/bin/bash

# SSL Certificate Renewal Script
certbot renew --quiet --no-self-upgrade

# Copy renewed certificates
if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/reddit-bot/nginx/ssl/
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/reddit-bot/nginx/ssl/
    
    # Set permissions
    chown deploy:deploy /opt/reddit-bot/nginx/ssl/*
    chmod 600 /opt/reddit-bot/nginx/ssl/privkey.pem
    chmod 644 /opt/reddit-bot/nginx/ssl/fullchain.pem
    
    # Reload nginx
    docker-compose -f /opt/reddit-bot/docker-compose.prod.yml exec nginx nginx -s reload
    
    echo "$(date): SSL certificates renewed successfully" >> /opt/reddit-bot/logs/ssl-renewal.log
fi
EOF

chmod +x /opt/reddit-bot/renew-ssl.sh

# Add renewal to crontab
print_status "Adding certificate renewal to crontab..."
(crontab -l 2>/dev/null | grep -v "renew-ssl.sh"; echo "0 3 * * * /opt/reddit-bot/renew-ssl.sh") | crontab -

# Create nginx test configuration
print_status "Creating nginx test configuration..."
nginx -t -c /opt/reddit-bot/nginx/nginx.prod.conf || {
    print_error "Nginx configuration test failed"
    exit 1
}

# Start nginx
print_status "Starting nginx..."
systemctl start nginx
systemctl enable nginx

# Test SSL certificate
print_status "Testing SSL certificate..."
sleep 5
if curl -sSf https://$DOMAIN/health > /dev/null; then
    print_success "SSL certificate is working correctly!"
else
    print_warning "SSL test failed - certificate may still be propagating"
fi

# Display certificate information
print_status "Certificate information:"
certbot certificates | grep -A 10 $DOMAIN

print_success "🎉 SSL setup completed successfully!"
print_status ""
print_status "Your SSL certificate is now active for:"
print_status "- https://$DOMAIN"
print_status "- https://www.$DOMAIN"
print_status ""
print_status "Certificate will auto-renew every day at 3 AM"
print_status "Manual renewal: /opt/reddit-bot/renew-ssl.sh"
print_status ""
print_warning "Make sure your DNS A records point to this server's IP address"
print_warning "It may take a few minutes for DNS changes to propagate"