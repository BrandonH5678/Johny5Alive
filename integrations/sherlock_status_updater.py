#!/usr/bin/env python3
"""
Sherlock Package Status Updater

Updates package status in Sherlock database after task execution.

This module provides the feedback loop from J5A queue execution back to
Sherlock's targeting packages table, enabling proper package lifecycle management.

Package Lifecycle:
    draft → ready → queued → running → completed → validated → closed

Status can also go to: failed, blocked
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


def update_package_status(
    package_id: int,
    new_status: str,
    metadata: Optional[Dict] = None,
    sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db"
) -> bool:
    """
    Update package status in Sherlock database.

    Args:
        package_id: Package ID to update
        new_status: New status (queued, running, completed, validated, failed, etc.)
        metadata: Additional metadata to merge into package metadata
        sherlock_db: Path to Sherlock database

    Returns:
        True if update successful, False otherwise
    """
    try:
        conn = sqlite3.connect(sherlock_db)
        cursor = conn.cursor()

        # Get current package metadata
        cursor.execute('''
            SELECT metadata FROM targeting_packages WHERE package_id = ?
        ''', (package_id,))

        row = cursor.fetchone()
        if not row:
            print(f"⚠️  Package {package_id} not found in database")
            conn.close()
            return False

        # Merge metadata
        current_metadata = json.loads(row[0]) if row[0] else {}

        if metadata:
            current_metadata.update(metadata)

        # Add status update timestamp
        if 'status_history' not in current_metadata:
            current_metadata['status_history'] = []

        current_metadata['status_history'].append({
            'status': new_status,
            'timestamp': datetime.now().isoformat(),
            'updated_by': 'j5a_queue_system'
        })

        # Update package
        cursor.execute('''
            UPDATE targeting_packages
            SET status = ?,
                updated_at = ?,
                metadata = ?
            WHERE package_id = ?
        ''', (
            new_status,
            datetime.now().isoformat(),
            json.dumps(current_metadata),
            package_id
        ))

        conn.commit()
        conn.close()

        print(f"✅ Package {package_id} status updated: {new_status}")
        return True

    except Exception as e:
        print(f"❌ Failed to update package {package_id} status: {e}")
        return False


def get_package_status(
    package_id: int,
    sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db"
) -> Optional[Dict]:
    """
    Get current package status and metadata.

    Args:
        package_id: Package ID to query
        sherlock_db: Path to Sherlock database

    Returns:
        Dictionary with package info or None if not found
    """
    try:
        conn = sqlite3.connect(sherlock_db)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT package_id, target_id, version, package_type, status,
                   validation_level, created_at, updated_at, metadata
            FROM targeting_packages
            WHERE package_id = ?
        ''', (package_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'package_id': row[0],
            'target_id': row[1],
            'version': row[2],
            'package_type': row[3],
            'status': row[4],
            'validation_level': row[5],
            'created_at': row[6],
            'updated_at': row[7],
            'metadata': json.loads(row[8]) if row[8] else {}
        }

    except Exception as e:
        print(f"❌ Failed to get package {package_id} status: {e}")
        return None


def mark_package_completed(
    package_id: int,
    outputs_generated: list,
    claims_extracted: int = 0,
    entities_found: int = 0,
    sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db"
) -> bool:
    """
    Mark package as completed with execution results.

    Args:
        package_id: Package ID
        outputs_generated: List of output file paths
        claims_extracted: Number of claims extracted
        entities_found: Number of entities found
        sherlock_db: Path to Sherlock database

    Returns:
        True if successful
    """
    metadata = {
        'execution_completed_at': datetime.now().isoformat(),
        'outputs_generated': outputs_generated,
        'claims_extracted': claims_extracted,
        'entities_found': entities_found,
        'ready_for_validation': True
    }

    return update_package_status(
        package_id=package_id,
        new_status='completed',
        metadata=metadata,
        sherlock_db=sherlock_db
    )


def mark_package_validated(
    package_id: int,
    validation_level: str,
    validation_results: Dict,
    sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db"
) -> bool:
    """
    Mark package as validated at specific level (V1 or V2).

    Args:
        package_id: Package ID
        validation_level: Validation level (v1, v2)
        validation_results: Validation results dictionary
        sherlock_db: Path to Sherlock database

    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(sherlock_db)
        cursor = conn.cursor()

        # Get current metadata
        cursor.execute('''
            SELECT metadata FROM targeting_packages WHERE package_id = ?
        ''', (package_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        metadata = json.loads(row[0]) if row[0] else {}

        # Add validation results
        metadata[f'{validation_level}_validation'] = {
            **validation_results,
            'validated_at': datetime.now().isoformat()
        }

        # Update package
        cursor.execute('''
            UPDATE targeting_packages
            SET validation_level = ?,
                updated_at = ?,
                metadata = ?
            WHERE package_id = ?
        ''', (
            validation_level,
            datetime.now().isoformat(),
            json.dumps(metadata),
            package_id
        ))

        # If V2 validation passed, mark as validated status
        if validation_level == 'v2' and validation_results.get('passed', False):
            cursor.execute('''
                UPDATE targeting_packages
                SET status = ?
                WHERE package_id = ?
            ''', ('validated', package_id))

        conn.commit()
        conn.close()

        print(f"✅ Package {package_id} validated at level {validation_level}")
        return True

    except Exception as e:
        print(f"❌ Failed to mark package {package_id} as validated: {e}")
        return False


def main():
    """CLI interface for package status updates"""
    import argparse

    parser = argparse.ArgumentParser(description="Update Sherlock package status")
    parser.add_argument("--package-id", type=int, required=True, help="Package ID")
    parser.add_argument("--status", help="New status")
    parser.add_argument("--show", action="store_true", help="Show current status")
    parser.add_argument("--db", default="/home/johnny5/Sherlock/sherlock.db", help="Database path")

    args = parser.parse_args()

    if args.show:
        pkg = get_package_status(args.package_id, args.db)
        if pkg:
            print(f"\nPackage {args.package_id}:")
            print(f"  Status: {pkg['status']}")
            print(f"  Type: {pkg['package_type']}")
            print(f"  Validation: {pkg['validation_level']}")
            print(f"  Updated: {pkg['updated_at']}")

            if 'status_history' in pkg['metadata']:
                print(f"\n  Status History:")
                for entry in pkg['metadata']['status_history'][-5:]:
                    print(f"    {entry['timestamp']}: {entry['status']}")
        else:
            print(f"Package {args.package_id} not found")

    elif args.status:
        update_package_status(args.package_id, args.status, sherlock_db=args.db)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
