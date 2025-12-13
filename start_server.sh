#!/bin/bash
# Platform-agnostic Nexus Server Launcher for Linux/macOS
# This script handles dependency installation and server startup

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[STARTUP] Nexus Server Launcher for Linux/macOS"
echo "[STARTUP] Python: $(which python3)"
echo "[STARTUP] Platform: $(uname)"
echo ""

# Run the startup wrapper
python3 start_server.py
