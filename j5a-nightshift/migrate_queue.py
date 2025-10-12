#!/usr/bin/env python3
"""
Queue Migration Script - Migrate existing J5A queue to Nightshift format

Reads task_definitions from j5a_queue_manager.db and creates Nightshift-compatible
job specifications for processing with local LLM.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueMigrator:
    """
    Migrates tasks from J5A queue database to Nightshift format

    Responsibilities:
    - Read task_definitions from existing queue
    - Classify tasks as standard vs demanding (Phase 1 routing)
    - Map to Nightshift job types (summary, research_report, code_stub)
    - Create job input/output specifications
    - Update task_executions with Nightshift metadata
    """

    def __init__(self, queue_db_path: str = None):
        """Initialize migrator with queue database"""
        if queue_db_path is None:
            queue_db_path = "/home/johnny5/Johny5Alive/j5a_queue_manager.db"

        self.queue_db_path = queue_db_path
        self.conn = sqlite3.connect(queue_db_path)
        self.conn.row_factory = sqlite3.Row

        logger.info(f"Queue migrator initialized with {queue_db_path}")

    def classify_task(self, task: Dict[str, Any]) -> str:
        """
        Classify task as 'standard' or 'demanding' for Phase 1 routing

        Standard (local 7B):
        - Summaries <3000 words
        - Simple research reports
        - Code <40 lines (stdlib only)

        Demanding (park for Phase 2):
        - Summaries >10K words
        - Complex composite research
        - Code >100 lines or external deps
        """
        task_type = task['task_type']
        duration = task.get('estimated_duration_minutes', 0)

        # Development tasks are demanding (code generation with complex requirements)
        if task_type == 'development':
            return 'demanding'

        # Throughput tasks (Sherlock research) - classify by outputs
        if task_type == 'throughput':
            outputs = json.loads(task.get('expected_outputs', '[]'))

            # Single document summary = standard
            if len(outputs) == 1 and outputs[0].endswith('.txt'):
                return 'standard'

            # Composite research (multiple outputs: claims.json, overview.json, etc.) = demanding
            if len(outputs) >= 3:
                return 'demanding'

            # Default throughput = standard
            return 'standard'

        # Maintenance tasks are standard
        if task_type == 'maintenance':
            return 'standard'

        # Unknown = demanding (conservative)
        return 'demanding'

    def map_to_nightshift_type(self, task: Dict[str, Any]) -> str:
        """
        Map J5A task_type to Nightshift job type

        Mappings:
        - throughput (Sherlock) → research_report or summary
        - development (Squirt) → code_stub
        - maintenance → summary (documentation)
        """
        task_type = task['task_type']
        outputs = json.loads(task.get('expected_outputs', '[]'))

        if task_type == 'throughput':
            # Multiple outputs = research_report
            if len(outputs) >= 3:
                return 'research_report'
            # Single output = summary
            return 'summary'

        elif task_type == 'development':
            return 'code_stub'

        elif task_type == 'maintenance':
            return 'summary'

        else:
            # Default to summary
            return 'summary'

    def create_nightshift_job(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Nightshift-compatible job specification from task definition

        Returns:
            Job dict with:
            {
                "job_id": str,
                "type": "summary" | "research_report" | "code_stub",
                "class": "standard" | "demanding",
                "inputs": [{"path": str} or {"url": str}],
                "outputs": [{"kind": str, "path": str}],
                "metadata": {original task info}
            }
        """
        job = {
            "job_id": task['task_id'],
            "type": self.map_to_nightshift_type(task),
            "class": self.classify_task(task),
            "inputs": self._create_inputs(task),
            "outputs": self._create_outputs(task),
            "metadata": {
                "name": task['name'],
                "description": task.get('description'),
                "target_system": task.get('target_system'),
                "priority": task.get('priority', 3),
                "estimated_duration_minutes": task.get('estimated_duration_minutes'),
                "created_timestamp": task.get('created_timestamp'),
                "thermal_safety_required": task.get('thermal_safety_required', True)
            }
        }

        return job

    def _create_inputs(self, task: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Create input specifications from task

        For Sherlock throughput tasks: Look for source documents/URLs
        For development tasks: Look for spec files
        """
        inputs = []
        task_id = task['task_id']

        # Check for input files in ops/inbox
        inbox_path = Path("/home/johnny5/Johny5Alive/j5a-nightshift/ops/inbox")

        # Look for task-specific input files
        task_input = inbox_path / f"{task_id}_input.txt"
        if task_input.exists():
            inputs.append({"path": str(task_input)})

        # If no inputs found, create placeholder
        # (will need to be populated before job execution)
        if not inputs:
            inputs.append({"path": str(inbox_path / f"{task_id}_input.txt")})

        return inputs

    def _create_outputs(self, task: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Create output specifications from task expected_outputs

        Maps file extensions to output kinds:
        - .txt, .md → markdown
        - .json → json
        - .py → python
        """
        outputs = []
        expected_outputs = json.loads(task.get('expected_outputs', '[]'))

        output_dir = Path("/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs")

        for output_file in expected_outputs:
            # Determine kind from extension
            if output_file.endswith(('.txt', '.md')):
                kind = 'markdown'
            elif output_file.endswith('.json'):
                kind = 'json'
            elif output_file.endswith('.py'):
                kind = 'python'
            else:
                kind = 'text'

            # Map to Nightshift output path
            output_path = output_dir / Path(output_file).name

            outputs.append({
                "kind": kind,
                "path": str(output_path)
            })

        # If no outputs specified, create default
        if not outputs:
            outputs.append({
                "kind": "markdown",
                "path": str(output_dir / f"{task['task_id']}_output.md")
            })

        return outputs

    def migrate_tasks(self, status_filter: Optional[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Migrate tasks from queue to Nightshift format

        Args:
            status_filter: Only migrate tasks with this status (e.g., 'queued', 'deferred')
            limit: Maximum number of tasks to migrate

        Returns:
            List of Nightshift job specifications
        """
        # Build query
        query = "SELECT * FROM task_definitions"
        params = []

        if status_filter:
            # Join with task_executions to filter by status
            query = """
                SELECT td.* FROM task_definitions td
                JOIN task_executions te ON td.task_id = te.task_id
                WHERE te.status = ?
            """
            params.append(status_filter)

        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        cursor = self.conn.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]

        logger.info(f"Found {len(tasks)} tasks to migrate")

        # Create Nightshift jobs
        jobs = []
        for task in tasks:
            job = self.create_nightshift_job(task)
            jobs.append(job)

            logger.info(f"Migrated {task['task_id']}: {job['type']} ({job['class']})")

        return jobs

    def save_jobs(self, jobs: List[Dict[str, Any]], output_path: str = None):
        """
        Save Nightshift jobs to JSON file

        Args:
            jobs: List of job specifications
            output_path: Path to output file (default: ops/queue/nightshift_jobs.json)
        """
        if output_path is None:
            output_path = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/queue/nightshift_jobs.json"

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save jobs
        with open(output_path, 'w') as f:
            json.dump(jobs, f, indent=2)

        logger.info(f"Saved {len(jobs)} jobs to {output_path}")

    def update_task_status(self, task_id: str, status: str, metadata: Dict[str, Any] = None):
        """
        Update task_executions with Nightshift migration status

        Args:
            task_id: Task ID to update
            status: New status (e.g., 'nightshift_queued')
            metadata: Additional metadata to store
        """
        updates = {
            "status": status,
            "end_time": datetime.now().isoformat()
        }

        if metadata:
            # Store metadata in validation_results field
            updates["validation_results"] = json.dumps(metadata)

        # Build UPDATE query
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]

        self.conn.execute(
            f"UPDATE task_executions SET {set_clause} WHERE task_id = ?",
            values
        )
        self.conn.commit()

        logger.info(f"Updated {task_id}: {status}")

    def close(self):
        """Close database connection"""
        self.conn.close()


# Example usage and testing
if __name__ == "__main__":
    migrator = QueueMigrator()

    print("="*60)
    print("J5A QUEUE MIGRATION TO NIGHTSHIFT")
    print("="*60)
    print()

    # Migrate queued tasks only
    print("Migrating 'queued' tasks...")
    queued_jobs = migrator.migrate_tasks(status_filter='queued', limit=5)

    print(f"\nFound {len(queued_jobs)} queued tasks")
    print()

    # Migrate deferred tasks (limited sample for testing)
    print("Migrating sample of 'deferred' tasks...")
    deferred_jobs = migrator.migrate_tasks(status_filter='deferred', limit=3)

    print(f"\nFound {len(deferred_jobs)} deferred tasks (showing first 3)")
    print()

    # Combine all jobs
    all_jobs = queued_jobs + deferred_jobs

    # Display migration results
    print("="*60)
    print("MIGRATION RESULTS:")
    print("="*60)

    for job in all_jobs:
        print(f"\nJob ID: {job['job_id']}")
        print(f"  Name: {job['metadata']['name']}")
        print(f"  Type: {job['type']}")
        print(f"  Class: {job['class']}")
        print(f"  Inputs: {len(job['inputs'])} files")
        print(f"  Outputs: {len(job['outputs'])} files")

        # Show classification reasoning
        if job['class'] == 'demanding':
            print(f"  ⚠️  DEMANDING - Will be parked in Phase 1")
        else:
            print(f"  ✅ STANDARD - Can process with local 7B")

    # Save jobs
    print()
    migrator.save_jobs(all_jobs)

    print()
    print("="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Review migrated jobs in ops/queue/nightshift_jobs.json")
    print("2. Create input files in ops/inbox/ for each job")
    print("3. Run worker: python3 j5a_worker.py --process-nightshift-queue")
    print("4. Monitor outputs in ops/outputs/")

    migrator.close()
