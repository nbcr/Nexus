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
from pathlib import Path
from datetime import datetime


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


def check_for_changes(static_dir: str, hashes_file: str) -> dict:
    """Check which files have changed since last run."""
    old_hashes = load_file_hashes(hashes_file)
    new_hashes = {}
    changed_files = {}

    # Scan static directory
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, static_dir)

            # Get current hash
            current_hash = get_file_hash(filepath)
            new_hashes[relpath] = current_hash

            # Check if changed
            if relpath not in old_hashes or old_hashes[relpath] != current_hash:
                changed_files[relpath] = current_hash

    # Save new hashes
    save_file_hashes(hashes_file, new_hashes)

    return changed_files


def extract_filename_from_path(relpath: str) -> str:
    """Extract just the filename from relative path."""
    return os.path.basename(relpath)


def update_template_versions(
    templates_dir: str, changed_files: dict, new_version: str
) -> None:
    """Update version strings in template files."""
    if not changed_files:
        print("✓ No file changes detected, skipping template updates")
        return

    print(f"📝 Detected {len(changed_files)} changed file(s)")
    print(f"🔄 Updating version to: {new_version}")

    # Group changed files by type
    css_files = {f for f in changed_files if f.endswith(".css")}
    js_files = {f for f in changed_files if f.endswith(".js")}

    # Read all templates
    template_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                template_files.append(os.path.join(root, file))

    updated_count = 0

    # Update each template
    for template_path in template_files:
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Update version strings for changed files
            for changed_file in changed_files:
                filename = extract_filename_from_path(changed_file)

                # Normalize path separators to forward slashes for regex
                normalized_path = changed_file.replace("\\", "/")

                # Create regex patterns to match different URL formats
                patterns = [
                    # Standard pattern: /static/path/to/file.ext?v=XXXXXXXX
                    (
                        rf"(/{re.escape(normalized_path)}\?v=)\d{{12}}",
                        rf"\1{new_version}",
                    ),
                    # Alternative with quotes: "/static/path/file.ext?v=XXXXXXXX"
                    (
                        rf'("{re.escape(normalized_path)}\?v=)\d{{12}}"',
                        rf'\1{new_version}"',
                    ),
                    # Apostrophes: '/static/path/file.ext?v=XXXXXXXX'
                    (
                        rf"('{re.escape(normalized_path)}\?v=)\d{{12}}'",
                        rf"\1{new_version}'",
                    ),
                ]

                for pattern, replacement in patterns:
                    try:
                        content = re.sub(pattern, replacement, content)
                    except Exception:
                        pass

            # Also do wildcard updates for any files matching just the filename
            # This catches cases where multiple files with same name might exist
            for changed_file in changed_files:
                filename = extract_filename_from_path(changed_file)
                # Match any occurrence of filename?v=OLDVERSION
                pattern = rf"({re.escape(filename)}\?v=)\d{{12}}"
                replacement = rf"\1{new_version}"
                content = re.sub(pattern, replacement, content)

            # Write back if changed
            if content != original_content:
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  ✓ Updated {os.path.basename(template_path)}")
                updated_count += 1

        except Exception as e:
            print(f"  ✗ Error updating {template_path}: {e}")

    if updated_count > 0:
        print(f"✅ Updated {updated_count} template file(s)")
    else:
        print("ℹ️ No templates needed updating")


def main():
    """Main entry point."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    static_dir = os.path.join(project_root, "app", "static")
    templates_dir = os.path.join(project_root, "app", "templates")
    hashes_file = os.path.join(script_dir, ".cache_bust_hashes.json")

    print("🔍 Cache Busting Update Check")
    print(f"📂 Static directory: {static_dir}")
    print(f"📂 Templates directory: {templates_dir}")
    print()

    # Check for changes
    changed_files = check_for_changes(static_dir, hashes_file)

    # Update templates if needed
    if changed_files:
        new_version = get_version_string()
        update_template_versions(templates_dir, changed_files, new_version)
        print("\n✨ Cache busting update complete!")
    else:
        print("✓ No changes detected")


if __name__ == "__main__":
    main()
