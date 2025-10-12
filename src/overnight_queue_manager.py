#!/usr/bin/env python3
"""
J5A Overnight Queue/Batch Manager with Validation-Focused Protocols
Manages overnight tasks for Squirt, Sherlock, and other AI systems with statistical sampling validation
"""

import os
import sys
import json
import time
import sqlite3
import logging
import random
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import subordinate system modules
sys.path.append('/home/johnny5/Squirt/src')
sys.path.append('/home/johnny5/Sherlock')

try:
    # Thermal safety integration
    from thermal_check import check_thermal_status
except ImportError:
    def check_thermal_status():
        return {"temp": 70.0, "status": "normal"}

try:
    # J5A visual validation
    from j5a_visual_validator import J5AVisualValidator
except ImportError:
    J5AVisualValidator = None

try:
    # Token budget management
    from src.j5a_token_governor import TokenGovernor, TokenEstimate, AdaptationTier
except ImportError:
    print("Warning: TokenGovernor not available, using fallback")
    class TokenGovernor:
        def __init__(self):
            self.budget_remaining = 200000
        def check_budget(self, estimate):
            return True
        def record_usage(self, tokens):
            pass
    class TokenEstimate:
        def __init__(self, input_tokens=0, output_tokens=0, total=0, confidence=1.0):
            self.input_tokens = input_tokens
            self.output_tokens = output_tokens
            self.total = total
            self.confidence = confidence
    class AdaptationTier(Enum):
        FULL = "full"
        MODERATE = "moderate"
        CONSTRAINED = "constrained"
        CRITICAL = "critical"
        EMERGENCY = "emergency"

try:
    # Sherlock research execution
    from src.sherlock_research_executor import SherlockResearchExecutor
except ImportError:
    SherlockResearchExecutor = None


class TaskType(Enum):
    """Task classification for queue management"""
    DEVELOPMENT = "development"      # System development/programming
    THROUGHPUT = "throughput"       # Production workload execution
    MAINTENANCE = "maintenance"     # System maintenance tasks
    VALIDATION = "validation"       # Quality validation tasks


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1    # Emergency system tasks
    HIGH = 2        # Business-critical tasks
    NORMAL = 3      # Standard tasks
    LOW = 4         # Background tasks
    BATCH = 5       # Bulk processing tasks


class SystemTarget(Enum):
    """Target systems for task execution"""
    SQUIRT = "squirt"
    SHERLOCK = "sherlock"
    J5A = "j5a"
    MULTI_SYSTEM = "multi_system"


class TaskStatus(Enum):
    """Task execution status"""
    QUEUED = "queued"
    VALIDATION_PENDING = "validation_pending"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    OUTPUT_VALIDATION = "output_validation"
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"


@dataclass
class ValidationCheckpoint:
    """Validation checkpoint configuration"""
    checkpoint_id: str
    name: str
    description: str
    validation_function: str
    blocking: bool
    quality_threshold: float
    sample_size: int = 3


@dataclass
class TaskDefinition:
    """Complete task definition with validation requirements"""
    task_id: str
    name: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    target_system: SystemTarget
    estimated_duration_minutes: int
    thermal_safety_required: bool
    validation_checkpoints: List[ValidationCheckpoint]
    dependencies: List[str]
    expected_outputs: List[str]  # Expected output files/deliverables
    success_criteria: Dict[str, Any]
    created_timestamp: str
    scheduled_start: Optional[str] = None


@dataclass
class TaskExecution:
    """Task execution tracking with validation results"""
    task_id: str
    status: TaskStatus
    start_time: Optional[str]
    end_time: Optional[str]
    current_checkpoint: Optional[str]
    validation_results: Dict[str, Any]
    output_files: List[str]
    error_log: List[str]
    performance_metrics: Dict[str, float]
    retry_count: int = 0


@dataclass
class StatisticalSample:
    """Statistical sampling result for validation"""
    sample_id: str
    sample_path: str
    validation_success: bool
    quality_score: float
    processing_time: float
    error_message: Optional[str]
    metrics: Dict[str, Any]


@dataclass
class ValidationReport:
    """Validation report for task execution"""
    task_id: str
    checkpoint_id: str
    timestamp: str
    total_samples: int
    successful_samples: int
    average_quality_score: float
    success_rate: float
    processing_viability: bool
    recommendations: List[str]
    blocked_progression: bool


class J5AOvernightQueueManager:
    """
    J5A Overnight Queue/Batch Manager with Validation-Focused Protocols

    Manages overnight tasks across Squirt, Sherlock, and other AI systems with:
    - Statistical sampling validation before resource allocation
    - Output-focused validation checkpoints
    - Thermal safety integration
    - Cross-system coordination
    """

    def __init__(self, db_path: str = "j5a_queue_manager.db"):
        """Initialize the overnight queue manager"""
        self.db_path = db_path
        self.visual_validator = None
        self.active_tasks = {}
        self.validation_history = []

        # Token budget management
        self.token_governor = TokenGovernor()

        # Sherlock research executor
        self.sherlock_executor = SherlockResearchExecutor()

        # Quality thresholds adapted from Sherlock
        self.quality_thresholds = {
            "min_success_rate": 0.6,           # 60% of samples must succeed
            "min_quality_score": 0.5,          # Average quality score threshold
            "min_output_completeness": 0.8,    # 80% of expected outputs must be generated
            "max_thermal_temp": 80.0,          # Maximum CPU temperature (°C)
            "max_memory_usage_gb": 3.0         # Maximum memory usage
        }

        # TEMPORARY: RAM upgrade constraint (remove after RAM upgrade delivered)
        # Block multi-speaker audio (podcasts/interviews) until 8GB+ RAM available
        self.ram_upgrade_pending = False  # RAM UPGRADE COMPLETE - 16GB installed
        self.blocked_content_types = [
            "podcast",
            "interview_series",
            "youtube",  # Often multi-speaker
            "multi_speaker_audio"
        ]
        self.allowed_content_types = [
            "document",
            "book",
            "single_speaker_audio",
            "visual_media"
        ]

        # Initialize database
        self._init_database()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/johnny5/Johny5Alive/j5a_queue_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _init_database(self):
        """Initialize SQLite database for queue management"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS task_definitions (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    target_system TEXT NOT NULL,
                    estimated_duration_minutes INTEGER,
                    thermal_safety_required BOOLEAN,
                    validation_checkpoints TEXT,
                    dependencies TEXT,
                    expected_outputs TEXT,
                    success_criteria TEXT,
                    created_timestamp TEXT NOT NULL,
                    scheduled_start TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS task_executions (
                    task_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    current_checkpoint TEXT,
                    validation_results TEXT,
                    output_files TEXT,
                    error_log TEXT,
                    performance_metrics TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (task_id) REFERENCES task_definitions (task_id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS validation_reports (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    total_samples INTEGER,
                    successful_samples INTEGER,
                    average_quality_score REAL,
                    success_rate REAL,
                    processing_viability BOOLEAN,
                    recommendations TEXT,
                    blocked_progression BOOLEAN,
                    FOREIGN KEY (task_id) REFERENCES task_definitions (task_id)
                )
            ''')

            conn.commit()

    def queue_task(self, task_def: TaskDefinition) -> bool:
        """
        Queue a new task with validation checkpoints

        Args:
            task_def: Complete task definition

        Returns:
            bool: Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store task definition
                conn.execute('''
                    INSERT INTO task_definitions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_def.task_id,
                    task_def.name,
                    task_def.description,
                    task_def.task_type.value,
                    task_def.priority.value,
                    task_def.target_system.value,
                    task_def.estimated_duration_minutes,
                    task_def.thermal_safety_required,
                    json.dumps([asdict(cp) for cp in task_def.validation_checkpoints]),
                    json.dumps(task_def.dependencies),
                    json.dumps(task_def.expected_outputs),
                    json.dumps(task_def.success_criteria),
                    task_def.created_timestamp,
                    task_def.scheduled_start
                ))

                # Initialize task execution tracking
                execution = TaskExecution(
                    task_id=task_def.task_id,
                    status=TaskStatus.QUEUED,
                    start_time=None,
                    end_time=None,
                    current_checkpoint=None,
                    validation_results={},
                    output_files=[],
                    error_log=[],
                    performance_metrics={}
                )

                conn.execute('''
                    INSERT INTO task_executions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution.task_id,
                    execution.status.value,
                    execution.start_time,
                    execution.end_time,
                    execution.current_checkpoint,
                    json.dumps(execution.validation_results),
                    json.dumps(execution.output_files),
                    json.dumps(execution.error_log),
                    json.dumps(execution.performance_metrics),
                    execution.retry_count
                ))

                conn.commit()

            self.logger.info(f"✅ Task queued: {task_def.task_id} - {task_def.name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to queue task {task_def.task_id}: {e}")
            return False

    def import_sherlock_queue(self) -> Dict[str, Any]:
        """
        Import Sherlock research packages from queue/ directory

        Returns:
            Dict with import summary
        """
        import_summary = {
            "total_found": 0,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        queue_dir = Path("/home/johnny5/Johny5Alive/queue")

        if not queue_dir.exists():
            self.logger.warning(f"⚠️ Queue directory not found: {queue_dir}")
            return import_summary

        self.logger.info(f"📥 Importing Sherlock research packages from {queue_dir}")

        # Find all Sherlock package JSON files
        for json_file in sorted(queue_dir.glob("sherlock_pkg_*.json")):
            import_summary["total_found"] += 1

            try:
                with open(json_file) as f:
                    pkg_data = json.load(f)

                # Check if already imported
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        'SELECT task_id FROM task_definitions WHERE task_id = ?',
                        (pkg_data["task_id"],)
                    )
                    if cursor.fetchone():
                        self.logger.debug(f"⏭️ Skipping already imported: {pkg_data['task_id']}")
                        import_summary["skipped"] += 1
                        continue

                # Determine if task is RAM-blocked
                package_type = pkg_data.get("package_type", "")
                is_ram_blocked = package_type in self.blocked_content_types

                # Map priority (JSON uses 1-5, TaskPriority uses enum)
                priority_map = {1: TaskPriority.CRITICAL, 2: TaskPriority.HIGH,
                               3: TaskPriority.NORMAL, 4: TaskPriority.LOW, 5: TaskPriority.BATCH}
                priority = priority_map.get(pkg_data.get("priority", 3), TaskPriority.NORMAL)

                # Create TaskDefinition
                task_def = TaskDefinition(
                    task_id=pkg_data["task_id"],
                    name=pkg_data["target_name"],
                    description=f"Sherlock research: {pkg_data['target_name']} ({package_type})",
                    task_type=TaskType.THROUGHPUT,
                    priority=priority,
                    target_system=SystemTarget.SHERLOCK,
                    estimated_duration_minutes=pkg_data.get("estimated_duration_min", 30),
                    thermal_safety_required=True,
                    validation_checkpoints=[],
                    dependencies=[],
                    expected_outputs=pkg_data.get("expected_outputs", []),
                    success_criteria={"research_complete": True},
                    created_timestamp=pkg_data.get("created_at", datetime.now().isoformat())
                )

                # Queue task (will be deferred automatically if RAM-blocked)
                if self.queue_task(task_def):
                    import_summary["imported"] += 1

                    # If RAM-blocked, immediately defer
                    if is_ram_blocked:
                        self._update_task_status(task_def.task_id, TaskStatus.DEFERRED)
                        self.logger.info(f"⚠️ Deferred (RAM constraint): {task_def.task_id}")

            except Exception as e:
                error_msg = f"Failed to import {json_file.name}: {e}"
                self.logger.error(f"❌ {error_msg}")
                import_summary["errors"].append(error_msg)

        self.logger.info(
            f"✅ Sherlock import complete: {import_summary['imported']} imported, "
            f"{import_summary['skipped']} skipped, {len(import_summary['errors'])} errors"
        )

        return import_summary

    def import_j5a_plans(self) -> Dict[str, Any]:
        """
        Import development tasks from j5a_plans/ directory

        Returns:
            Dict with import summary
        """
        import importlib.util

        import_summary = {
            "plans_found": 0,
            "tasks_imported": 0,
            "tasks_blocked": 0,
            "errors": []
        }

        plans_dir = Path("/home/johnny5/Johny5Alive/j5a_plans")

        if not plans_dir.exists():
            self.logger.warning(f"⚠️ Plans directory not found: {plans_dir}")
            return import_summary

        self.logger.info(f"📥 Importing J5A development plans from {plans_dir}")

        # Find all metadata.json files
        for metadata_file in sorted(plans_dir.glob("*_metadata.json")):
            import_summary["plans_found"] += 1

            try:
                with open(metadata_file) as f:
                    plan_meta = json.load(f)

                plan_name = plan_meta.get("plan_name", metadata_file.stem)
                self.logger.info(f"📋 Processing plan: {plan_name}")

                # Find corresponding tasks.py file
                tasks_file = metadata_file.with_name(
                    metadata_file.stem.replace("_metadata", "_tasks") + ".py"
                )

                if not tasks_file.exists():
                    self.logger.warning(f"⚠️ Tasks file not found: {tasks_file.name}")
                    continue

                # Dynamically import tasks module
                spec = importlib.util.spec_from_file_location(
                    f"j5a_plans.{tasks_file.stem}",
                    tasks_file
                )
                tasks_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tasks_module)

                # Get tasks from module - try multiple function name patterns
                tasks = []
                if hasattr(tasks_module, 'create_tasks'):
                    tasks = tasks_module.create_tasks()
                elif hasattr(tasks_module, 'create_phase_tasks'):
                    tasks = tasks_module.create_phase_tasks()
                else:
                    # Try phase-specific functions (create_phase1_tasks, create_phase2_tasks, etc.)
                    for attr_name in dir(tasks_module):
                        if attr_name.startswith('create_phase') and attr_name.endswith('_tasks'):
                            phase_func = getattr(tasks_module, attr_name)
                            if callable(phase_func):
                                try:
                                    phase_tasks = phase_func()
                                    if phase_tasks:
                                        tasks.extend(phase_tasks)
                                except Exception as e:
                                    self.logger.warning(f"⚠️ Error calling {attr_name}(): {e}")

                if not tasks:
                    self.logger.warning(f"⚠️ No tasks found in {tasks_file.name}")
                    continue

                # Import each task from the plan
                for task in tasks:
                    # Check if already imported
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.execute(
                            'SELECT task_id FROM task_definitions WHERE task_id = ?',
                            (task.task_id,)
                        )
                        if cursor.fetchone():
                            continue

                    # Check blocking conditions from metadata
                    is_blocked = False
                    if "phases" in plan_meta:
                        for phase in plan_meta["phases"]:
                            if phase.get("status") == "blocked":
                                # Check if this task is in a blocked phase
                                phase_tasks = [t.get("task_id") for t in phase.get("tasks", [])]
                                if task.task_id in phase_tasks:
                                    is_blocked = True
                                    import_summary["tasks_blocked"] += 1
                                    self.logger.info(f"⏸️ Blocked task skipped: {task.task_id}")
                                    break

                    if is_blocked:
                        continue

                    # Convert J5AWorkAssignment to TaskDefinition
                    task_def = self._convert_work_assignment_to_task_def(task)

                    if self.queue_task(task_def):
                        import_summary["tasks_imported"] += 1

            except Exception as e:
                error_msg = f"Failed to import plan {metadata_file.name}: {e}"
                self.logger.error(f"❌ {error_msg}")
                import_summary["errors"].append(error_msg)

        self.logger.info(
            f"✅ J5A plans import complete: {import_summary['tasks_imported']} tasks imported, "
            f"{import_summary['tasks_blocked']} blocked, {len(import_summary['errors'])} errors"
        )

        return import_summary

    def _convert_work_assignment_to_task_def(self, work_assignment) -> TaskDefinition:
        """
        Convert J5AWorkAssignment to TaskDefinition

        Args:
            work_assignment: J5AWorkAssignment object

        Returns:
            TaskDefinition
        """
        # Map J5AWorkAssignment priority to TaskPriority
        priority_map = {
            "CRITICAL": TaskPriority.CRITICAL,
            "HIGH": TaskPriority.HIGH,
            "NORMAL": TaskPriority.NORMAL,
            "LOW": TaskPriority.LOW
        }

        priority_str = str(work_assignment.priority).split('.')[-1] if hasattr(work_assignment.priority, 'name') else "NORMAL"
        priority = priority_map.get(priority_str, TaskPriority.NORMAL)

        # Determine target system from domain
        domain = getattr(work_assignment, 'domain', 'j5a')
        if 'squirt' in domain.lower():
            target_system = SystemTarget.SQUIRT
        elif 'sherlock' in domain.lower():
            target_system = SystemTarget.SHERLOCK
        else:
            target_system = SystemTarget.J5A

        # Extract expected outputs - handle OutputSpecification objects
        expected_outputs = []
        outputs_raw = getattr(work_assignment, 'expected_outputs', [])
        for output in outputs_raw:
            if isinstance(output, str):
                expected_outputs.append(output)
            elif hasattr(output, 'path'):  # OutputSpecification object
                expected_outputs.append(str(output.path))
            else:
                expected_outputs.append(str(output))

        # Extract success criteria - handle QuantitativeMeasure objects
        success_criteria = {}
        criteria_raw = getattr(work_assignment, 'success_criteria', {})
        if isinstance(criteria_raw, dict):
            for key, value in criteria_raw.items():
                if isinstance(value, (str, int, float, bool)):
                    success_criteria[key] = value
                else:
                    success_criteria[key] = str(value)
        else:
            success_criteria = {"task_complete": True}

        # Extract dependencies - ensure simple strings
        dependencies = []
        deps_raw = getattr(work_assignment, 'dependencies', [])
        for dep in deps_raw:
            if isinstance(dep, str):
                dependencies.append(dep)
            else:
                dependencies.append(str(dep))

        return TaskDefinition(
            task_id=work_assignment.task_id,
            name=work_assignment.task_name,
            description=work_assignment.description,
            task_type=TaskType.DEVELOPMENT,
            priority=priority,
            target_system=target_system,
            estimated_duration_minutes=getattr(work_assignment, 'estimated_duration_minutes', 60),
            thermal_safety_required=True,
            validation_checkpoints=[],
            dependencies=dependencies,
            expected_outputs=expected_outputs,
            success_criteria=success_criteria,
            created_timestamp=datetime.now().isoformat()
        )

    def process_overnight_queue(self, max_concurrent_tasks: int = 2) -> Dict[str, Any]:
        """
        Process overnight queue with validation-focused protocols

        Args:
            max_concurrent_tasks: Maximum concurrent task execution

        Returns:
            Dict with processing summary
        """
        self.logger.info("🌙 Starting overnight queue processing")

        processing_summary = {
            "start_time": datetime.now().isoformat(),
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "validation_blocks": 0,
            "thermal_safety_events": 0
        }

        try:
            # Get queued tasks ordered by priority
            queued_tasks = self._get_queued_tasks_by_priority()

            if not queued_tasks:
                self.logger.info("📝 No tasks in overnight queue")
                return processing_summary

            self.logger.info(f"📋 Processing {len(queued_tasks)} queued tasks")

            # Process tasks with concurrency control
            with ThreadPoolExecutor(max_workers=max_concurrent_tasks) as executor:
                future_to_task = {
                    executor.submit(self._process_single_task, task): task
                    for task in queued_tasks[:max_concurrent_tasks]
                }

                completed_count = 0
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    processing_summary["tasks_processed"] += 1

                    try:
                        result = future.result()
                        if result["success"]:
                            processing_summary["tasks_completed"] += 1
                        else:
                            processing_summary["tasks_failed"] += 1
                            if result.get("validation_blocked"):
                                processing_summary["validation_blocks"] += 1
                            if result.get("thermal_event"):
                                processing_summary["thermal_safety_events"] += 1

                    except Exception as e:
                        self.logger.error(f"❌ Task processing error: {e}")
                        processing_summary["tasks_failed"] += 1

                    completed_count += 1

                    # Queue next task if available
                    if completed_count < len(queued_tasks):
                        next_task = queued_tasks[completed_count + max_concurrent_tasks - 1]
                        if next_task:
                            future_to_task[executor.submit(self._process_single_task, next_task)] = next_task

            processing_summary["end_time"] = datetime.now().isoformat()
            processing_summary["total_duration_minutes"] = (
                datetime.fromisoformat(processing_summary["end_time"]) -
                datetime.fromisoformat(processing_summary["start_time"])
            ).total_seconds() / 60

            self.logger.info(f"🎯 Overnight processing complete: {processing_summary}")
            return processing_summary

        except Exception as e:
            self.logger.error(f"❌ Overnight processing failed: {e}")
            processing_summary["error"] = str(e)
            return processing_summary

    def _get_queued_tasks_by_priority(self) -> List[TaskDefinition]:
        """Get queued tasks ordered by priority and schedule"""
        tasks = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT td.*, te.status
                FROM task_definitions td
                JOIN task_executions te ON td.task_id = te.task_id
                WHERE te.status = ?
                ORDER BY td.priority ASC, td.created_timestamp ASC
            ''', (TaskStatus.QUEUED.value,))

            for row in cursor.fetchall():
                task_def = TaskDefinition(
                    task_id=row[0],
                    name=row[1],
                    description=row[2],
                    task_type=TaskType(row[3]),
                    priority=TaskPriority(row[4]),
                    target_system=SystemTarget(row[5]),
                    estimated_duration_minutes=row[6],
                    thermal_safety_required=bool(row[7]),
                    validation_checkpoints=[
                        ValidationCheckpoint(**cp)
                        for cp in json.loads(row[8])
                    ],
                    dependencies=json.loads(row[9]),
                    expected_outputs=json.loads(row[10]),
                    success_criteria=json.loads(row[11]),
                    created_timestamp=row[12],
                    scheduled_start=row[13]
                )
                tasks.append(task_def)

        return tasks

    def _process_single_task(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """
        Process a single task with validation checkpoints

        Args:
            task_def: Task definition to process

        Returns:
            Dict with processing results
        """
        result = {
            "task_id": task_def.task_id,
            "success": False,
            "validation_blocked": False,
            "thermal_event": False,
            "checkpoints_passed": 0,
            "outputs_generated": []
        }

        try:
            self.logger.info(f"🚀 Starting task: {task_def.task_id} - {task_def.name}")

            # Update task status to in_progress
            self._update_task_status(task_def.task_id, TaskStatus.IN_PROGRESS)

            # TEMPORARY: RAM upgrade constraint check
            if not self._check_ram_constraint(task_def):
                result["validation_blocked"] = True
                result["ram_constraint"] = True
                self.logger.warning(f"⚠️ RAM CONSTRAINT: Task {task_def.task_id} blocked - multi-speaker audio requires RAM upgrade")
                self._update_task_status(task_def.task_id, TaskStatus.DEFERRED)
                return result

            # Token budget constraint check
            token_check = self._check_token_budget(task_def)
            if not token_check["can_execute"]:
                result["validation_blocked"] = True
                result["token_constraint"] = True
                result["token_reason"] = token_check["reason"]
                result["adapted_estimate"] = token_check.get("adapted_estimate")
                self.logger.warning(f"⚠️ TOKEN CONSTRAINT: {token_check['reason']}")

                # Defer task if cannot adapt
                if token_check["adapted_estimate"] is None:
                    self._update_task_status(task_def.task_id, TaskStatus.DEFERRED)
                    return result
                else:
                    # Use adapted estimate for execution
                    self.logger.info(f"✅ ADAPTED: Using {token_check['adapted_estimate'].total:,} tokens (estimated)")
                    task_def.token_estimate = token_check["adapted_estimate"]

            # Pre-execution validation checkpoint
            if not self._execute_validation_checkpoint(task_def, "pre_execution"):
                result["validation_blocked"] = True
                self._update_task_status(task_def.task_id, TaskStatus.FAILED)
                return result

            # Thermal safety check if required
            if task_def.thermal_safety_required:
                if not self._thermal_safety_check():
                    result["thermal_event"] = True
                    self._update_task_status(task_def.task_id, TaskStatus.DEFERRED)
                    return result

            # Execute task with checkpoint validation
            execution_result = self._execute_task_with_validation(task_def)

            if execution_result["success"]:
                # Record actual token usage
                actual_tokens = execution_result.get("token_usage", {})
                if actual_tokens:
                    input_tokens = actual_tokens.get("input", 0)
                    output_tokens = actual_tokens.get("output", 0)
                    self.token_governor.record(input_tokens, output_tokens)
                elif hasattr(task_def, 'token_estimate'):
                    # Fallback: record estimate if no actual usage reported
                    estimate = task_def.token_estimate
                    self.token_governor.record(estimate.input_tokens, estimate.output_tokens)

                # Output validation checkpoint
                if self._execute_output_validation(task_def, execution_result["outputs"]):
                    result["success"] = True
                    result["outputs_generated"] = execution_result["outputs"]
                    self._update_task_status(task_def.task_id, TaskStatus.COMPLETED)
                else:
                    result["validation_blocked"] = True
                    self._update_task_status(task_def.task_id, TaskStatus.FAILED)
            else:
                self._update_task_status(task_def.task_id, TaskStatus.FAILED)

            return result

        except Exception as e:
            self.logger.error(f"❌ Task processing error for {task_def.task_id}: {e}")
            self._update_task_status(task_def.task_id, TaskStatus.FAILED)
            result["error"] = str(e)
            return result

    def _execute_validation_checkpoint(self, task_def: TaskDefinition, checkpoint_type: str) -> bool:
        """
        Execute validation checkpoint with statistical sampling

        Args:
            task_def: Task definition
            checkpoint_type: Type of checkpoint to execute

        Returns:
            bool: Validation success
        """
        try:
            # Find appropriate validation checkpoint
            checkpoint = None
            for cp in task_def.validation_checkpoints:
                if checkpoint_type in cp.checkpoint_id:
                    checkpoint = cp
                    break

            if not checkpoint:
                self.logger.info(f"📋 No {checkpoint_type} checkpoint for {task_def.task_id}")
                return True

            self.logger.info(f"🔍 Executing validation checkpoint: {checkpoint.name}")

            # Statistical sampling validation
            samples = self._generate_statistical_samples(task_def, checkpoint.sample_size)

            if not samples:
                self.logger.warning(f"⚠️ No samples generated for validation")
                return False

            # Validate samples
            validation_results = []
            for sample in samples:
                sample_result = self._validate_sample(sample, checkpoint)
                validation_results.append(sample_result)

            # Calculate validation metrics
            success_rate = len([r for r in validation_results if r.validation_success]) / len(validation_results)
            average_quality = sum(r.quality_score for r in validation_results) / len(validation_results)

            # Create validation report
            report = ValidationReport(
                task_id=task_def.task_id,
                checkpoint_id=checkpoint.checkpoint_id,
                timestamp=datetime.now().isoformat(),
                total_samples=len(validation_results),
                successful_samples=len([r for r in validation_results if r.validation_success]),
                average_quality_score=average_quality,
                success_rate=success_rate,
                processing_viability=success_rate >= checkpoint.quality_threshold,
                recommendations=self._generate_validation_recommendations(success_rate, average_quality),
                blocked_progression=not (success_rate >= checkpoint.quality_threshold)
            )

            # Store validation report
            self._store_validation_report(report)

            self.logger.info(f"📊 Validation results - Success rate: {success_rate:.1%}, Quality: {average_quality:.1%}")

            if report.blocked_progression and checkpoint.blocking:
                self.logger.error(f"🚨 BLOCKING VALIDATION FAILURE: {checkpoint.name}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"❌ Validation checkpoint error: {e}")
            return False

    def _generate_statistical_samples(self, task_def: TaskDefinition, sample_size: int) -> List[StatisticalSample]:
        """
        Generate statistical samples for validation (adapted from Sherlock)

        Args:
            task_def: Task definition
            sample_size: Number of samples to generate

        Returns:
            List of statistical samples
        """
        samples = []

        try:
            # Generate samples based on task type and expected inputs
            if task_def.task_type == TaskType.THROUGHPUT:
                # For throughput tasks, sample from input data
                samples = self._sample_throughput_inputs(task_def, sample_size)
            elif task_def.task_type == TaskType.DEVELOPMENT:
                # For development tasks, sample from test cases
                samples = self._sample_development_tests(task_def, sample_size)
            else:
                # For other tasks, generate synthetic samples
                samples = self._generate_synthetic_samples(task_def, sample_size)

        except Exception as e:
            self.logger.error(f"❌ Sample generation error: {e}")

        return samples

    def _validate_sample(self, sample: StatisticalSample, checkpoint: ValidationCheckpoint) -> StatisticalSample:
        """
        Validate a single sample against checkpoint criteria

        Args:
            sample: Sample to validate
            checkpoint: Validation checkpoint

        Returns:
            Updated sample with validation results
        """
        start_time = time.time()

        try:
            # Execute validation function based on checkpoint type
            if "format" in checkpoint.checkpoint_id:
                sample.validation_success = self._validate_format_compliance(sample)
            elif "processing" in checkpoint.checkpoint_id:
                sample.validation_success = self._validate_processing_capability(sample)
            elif "output" in checkpoint.checkpoint_id:
                sample.validation_success = self._validate_output_generation(sample)
            else:
                # Generic validation
                sample.validation_success = self._generic_sample_validation(sample)

            # Calculate quality score based on validation results
            sample.quality_score = self._calculate_sample_quality_score(sample)

        except Exception as e:
            sample.validation_success = False
            sample.error_message = str(e)
            sample.quality_score = 0.0

        sample.processing_time = time.time() - start_time
        return sample

    def _check_ram_constraint(self, task_def: TaskDefinition) -> bool:
        """
        TEMPORARY: Check RAM upgrade constraint

        Block multi-speaker audio (podcasts, interviews, youtube) until RAM upgrade.
        Allow: documents, books, single-speaker audio, visual media.

        Args:
            task_def: Task definition to check

        Returns:
            bool: True if allowed, False if blocked by RAM constraint
        """
        if not self.ram_upgrade_pending:
            return True  # RAM upgrade complete, all tasks allowed

        # Check task metadata for content type indicators
        task_name = task_def.name.lower()
        task_desc = task_def.description.lower()

        # Check if Sherlock research package
        if task_def.target_system == SystemTarget.SHERLOCK:
            # Load package metadata from queue file if exists
            queue_file = Path(f"/home/johnny5/Johny5Alive/queue/{task_def.task_id}.json")
            if queue_file.exists():
                with open(queue_file) as f:
                    pkg_data = json.load(f)
                    package_type = pkg_data.get('package_type', '').lower()

                    # Block multi-speaker audio types
                    if package_type in self.blocked_content_types:
                        self.logger.info(f"🚫 RAM CONSTRAINT: Blocking {package_type} package - requires RAM upgrade")
                        return False

                    # Explicitly allow document types
                    if package_type in ['document', 'book']:
                        return True

        # Check task name/description for blocked keywords
        blocked_keywords = ['podcast', 'interview', 'multi-speaker', 'youtube', 'video']
        for keyword in blocked_keywords:
            if keyword in task_name or keyword in task_desc:
                self.logger.info(f"🚫 RAM CONSTRAINT: Blocking task with '{keyword}' - requires RAM upgrade")
                return False

        # Allow by default (document/single-speaker content)
        return True

    def _check_token_budget(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """
        Check token budget and adapt task sizing if needed.

        Args:
            task_def: Task definition to check

        Returns:
            Dict with keys:
                - can_execute: bool
                - reason: str explaining decision
                - adapted_estimate: TokenEstimate if adapted, None if deferred
        """
        # Estimate token usage for task
        if task_def.target_system == SystemTarget.SHERLOCK:
            # Load package metadata
            queue_file = Path(f"/home/johnny5/Johny5Alive/queue/{task_def.task_id}.json")
            if queue_file.exists():
                with open(queue_file) as f:
                    pkg_data = json.load(f)
                    package_type = pkg_data.get('package_type', 'composite')
                    url_count = len(pkg_data.get('collection_urls', []))

                    estimate = self.token_governor.estimate_sherlock_task(
                        package_type=package_type,
                        url_count=url_count
                    )
            else:
                # Conservative fallback estimate
                estimate = self.token_governor.estimate_sherlock_task('composite', 2)

        elif task_def.target_system == SystemTarget.SQUIRT:
            # Estimate based on task duration (minutes)
            audio_minutes = task_def.estimated_duration_minutes
            estimate = self.token_governor.estimate_squirt_task(audio_minutes)

        else:
            # Generic estimate
            estimate = TokenEstimate(
                input_tokens=500,
                output_tokens=300,
                total=800,
                confidence=0.5
            )

        # Check if can run with current estimate
        if self.token_governor.can_run(estimate):
            return {
                "can_execute": True,
                "reason": f"Within budget: {estimate.total:,} tokens estimated",
                "adapted_estimate": estimate
            }

        # Try adaptation
        priority = task_def.priority.value if isinstance(task_def.priority, TaskPriority) else task_def.priority
        can_execute, reason, adapted_estimate = self.token_governor.adapt_or_defer(
            task_id=task_def.task_id,
            estimate=estimate,
            priority=priority
        )

        return {
            "can_execute": can_execute,
            "reason": reason,
            "adapted_estimate": adapted_estimate
        }

    def _thermal_safety_check(self) -> bool:
        """
        Thermal safety check integration

        Returns:
            bool: Safe to proceed
        """
        try:
            thermal_status = check_thermal_status()
            cpu_temp = thermal_status.get('cpu_temp', 0)

            if cpu_temp > self.quality_thresholds["max_thermal_temp"]:
                self.logger.warning(f"🔥 Thermal safety violation: {cpu_temp}°C > {self.quality_thresholds['max_thermal_temp']}°C")
                return False

            return True

        except Exception as e:
            self.logger.error(f"❌ Thermal safety check failed: {e}")
            return False

    def _execute_task_with_validation(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """
        Execute task with intermediate validation checkpoints

        Args:
            task_def: Task definition

        Returns:
            Dict with execution results
        """
        result = {
            "success": False,
            "outputs": [],
            "checkpoints_passed": 0,
            "performance_metrics": {}
        }

        try:
            start_time = time.time()

            # Route task to appropriate system
            if task_def.target_system == SystemTarget.SQUIRT:
                execution_result = self._execute_squirt_task(task_def)
            elif task_def.target_system == SystemTarget.SHERLOCK:
                execution_result = self._execute_sherlock_task(task_def)
            elif task_def.target_system == SystemTarget.J5A:
                execution_result = self._execute_j5a_task(task_def)
            else:
                execution_result = self._execute_multi_system_task(task_def)

            result.update(execution_result)
            result["performance_metrics"]["execution_time"] = time.time() - start_time

            return result

        except Exception as e:
            self.logger.error(f"❌ Task execution error: {e}")
            result["error"] = str(e)
            return result

    def _execute_output_validation(self, task_def: TaskDefinition, outputs: List[str]) -> bool:
        """
        Validate task outputs against expected deliverables

        Args:
            task_def: Task definition with expected outputs
            outputs: Generated output files

        Returns:
            bool: Output validation success
        """
        try:
            # Normalize paths for comparison (extract relative paths from absolute)
            expected_set = set()
            for exp_path in task_def.expected_outputs:
                # Expected paths are relative like "documents/file.txt"
                expected_set.add(Path(exp_path).as_posix())

            actual_set = set()
            for out_path in outputs:
                # Actual paths are absolute, extract the relative part
                # Match pattern: .../documents/file.txt -> documents/file.txt
                path_obj = Path(out_path)
                # Find where documents/, evidence/, or analysis/ starts
                parts = path_obj.parts
                for i, part in enumerate(parts):
                    if part in ['documents', 'evidence', 'analysis', 'research', 'timeline', 'network', 'entities']:
                        rel_path = '/'.join(parts[i:])
                        actual_set.add(rel_path)
                        break

            # Check output completeness
            missing_outputs = expected_set - actual_set
            completeness_rate = (len(expected_set) - len(missing_outputs)) / len(expected_set) if expected_set else 1.0

            if completeness_rate < self.quality_thresholds["min_output_completeness"]:
                self.logger.error(f"❌ Output validation failed: {completeness_rate:.1%} completeness")
                self.logger.error(f"Expected: {expected_set}")
                self.logger.error(f"Actual: {actual_set}")
                self.logger.error(f"Missing: {missing_outputs}")
                return False

            # Validate output file integrity
            for output_file in outputs:
                if not os.path.exists(output_file):
                    self.logger.error(f"❌ Output file missing: {output_file}")
                    return False

                if os.path.getsize(output_file) == 0:
                    self.logger.error(f"❌ Output file empty: {output_file}")
                    return False

            self.logger.info(f"✅ Output validation passed: {completeness_rate:.1%} completeness ({len(actual_set)} files)")
            return True

        except Exception as e:
            self.logger.error(f"❌ Output validation error: {e}")
            return False

    # Placeholder methods for system-specific task execution
    def _execute_squirt_task(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """Execute Squirt-specific task"""
        return {"success": True, "outputs": [], "system": "squirt"}

    def _execute_sherlock_task(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """
        Execute Sherlock research package.

        Args:
            task_def: Task definition with package metadata

        Returns:
            Dict with execution results and token usage
        """
        try:
            # Load package data from queue file
            queue_file = Path(f"/home/johnny5/Johny5Alive/queue/{task_def.task_id}.json")
            if not queue_file.exists():
                return {
                    "success": False,
                    "outputs": [],
                    "system": "sherlock",
                    "error": f"Package file not found: {queue_file}"
                }

            with open(queue_file) as f:
                package_data = json.load(f)

            # Execute research package
            self.logger.info(f"🔬 Executing Sherlock research: {package_data['target_name']}")
            result = self.sherlock_executor.execute_package(package_data)

            # Return in J5A format
            return {
                "success": result.success,
                "outputs": result.outputs_generated,
                "system": "sherlock",
                "token_usage": result.token_usage,
                "performance_metrics": {
                    "claims_extracted": result.claims_extracted,
                    "entities_found": result.entities_found,
                    "processing_time": result.processing_time
                },
                "error": result.error_message
            }

        except Exception as e:
            self.logger.error(f"❌ Sherlock execution error: {e}")
            return {
                "success": False,
                "outputs": [],
                "system": "sherlock",
                "error": str(e)
            }

    def _execute_j5a_task(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """Execute J5A-specific task"""
        return {"success": True, "outputs": [], "system": "j5a"}

    def _execute_multi_system_task(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """Execute multi-system coordination task"""
        return {"success": True, "outputs": [], "system": "multi_system"}

    # Additional helper methods would be implemented here...

    def _update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE task_executions
                    SET status = ?, end_time = ?
                    WHERE task_id = ?
                ''', (status.value, datetime.now().isoformat(), task_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Status update error: {e}")

    def _store_validation_report(self, report: ValidationReport):
        """Store validation report in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO validation_reports
                    (task_id, checkpoint_id, timestamp, total_samples, successful_samples,
                     average_quality_score, success_rate, processing_viability,
                     recommendations, blocked_progression)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.task_id,
                    report.checkpoint_id,
                    report.timestamp,
                    report.total_samples,
                    report.successful_samples,
                    report.average_quality_score,
                    report.success_rate,
                    report.processing_viability,
                    json.dumps(report.recommendations),
                    report.blocked_progression
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Validation report storage error: {e}")

    # Placeholder validation methods - would be fully implemented
    def _sample_throughput_inputs(self, task_def: TaskDefinition, sample_size: int) -> List[StatisticalSample]:
        return []

    def _sample_development_tests(self, task_def: TaskDefinition, sample_size: int) -> List[StatisticalSample]:
        return []

    def _generate_synthetic_samples(self, task_def: TaskDefinition, sample_size: int) -> List[StatisticalSample]:
        return []

    def _validate_format_compliance(self, sample: StatisticalSample) -> bool:
        return True

    def _validate_processing_capability(self, sample: StatisticalSample) -> bool:
        return True

    def _validate_output_generation(self, sample: StatisticalSample) -> bool:
        return True

    def _generic_sample_validation(self, sample: StatisticalSample) -> bool:
        return True

    def _calculate_sample_quality_score(self, sample: StatisticalSample) -> float:
        return 0.8

    def _generate_validation_recommendations(self, success_rate: float, quality_score: float) -> List[str]:
        return ["Validation completed successfully"]


if __name__ == "__main__":
    import argparse

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="J5A Overnight Queue/Batch Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import and process overnight queue
  python3 overnight_queue_manager.py --import-sherlock --import-plans --process-queue

  # Import Sherlock queue only
  python3 overnight_queue_manager.py --import-sherlock

  # Process existing queue without importing
  python3 overnight_queue_manager.py --process-queue

  # Full overnight automation (typical usage)
  python3 overnight_queue_manager.py --import-all --process-queue
        """
    )

    parser.add_argument(
        '--import-sherlock',
        action='store_true',
        help='Import Sherlock research packages from queue/ directory'
    )

    parser.add_argument(
        '--import-plans',
        action='store_true',
        help='Import development tasks from j5a_plans/ directory'
    )

    parser.add_argument(
        '--import-all',
        action='store_true',
        help='Import both Sherlock queue and J5A plans (equivalent to --import-sherlock --import-plans)'
    )

    parser.add_argument(
        '--process-queue',
        action='store_true',
        help='Process the overnight queue'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported/processed without making changes'
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any([args.import_sherlock, args.import_plans, args.import_all, args.process_queue]):
        parser.print_help()
        sys.exit(0)

    # Initialize manager
    manager = J5AOvernightQueueManager()

    # Import Sherlock queue
    if args.import_sherlock or args.import_all:
        print("\n" + "="*70)
        print("📥 IMPORTING SHERLOCK RESEARCH QUEUE")
        print("="*70)
        sherlock_summary = manager.import_sherlock_queue()
        print(f"\n📊 Sherlock Import Summary:")
        print(f"   Found: {sherlock_summary['total_found']}")
        print(f"   Imported: {sherlock_summary['imported']}")
        print(f"   Skipped: {sherlock_summary['skipped']}")
        print(f"   Errors: {len(sherlock_summary['errors'])}")
        if sherlock_summary['errors']:
            print(f"\n❌ Import Errors:")
            for error in sherlock_summary['errors']:
                print(f"   - {error}")

    # Import J5A plans
    if args.import_plans or args.import_all:
        print("\n" + "="*70)
        print("📥 IMPORTING J5A DEVELOPMENT PLANS")
        print("="*70)
        plans_summary = manager.import_j5a_plans()
        print(f"\n📊 J5A Plans Import Summary:")
        print(f"   Plans Found: {plans_summary['plans_found']}")
        print(f"   Tasks Imported: {plans_summary['tasks_imported']}")
        print(f"   Tasks Blocked: {plans_summary['tasks_blocked']}")
        print(f"   Errors: {len(plans_summary['errors'])}")
        if plans_summary['errors']:
            print(f"\n❌ Import Errors:")
            for error in plans_summary['errors']:
                print(f"   - {error}")

    # Process overnight queue
    if args.process_queue:
        print("\n" + "="*70)
        print("🌙 PROCESSING OVERNIGHT QUEUE")
        print("="*70)
        summary = manager.process_overnight_queue()
        print(f"\n📊 Processing Summary:")
        print(f"   Start: {summary.get('start_time', 'N/A')}")
        print(f"   Tasks Processed: {summary.get('tasks_processed', 0)}")
        print(f"   Tasks Completed: {summary.get('tasks_completed', 0)}")
        print(f"   Tasks Failed: {summary.get('tasks_failed', 0)}")
        print(f"   Validation Blocks: {summary.get('validation_blocks', 0)}")
        print(f"   Thermal Events: {summary.get('thermal_safety_events', 0)}")
        print(f"   End: {summary.get('end_time', 'N/A')}")
        print(f"   Duration: {summary.get('total_duration_minutes', 0):.2f} minutes")

    print("\n" + "="*70)
    print("✅ J5A OVERNIGHT QUEUE MANAGER - COMPLETE")
    print("="*70 + "\n")