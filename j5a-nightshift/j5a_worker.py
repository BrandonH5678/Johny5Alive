#!/usr/bin/env python3
"""
J5A Nightshift Worker - Main orchestrator for autonomous overnight operations
Processes jobs from queue with local LLM execution and validation
"""

import os
import sys
import yaml
import json
import time
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Import Nightshift components
from llm_gateway import LLMGateway, LLMMode, retry_with_backoff
from sherlock_ingest import ingest
from sherlock_chunk import chunk, select_excerpts
from summarize_local import summarize

# Import validators
sys.path.append('ops/validators')
from code_validator import validate_code_file
from summaries_validator import validate_summary

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Job types supported by Nightshift"""
    RESEARCH_REPORT = "research_report"
    CODE_STUB = "code_stub"
    SUMMARY = "summary"


class JobClass(Enum):
    """Job complexity classification"""
    STANDARD = "standard"      # Local 7B can handle
    DEMANDING = "demanding"    # Requires larger model or API


class J5AWorker:
    """
    Main Nightshift worker orchestrator

    Responsibilities:
    - Load jobs from queue database
    - Route to appropriate processing pipeline
    - Validate outputs using quality gates
    - Update job status and metrics
    """

    def __init__(self, config_path: str = None):
        """Initialize worker with configuration"""
        if config_path is None:
            config_path = "/home/johnny5/Johny5Alive/j5a-nightshift/rules.yaml"

        # Load configuration
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.phase = self.config.get("phase", 1)
        self.base_path = Path(self.config["paths"]["base"])

        # Initialize LLM gateway
        llm_mode = LLMMode.LOCAL if self.config["llm"]["default_mode"] == "local" else LLMMode.REMOTE
        self.gateway = LLMGateway(mode=llm_mode, config=self.config)

        logger.info(f"J5A Worker initialized (Phase {self.phase}, LLM mode: {llm_mode.value})")

    def process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single job from queue

        Args:
            job: Job definition dict with type, inputs, outputs, etc.

        Returns:
            Result dict with success, outputs, errors
        """
        job_id = job.get("job_id", "unknown")
        job_type = job.get("type", "")
        job_class = job.get("class", JobClass.STANDARD.value)

        logger.info(f"Processing job {job_id}: {job_type} (class: {job_class})")

        # Phase 1: Park demanding jobs
        if self.phase == 1 and job_class == JobClass.DEMANDING.value:
            logger.info(f"Parking demanding job {job_id} (Phase 1 local-only)")
            return {
                "success": False,
                "status": "parked",
                "reason": "Phase 1: Demanding jobs parked for Phase 2"
            }

        # Check thermal safety
        if not self._check_thermal_safe():
            logger.warning(f"Thermal unsafe, deferring job {job_id}")
            return {
                "success": False,
                "status": "deferred",
                "reason": "CPU temperature too high"
            }

        # Route to appropriate processor
        try:
            if job_type == JobType.SUMMARY.value or job_type == JobType.RESEARCH_REPORT.value:
                return self._process_summary_job(job)
            elif job_type == JobType.CODE_STUB.value:
                return self._process_code_job(job)
            else:
                return {
                    "success": False,
                    "status": "failed",
                    "reason": f"Unknown job type: {job_type}"
                }

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    def _process_summary_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process summary/research report job"""
        job_id = job["job_id"]
        inputs = job.get("inputs", [])

        if not inputs:
            return {"success": False, "reason": "No inputs provided"}

        # Ingest content
        txt_paths = []
        for input_spec in inputs:
            path_or_url = input_spec.get("path") or input_spec.get("url")
            if path_or_url:
                txt_path = ingest(path_or_url)
                txt_paths.append(txt_path)

        if not txt_paths:
            return {"success": False, "reason": "Content ingestion failed"}

        # Chunk and select excerpts (using first input for now)
        chunks_path = chunk(txt_paths[0])

        # Generate summary
        try:
            summary_path = summarize(
                chunks_path,
                mode=LLMMode.LOCAL,
                max_excerpts=10,
                max_tokens_input=self.config["llm"]["max_context"]
            )
        except ValueError as e:
            # LLM returned INSUFFICIENT_EVIDENCE or validation failed
            return {
                "success": True,  # Job completed, just insufficient data
                "status": "insufficient_evidence",
                "outputs": [],
                "reason": str(e)
            }

        # Validate summary
        if not validate_summary(summary_path, chunks_path):
            return {
                "success": False,
                "status": "validation_failed",
                "reason": "Summary validation failed (< 3 citations)"
            }

        return {
            "success": True,
            "status": "completed",
            "outputs": [summary_path],
            "validation": "passed"
        }

    def _process_code_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process code generation job"""
        job_id = job["job_id"]

        # Load contract
        contract_path = self.base_path / "contracts" / "code_stub_contract.txt"
        with open(contract_path) as f:
            contract = f.read()

        # Get function spec and tests from inputs
        inputs = job.get("inputs", [])
        if not inputs:
            return {"success": False, "reason": "No inputs (need spec + tests)"}

        # Ingest spec and tests
        excerpts = []
        for input_spec in inputs:
            path = input_spec.get("path")
            if path:
                txt_path = ingest(path)
                with open(txt_path, 'r') as f:
                    excerpts.append({
                        "text": f.read(),
                        "source": Path(path).name,
                        "score": 1.0
                    })

        # Generate code
        code_text = self.gateway.complete(
            instructions=contract,
            excerpts=excerpts,
            limits={"max_output": self.config["llm"]["max_output"]}
        )

        # Save code
        output_dir = self.base_path / "ops" / "outputs"
        code_path = output_dir / f"{job_id}_generated.py"

        with open(code_path, 'w') as f:
            f.write(code_text)

        # Find test file (if provided)
        test_path = None
        for input_spec in inputs:
            if "test" in input_spec.get("path", "").lower():
                test_path = input_spec["path"]
                break

        # Validate code
        if not validate_code_file(str(code_path), test_path):
            return {
                "success": False,
                "status": "validation_failed",
                "reason": "Code validation failed (ruff/mypy/pytest)"
            }

        return {
            "success": True,
            "status": "completed",
            "outputs": [str(code_path)],
            "validation": "passed"
        }

    def _check_thermal_safe(self) -> bool:
        """Check if CPU temperature is safe for processing"""
        thermal_limit = self.config["resources"]["thermal_limit_celsius"]

        try:
            # Try to get CPU temperature
            import subprocess
            result = subprocess.run(
                ['sensors'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse temperature from output
                for line in result.stdout.split('\n'):
                    if 'Package id 0' in line or 'Core 0' in line:
                        # Extract temperature (format: +XX.X°C)
                        import re
                        match = re.search(r'\+(\d+\.\d+)°C', line)
                        if match:
                            temp = float(match.group(1))
                            if temp > thermal_limit:
                                logger.warning(f"CPU temp {temp}°C exceeds limit {thermal_limit}°C")
                                return False
                            return True

        except Exception as e:
            logger.warning(f"Could not check thermal status: {e}")
            # If we can't check, assume safe (better than blocking all jobs)
            return True

        return True


def process_queue(worker: J5AWorker, queue_db_path: str = None):
    """
    Process jobs from queue database

    Args:
        worker: J5AWorker instance
        queue_db_path: Path to queue database (default: from config)
    """
    if queue_db_path is None:
        queue_db_path = worker.config["paths"]["queue_db"]

    # Connect to queue database
    conn = sqlite3.connect(queue_db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    try:
        # Find queued jobs
        cursor = conn.execute("""
            SELECT * FROM task_executions
            WHERE status = 'queued'
            ORDER BY priority ASC, created_timestamp ASC
            LIMIT 10
        """)

        jobs = cursor.fetchall()
        logger.info(f"Found {len(jobs)} queued jobs")

        for job_row in jobs:
            job = dict(job_row)

            # Process job
            result = worker.process_job(job)

            # Update status
            new_status = result.get("status", "failed")
            outputs = json.dumps(result.get("outputs", []))

            conn.execute("""
                UPDATE task_executions
                SET status = ?, outputs = ?, updated_timestamp = ?
                WHERE task_id = ?
            """, (new_status, outputs, datetime.now().isoformat(), job["task_id"]))

            conn.commit()

            logger.info(f"Job {job['task_id']}: {new_status}")

    finally:
        conn.close()


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize worker
    worker = J5AWorker()

    # Test with sample job
    test_job = {
        "job_id": "test_001",
        "type": "summary",
        "class": "standard",
        "inputs": [
            {"path": "/home/johnny5/Johny5Alive/j5a-nightshift/ops/inbox/test_input.txt"}
        ],
        "outputs": [
            {"kind": "markdown", "path": "/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs/test_summary.md"}
        ]
    }

    # Create test input if doesn't exist
    test_input_path = test_job["inputs"][0]["path"]
    os.makedirs(os.path.dirname(test_input_path), exist_ok=True)

    if not os.path.exists(test_input_path):
        with open(test_input_path, 'w') as f:
            f.write("""
# Introduction to Autonomous Systems

Autonomous systems are capable of performing tasks without human intervention.
They use sensors, algorithms, and machine learning to make decisions.

# Applications

Autonomous systems are used in:
- Self-driving cars
- Robotics
- Drone delivery
- Industrial automation

# Challenges

Key challenges include safety, reliability, and ethical considerations.
            """.strip())

    print("Testing J5A Worker with sample job...")
    result = worker.process_job(test_job)

    print("\n" + "="*60)
    print("JOB RESULT:")
    print("="*60)
    print(f"Success: {result.get('success')}")
    print(f"Status: {result.get('status')}")
    if result.get('outputs'):
        print(f"Outputs: {result['outputs']}")
    if result.get('reason'):
        print(f"Reason: {result['reason']}")
