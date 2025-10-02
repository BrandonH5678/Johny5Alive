#!/usr/bin/env python3
"""
J5A Sherlock Integration Module

Integrates Sherlock Targeting Officer with J5A overnight queue.

AUTOMATION:
- Runs Targeting Officer nightly at 1am via cron
- Imports generated packages into J5A queue
- Applies J5A decision logic for execution scheduling
- Manages Sherlock research package lifecycle

Usage:
    # Manual invocation
    python3 j5a_sherlock_integration.py --run-targeting-officer

    # Add to crontab for 1am daily execution:
    0 1 * * * cd /home/johnny5/Johny5Alive && python3 src/j5a_sherlock_integration.py --run-targeting-officer --auto
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

# Add Sherlock to path
sys.path.append('/home/johnny5/Sherlock')
sys.path.append('/home/johnny5/Sherlock/src')

from sherlock_targeting_officer import TargetingOfficer, SweepReport
from overnight_queue_manager import (
    J5AOvernightQueueManager,
    TaskDefinition,
    TaskType,
    TaskPriority,
    SystemTarget,
    ValidationCheckpoint
)


class SherlockPackagePriority(Enum):
    """J5A priority mapping for Sherlock packages"""
    PRIORITY_1_CRITICAL = TaskPriority.HIGH      # Priority 1 targets
    PRIORITY_2_HIGH = TaskPriority.NORMAL        # Priority 2 targets
    PRIORITY_3_MEDIUM = TaskPriority.LOW         # Priority 3 targets
    PRIORITY_4_LOW = TaskPriority.BATCH          # Priority 4+ targets


class J5ASherlockIntegration:
    """
    Integration layer between Targeting Officer and J5A Queue Manager.

    DETERMINISTIC DECISION RULES:
    1. Target Priority 1 → J5A HIGH priority
    2. Target Priority 2 → J5A NORMAL priority
    3. Target Priority 3+ → J5A LOW/BATCH priority
    4. YouTube packages → Execute only during off-hours (thermal intensive)
    5. Document packages → Can execute anytime (low thermal)
    6. Composite packages → Requires resource availability check
    """

    def __init__(
        self,
        sherlock_db: str = "/home/johnny5/Sherlock/sherlock.db",
        j5a_db: str = "/home/johnny5/Johny5Alive/j5a_queue_manager.db"
    ):
        self.targeting_officer = TargetingOfficer(db_path=sherlock_db)
        self.queue_manager = J5AOvernightQueueManager(db_path=j5a_db)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/johnny5/Johny5Alive/j5a_sherlock_integration.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def map_sherlock_priority_to_j5a(self, sherlock_priority: int) -> TaskPriority:
        """
        Map Sherlock target priority to J5A task priority.

        Deterministic mapping:
        - Priority 1 (Critical) → HIGH
        - Priority 2 (High) → NORMAL
        - Priority 3 (Medium) → LOW
        - Priority 4+ (Low/Background) → BATCH
        """
        if sherlock_priority == 1:
            return TaskPriority.HIGH
        elif sherlock_priority == 2:
            return TaskPriority.NORMAL
        elif sherlock_priority == 3:
            return TaskPriority.LOW
        else:
            return TaskPriority.BATCH

    def estimate_package_duration(self, package_type: str, urls_count: int) -> int:
        """
        Estimate execution duration for package.

        Heuristics:
        - YouTube: 30 min per URL (download + transcription + diarization)
        - Document: 10 min per URL (download + OCR/parsing)
        - Composite: 20 min per URL (multi-source aggregation)
        """
        duration_per_url = {
            'youtube': 30,
            'document': 10,
            'composite': 20
        }

        base_duration = duration_per_url.get(package_type, 15)
        return base_duration * urls_count

    def requires_thermal_safety(self, package_type: str) -> bool:
        """
        Determine if package requires thermal safety monitoring.

        Rules:
        - YouTube: YES (ffmpeg video processing, Whisper transcription)
        - Document: NO (lightweight text processing)
        - Composite: MAYBE (depends on complexity)
        """
        if package_type == 'youtube':
            return True
        elif package_type == 'document':
            return False
        else:  # composite
            return True  # Conservative: assume thermal required

    def create_j5a_task_from_package(self, package: Dict) -> TaskDefinition:
        """
        Convert Sherlock package to J5A task definition.

        Applies deterministic conversion rules.
        """
        # Map priority
        package_priority = package['metadata'].get('priority', 3)
        j5a_priority = self.map_sherlock_priority_to_j5a(package_priority)

        # Estimate duration
        urls_count = len(package['collection_urls'])
        duration = self.estimate_package_duration(package['package_type'], urls_count)

        # Determine thermal safety requirement
        thermal_required = self.requires_thermal_safety(package['package_type'])

        # Create validation checkpoints
        checkpoints = [
            ValidationCheckpoint(
                checkpoint_id="sherlock_pre_execution_format",
                name="Sherlock Format Validation",
                description="Validate package format and collection URLs",
                validation_function="validate_sherlock_package_format",
                blocking=True,
                quality_threshold=0.9,
                sample_size=1  # Single package validation
            ),
            ValidationCheckpoint(
                checkpoint_id="sherlock_output_validation",
                name="Sherlock Output Validation",
                description="Validate evidence extraction and claim generation",
                validation_function="validate_sherlock_outputs",
                blocking=True,
                quality_threshold=0.8,
                sample_size=3  # Sample 3 outputs for validation
            )
        ]

        # Create task definition
        task = TaskDefinition(
            task_id=f"sherlock_pkg_{package['package_id']}",
            name=f"Sherlock Research: {package['target_name']}",
            description=f"Execute research package for {package['target_name']} ({package['package_type']})",
            task_type=TaskType.THROUGHPUT,  # Research packages are throughput work
            priority=j5a_priority,
            target_system=SystemTarget.SHERLOCK,
            estimated_duration_minutes=duration,
            thermal_safety_required=thermal_required,
            validation_checkpoints=checkpoints,
            dependencies=[],
            expected_outputs=package['expected_outputs'],
            success_criteria={
                'min_claims_extracted': 5,
                'min_evidence_quality': 0.5,
                'output_completeness': 0.8
            },
            created_timestamp=datetime.now().isoformat()
        )

        return task

    def import_sherlock_packages_to_j5a(self, package_ids: List[int]) -> Dict[str, int]:
        """
        Import Sherlock packages into J5A queue.

        Args:
            package_ids: List of package IDs from Targeting Officer sweep

        Returns:
            Dict with import statistics
        """
        stats = {
            'total': len(package_ids),
            'queued': 0,
            'failed': 0,
            'skipped': 0
        }

        # Load packages from Sherlock database
        import sqlite3
        conn = sqlite3.connect(self.targeting_officer.db_path)
        cursor = conn.cursor()

        for package_id in package_ids:
            try:
                # Get package details
                cursor.execute('''
                    SELECT p.*, t.name, t.priority
                    FROM targeting_packages p
                    JOIN targets t ON p.target_id = t.target_id
                    WHERE p.package_id = ?
                ''', (package_id,))

                row = cursor.fetchone()
                if not row:
                    self.logger.warning(f"Package {package_id} not found")
                    stats['skipped'] += 1
                    continue

                # Parse package data
                package = {
                    'package_id': row[0],
                    'target_id': row[1],
                    'version': row[2],
                    'package_type': row[3],
                    'status': row[4],
                    'collection_urls': json.loads(row[5]),
                    'expected_outputs': json.loads(row[6]),
                    'validation_level': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                    'metadata': json.loads(row[10]),
                    'target_name': row[11],
                    'priority': row[12]
                }

                # Update metadata with target info
                package['metadata']['priority'] = package['priority']
                package['metadata']['target_name'] = package['target_name']

                # Create J5A task
                j5a_task = self.create_j5a_task_from_package(package)

                # Queue task
                if self.queue_manager.queue_task(j5a_task):
                    stats['queued'] += 1
                    self.logger.info(f"✅ Queued package {package_id}: {package['target_name']}")
                else:
                    stats['failed'] += 1
                    self.logger.error(f"❌ Failed to queue package {package_id}")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"❌ Error importing package {package_id}: {e}")

        conn.close()
        return stats

    def run_targeting_officer_and_import(self) -> Dict:
        """
        Execute Targeting Officer sweep and import packages to J5A.

        WORKFLOW:
        1. Run Targeting Officer daily sweep
        2. Get list of created/submitted packages
        3. Import packages to J5A queue
        4. J5A applies scheduling logic

        Returns:
            Dict with complete operation report
        """
        self.logger.info("=" * 70)
        self.logger.info("J5A Sherlock Integration - Nightly Execution (1am)")
        self.logger.info("=" * 70)

        operation_report = {
            'timestamp': datetime.now().isoformat(),
            'targeting_officer_report': None,
            'j5a_import_stats': None,
            'errors': []
        }

        try:
            # Step 1: Run Targeting Officer sweep
            self.logger.info("🎯 Running Targeting Officer daily sweep...")
            sweep_report = self.targeting_officer.run_daily_sweep()

            operation_report['targeting_officer_report'] = {
                'targets_scanned': sweep_report.targets_scanned,
                'targets_needing_packages': sweep_report.targets_needing_packages,
                'packages_created': sweep_report.packages_created,
                'packages_validated': sweep_report.packages_validated,
                'packages_submitted': sweep_report.packages_submitted_to_j5a
            }

            self.logger.info(f"📊 Targeting Officer Results:")
            self.logger.info(f"   Targets scanned: {sweep_report.targets_scanned}")
            self.logger.info(f"   Packages created: {sweep_report.packages_created}")
            self.logger.info(f"   Packages validated: {sweep_report.packages_validated}")

            # Step 2: Import packages to J5A queue
            if sweep_report.packages_submitted_to_j5a > 0:
                self.logger.info(f"📥 Importing {sweep_report.packages_submitted_to_j5a} packages to J5A queue...")

                # Extract package IDs from created packages
                package_ids = [pkg['package_id'] for pkg in sweep_report.created_packages if pkg['status'] == 'ready']

                import_stats = self.import_sherlock_packages_to_j5a(package_ids)
                operation_report['j5a_import_stats'] = import_stats

                self.logger.info(f"📊 J5A Import Results:")
                self.logger.info(f"   Total packages: {import_stats['total']}")
                self.logger.info(f"   Successfully queued: {import_stats['queued']}")
                self.logger.info(f"   Failed: {import_stats['failed']}")
            else:
                self.logger.info("ℹ️  No packages to import (all targets have active packages)")
                operation_report['j5a_import_stats'] = {'total': 0, 'queued': 0, 'failed': 0, 'skipped': 0}

            # Step 3: Report summary
            self.logger.info("=" * 70)
            self.logger.info("✅ Targeting Officer + J5A Integration Complete")
            self.logger.info("=" * 70)

            return operation_report

        except Exception as e:
            self.logger.error(f"❌ Integration error: {e}")
            operation_report['errors'].append(str(e))
            return operation_report


def main():
    """Main entry point for integration"""
    import argparse

    parser = argparse.ArgumentParser(description="J5A Sherlock Integration")
    parser.add_argument(
        '--run-targeting-officer',
        action='store_true',
        help='Run Targeting Officer sweep and import to J5A'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Automated execution (for cron)'
    )

    args = parser.parse_args()

    # Initialize integration
    integration = J5ASherlockIntegration()

    if args.run_targeting_officer:
        # Execute Targeting Officer + J5A import
        report = integration.run_targeting_officer_and_import()

        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"/home/johnny5/Johny5Alive/logs/sherlock_integration_{timestamp}.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📄 Report saved: {report_path}")

        # Print summary
        if not args.auto:
            print("\n" + "=" * 70)
            print("OPERATION SUMMARY")
            print("=" * 70)
            print(f"Timestamp: {report['timestamp']}")
            if report['targeting_officer_report']:
                print(f"\nTargeting Officer:")
                print(f"  Packages created: {report['targeting_officer_report']['packages_created']}")
                print(f"  Packages validated: {report['targeting_officer_report']['packages_validated']}")
            if report['j5a_import_stats']:
                print(f"\nJ5A Import:")
                print(f"  Successfully queued: {report['j5a_import_stats']['queued']}")
                print(f"  Failed: {report['j5a_import_stats']['failed']}")
            print("=" * 70)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
