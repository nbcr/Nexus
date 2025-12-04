# Backup Storage Monitor - Quick Start

## What Was Installed

A new backup system that prevents out-of-disk-space errors by checking storage before creating backups.

## Key Features

✅ **Scans entire filesystem** to calculate current usage  
✅ **Estimates backup size** from database  
✅ **Prevents backups** if they would exceed 19.5GB limit  
✅ **Sends email alerts** when storage is critical  
✅ **Provides cleanup recommendations**  
✅ **Logs all activities** to `/home/nexus/nexus/logs/backup.log`  

## Files Created

```
/home/nexus/nexus/scripts/backup_with_storage_check.py  - Main backup script
/home/nexus/nexus/scripts/backup.sh                      - Wrapper for cron
/home/nexus/nexus/.backup-monitor.env                    - Email configuration
/home/nexus/nexus/BACKUP_MONITOR_SETUP.md                - Detailed setup guide
```

## Configuration (REQUIRED)

**Edit email settings:**
```bash
nano /home/nexus/nexus/.backup-monitor.env
```

Update these fields:
```bash
ADMIN_EMAIL=your-email@example.com      # Where alerts go
SMTP_SERVER=localhost                   # Mail server
SMTP_PORT=25                            # Mail server port
SENDER_EMAIL=nexus@your-hostname        # From address
SMTP_USER=                              # Leave empty for local mail
SMTP_PASSWORD=                          # Leave empty for local mail
```

## Storage Limits

- **Total storage:** 20 GB
- **Reserved for OS:** 500 MB
- **Backup limit:** 19.5 GB (90% of total)

If projected usage > 19.5 GB, backup is prevented and email alert is sent.

## When Backup Fails

You'll receive an email with:
- ❌ Current disk usage (GB and %)
- ❌ Space needed to free up
- ❌ Recommendations for cleanup
- ❌ Server hostname and timestamp

## Manual Backup

```bash
# Test the backup (runs immediately)
source /home/nexus/nexus/.backup-monitor.env
/home/nexus/nexus/scripts/backup.sh

# View results
tail -50 /home/nexus/nexus/logs/backup.log
```

## Check Current Status

```bash
# Disk usage
df -h /

# Backup history
ls -lh /home/nexus/backups/

# Recent logs
tail -30 /home/nexus/nexus/logs/backup.log
```

## Scheduled Backup

Runs daily at **1:00 AM UTC** (cron job):
```
0 1 * * * source /home/nexus/nexus/.backup-monitor.env && /home/nexus/nexus/scripts/backup.sh
```

## Cleanup if Storage Alert

**Option 1: Delete old backups**
```bash
# Keep only backups from last 7 days
find /home/nexus/backups -name "*.sql.gz" -mtime +7 -delete
```

**Option 2: Compress old logs**
```bash
# Logs are auto-managed but can be manually compressed
find /home/nexus/nexus/logs -name "*.log" -mtime +7 -exec gzip {} \;
find /home/nexus/nexus/logs -name "*.gz" -mtime +30 -delete
```

**Option 3: Clear temp files**
```bash
sudo rm -rf /tmp/*
```

**Option 4: Check what's using space**
```bash
du -sh /home/nexus/nexus/*
du -sh /var/*
```

## Troubleshooting

### Email not working
```bash
# Test SMTP connection
source /home/nexus/nexus/.backup-monitor.env
python3 -c "import smtplib; s = smtplib.SMTP('$SMTP_SERVER', $SMTP_PORT); print('OK')"
```

### Backup script permissions
```bash
chmod +x /home/nexus/nexus/scripts/backup_with_storage_check.py
chmod +x /home/nexus/nexus/scripts/backup.sh
```

### View detailed logs
```bash
tail -100 /home/nexus/nexus/logs/backup.log
```

## Server Configuration Summary

| Setting | Value |
|---------|-------|
| Total RAM | 1 GB |
| Total Storage | 20 GB |
| Current Usage | ~13 GB (65%) |
| Gunicorn Workers | 3 (limited to prevent OOM) |
| Worker Timeout | 120 seconds |
| Graceful Shutdown | 30 seconds |
| Backup Schedule | Daily 1:00 AM |
| Backup Limit | 19.5 GB |

---

For detailed setup instructions, see `BACKUP_MONITOR_SETUP.md`
