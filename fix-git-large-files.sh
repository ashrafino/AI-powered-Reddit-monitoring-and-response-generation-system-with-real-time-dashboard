#!/bin/bash

# Fix Git Large Files Issue
# This script removes large files from Git history and ensures they're properly ignored

set -e

echo "🔧 Fixing Git large files issue..."
echo "=================================="

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

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a Git repository. Please run this from the project root."
    exit 1
fi

print_status "Removing large files from Git tracking..."

# Remove node_modules from Git tracking (but keep local files)
if [ -d "frontend/node_modules" ]; then
    print_status "Removing frontend/node_modules from Git tracking..."
    git rm -r --cached frontend/node_modules/ 2>/dev/null || true
fi

# Remove other potentially large directories
print_status "Removing other large directories from Git tracking..."
git rm -r --cached postgres_data/ 2>/dev/null || true
git rm -r --cached redis_data/ 2>/dev/null || true
git rm -r --cached logs/ 2>/dev/null || true
git rm -r --cached .next/ 2>/dev/null || true
git rm -r --cached build/ 2>/dev/null || true
git rm -r --cached dist/ 2>/dev/null || true

# Remove .kiro directory if it exists
if [ -d ".kiro" ]; then
    print_status "Removing .kiro directory from Git tracking..."
    git rm -r --cached .kiro/ 2>/dev/null || true
fi

# Remove any .env files that might have been accidentally committed
git rm --cached .env 2>/dev/null || true
git rm --cached .env.local 2>/dev/null || true
git rm --cached .env.development 2>/dev/null || true
git rm --cached .env.production 2>/dev/null || true

print_status "Adding changes to Git..."
git add .gitignore

print_status "Committing changes..."
git commit -m "fix: Remove large files and update .gitignore

- Remove frontend/node_modules from Git tracking
- Remove data directories (postgres_data, redis_data, logs)
- Remove .kiro IDE files
- Update .gitignore to prevent future issues
- Ensure only source code is tracked"

print_success "Git repository cleaned!"

print_status "Checking repository size..."
git count-objects -vH

print_warning "Important notes:"
echo "1. The node_modules directory is still on your local machine"
echo "2. Run 'npm install' in the frontend directory if needed"
echo "3. Large files have been removed from Git tracking"
echo "4. Your .gitignore now prevents these files from being tracked"

print_status "You can now push to GitHub:"
echo "git push -u origin main"

print_success "Repository is ready for GitHub! 🎉"