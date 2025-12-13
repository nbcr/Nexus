#!/usr/bin/env python3
"""
Platform-agnostic dependency checker.
Runs before the server starts and installs missing packages automatically.
"""

import subprocess
import sys
import os
import importlib.util
from pathlib import Path


def get_requirements_file():
    """Find requirements.txt in the project root"""
    root_dir = Path(__file__).parent
    req_file = root_dir / "requirements.txt"

    if req_file.exists():
        return str(req_file)

    raise FileNotFoundError("requirements.txt not found in project root")


def is_package_installed(package_name):
    """Check if a package is installed without importing it"""
    # Handle special cases where import name differs from package name
    import_names = {
        "pillow": "PIL",
        "pyyaml": "yaml",
        "python-dotenv": "dotenv",
    }

    import_name = import_names.get(package_name.lower(), package_name.lower())

    try:
        importlib.util.find_spec(import_name)
        return True
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def get_python_executable():
    """Get the Python executable path"""
    return sys.executable


def install_dependencies(requirements_file):
    """Install dependencies from requirements.txt"""
    print(f"[DEPENDENCY CHECK] Installing dependencies from {requirements_file}...")

    python_exe = get_python_executable()

    try:
        # Use pip to install from requirements.txt
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "-q", "-r", requirements_file],
            capture_output=False,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            print("[DEPENDENCY CHECK] ✓ All dependencies installed successfully")
            return True
        else:
            print(
                f"[DEPENDENCY CHECK] ✗ pip install failed with code {result.returncode}"
            )
            return False

    except subprocess.TimeoutExpired:
        print("[DEPENDENCY CHECK] ✗ Dependency installation timed out")
        return False
    except Exception as e:
        print(f"[DEPENDENCY CHECK] ✗ Error installing dependencies: {e}")
        return False


def check_critical_imports():
    """Check that critical packages are importable"""
    critical_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "aiofiles",
        "pydantic",
    ]

    missing = []
    for package in critical_packages:
        if not is_package_installed(package):
            missing.append(package)

    return missing


def ensure_dependencies():
    """
    Main function: Check and install dependencies if needed.
    Returns True if all dependencies are available, False otherwise.
    """
    print("[DEPENDENCY CHECK] Starting dependency verification...")

    # First check if critical packages are available
    missing = check_critical_imports()

    if missing:
        print(f"[DEPENDENCY CHECK] Missing packages: {', '.join(missing)}")

        try:
            req_file = get_requirements_file()
            success = install_dependencies(req_file)

            if not success:
                print("[DEPENDENCY CHECK] ✗ Failed to install dependencies")
                return False

            # Verify installation
            missing_after = check_critical_imports()
            if missing_after:
                print(
                    f"[DEPENDENCY CHECK] ✗ Still missing after install: {', '.join(missing_after)}"
                )
                return False

        except FileNotFoundError as e:
            print(f"[DEPENDENCY CHECK] ✗ {e}")
            return False

    print("[DEPENDENCY CHECK] ✓ All dependencies are available")
    return True


if __name__ == "__main__":
    success = ensure_dependencies()
    sys.exit(0 if success else 1)
