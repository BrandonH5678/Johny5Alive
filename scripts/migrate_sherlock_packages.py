#!/usr/bin/env python3
"""
Migrate Sherlock Packages to Dual-Queue System

This script migrates existing packages from the old queue format
(individual JSON files) to the new dual-queue system (JSONL format).

Usage:
    python3 migrate_sherlock_packages.py --dry-run  # Preview changes
    python3 migrate_sherlock_packages.py --execute  # Perform migration
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.append('/home/johnny5/Sherlock/src')
from sherlock_targeting_officer import TargetingOfficer, PackageType, PackageStatus, Package

def migrate_packages(dry_run=True):
    """Migrate packages from old queue to new dual-queue system"""

    sherlock_db = "/home/johnny5/Sherlock/sherlock.db"
    j5a_root = Path("/home/johnny5/Johny5Alive")
    old_queue_dir = j5a_root / "queue"

    print("="*70)
    print("SHERLOCK PACKAGE MIGRATION TO DUAL-QUEUE SYSTEM")
    print("="*70)
    print()

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()

    # Connect to Sherlock database
    conn = sqlite3.connect(sherlock_db)
    cursor = conn.cursor()

    # Find all packages in "submitted" status
    cursor.execute('''
        SELECT p.package_id, p.target_id, p.version, p.package_type,
               p.collection_urls, p.expected_outputs, p.metadata,
               t.name, t.priority
        FROM targeting_packages p
        JOIN targets t ON p.target_id = t.target_id
        WHERE p.status = 'submitted'
        ORDER BY p.package_id
    ''')

    packages = cursor.fetchall()

    print(f"Found {len(packages)} packages in 'submitted' status\n")

    stats = {
        'total': len(packages),
        'youtube': 0,
        'document': 0,
        'composite': 0,
        'queued_nightshift': 0,
        'queued_claude': 0
    }

    # Process each package
    for row in packages:
        package_id = row[0]
        target_id = row[1]
        version = row[2]
        package_type = row[3]
        collection_urls = json.loads(row[4])
        expected_outputs = json.loads(row[5])
        metadata = json.loads(row[6]) if row[6] else {}
        target_name = row[7]
        priority = row[8]

        print(f"Package {package_id}: {target_name}")
        print(f"  Type: {package_type}")
        print(f"  Priority: {priority}")
        print(f"  URLs: {len(collection_urls)}")

        stats[package_type] += 1

        # Determine queue routing
        today = datetime.now().strftime("%Y-%m-%d")

        if package_type in ['youtube', 'document']:
            # Route to NightShift
            queue_file = j5a_root / "queue" / "nightshift" / "inbox.jsonl"
            queue_type = "NightShift"

            task = {
                'id': f"sherlock_pkg_{package_id}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                'task': 'sherlock_content_collection',
                'args': {
                    'package_id': package_id,
                    'target_name': target_name,
                    'package_type': package_type,
                    'collection_urls': collection_urls,
                    'expected_outputs': expected_outputs,
                    'priority': priority
                },
                'priority': 'high' if priority == 1 else 'normal'
            }

            stats['queued_nightshift'] += 1

        else:  # composite
            # Route to Claude
            queue_file = j5a_root / "queue" / "claude" / f"{today}.jsonl"
            queue_type = "Claude"

            task = {
                'id': f"sherlock_pkg_{package_id}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                'type': 'analysis',
                'priority': 'high' if priority == 1 else 'normal',
                'inputs': [],
                'deliverables': expected_outputs,
                'constraints': {
                    'max_tokens': 60000,
                    'style': 'research',
                    'citations': True
                },
                'notes': f"Research package for {target_name}. Package ID: {package_id}. Collection URLs: {len(collection_urls)} sources."
            }

            stats['queued_claude'] += 1

        print(f"  → Routing to: {queue_type} queue")

        if not dry_run:
            # Create queue directory if needed
            queue_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to queue (JSONL format)
            with open(queue_file, 'a') as f:
                f.write(json.dumps(task) + '\n')

            # Update package status from 'submitted' to 'queued'
            cursor.execute('''
                UPDATE targeting_packages
                SET status = ?, updated_at = ?
                WHERE package_id = ?
            ''', ('queued', datetime.now().isoformat(), package_id))

            print(f"  ✅ Queued to {queue_file.name}")

            # Archive old queue file if exists
            old_queue_file = old_queue_dir / f"sherlock_pkg_{package_id}.json"
            if old_queue_file.exists():
                archive_dir = old_queue_dir / "archive_old_format"
                archive_dir.mkdir(exist_ok=True)
                old_queue_file.rename(archive_dir / old_queue_file.name)
                print(f"  📦 Archived old queue file")
        else:
            print(f"  [Dry run] Would queue to: {queue_file}")

        print()

    if not dry_run:
        conn.commit()

    conn.close()

    # Summary
    print("="*70)
    print("MIGRATION SUMMARY")
    print("="*70)
    print(f"Total packages processed: {stats['total']}")
    print(f"\nBy Type:")
    print(f"  YouTube packages: {stats['youtube']}")
    print(f"  Document packages: {stats['document']}")
    print(f"  Composite packages: {stats['composite']}")
    print(f"\nRouting:")
    print(f"  Queued to NightShift: {stats['queued_nightshift']}")
    print(f"  Queued to Claude: {stats['queued_claude']}")

    if dry_run:
        print(f"\n⚠️  This was a DRY RUN - no changes were made")
        print(f"   Run with --execute to perform migration")
    else:
        print(f"\n✅ Migration complete!")
        print(f"\nNext steps:")
        print(f"  1. Process NightShift queue: bash scripts/nightshift_dispatcher.sh")
        print(f"  2. Process Claude queue: python3 scripts/claude_queue_processor.py")

    print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Sherlock packages to dual-queue system")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Execute migration")

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Please specify --dry-run or --execute")
        parser.print_help()
        sys.exit(1)

    migrate_packages(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
