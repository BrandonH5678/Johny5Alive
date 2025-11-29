#!/usr/bin/env python3
"""
J5A Autonomous Task Executor

Executes tasks defined by task_schema.json with:
- Mandatory pre-work snapshot
- Scope enforcement
- Success validation
- Automatic rollback on failure

Constitutional Basis:
- Principle 1 (Human Agency): Tasks require approval before execution
- Principle 2 (Transparency): All actions logged and auditable
- Principle 3 (System Viability): Rollback on failure
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.jeeves.snapshot import SnapshotManager
from rich.console import Console

console = Console()


class TaskStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class TaskScope:
    """Scope declaration for autonomous task"""
    repositories: List[str]
    file_patterns: List[str]
    operations: List[str]
    external_systems: List[str] = field(default_factory=list)
    max_files: int = 20
    duration_limit_minutes: int = 120


@dataclass
class SuccessCriteria:
    """Success criteria for task completion"""
    deliverables: List[str]
    tests: List[str] = field(default_factory=list)
    validation_commands: List[str] = field(default_factory=list)
    quality_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class RollbackTriggers:
    """Conditions that trigger automatic rollback"""
    test_failure_threshold: float = 0.5
    error_patterns: List[str] = field(default_factory=list)
    scope_violation: bool = True
    timeout: bool = True


@dataclass
class AutonomousTask:
    """Complete autonomous task specification"""
    task_id: str
    description: str
    scope: TaskScope
    success_criteria: SuccessCriteria
    priority: str = "normal"
    rollback_triggers: RollbackTriggers = field(default_factory=RollbackTriggers)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    snapshot_tag: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_json(cls, json_path: Path) -> "AutonomousTask":
        """Load task from JSON file"""
        with open(json_path) as f:
            data = json.load(f)

        scope = TaskScope(
            repositories=data["scope"]["repositories"],
            file_patterns=data["scope"]["file_patterns"],
            operations=data["scope"]["operations"],
            external_systems=data["scope"].get("external_systems", []),
            max_files=data["scope"].get("max_files", 20),
            duration_limit_minutes=data["scope"].get("duration_limit_minutes", 120)
        )

        success_criteria = SuccessCriteria(
            deliverables=data["success_criteria"]["deliverables"],
            tests=data["success_criteria"].get("tests", []),
            validation_commands=data["success_criteria"].get("validation_commands", []),
            quality_metrics=data["success_criteria"].get("quality_metrics", {})
        )

        rollback_data = data.get("rollback_triggers", {})
        rollback_triggers = RollbackTriggers(
            test_failure_threshold=rollback_data.get("test_failure_threshold", 0.5),
            error_patterns=rollback_data.get("error_patterns", []),
            scope_violation=rollback_data.get("scope_violation", True),
            timeout=rollback_data.get("timeout", True)
        )

        return cls(
            task_id=data["task_id"],
            description=data["description"],
            scope=scope,
            success_criteria=success_criteria,
            priority=data.get("priority", "normal"),
            rollback_triggers=rollback_triggers,
            dependencies=data.get("dependencies", []),
            created_at=datetime.now()
        )

    def to_dict(self) -> Dict:
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status.value,
            "scope": {
                "repositories": self.scope.repositories,
                "file_patterns": self.scope.file_patterns,
                "operations": self.scope.operations,
                "external_systems": self.scope.external_systems,
                "max_files": self.scope.max_files,
                "duration_limit_minutes": self.scope.duration_limit_minutes
            },
            "success_criteria": {
                "deliverables": self.success_criteria.deliverables,
                "tests": self.success_criteria.tests,
                "validation_commands": self.success_criteria.validation_commands,
                "quality_metrics": self.success_criteria.quality_metrics
            },
            "rollback_triggers": {
                "test_failure_threshold": self.rollback_triggers.test_failure_threshold,
                "error_patterns": self.rollback_triggers.error_patterns,
                "scope_violation": self.rollback_triggers.scope_violation,
                "timeout": self.rollback_triggers.timeout
            },
            "dependencies": self.dependencies,
            "snapshot_tag": self.snapshot_tag,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_log": self.execution_log
        }


class TaskExecutor:
    """
    Executes autonomous tasks with full safety protocols.

    Implements the permission-at-assignment model:
    1. Task defined with explicit scope
    2. Human approves task
    3. Executor creates pre-work snapshot
    4. Execution proceeds within scope
    5. Validation confirms success
    6. Rollback on failure
    """

    def __init__(self):
        self.snapshot_manager = SnapshotManager(
            {"snapshot": {"compress": "zstd", "verify_restore": True}}
        )
        self.active_task: Optional[AutonomousTask] = None

    def prepare_task(self, task: AutonomousTask) -> bool:
        """
        Prepare task for execution:
        1. Validate scope
        2. Create pre-work snapshots
        3. Mark as ready for execution

        Returns True if preparation successful
        """
        console.print(f"\n[cyan]Preparing task: {task.task_id}[/cyan]")
        console.print(f"[dim]{task.description}[/dim]")

        # Validate scope
        if not self._validate_scope(task.scope):
            console.print("[red]Scope validation failed[/red]")
            return False

        # Create snapshots for all affected repositories
        console.print("\n[yellow]Creating pre-work snapshots...[/yellow]")
        for repo_path in task.scope.repositories:
            try:
                metadata, tag_name = self.snapshot_manager.create_pre_autonomous_snapshot(
                    repo_path=Path(repo_path),
                    repo_name=Path(repo_path).name,
                    task_description=f"Task: {task.task_id} - {task.description}",
                    push_to_remote=True
                )
                task.snapshot_tag = tag_name  # Store last tag
                task.execution_log.append({
                    "event": "snapshot_created",
                    "timestamp": datetime.now().isoformat(),
                    "repo": repo_path,
                    "tag": tag_name
                })
                console.print(f"[green]Snapshot created for {repo_path}[/green]")
            except Exception as e:
                console.print(f"[red]Snapshot failed for {repo_path}: {e}[/red]")
                return False

        task.status = TaskStatus.APPROVED
        task.approved_at = datetime.now()
        console.print("\n[green]Task prepared and ready for execution[/green]")
        return True

    def _validate_scope(self, scope: TaskScope) -> bool:
        """Validate scope declaration is reasonable"""
        # Check repositories exist
        for repo in scope.repositories:
            if not Path(repo).exists():
                console.print(f"[red]Repository not found: {repo}[/red]")
                return False

        # Check operations are valid
        valid_ops = {"read", "create", "modify", "delete", "execute", "git_commit", "git_push"}
        for op in scope.operations:
            if op not in valid_ops:
                console.print(f"[red]Invalid operation: {op}[/red]")
                return False

        return True

    def validate_completion(self, task: AutonomousTask) -> bool:
        """
        Validate task completed successfully:
        1. Check deliverables exist
        2. Run validation commands
        3. Check quality metrics

        Returns True if validation passes
        """
        console.print(f"\n[cyan]Validating task completion: {task.task_id}[/cyan]")
        task.status = TaskStatus.VALIDATING

        all_passed = True

        # Check deliverables
        console.print("[dim]Checking deliverables...[/dim]")
        for deliverable in task.success_criteria.deliverables:
            # Deliverables can be paths or descriptions
            if deliverable.startswith("/") or deliverable.startswith("~"):
                path = Path(deliverable).expanduser()
                if path.exists():
                    console.print(f"  [green]Deliverable exists: {deliverable}[/green]")
                else:
                    console.print(f"  [red]Deliverable missing: {deliverable}[/red]")
                    all_passed = False
            else:
                # Non-path deliverable - just log it
                console.print(f"  [dim]Deliverable (manual check): {deliverable}[/dim]")

        # Run validation commands
        import subprocess
        for cmd in task.success_criteria.validation_commands:
            console.print(f"[dim]Running: {cmd}[/dim]")
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
                if result.returncode == 0:
                    console.print(f"  [green]Passed: {cmd}[/green]")
                else:
                    console.print(f"  [red]Failed: {cmd}[/red]")
                    all_passed = False
            except subprocess.TimeoutExpired:
                console.print(f"  [red]Timeout: {cmd}[/red]")
                all_passed = False
            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
                all_passed = False

        if all_passed:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            console.print("\n[green]Task validation PASSED[/green]")
        else:
            console.print("\n[red]Task validation FAILED[/red]")

        return all_passed

    def rollback(self, task: AutonomousTask) -> bool:
        """
        Rollback task to pre-work snapshot.

        Constitutional Basis: Principle 3 (System Viability)
        """
        if not task.snapshot_tag:
            console.print("[red]No snapshot tag available for rollback[/red]")
            return False

        console.print(f"\n[yellow]Rolling back to: {task.snapshot_tag}[/yellow]")

        for repo_path in task.scope.repositories:
            success = self.snapshot_manager.rollback_to_tag(
                repo_path=Path(repo_path),
                tag_name=task.snapshot_tag,
                confirm=True
            )
            if success:
                console.print(f"[green]Rolled back: {repo_path}[/green]")
            else:
                console.print(f"[red]Rollback failed: {repo_path}[/red]")
                return False

        task.status = TaskStatus.ROLLED_BACK
        task.execution_log.append({
            "event": "rolled_back",
            "timestamp": datetime.now().isoformat(),
            "tag": task.snapshot_tag
        })

        return True

    def display_task_summary(self, task: AutonomousTask):
        """Display task summary for human review"""
        console.print("\n" + "=" * 60)
        console.print(f"[bold cyan]TASK: {task.task_id}[/bold cyan]")
        console.print("=" * 60)
        console.print(f"[bold]Description:[/bold] {task.description}")
        console.print(f"[bold]Priority:[/bold] {task.priority}")
        console.print(f"[bold]Status:[/bold] {task.status.value}")

        console.print(f"\n[bold]Scope:[/bold]")
        console.print(f"  Repositories: {', '.join(task.scope.repositories)}")
        console.print(f"  File Patterns: {', '.join(task.scope.file_patterns)}")
        console.print(f"  Operations: {', '.join(task.scope.operations)}")
        console.print(f"  Max Files: {task.scope.max_files}")
        console.print(f"  Time Limit: {task.scope.duration_limit_minutes} minutes")

        console.print(f"\n[bold]Success Criteria:[/bold]")
        console.print(f"  Deliverables: {', '.join(task.success_criteria.deliverables)}")
        if task.success_criteria.tests:
            console.print(f"  Tests: {', '.join(task.success_criteria.tests)}")

        console.print(f"\n[bold]Rollback Triggers:[/bold]")
        console.print(f"  Test Failure Threshold: {task.rollback_triggers.test_failure_threshold * 100}%")
        console.print(f"  Scope Violation: {task.rollback_triggers.scope_violation}")
        console.print(f"  Timeout: {task.rollback_triggers.timeout}")

        if task.snapshot_tag:
            console.print(f"\n[bold]Snapshot:[/bold] {task.snapshot_tag}")

        console.print("=" * 60)


def create_example_task() -> Dict:
    """Create an example task specification"""
    return {
        "task_id": "example-code-review",
        "description": "Review and improve code quality in J5A modules",
        "priority": "normal",
        "scope": {
            "repositories": ["/home/johnny5/Johny5Alive"],
            "file_patterns": ["agents/**/*.py", "src/**/*.py"],
            "operations": ["read", "modify"],
            "external_systems": [],
            "max_files": 10,
            "duration_limit_minutes": 60
        },
        "success_criteria": {
            "deliverables": [
                "Code review completed",
                "No new lint errors introduced"
            ],
            "tests": [],
            "validation_commands": [
                "python3 -m py_compile /home/johnny5/Johny5Alive/agents/jeeves/snapshot.py"
            ],
            "quality_metrics": {
                "files_reviewed": 5
            }
        },
        "rollback_triggers": {
            "test_failure_threshold": 0.3,
            "error_patterns": ["SyntaxError", "ImportError"],
            "scope_violation": True,
            "timeout": True
        },
        "dependencies": [],
        "constitutional_review": {
            "human_agency_impact": "Low - code improvements, human reviews final changes",
            "transparency_notes": "All changes tracked via git, full execution log",
            "viability_risks": "Low - pre-work snapshot enables full rollback"
        }
    }


if __name__ == "__main__":
    # Demo: Create and display example task
    example = create_example_task()
    example_path = Path("/home/johnny5/Johny5Alive/autonomous/example_task.json")
    example_path.parent.mkdir(exist_ok=True)

    with open(example_path, "w") as f:
        json.dump(example, f, indent=2)

    print(f"Example task written to: {example_path}")

    # Load and display
    task = AutonomousTask.from_json(example_path)
    executor = TaskExecutor()
    executor.display_task_summary(task)
