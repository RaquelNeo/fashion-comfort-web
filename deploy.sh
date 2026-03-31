#!/bin/bash
# Fashion Comfort — Auto deploy script
# This script runs on the server via cron
# It pulls latest changes from GitHub and deploys to /var/www/html

REPO_DIR="/var/www/fashion-comfort-web"
WEB_DIR="/var/www/html"
REPO_URL="https://github.com/RaquelNeo/fashion-comfort-web.git"

# Clone if not exists
if [ ! -d "$REPO_DIR" ]; then
    git clone "$REPO_URL" "$REPO_DIR"
fi

# Pull latest
cd "$REPO_DIR"
git pull origin main 2>&1

# Sync files to web directory (exclude git, backend, docs)
rsync -av --delete \
    --exclude '.git' \
    --exclude 'backend' \
    --exclude 'docs' \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '*.mov' \
    --exclude '.gitignore' \
    --exclude 'deploy.sh' \
    --exclude 'package.json' \
    --exclude 'package-lock.json' \
    "$REPO_DIR/" "$WEB_DIR/"

echo "Deploy completed: $(date)"
