#!/bin/bash
# Automated deployment with automatic cache busting
# Usage: ./scripts/deploy.sh [ec2_host] [ec2_user]
# Example: ./scripts/deploy.sh ec2-35-172-220-70.compute-1.amazonaws.com admin

set -e

# Default values
EC2_HOST="${1:-ec2-35-172-220-70.compute-1.amazonaws.com}"
EC2_USER="${2:-admin}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/nexus_ec2.pem}"
NEXUS_USER="nexus"
NEXUS_HOME="/home/nexus/nexus"

echo "🚀 Nexus Deployment Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🖥️  Target: $EC2_USER@$EC2_HOST"
echo "📍 Path: $NEXUS_HOME"
echo ""

# Step 1: Update cache busting locally
echo "📦 Step 1/4: Updating cache busting versions..."
python3 scripts/update_cache_bust.py
echo ""

# Step 2: Commit changes if any
echo "💾 Step 2/4: Committing changes..."
if git status --porcelain | grep -q .; then
    git add app/templates/
    git commit -m "Auto: Update cache busting versions" || true
    echo "✓ Changes committed"
else
    echo "✓ No changes to commit"
fi
echo ""

# Step 3: Push to remote
echo "⬆️  Step 3/4: Pushing to repository..."
git push origin main || true
echo "✓ Pushed to remote"
echo ""

# Step 4: Deploy to EC2
echo "🌐 Step 4/4: Deploying to EC2..."
ssh -o StrictHostKeyChecking=accept-new -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << 'DEPLOY_SCRIPT'
set -e
cd /home/nexus/nexus
echo "  Pulling latest changes..."
sudo -u nexus git pull
echo "  Restarting service..."
sudo systemctl restart nexus
echo "  ✓ Service restarted"
sleep 2
if sudo systemctl is-active --quiet nexus; then
    echo "  ✅ Service is running"
else
    echo "  ⚠️  Service check failed"
    sudo systemctl status nexus || true
fi
DEPLOY_SCRIPT

echo ""
echo "✨ Deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌍 Live at: https://comdat.ca"
