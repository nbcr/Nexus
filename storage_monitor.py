#!/usr/bin/env python3
"""
Storage monitoring script for Nexus
Tracks disk usage, database growth, and projects storage capacity
Runs daily via cron and can be executed on-demand
"""

import subprocess
import json
import datetime
from pathlib import Path
from typing import Dict, Any

# Configuration
# Use project root directory for file storage
PROJECT_ROOT = Path(__file__).parent
REPORT_FILE = PROJECT_ROOT / "storage_report.json"
PREVIOUS_REPORT_FILE = PROJECT_ROOT / "storage_report_previous.json"
DISPLAY_FILE = PROJECT_ROOT / "STORAGE_STATUS.txt"
HISTORY_FILE = PROJECT_ROOT / "storage_history.json"

# Database query
DB_SIZE_QUERY = """SELECT pg_size_pretty(pg_database_size('nexus')) as size;"""
DB_ITEM_COUNT = """SELECT COUNT(*) as count FROM content_items;"""


def run_command(cmd: str) -> str:
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command: {e}")
        return ""


def get_disk_usage() -> Dict[str, Any]:
    """Get disk usage statistics"""
    df_output = run_command("df -B1 / | tail -1")
    if not df_output:
        return {}

    parts = df_output.split()
    total = int(parts[1])
    used = int(parts[2])
    available = int(parts[3])

    return {
        "total_bytes": total,
        "used_bytes": used,
        "available_bytes": available,
        "percent_used": (used / total) * 100,
    }


def get_db_stats() -> Dict[str, Any]:
    """Get database statistics"""
    # Query database for size and item count
    size_bytes = 0
    item_count = 0
    size_display = ""

    try:
        # Get database size
        size_result = subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "psql",
                "-d",
                "nexus",
                "-t",
                "-c",
                "SELECT pg_size_pretty(pg_database_size(current_database()));",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        size_display = size_result.stdout.strip() if size_result.returncode == 0 else ""

        if size_display:
            try:
                value, unit = size_display.split()
                value = float(value)
                unit_map = {"B": 1, "kB": 1024, "MB": 1024**2, "GB": 1024**3}
                size_bytes = int(value * unit_map.get(unit, 1))
            except (ValueError, IndexError) as e:
                pass

        # Get item count
        count_result = subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "psql",
                "-d",
                "nexus",
                "-t",
                "-c",
                "SELECT COUNT(*) FROM content_items;",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if count_result.returncode == 0:
            item_count = int(count_result.stdout.strip() or 0)

    except Exception as e:
        print(f"Warning: Could not query database: {e}")

    return {
        "size_bytes": size_bytes,
        "item_count": item_count,
        "size_display": size_display,
    }


def calculate_projections(
    current_report: Dict, previous_report: Dict
) -> Dict[str, Any]:
    """Calculate growth rate and project future capacity"""
    if not previous_report:
        return {}

    current_time = datetime.datetime.now()
    previous_time = datetime.datetime.fromisoformat(
        previous_report.get("timestamp", "")
    )
    time_delta_days = (current_time - previous_time).total_seconds() / 86400

    if time_delta_days < 0.5:  # Skip if less than 12 hours apart
        return {}

    db_growth_bytes = (
        current_report["database"]["size_bytes"]
        - previous_report["database"]["size_bytes"]
    )

    disk_used_growth = (
        current_report["disk"]["used_bytes"] - previous_report["disk"]["used_bytes"]
    )
    disk_growth_per_day = (
        disk_used_growth / time_delta_days if time_delta_days > 0 else 0
    )

    item_growth = (
        current_report["database"]["item_count"]
        - previous_report["database"]["item_count"]
    )
    items_per_day = item_growth / time_delta_days if time_delta_days > 0 else 0

    # Calculate days until full (at current growth rate)
    available = current_report["disk"]["available_bytes"]
    disk_full_days = (
        available / disk_growth_per_day if disk_growth_per_day > 0 else float("inf")
    )

    return {
        "db_growth_bytes_per_day": db_growth_bytes / time_delta_days,
        "disk_growth_bytes_per_day": disk_growth_per_day,
        "items_added_per_day": items_per_day,
        "days_until_disk_full": disk_full_days,
        "calculation_period_days": time_delta_days,
    }


def format_bytes(bytes_val: int) -> str:
    """Convert bytes to human readable format"""
    bytes_val_float = float(bytes_val)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val_float < 1024:
            return f"{bytes_val_float:.1f}{unit}"
        bytes_val_float /= 1024
    return f"{bytes_val_float:.1f}TB"


def generate_report() -> Dict[str, Any]:
    """Generate complete storage report"""
    timestamp = datetime.datetime.now().isoformat()

    disk_stats = get_disk_usage()
    db_stats = get_db_stats()

    # Load previous report if it exists
    previous_report = {}
    if REPORT_FILE.exists():
        try:
            with open(REPORT_FILE) as f:
                previous_report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # Calculate projections
    projections = calculate_projections(
        {"database": db_stats, "disk": disk_stats, "timestamp": timestamp},
        previous_report,
    )

    report = {
        "timestamp": timestamp,
        "disk": disk_stats,
        "database": db_stats,
        "projections": projections,
    }

    return report


def save_report(report: Dict[str, Any]) -> None:
    """Save report to JSON file"""
    # Backup previous report
    if REPORT_FILE.exists():
        import shutil

        shutil.copy(REPORT_FILE, PREVIOUS_REPORT_FILE)

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    # Update history file
    update_history(report)


def update_history(report: Dict[str, Any]) -> None:
    """Track historical metrics for trend analysis"""
    history = {}
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # Add today's data
    today = datetime.datetime.now().date().isoformat()
    history[today] = {
        "timestamp": report["timestamp"],
        "disk_used_bytes": report["disk"]["used_bytes"],
        "db_size_bytes": report["database"]["size_bytes"],
        "item_count": report["database"]["item_count"],
        "disk_percent": report["disk"]["percent_used"],
    }

    # Keep only last 90 days
    dates = sorted(history.keys())
    if len(dates) > 90:
        for old_date in dates[:-90]:
            del history[old_date]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def calculate_statistics() -> Dict[str, Any]:
    """Calculate min/max/avg statistics from history"""
    stats = {
        "daily_new_stories_min": 0.0,
        "daily_new_stories_max": 0.0,
        "daily_new_stories_avg": 0.0,
        "daily_db_growth_min_bytes": 0.0,
        "daily_db_growth_max_bytes": 0.0,
        "daily_db_growth_avg_bytes": 0.0,
        "stories_per_fetch_avg": 0.0,
        "predicted_backup_size_mb": 0.0,
        "days_tracked": 0,
    }

    if not HISTORY_FILE.exists():
        return stats

    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return stats

    if len(history) < 2:
        return stats

    # Calculate daily metrics
    dates = sorted(history.keys())
    daily_new_stories = []
    daily_db_growth = []

    for i in range(1, len(dates)):
        prev_date = dates[i - 1]
        curr_date = dates[i]

        prev_items = history[prev_date]["item_count"]
        curr_items = history[curr_date]["item_count"]
        new_stories = max(0, curr_items - prev_items)
        daily_new_stories.append(new_stories)

        prev_db_size = history[prev_date]["db_size_bytes"]
        curr_db_size = history[curr_date]["db_size_bytes"]
        db_growth = max(0, curr_db_size - prev_db_size)
        daily_db_growth.append(db_growth)

    if daily_new_stories:
        stats["daily_new_stories_min"] = min(daily_new_stories)
        stats["daily_new_stories_max"] = max(daily_new_stories)
        stats["daily_new_stories_avg"] = sum(daily_new_stories) / len(daily_new_stories)

        # Stories per fetch (96 fetches per day)
        stats["stories_per_fetch_avg"] = stats["daily_new_stories_avg"] / 96

    if daily_db_growth:
        stats["daily_db_growth_min_bytes"] = min(daily_db_growth)
        stats["daily_db_growth_max_bytes"] = max(daily_db_growth)
        stats["daily_db_growth_avg_bytes"] = sum(daily_db_growth) / len(daily_db_growth)

        # Predict backup size (compressed SQL is typically 1-2% of database size)
        stats["predicted_backup_size_mb"] = (
            stats["daily_db_growth_avg_bytes"] * 0.015 / (1024 * 1024)
        )  # 1.5% compression

    stats["days_tracked"] = len(dates) - 1

    return stats


def generate_display_text(report: Dict[str, Any]) -> str:
    """Generate human-readable display text"""
    disk = report["disk"]
    db = report["database"]
    proj = report["projections"]
    stats = calculate_statistics()

    lines = [
        "=" * 70,
        "NEXUS STORAGE STATUS",
        "=" * 70,
        f"Generated: {report['timestamp']}",
        "",
        "DISK USAGE:",
        f"  Total:      {format_bytes(disk['total_bytes'])}",
        f"  Used:       {format_bytes(disk['used_bytes'])} ({disk['percent_used']:.1f}%)",
        f"  Available:  {format_bytes(disk['available_bytes'])}",
        "",
        "DATABASE:",
        f"  Size:       {db['size_display']}",
        f"  Items:      {db['item_count']:,} stories",
        "",
    ]

    # Add statistics if we have history
    if stats["days_tracked"] > 0:
        lines.extend(
            [
                f"DAILY STATISTICS (tracked {stats['days_tracked']} days):",
                "  New Stories Added:",
                f"    Min:  {stats['daily_new_stories_min']:,.0f}/day",
                f"    Avg:  {stats['daily_new_stories_avg']:,.0f}/day",
                f"    Max:  {stats['daily_new_stories_max']:,.0f}/day",
                "  Database Growth:",
                f"    Min:  {format_bytes(stats['daily_db_growth_min_bytes'])}/day",
                f"    Avg:  {format_bytes(stats['daily_db_growth_avg_bytes'])}/day",
                f"    Max:  {format_bytes(stats['daily_db_growth_max_bytes'])}/day",
                f"  Stories per Fetch: {stats['stories_per_fetch_avg']:.1f}",
                f"  Predicted Daily Backup Size: {stats['predicted_backup_size_mb']:.2f}MB",
                "",
            ]
        )

    if proj:
        lines.extend(
            [
                "GROWTH METRICS (last {:.1f} days):".format(
                    proj.get("calculation_period_days", 0)
                ),
                f"  DB Growth:        {format_bytes(proj['db_growth_bytes_per_day'])}/day",
                f"  Disk Growth:      {format_bytes(proj['disk_growth_bytes_per_day'])}/day",
                f"  Items Added:      {proj['items_added_per_day']:.0f}/day",
                "",
                "CAPACITY PROJECTIONS:",
                f"  Days Until Full:  {proj['days_until_disk_full']:.1f} days",
                f"  Full Date:        {(datetime.datetime.now() + datetime.timedelta(days=proj['days_until_disk_full'])).strftime('%Y-%m-%d')}",
                "",
            ]
        )

        if proj["days_until_disk_full"] < 14:
            lines.append("⚠️  WARNING: Less than 2 weeks of disk space remaining!")
        elif proj["days_until_disk_full"] < 30:
            lines.append("⚠️  CAUTION: Less than 30 days of disk space")
        else:
            lines.append("✅ Disk space adequate")

    lines.extend(
        [
            "",
            "FREE TIER LIMITS:",
            f"  EBS Storage:  30GB/month (using {format_bytes(disk['total_bytes'])})",
            "  EC2 Hours:    750 hours/month",
            "",
            "=" * 70,
        ]
    )

    return "\n".join(lines)


def main():
    """Main execution"""
    print("🔍 Collecting storage metrics...")

    report = generate_report()
    save_report(report)

    display_text = generate_display_text(report)
    with open(DISPLAY_FILE, "w") as f:
        f.write(display_text)

    print(display_text)
    print("\n✅ Reports saved:")
    print(f"   JSON: {REPORT_FILE}")
    print(f"   Text: {DISPLAY_FILE}")


if __name__ == "__main__":
    main()
