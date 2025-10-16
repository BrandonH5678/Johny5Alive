#!/usr/bin/env python3
"""
Nightshift Queue Processor - Process migrated jobs from Nightshift queue

Reads nightshift_jobs.json and processes jobs through j5a_worker.py
Updates original queue database with results
"""

import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from j5a_worker import J5AWorker

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
    """

    def __init__(
        self,
        jobs_file: str = None,
        queue_db: str = None
    ):
        """Initialize processor"""
        if jobs_file is None:
            jobs_file = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/queue/nightshift_jobs.json"

        if queue_db is None:
            queue_db = "/home/johnny5/Johny5Alive/j5a_queue_manager.db"

        self.jobs_file = jobs_file
        self.queue_db = queue_db

        # Initialize worker
        self.worker = J5AWorker()

        # Connect to queue database
        self.conn = sqlite3.connect(queue_db)

        logger.info(f"Nightshift processor initialized")
        logger.info(f"  Jobs file: {jobs_file}")
        logger.info(f"  Queue DB: {queue_db}")

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
        Process Nightshift queue

        Args:
            max_jobs: Maximum number of jobs to process (default: all)
        """
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

        return results

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


# Example usage
if __name__ == "__main__":
    import sys

    # Parse arguments
    max_jobs = None
    if len(sys.argv) > 1:
        try:
            max_jobs = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [max_jobs]")
            sys.exit(1)

    # Process queue
    processor = NightshiftQueueProcessor()

    try:
        results = processor.process_queue(max_jobs=max_jobs)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        processor.close()

    print()
    print("Queue processing complete!")
