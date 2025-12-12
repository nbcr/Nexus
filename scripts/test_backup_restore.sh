#!/bin/bash
# Test backup and restore process
# This verifies the latest backup can be restored successfully

echo "=== Backup Restore Test ==="
echo "Starting at: $(date)"

# Find latest backup
LATEST_BACKUP=$(ls -t /home/nexus/backups/nexus_db_*.sql.gz | head -1)

if [[ -z "$LATEST_BACKUP" ]]; then
    echo "❌ ERROR: No backup files found" >&2
    exit 1
fi

echo "Latest backup: $LATEST_BACKUP"
echo "Backup size: $(du -h $LATEST_BACKUP | cut -f1)"
echo "Lines in backup: $(gunzip -c $LATEST_BACKUP | wc -l)"

# Create test database
echo ""
echo "Creating test database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS nexus_test;" 2>/dev/null
sudo -u postgres psql -c "CREATE DATABASE nexus_test;"

# Restore to test database
echo "Restoring backup to test database..."
gunzip -c $LATEST_BACKUP | sudo -u postgres psql nexus_test > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
    echo "✅ Restore successful"
    
    # Check table counts
    echo ""
    echo "Table counts:"
    sudo -u postgres psql nexus_test -c "SELECT 'content_items' as table, COUNT(*) FROM content_items
    UNION ALL SELECT 'topics', COUNT(*) FROM topics
    UNION ALL SELECT 'users', COUNT(*) FROM users;" 2>/dev/null
    
    # Cleanup test database
    sudo -u postgres psql -c "DROP DATABASE nexus_test;" 2>/dev/null
    echo ""
    echo "✅ Backup is valid and can be restored"
else
    echo "❌ ERROR: Restore failed" >&2
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS nexus_test;" 2>/dev/null
    exit 1
fi

echo ""
echo "Finished at: $(date)"
