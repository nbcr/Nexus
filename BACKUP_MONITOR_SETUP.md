# Backup Storage Monitor Setup Guide

## Overview

The backup storage monitor script prevents backups from failing due to out-of-disk-space errors. It:

1. **Checks filesystem usage** - Scans the entire filesystem to determine current usage
2. **Estimates backup size** - Queries the database and calculates compressed backup size
3. **Validates backup fits** - Ensures the backup won't exceed storage limits
4. **Sends alerts** - Emails admin if backup is prevented or fails

### Configuration

**Storage Limits:**
- Total storage: 20 GB
- Safety margin: 500 MB (reserved for OS)
- Effective limit: 19.5 GB (90% of storage)

Backups are aborted if projected usage would exceed the limit.

## Setup Instructions

### 1. Configure Email Alerts

Copy the example configuration:
```bash
cp /home/nexus/nexus/scripts/.backup-monitor.env.example /home/nexus/nexus/.backup-monitor.env
```

Edit the configuration with your settings:
```bash
nano /home/nexus/nexus/.backup-monitor.env
```

**Email Options:**

#### Option A: Local Mail (sendmail/postfix)
```bash
SMTP_SERVER=localhost
SMTP_PORT=25
SENDER_EMAIL=nexus@your-hostname
ADMIN_EMAIL=your-email@example.com
SMTP_USER=
SMTP_PASSWORD=
```

To install postfix (if needed):
```bash
sudo apt update && sudo apt install -y postfix
# Select "Internet Site" during installation
```

#### Option B: Gmail/OAuth
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-gmail@gmail.com
ADMIN_EMAIL=your-email@example.com
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password  # Generate from Google Account > Security
```

#### Option C: AWS SES
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SENDER_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=your-email@example.com
SMTP_USER=your-ses-username
SMTP_PASSWORD=your-ses-password
```

### 2. Source Configuration in Crontab

Edit crontab:
```bash
crontab -e
```

Add this line to source the environment before running backup:
```bash
0 1 * * * source /home/nexus/nexus/.backup-monitor.env && /home/nexus/nexus/scripts/backup.sh
```

### 3. Verify Installation

Test the backup script manually:
```bash
source /home/nexus/nexus/.backup-monitor.env
/home/nexus/nexus/scripts/backup.sh
```

Check the logs:
```bash
tail -50 /home/nexus/nexus/logs/backup.log
```

## What Happens When Storage Is Full

If the script detects that the next backup would exceed storage limits:

1. **Backup is PREVENTED** - No incomplete backup is created
2. **Email Alert** - Admin receives detailed alert with:
   - Current usage statistics
   - Space needed to proceed
   - Recommendations for cleanup
   - Timestamp and hostname
3. **Retry on Next Run** - Backup attempts again at next scheduled time
4. **Log Entry** - Detailed information in `/home/nexus/nexus/logs/backup.log`

## Manual Cleanup Recommendations

If you receive a storage alert, clean up in this order:

### 1. Old Backups
```bash
ls -lh /home/nexus/backups/
# Remove backups older than 30 days
find /home/nexus/backups -name "*.sql.gz" -mtime +30 -delete
```

### 2. Old Logs
```bash
# Logs are auto-archived after 7 days and auto-deleted after 30
# But you can manually clean if needed:
find /home/nexus/nexus/logs -name "*.log" -mtime +7 -exec gzip {} \;
find /home/nexus/nexus/logs -name "*.gz" -mtime +30 -delete
```

### 3. Temporary Files
```bash
# Clean /tmp
sudo rm -rf /tmp/*

# Check other directories
du -sh /var/cache /var/log /var/tmp
```

### 4. Database Cleanup
```bash
# Run orphaned history cleanup
cd /home/nexus/nexus
python scripts/find_orphaned_history.py
```

### 5. Check Large Directories
```bash
du -sh /home/nexus/nexus/*
du -sh /var/*
```

## Monitoring

Check current usage:
```bash
df -h /
```

View backup history:
```bash
tail -100 /home/nexus/nexus/logs/backup.log
```

List existing backups:
```bash
ls -lh /home/nexus/backups/
```

## Troubleshooting

### Email not sending
- Verify email config: `cat /home/nexus/nexus/.backup-monitor.env`
- Check system mail logs: `sudo tail /var/log/mail.log`
- Test manually:
  ```bash
  source /home/nexus/nexus/.backup-monitor.env
  python -c "import smtplib; s = smtplib.SMTP('$SMTP_SERVER', $SMTP_PORT); print('SMTP OK')"
  ```

### Script permissions
```bash
chmod +x /home/nexus/nexus/scripts/backup_with_storage_check.py
chmod +x /home/nexus/nexus/scripts/backup.sh
```

### Database dump issues
```bash
# Test manual dump
pg_dump -U nexus nexus_db | head -20
```

## Cron Schedule

Backup runs daily at **1:00 AM** (01:00 UTC):
```
0 1 * * * source /home/nexus/nexus/.backup-monitor.env && /home/nexus/nexus/scripts/backup.sh
```

To change timing, edit crontab and modify the time fields.
