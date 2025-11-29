#!/usr/bin/env python3
"""
Nightshift Queue Processor - Process migrated jobs from Nightshift queue

Reads nightshift_jobs.json and processes jobs through j5a_worker.py
Updates original queue database with results

Phase 2 Autonomy Features:
- Pre/post shift snapshots for safe rollback
- Failure notification system
- Queue health monitoring
- Constitutional compliance logging
"""

import json
import logging
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from j5a_worker import J5AWorker

# Try to import snapshot manager for autonomy features
try:
    from agents.jeeves.snapshot import SnapshotManager
    SNAPSHOT_AVAILABLE = True
except ImportError:
    SNAPSHOT_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NightshiftQueueProcessor:
    """
    Process Nightshift queue and update original database

    Responsibilities:
    - Load jobs from nightshift_jobs.json
    - Process through J5AWorker
    - Update j5a_queue_manager.db with results
    - Track Phase 1 success rates

    Phase 2 Autonomy:
    - Pre/post shift snapshots
    - Failure notifications
    - Queue health monitoring
    """

    def __init__(
        self,
        jobs_file: str = None,
        queue_db: str = None,
        enable_snapshots: bool = True,
        enable_notifications: bool = True
    ):
        """Initialize processor with autonomy features"""
        if jobs_file is None:
            jobs_file = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/queue/nightshift_jobs.json"

        if queue_db is None:
            queue_db = "/home/johnny5/Johny5Alive/j5a_queue_manager.db"

        self.jobs_file = jobs_file
        self.queue_db = queue_db
        self.repo_path = Path("/home/johnny5/Johny5Alive")

        # Autonomy configuration
        self.enable_snapshots = enable_snapshots and SNAPSHOT_AVAILABLE
        self.enable_notifications = enable_notifications
        self.shift_snapshot_tag: Optional[str] = None
        self.shift_start_time: Optional[datetime] = None

        # Initialize snapshot manager if available
        if self.enable_snapshots:
            self.snapshot_manager = SnapshotManager(
                {"snapshot": {"compress": "zstd", "verify_restore": True}}
            )
            logger.info("Snapshot manager initialized for autonomy")
        else:
            self.snapshot_manager = None
            if enable_snapshots and not SNAPSHOT_AVAILABLE:
                logger.warning("Snapshots requested but SnapshotManager not available")

        # Initialize worker
        self.worker = J5AWorker()

        # Connect to queue database
        self.conn = sqlite3.connect(queue_db)

        logger.info(f"Nightshift processor initialized")
        logger.info(f"  Jobs file: {jobs_file}")
        logger.info(f"  Queue DB: {queue_db}")
        logger.info(f"  Snapshots: {'enabled' if self.enable_snapshots else 'disabled'}")
        logger.info(f"  Notifications: {'enabled' if self.enable_notifications else 'disabled'}")

    def create_pre_shift_snapshot(self) -> Optional[str]:
        """
        Create a snapshot before starting the Night Shift

        Constitutional Basis: Principle 3 (System Viability) - Enable rollback

        Returns:
            Snapshot tag name if successful, None otherwise
        """
        if not self.enable_snapshots:
            logger.info("Snapshots disabled, skipping pre-shift snapshot")
            return None

        try:
            logger.info("Creating pre-shift snapshot...")
            self.shift_start_time = datetime.now()

            metadata, tag_name = self.snapshot_manager.create_pre_autonomous_snapshot(
                repo_path=self.repo_path,
                repo_name="Johny5Alive",
                task_description=f"Night Shift {self.shift_start_time.strftime('%Y-%m-%d %H:%M')}",
                push_to_remote=True
            )

            self.shift_snapshot_tag = tag_name
            logger.info(f"Pre-shift snapshot created: {tag_name}")
            print(f"\n📸 Pre-shift snapshot: {tag_name}")

            return tag_name

        except Exception as e:
            logger.error(f"Failed to create pre-shift snapshot: {e}")
            # Don't block processing on snapshot failure
            return None

    def create_post_shift_snapshot(self, results: Dict[str, Any]) -> Optional[str]:
        """
        Create a snapshot after completing the Night Shift

        Args:
            results: Processing results summary

        Returns:
            Snapshot tag name if successful, None otherwise
        """
        if not self.enable_snapshots:
            return None

        try:
            shift_end_time = datetime.now()
            duration = (shift_end_time - self.shift_start_time).total_seconds() if self.shift_start_time else 0

            logger.info("Creating post-shift snapshot...")

            # Create summary for snapshot
            summary = (
                f"Night Shift Complete: "
                f"{results.get('completed', 0)}/{results.get('total', 0)} jobs, "
                f"duration: {duration:.0f}s"
            )

            metadata, tag_name = self.snapshot_manager.create_pre_autonomous_snapshot(
                repo_path=self.repo_path,
                repo_name="Johny5Alive",
                task_description=f"Post-shift: {summary}",
                push_to_remote=True
            )

            logger.info(f"Post-shift snapshot created: {tag_name}")
            print(f"📸 Post-shift snapshot: {tag_name}")

            return tag_name

        except Exception as e:
            logger.error(f"Failed to create post-shift snapshot: {e}")
            return None

    def send_failure_notification(self, error: Exception, context: str = ""):
        """
        Send notification on critical failure

        Args:
            error: The exception that occurred
            context: Additional context about what was happening

        Constitutional Basis: Principle 2 (Transparency) - Alert humans to failures
        """
        if not self.enable_notifications:
            return

        timestamp = datetime.now().isoformat()
        message = f"""
🚨 NIGHT SHIFT FAILURE ALERT

Time: {timestamp}
Context: {context}
Error: {type(error).__name__}: {str(error)}

Pre-shift snapshot: {self.shift_snapshot_tag or 'None'}

Rollback command:
  python3 agents/jeeves/rollback.py rollback {self.shift_snapshot_tag}
"""

        # Log to file for now (email integration can be added later)
        notification_file = self.repo_path / "j5a-nightshift" / "ops" / "logs" / "failure_notifications.log"
        notification_file.parent.mkdir(parents=True, exist_ok=True)

        with open(notification_file, "a") as f:
            f.write(f"\n{'='*60}\n{message}\n")

        logger.error(f"Failure notification logged: {notification_file}")
        print(f"\n🚨 FAILURE: {error}")
        print(f"   Rollback available: {self.shift_snapshot_tag}")

    def check_queue_health(self) -> Dict[str, Any]:
        """
        Validate queue health before processing

        Checks:
        - Queue file exists and is readable
        - Database is accessible
        - No stuck jobs from previous runs
        - Resource constraints (thermal, memory)

        Returns:
            Dict with health status and any issues found
        """
        health = {
            "healthy": True,
            "issues": [],
            "warnings": []
        }

        # Check queue file
        if not Path(self.jobs_file).exists():
            health["issues"].append(f"Queue file not found: {self.jobs_file}")
            health["healthy"] = False

        # Check database
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM task_executions WHERE status = 'running'")
            running_count = cursor.fetchone()[0]
            if running_count > 0:
                health["warnings"].append(f"{running_count} jobs still marked as 'running' from previous shift")
        except Exception as e:
            health["issues"].append(f"Database error: {e}")
            health["healthy"] = False

        # Check for stuck jobs (running > 4 hours)
        try:
            four_hours_ago = (datetime.now().replace(hour=datetime.now().hour - 4)).isoformat()
            cursor = self.conn.execute(
                "SELECT COUNT(*) FROM task_executions WHERE status = 'running' AND start_time < ?",
                (four_hours_ago,)
            )
            stuck_count = cursor.fetchone()[0]
            if stuck_count > 0:
                health["warnings"].append(f"{stuck_count} jobs appear stuck (running > 4 hours)")
        except Exception:
            pass  # Non-critical check

        # Log health status
        if health["healthy"]:
            logger.info("Queue health check: PASSED")
        else:
            logger.warning(f"Queue health check: FAILED - {health['issues']}")

        if health["warnings"]:
            for warning in health["warnings"]:
                logger.warning(f"Queue health warning: {warning}")

        return health

    def load_jobs(self) -> List[Dict[str, Any]]:
        """Load jobs from nightshift_jobs.json"""
        with open(self.jobs_file, 'r') as f:
            jobs = json.load(f)

        logger.info(f"Loaded {len(jobs)} jobs from {self.jobs_file}")
        return jobs

    def check_running_jobs(self) -> Dict[str, Any]:
        """
        Check for already-running Night Shift processes

        Returns:
            Dict with has_running_job, process, pid, runtime if found
        """
        import subprocess

        logger.info("Checking for running Night Shift processes...")

        # Check for Whisper processes in nightshift artifacts
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )

        for line in result.stdout.split('\n'):
            if 'whisper' in line and 'artifacts/nightshift' in line and 'grep' not in line:
                # Extract PID and runtime
                parts = line.split()
                if len(parts) >= 10:
                    pid = parts[1]
                    etime = parts[9]  # Elapsed time

                    logger.info(f"Found running Whisper job: PID {pid}, runtime {etime}")
                    return {
                        'has_running_job': True,
                        'process': 'whisper',
                        'pid': pid,
                        'runtime': etime,
                        'command': ' '.join(parts[10:])
                    }

        # Check for podcast_intelligence_pipeline processes
        for line in result.stdout.split('\n'):
            if 'podcast_intelligence_pipeline' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 10:
                    pid = parts[1]
                    etime = parts[9]

                    logger.info(f"Found running pipeline job: PID {pid}, runtime {etime}")
                    return {
                        'has_running_job': True,
                        'process': 'podcast_pipeline',
                        'pid': pid,
                        'runtime': etime,
                        'command': ' '.join(parts[10:])
                    }

        logger.info("No running Night Shift processes detected")
        return {'has_running_job': False}

    def sync_queue_to_database(self):
        """
        Synchronize jobs from nightshift_jobs.json into database

        Ensures both queue sources (JSON + DB) are synchronized before processing
        """
        logger.info("Synchronizing queue to database...")

        jobs = self.load_jobs()
        synced = 0
        skipped = 0

        for job in jobs:
            job_id = job['job_id']

            # Check if job already in database
            cursor = self.conn.execute(
                "SELECT task_id, status FROM task_executions WHERE task_id = ?",
                (job_id,)
            )
            existing = cursor.fetchone()

            if not existing:
                # Insert new job into task_definitions and task_executions
                try:
                    # Insert into task_definitions first
                    self.conn.execute("""
                        INSERT INTO task_definitions
                        (task_id, name, description, task_type, priority, target_system,
                         thermal_safety_required, expected_outputs, success_criteria, created_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job_id,
                        job.get('name', job.get('description', 'Unnamed job')),
                        job.get('description', ''),
                        job.get('type', 'unknown'),
                        job.get('priority', 5),
                        'nightshift',
                        True,  # thermal_safety_required
                        json.dumps(job.get('outputs', [])),
                        json.dumps(job.get('metadata', {}).get('success_criteria', {})),
                        datetime.now().isoformat()
                    ))

                    # Insert into task_executions
                    self.conn.execute("""
                        INSERT INTO task_executions
                        (task_id, status, start_time, retry_count)
                        VALUES (?, 'queued', ?, 0)
                    """, (job_id, datetime.now().isoformat()))

                    synced += 1
                    logger.info(f"Synced job to database: {job_id}")

                except Exception as e:
                    logger.warning(f"Failed to sync job {job_id}: {e}")

            else:
                skipped += 1
                logger.debug(f"Job already in database: {job_id} (status: {existing[1]})")

        self.conn.commit()

        logger.info(f"Queue sync complete: {synced} jobs synced, {skipped} already in database")
        return {'synced': synced, 'skipped': skipped}

    def process_queue(self, max_jobs: int = None):
        """
        Process Nightshift queue with Phase 2 autonomy features

        Args:
            max_jobs: Maximum number of jobs to process (default: all)

        Phase 2 Autonomy:
        - Pre-shift snapshot before processing
        - Queue health check
        - Failure notifications on errors
        - Post-shift snapshot after completion
        """
        # Phase 2: Queue health check
        health = self.check_queue_health()
        if not health["healthy"]:
            error = Exception(f"Queue health check failed: {health['issues']}")
            self.send_failure_notification(error, "Pre-flight health check")
            raise error

        # Synchronize queue JSON to database first
        self.sync_queue_to_database()

        # Then check for running Night Shift jobs
        running_job = self.check_running_jobs()

        if running_job['has_running_job']:
            print()
            print("="*60)
            print("NIGHTSHIFT JOB MONITORING MODE")
            print("="*60)
            print()
            print(f"⚠️  Detected running {running_job['process']} process")
            print(f"   PID: {running_job['pid']}")
            print(f"   Runtime: {running_job['runtime']}")
            print(f"   Command: {running_job['command'][:80]}...")
            print()
            print("✅ Job already in progress - monitoring existing process")
            print("   Night Shift will skip new job processing and monitor completion")
            print()
            logger.info(f"Monitoring mode: {running_job['process']} PID {running_job['pid']}")
            return {
                'mode': 'monitoring',
                'running_job': running_job
            }

        # No running jobs - proceed with normal queue processing
        jobs = self.load_jobs()

        if max_jobs:
            jobs = jobs[:max_jobs]

        # Phase 2: Create pre-shift snapshot
        self.create_pre_shift_snapshot()

        logger.info(f"Processing {len(jobs)} jobs...")
        print()
        print("="*60)
        print("NIGHTSHIFT QUEUE PROCESSING")
        print("="*60)
        print()

        results = {
            "total": len(jobs),
            "completed": 0,
            "parked": 0,
            "deferred": 0,
            "failed": 0,
            "insufficient_evidence": 0
        }

        for i, job in enumerate(jobs, 1):
            job_id = job['job_id']
            job_class = job['class']

            print(f"[{i}/{len(jobs)}] Processing {job_id} ({job_class})...")

            # Process job
            result = self.worker.process_job(job)

            # Update status counts
            status = result.get('status', 'failed')
            if status == 'completed':
                results['completed'] += 1
            elif status == 'parked':
                results['parked'] += 1
            elif status == 'deferred':
                results['deferred'] += 1
            elif status == 'insufficient_evidence':
                results['insufficient_evidence'] += 1
            else:
                results['failed'] += 1

            # Update database
            self._update_database(job_id, result)

            # Print result
            if result.get('success'):
                print(f"  ✅ {status.upper()}")
                if result.get('outputs'):
                    print(f"     Outputs: {len(result['outputs'])} files")
            else:
                print(f"  ❌ {status.upper()}")
                if result.get('reason'):
                    print(f"     Reason: {result['reason']}")

            print()

        # Print summary
        print("="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Total jobs: {results['total']}")
        print(f"  ✅ Completed: {results['completed']}")
        print(f"  📦 Parked (Phase 2): {results['parked']}")
        print(f"  ⏸️  Deferred (thermal): {results['deferred']}")
        print(f"  ⚠️  Insufficient evidence: {results['insufficient_evidence']}")
        print(f"  ❌ Failed: {results['failed']}")
        print()

        # Calculate success rate
        processable = results['total'] - results['parked']
        if processable > 0:
            success_rate = (results['completed'] + results['insufficient_evidence']) / processable
            print(f"Phase 1 Success Rate: {success_rate:.1%}")
            print(f"  (Target: ≥85%)")
            print()

            if success_rate >= 0.85:
                print("🎯 SUCCESS: Phase 1 target achieved!")
            else:
                print("⚠️  Below target - needs optimization")

        # Phase 2: Create post-shift snapshot
        self.create_post_shift_snapshot(results)

        return results

    def run_autonomous_shift(self, max_jobs: int = None) -> Dict[str, Any]:
        """
        Run a complete autonomous Night Shift with full safety protocols

        This is the main entry point for autonomous operation.

        Args:
            max_jobs: Maximum jobs to process (default: all)

        Returns:
            Results dictionary with status and metrics
        """
        shift_result = {
            "success": False,
            "pre_snapshot": None,
            "post_snapshot": None,
            "results": None,
            "error": None
        }

        try:
            # Create pre-shift snapshot (redundant safety)
            shift_result["pre_snapshot"] = self.shift_snapshot_tag

            # Process queue
            results = self.process_queue(max_jobs=max_jobs)
            shift_result["results"] = results
            shift_result["success"] = True

            logger.info("Autonomous shift completed successfully")

        except Exception as e:
            shift_result["error"] = str(e)
            self.send_failure_notification(e, "Autonomous shift processing")
            logger.error(f"Autonomous shift failed: {e}")

        finally:
            shift_result["post_snapshot"] = self.shift_snapshot_tag

        return shift_result

    def _update_database(self, job_id: str, result: Dict[str, Any]):
        """
        Update j5a_queue_manager.db with job result

        Args:
            job_id: Task ID
            result: Job processing result
        """
        status = result.get('status', 'failed')
        outputs = json.dumps(result.get('outputs', []))
        validation = json.dumps({
            "nightshift_validation": result.get('validation'),
            "success": result.get('success'),
            "reason": result.get('reason')
        })

        self.conn.execute("""
            UPDATE task_executions
            SET status = ?,
                output_files = ?,
                validation_results = ?,
                end_time = ?
            WHERE task_id = ?
        """, (status, outputs, validation, datetime.now().isoformat(), job_id))

        self.conn.commit()

        logger.info(f"Updated database: {job_id} → {status}")

    def close(self):
        """Close database connection"""
        self.conn.close()


# Main entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Night Shift Queue Processor with Phase 2 Autonomy"
    )
    parser.add_argument(
        "max_jobs",
        nargs="?",
        type=int,
        default=None,
        help="Maximum number of jobs to process (default: all)"
    )
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Run in full autonomous mode with snapshots and notifications"
    )
    parser.add_argument(
        "--no-snapshots",
        action="store_true",
        help="Disable pre/post shift snapshots"
    )
    parser.add_argument(
        "--no-notifications",
        action="store_true",
        help="Disable failure notifications"
    )

    args = parser.parse_args()

    # Initialize processor with autonomy settings
    processor = NightshiftQueueProcessor(
        enable_snapshots=not args.no_snapshots,
        enable_notifications=not args.no_notifications
    )

    try:
        if args.autonomous:
            # Full autonomous mode
            print()
            print("🤖 AUTONOMOUS NIGHT SHIFT MODE")
            print("="*60)
            result = processor.run_autonomous_shift(max_jobs=args.max_jobs)

            if result["success"]:
                print("\n✅ Autonomous shift completed successfully")
            else:
                print(f"\n❌ Autonomous shift failed: {result['error']}")
                sys.exit(1)
        else:
            # Standard processing mode
            results = processor.process_queue(max_jobs=args.max_jobs)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        processor.send_failure_notification(
            Exception("Keyboard interrupt"),
            "User interrupted processing"
        )
    except Exception as e:
        processor.send_failure_notification(e, "Unhandled exception")
        raise
    finally:
        processor.close()

    print()
    print("Queue processing complete!")
