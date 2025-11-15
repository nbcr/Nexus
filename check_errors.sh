#!/bin/bash
# Get recent error logs
echo "=== Checking for errors ==="
sudo journalctl -u nexus.service --since "1 minute ago" | grep -i "error\|traceback\|exception" -A 10
