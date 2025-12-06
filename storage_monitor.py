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
REPORT_FILE = Path("/home/nexus/nexus/storage_report.json")
PREVIOUS_REPORT_FILE = Path("/home/nexus/nexus/storage_report_previous.json")
DISPLAY_FILE = Path("/home/nexus/nexus/STORAGE_STATUS.txt")

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
    size_output = run_command(
        'sudo -u postgres psql -d nexus -t -c \'SELECT pg_size_pretty(pg_database_size("""nexus"""))\''
    )
    count_output = run_command(
        "sudo -u postgres psql -d nexus -t -c 'SELECT COUNT(*) FROM content_items'"
    )

    # Parse size (e.g., "65 MB" -> bytes)
    size_bytes = 0
    if size_output:
        try:
            value, unit = size_output.strip().split()
            value = float(value)
            unit_map = {"B": 1, "kB": 1024, "MB": 1024**2, "GB": 1024**3}
            size_bytes = int(value * unit_map.get(unit, 1))
        except:
            pass

    item_count = 0
    if count_output:
        try:
            item_count = int(count_output.strip())
        except:
            pass

    return {
        "size_bytes": size_bytes,
        "item_count": item_count,
        "size_display": size_output,
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
    db_growth_per_day = db_growth_bytes / time_delta_days if time_delta_days > 0 else 0

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
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TB"


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
        except:
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


def generate_display_text(report: Dict[str, Any]) -> str:
    """Generate human-readable display text"""
    disk = report["disk"]
    db = report["database"]
    proj = report["projections"]

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
            f"  EC2 Hours:    750 hours/month",
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
    print(f"\n✅ Reports saved:")
    print(f"   JSON: {REPORT_FILE}")
    print(f"   Text: {DISPLAY_FILE}")


if __name__ == "__main__":
    main()
