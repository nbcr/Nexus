#!/bin/bash
# Display the most recent log files in the logs folder
LOG_DIR="$(dirname "$0")/logs"

if [[ ! -d "$LOG_DIR" ]]; then
    echo "Logs directory not found: $LOG_DIR"
    exit 1
fi

# List log files, sorted by modification time (newest first)
LOG_FILES=$(ls -1t "$LOG_DIR"/*.log 2>/dev/null)

if [[ -z "$LOG_FILES" ]]; then
    echo "No log files found in $LOG_DIR"
    exit 1
fi

for LOG in $LOG_FILES; do
    echo "=== $LOG ==="
    tail -n 50 "$LOG"
    echo ""
done
