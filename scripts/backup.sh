#!/bin/bash
# Backup wrapper script with storage validation
# This replaces the simple pg_dump cron job with a Python script that checks storage first

cd /home/nexus/nexus
/home/nexus/nexus/venv/bin/python /home/nexus/nexus/scripts/backup_with_storage_check.py >> /home/nexus/nexus/logs/backup.log 2>&1
