#!/usr/bin/env python3
"""
Automatic cache busting updater.
Detects changes in static files and updates version strings in templates.
Run this before deployment to ensure browsers get fresh assets.
"""

import os
import re
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime


# Configure logging
def _create_file_handler(log_file: str) -> logging.FileHandler:
    """Create file handler for logging."""
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    return file_handler

def _create_console_handler() -> logging.StreamHandler:
    """Create console handler for logging."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    return console_handler

def setup_logging():
    """Set up logging to both file and console."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "cache_bust.log")

    logger = logging.getLogger("cache_bust")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    logger.addHandler(_create_file_handler(log_file))
    logger.addHandler(_create_console_handler())

    return logger


logger = setup_logging()


def get_file_hash(filepath: str) -> str:
    """Generate MD5 hash of file content."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except Exception:
        return ""


def get_version_string() -> str:
    """Generate version string from current date/time."""
    return datetime.now().strftime("%Y%m%d%H%M")


def load_file_hashes(hashes_file: str) -> dict:
    """Load previously stored file hashes."""
    if os.path.exists(hashes_file):
        try:
            with open(hashes_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_file_hashes(hashes_file: str, hashes: dict) -> None:
    """Save current file hashes."""
    with open(hashes_file, "w") as f:
        json.dump(hashes, f, indent=2)


def _scan_static_files(static_dir: str) -> dict:
    """Scan static directory and return file hashes."""
    new_hashes = {}
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, static_dir)
            current_hash = get_file_hash(filepath)
            new_hashes[relpath] = current_hash
    return new_hashes

def _find_changed_files(old_hashes: dict, new_hashes: dict) -> dict:
    """Find files that have changed."""
    changed_files = {}
    for relpath, current_hash in new_hashes.items():
        if relpath not in old_hashes or old_hashes[relpath] != current_hash:
            changed_files[relpath] = current_hash
            logger.info(f"  Changed: {relpath}")
    return changed_files

def check_for_changes(static_dir: str, hashes_file: str) -> dict:
    """Check which files have changed since last run."""
    logger.info("Checking for file changes...")
    old_hashes = load_file_hashes(hashes_file)
    new_hashes = _scan_static_files(static_dir)
    changed_files = _find_changed_files(old_hashes, new_hashes)
    
    save_file_hashes(hashes_file, new_hashes)
    return changed_files


def extract_filename_from_path(relpath: str) -> str:
    """Extract just the filename from relative path."""
    return os.path.basename(relpath)


def _get_template_files(templates_dir: str) -> list:
    """Get all HTML template files."""
    template_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                template_files.append(os.path.join(root, file))
    return template_files

def _create_version_patterns(changed_file: str, new_version: str) -> list:
    """Create regex patterns for version replacement."""
    normalized_path = changed_file.replace("\\", "/")
    full_static_path = f"static/{normalized_path}"
    
    return [
        (rf"(/{re.escape(full_static_path)}\?v=)\d{{12}}", rf"\1{new_version}"),
        (rf'("{re.escape(full_static_path)}\?v=)\d{{12}}"', rf'\1{new_version}"'),
        (rf"('{re.escape(full_static_path)}\?v=)\d{{12}}'", rf"\1{new_version}'"),
    ]

def _apply_version_patterns(content: str, patterns: list) -> str:
    """Apply version patterns to content."""
    for pattern, replacement in patterns:
        try:
            content = re.sub(pattern, replacement, content)
        except Exception:
            pass
    return content

def _update_wildcard_versions(content: str, changed_files: dict, new_version: str) -> str:
    """Update wildcard version patterns."""
    for changed_file in changed_files:
        filename = extract_filename_from_path(changed_file)
        pattern = rf"({re.escape(filename)}\?v=)\d{{12}}"
        replacement = rf"\1{new_version}"
        content = re.sub(pattern, replacement, content)
    return content

def _update_single_template(template_path: str, changed_files: dict, new_version: str) -> bool:
    """Update a single template file."""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # Update version strings for changed files
        for changed_file in changed_files:
            patterns = _create_version_patterns(changed_file, new_version)
            content = _apply_version_patterns(content, patterns)
        
        # Apply wildcard updates
        content = _update_wildcard_versions(content, changed_files, new_version)
        
        # Write back if changed
        if content != original_content:
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"  ✓ Updated {os.path.basename(template_path)}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"  ✗ Error updating {template_path}: {e}")
        return False

def update_template_versions(
    templates_dir: str, changed_files: dict, new_version: str
) -> None:
    """Update version strings in template files."""
    if not changed_files:
        logger.info("✓ No file changes detected, skipping template updates")
        return

    logger.info(f"📝 Detected {len(changed_files)} changed file(s)")
    logger.info(f"🔄 Updating version to: {new_version}")

    template_files = _get_template_files(templates_dir)
    updated_count = 0

    # Update each template
    for template_path in template_files:
        if _update_single_template(template_path, changed_files, new_version):
            updated_count += 1

    if updated_count > 0:
        logger.info(f"✅ Updated {updated_count} template file(s)")
    else:
        logger.info("ℹ️ No templates needed updating")


def main():
    """Main entry point."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    static_dir = os.path.join(project_root, "app", "static")
    templates_dir = os.path.join(project_root, "app", "templates")
    hashes_file = os.path.join(script_dir, ".cache_bust_hashes.json")

    logger.info("🔍 Cache Busting Update Check")
    logger.info(f"📂 Static directory: {static_dir}")
    logger.info(f"📂 Templates directory: {templates_dir}")
    logger.info("")

    # Check for changes
    changed_files = check_for_changes(static_dir, hashes_file)

    # Update templates if needed
    if changed_files:
        new_version = get_version_string()
        update_template_versions(templates_dir, changed_files, new_version)
        logger.info("\n✨ Cache busting update complete!")
    else:
        logger.info("✓ No changes detected")


if __name__ == "__main__":
    main()
