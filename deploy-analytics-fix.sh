#!/bin/bash
# Deploy Analytics Fix - Update cache-busting version parameters
# This script deploys the updated templates with new version parameters
# to force browsers to load the latest JavaScript files with GA tracking

echo "🚀 Deploying Analytics Fix..."

# Navigate to project directory
cd /home/nexus/nexus

echo "📥 Pulling latest changes from git..."
git pull origin main

echo "🔄 Restarting FastAPI service to reload templates..."
sudo systemctl restart nexus

echo "✅ Checking service status..."
sudo systemctl status nexus --no-pager

echo ""
echo "🎯 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Open your browser to https://nexus.comdat.ca"
echo "2. Hard refresh (Ctrl+F5 or Cmd+Shift+R) to clear cache"
echo "3. Open browser DevTools (F12)"
echo "4. Go to Console tab"
echo "5. Click on an article to trigger 'article_open' event"
echo "6. Wait 10+ seconds to trigger 'article_read' event"
echo "7. Check GA4 Realtime reports to verify events"
echo ""
echo "🐛 If events still don't work:"
echo "   - Check browser console for 'gtag is not defined' errors"
echo "   - Verify Google Analytics tag loads in Network tab"
echo "   - Check if feed.js version is 202512010100 in Network tab"
echo ""

