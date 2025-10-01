#!/bin/bash

# DigitalOcean Deployment Setup Script for Reddit Bot System
# This script sets up a DigitalOcean droplet for production deployment

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

print_status "🚀 DigitalOcean Deployment Setup for Reddit Bot System"
print_status "======================================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install essential packages
print_status "Installing essential packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ufw \
    fail2ban \
    htop \
    git \
    unzip \
    wget

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    print_success "Docker installed successfully"
else
    print_success "Docker is already installed"
fi

# Install Docker Compose (standalone)
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed"
fi

# Configure firewall
print_status "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
print_success "Firewall configured"

# Configure fail2ban
print_status "Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
print_success "Fail2ban configured"

# Create application directory
print_status "Creating application directory..."
sudo mkdir -p /opt/reddit-bot
sudo chown $USER:$USER /opt/reddit-bot
cd /opt/reddit-bot

# Create necessary directories
mkdir -p {logs,backups,ssl,nginx}

print_success "Application directory created at /opt/reddit-bot"

# Install Certbot for SSL
print_status "Installing Certbot for SSL certificates..."
sudo apt-get install -y certbot python3-certbot-nginx
print_success "Certbot installed"

# Create deployment user
print_status "Creating deployment user..."
if ! id "deploy" &>/dev/null; then
    sudo useradd -m -s /bin/bash deploy
    sudo usermod -aG docker deploy
    sudo usermod -aG sudo deploy
    print_success "Deploy user created"
else
    print_success "Deploy user already exists"
fi

# Set up SSH key for deploy user (optional)
print_status "Setting up SSH for deploy user..."
sudo mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chown deploy:deploy /home/deploy/.ssh

# Create systemd service for the application
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/reddit-bot.service > /dev/null <<EOF
[Unit]
Description=Reddit Bot System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/reddit-bot
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=deploy
Group=deploy

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable reddit-bot.service
print_success "Systemd service created"

# Create log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/reddit-bot > /dev/null <<EOF
/opt/reddit-bot/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        /usr/local/bin/docker-compose -f /opt/reddit-bot/docker-compose.prod.yml exec nginx nginx -s reload
    endscript
}
EOF
print_success "Log rotation configured"

# Create backup script
print_status "Creating backup script..."
tee /opt/reddit-bot/backup.sh > /dev/null <<'EOF'
#!/bin/bash

# Reddit Bot System Backup Script
BACKUP_DIR="/opt/reddit-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="reddit-bot-backup-$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f /opt/reddit-bot/docker-compose.prod.yml exec -T postgres pg_dump -U postgres redditbot > $BACKUP_DIR/db-$DATE.sql

# Backup application data
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    /opt/reddit-bot

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x /opt/reddit-bot/backup.sh
print_success "Backup script created"

# Add backup to crontab
print_status "Setting up automated backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/reddit-bot/backup.sh >> /opt/reddit-bot/logs/backup.log 2>&1") | crontab -
print_success "Automated backups configured (daily at 2 AM)"

# Create monitoring script
print_status "Creating monitoring script..."
tee /opt/reddit-bot/monitor.sh > /dev/null <<'EOF'
#!/bin/bash

# Reddit Bot System Monitoring Script
cd /opt/reddit-bot

# Check if services are running
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "$(date): Services are down, attempting restart..." >> logs/monitor.log
    docker-compose -f docker-compose.prod.yml up -d
fi

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): High disk usage: $DISK_USAGE%" >> logs/monitor.log
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "$(date): High memory usage: $MEMORY_USAGE%" >> logs/monitor.log
fi
EOF

chmod +x /opt/reddit-bot/monitor.sh
print_success "Monitoring script created"

# Add monitoring to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/reddit-bot/monitor.sh") | crontab -
print_success "Monitoring configured (every 5 minutes)"

# Create deployment script
print_status "Creating deployment script..."
tee /opt/reddit-bot/deploy.sh > /dev/null <<'EOF'
#!/bin/bash

# Reddit Bot System Deployment Script
set -e

cd /opt/reddit-bot

echo "🚀 Starting deployment..."

# Pull latest changes
git pull origin main

# Build and deploy
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Clean up old images
docker image prune -f

echo "✅ Deployment completed successfully!"
EOF

chmod +x /opt/reddit-bot/deploy.sh
print_success "Deployment script created"

# Set up Docker daemon configuration for production
print_status "Configuring Docker for production..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF

sudo systemctl restart docker
print_success "Docker configured for production"

print_success "🎉 DigitalOcean setup completed successfully!"
print_status ""
print_status "Next steps:"
print_status "1. Clone your repository to /opt/reddit-bot"
print_status "2. Create .env.prod file with production environment variables"
print_status "3. Configure SSL certificates with Certbot"
print_status "4. Deploy your application with ./deploy.sh"
print_status ""
print_warning "Important: Please reboot the server to ensure all changes take effect"
print_warning "After reboot, you may need to re-run 'newgrp docker' or logout/login"
print_status ""
print_status "Useful commands:"
print_status "- Check service status: sudo systemctl status reddit-bot"
print_status "- View logs: docker-compose -f docker-compose.prod.yml logs -f"
print_status "- Monitor resources: htop"
print_status "- Backup manually: ./backup.sh"
print_status "- Deploy updates: ./deploy.sh"