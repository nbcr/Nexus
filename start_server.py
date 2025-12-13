#!/usr/bin/env python3
"""
Platform-agnostic server startup wrapper.
Handles dependency installation and server startup on Windows, Linux, and macOS.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_server():
    """Run the server with dependency checking"""
    project_root = Path(__file__).parent

    # Change to project root
    os.chdir(project_root)

    print("[STARTUP] Platform-agnostic Nexus Server Launcher")
    print(f"[STARTUP] Python: {sys.executable}")
    print(f"[STARTUP] Platform: {sys.platform}")
    print(f"[STARTUP] Working Directory: {os.getcwd()}")
    print()

    # Run the server with dependency checking
    try:
        result = subprocess.run(
            [sys.executable, "run_server.py"],
            cwd=str(project_root),
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n[STARTUP] Server stopped by user")
        return 0
    except Exception as e:
        print(f"[STARTUP] Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_server()
    sys.exit(exit_code)
