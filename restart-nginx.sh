#!/bin/bash
# Restart Nginx to apply redirect configuration changes

echo "🔄 Restarting Nginx..."

# Test nginx configuration first
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    
    # Reload nginx (graceful restart)
    sudo systemctl reload nginx
    
    echo "✅ Nginx reloaded successfully"
    echo ""
    echo "🧪 Testing redirects:"
    echo "Testing /login.html redirect..."
    curl -I https://nexus.comdat.ca/login.html 2>&1 | grep -E "HTTP|Location"
    
    echo ""
    echo "Testing /settings.html redirect..."
    curl -I https://nexus.comdat.ca/settings.html 2>&1 | grep -E "HTTP|Location"
    
    echo ""
    echo "✅ Done! The .html URLs should now redirect properly."
else
    echo "❌ Nginx configuration has errors. Please fix before restarting."
fi

