#!/bin/bash
# Check server logs for errors
echo "=== Recent server logs ==="
sudo journalctl -u nexus.service -n 50 --no-pager
