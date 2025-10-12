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

    def process_queue(self, max_jobs: int = None):
        """
        Process Nightshift queue

        Args:
            max_jobs: Maximum number of jobs to process (default: all)
        """
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
