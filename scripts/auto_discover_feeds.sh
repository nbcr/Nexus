#!/bin/bash
# Cron job for automatic RSS feed discovery
# Add to crontab: crontab -e
# Run weekly on Sundays at 2 AM:
# 0 2 * * 0 /home/nexus/nexus/scripts/auto_discover_feeds.sh

cd /home/nexus/nexus

# Activate virtual environment
source venv/bin/activate

# Run discovery script
/home/nexus/nexus/venv/bin/python scripts/discover_rss_feeds.py >> logs/feed_discovery.log 2>&1

# If new feeds were added, commit and deploy
if git diff --quiet app/services/trending_service.py; then
    echo "$(date): No new feeds discovered" >> logs/feed_discovery.log
else
    echo "$(date): New feeds discovered, committing..." >> logs/feed_discovery.log
    git add app/services/trending_service.py
    git commit -m "Auto-discovery: Add new RSS feeds based on user preferences"
    git push
    
    # Restart service to load new feeds
    sudo systemctl restart nexus
    echo "$(date): Service restarted with new feeds" >> logs/feed_discovery.log
fi
