#!/usr/bin/env python3
"""
J5A Queue Display - Show Tonight's Scheduled Queue

Usage:
    python3 show_queue.py [--full]
"""

import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


def show_queue_summary():
    """Display summary of queued tasks"""
    db_path = "j5a_queue_manager.db"

    # Check if database exists
    if not Path(db_path).exists():
        print("No J5A queue database found.")
        print("\nChecking for Sherlock packages in queue directory...")
        show_sherlock_queue()
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get queued tasks
    cursor.execute('''
        SELECT td.task_id, td.name, td.priority, td.target_system,
               td.estimated_duration_minutes, te.status
        FROM task_definitions td
        JOIN task_executions te ON td.task_id = te.task_id
        WHERE te.status IN ('queued', 'deferred')
        ORDER BY td.priority ASC, td.created_timestamp ASC
    ''')

    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        print("No tasks in J5A queue database.")
        print("\nChecking for Sherlock packages in queue directory...")
        show_sherlock_queue()
        return

    print("=" * 80)
    print("J5A OVERNIGHT QUEUE - Tonight's Schedule")
    print("=" * 80)
    print()

    # Group by status
    queued = [t for t in tasks if t[5] == 'queued']
    deferred = [t for t in tasks if t[5] == 'deferred']

    if queued:
        print(f"📋 QUEUED FOR EXECUTION ({len(queued)} tasks):")
        print("-" * 80)
        total_duration = 0
        for task_id, name, priority, system, duration, status in queued:
            priority_labels = {1: "CRITICAL", 2: "HIGH", 3: "NORMAL", 4: "LOW", 5: "BATCH"}
            priority_label = priority_labels.get(priority, "UNKNOWN")
            print(f"  [{task_id}] {name[:60]}")
            print(f"      Priority: {priority} ({priority_label}) | System: {system} | Duration: {duration} min")
            total_duration += duration
        print()
        print(f"  Estimated total execution time: {total_duration} minutes ({total_duration/60:.1f} hours)")
        print()

    if deferred:
        print(f"⏸️  DEFERRED ({len(deferred)} tasks):")
        print("-" * 80)
        for task_id, name, priority, system, duration, status in deferred:
            print(f"  [{task_id}] {name[:60]}")
            print(f"      System: {system} | Duration: {duration} min")
        print()

    print("=" * 80)


def show_sherlock_queue():
    """Display Sherlock packages waiting in queue directory"""
    queue_dir = Path("queue")

    if not queue_dir.exists():
        print("No queue directory found.")
        return

    packages = sorted(queue_dir.glob("sherlock_pkg_*.json"))

    if not packages:
        print("No Sherlock packages in queue directory.")
        return

    print("=" * 80)
    print("SHERLOCK RESEARCH PACKAGES - Waiting for J5A Import")
    print("=" * 80)
    print()

    # Analyze packages
    blocked_by_ram = []
    allowed = []

    blocked_types = ["podcast", "interview_series", "youtube", "multi_speaker_audio"]

    for pkg_file in packages:
        with open(pkg_file) as f:
            pkg = json.load(f)
            package_type = pkg.get('package_type', '').lower()

            pkg_info = {
                'id': pkg['package_id'],
                'name': pkg['target_name'],
                'type': package_type,
                'priority': pkg['priority'],
                'urls': len(pkg['collection_urls']),
                'url_list': pkg['collection_urls']
            }

            if package_type in blocked_types:
                blocked_by_ram.append(pkg_info)
            else:
                allowed.append(pkg_info)

    # Display allowed packages (will execute tonight)
    if allowed:
        print(f"✅ READY TO EXECUTE ({len(allowed)} packages):")
        print("-" * 80)

        # Sort by priority
        allowed.sort(key=lambda x: x['priority'])

        for pkg in allowed[:15]:  # Show first 15
            print(f"  [{pkg['id']:3d}] {pkg['name'][:55]}")
            print(f"       Type: {pkg['type']:12s} | Priority: {pkg['priority']}")
            print(f"       URLs ({pkg['urls']}):")
            for url in pkg.get('url_list', []):
                print(f"         - {url}")

        if len(allowed) > 15:
            print(f"  ... and {len(allowed) - 15} more packages")
        print()

    # Display blocked packages
    if blocked_by_ram:
        print(f"🚫 BLOCKED BY RAM CONSTRAINT ({len(blocked_by_ram)} packages):")
        print("-" * 80)
        print("   (Multi-speaker audio - requires RAM upgrade)")
        print()

        for pkg in blocked_by_ram:
            print(f"  [{pkg['id']:3d}] {pkg['name'][:55]}")
            print(f"       Type: {pkg['type']:12s} | Priority: {pkg['priority']}")
            print(f"       URLs ({pkg['urls']}):")
            for url in pkg.get('url_list', []):
                print(f"         - {url}")
        print()

    # Summary
    print("=" * 80)
    print(f"Summary: {len(allowed)} packages ready | {len(blocked_by_ram)} blocked by RAM constraint")
    print("=" * 80)
    print()

    # Priority breakdown
    p1_allowed = [p for p in allowed if p['priority'] == 1]
    p1_blocked = [p for p in blocked_by_ram if p['priority'] == 1]

    if p1_allowed:
        print(f"🎯 Priority 1 (Critical) ready to execute: {len(p1_allowed)}")
    if p1_blocked:
        print(f"⚠️  Priority 1 (Critical) blocked by RAM: {len(p1_blocked)}")


def show_full_queue():
    """Display detailed queue information"""
    queue_dir = Path("queue")

    if not queue_dir.exists():
        print("No queue directory found.")
        return

    packages = sorted(queue_dir.glob("sherlock_pkg_*.json"))

    print("=" * 80)
    print("FULL QUEUE DETAILS")
    print("=" * 80)
    print()

    for pkg_file in packages:
        with open(pkg_file) as f:
            pkg = json.load(f)

            print(f"Package ID: {pkg['package_id']}")
            print(f"Target: {pkg['target_name']}")
            print(f"Type: {pkg['package_type']}")
            print(f"Priority: {pkg['priority']}")
            print(f"Created: {pkg['created_at']}")
            print(f"\nCollection URLs ({len(pkg['collection_urls'])}):")
            for url in pkg['collection_urls']:
                print(f"  - {url}")
            print(f"\nExpected Outputs ({len(pkg['expected_outputs'])}):")
            for output in pkg['expected_outputs']:
                print(f"  - {output}")
            print()
            print("-" * 80)
            print()


def main():
    parser = argparse.ArgumentParser(description="Display J5A queue for tonight")
    parser.add_argument('--full', action='store_true', help='Show full details of all packages')

    args = parser.parse_args()

    print()
    print(f"🌙 J5A Queue Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if args.full:
        show_full_queue()
    else:
        show_queue_summary()


if __name__ == "__main__":
    main()
