#!/usr/bin/env python3
"""
J5A Plan Manager
Discovers, analyzes, and selects tasks from implementation plans for execution

Capabilities:
- Discover plans in j5a_plans/ directory
- Parse plan metadata
- Build dependency graphs
- Filter tasks by resource constraints
- Prioritize and order tasks for execution
- Track plan progress
"""

import json
import logging
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from j5a_work_assignment import J5AWorkAssignment, Priority, TaskStatus
from j5a_resource_manager import J5AResourceManager, TaskResourceEstimate


class PhaseStatus(Enum):
    """Phase execution status"""
    READY = "ready"
    WAITING = "waiting"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class PlanMetadata:
    """Parsed plan metadata"""
    plan_name: str
    plan_version: str
    project: str
    metadata_path: Path
    python_module_path: Path
    phases: List[Dict]
    current_status: Dict
    hardware_requirements: Dict
    blocking_conditions: List[str]


class J5APlanManager:
    """
    Manages implementation plans and task selection

    Discovers plans, builds dependency graphs, filters by constraints,
    and provides ordered task lists for execution.
    """

    def __init__(self, plans_dir: Optional[Path] = None, resource_manager: Optional[J5AResourceManager] = None):
        self.logger = logging.getLogger("J5APlanManager")
        self.plans_dir = plans_dir or Path("j5a_plans")
        self.resource_manager = resource_manager or J5AResourceManager()

        # Discovered plans
        self.plans: Dict[str, PlanMetadata] = {}

        # Task cache
        self.all_tasks: Dict[str, J5AWorkAssignment] = {}

        self.logger.info(f"📋 J5A Plan Manager initialized")
        self.logger.info(f"   Plans directory: {self.plans_dir}")

    def discover_plans(self) -> List[PlanMetadata]:
        """
        Discover all plans in plans directory

        Returns:
            List of discovered plan metadata
        """
        if not self.plans_dir.exists():
            self.logger.warning(f"Plans directory does not exist: {self.plans_dir}")
            return []

        self.plans.clear()

        # Find all metadata JSON files
        metadata_files = list(self.plans_dir.glob("*_metadata.json"))

        for metadata_path in metadata_files:
            try:
                plan = self._load_plan_metadata(metadata_path)
                if plan:
                    self.plans[plan.plan_name] = plan
                    self.logger.info(f"✅ Discovered plan: {plan.plan_name}")

            except Exception as e:
                self.logger.error(f"Failed to load plan {metadata_path}: {e}")

        self.logger.info(f"📊 Total plans discovered: {len(self.plans)}")
        return list(self.plans.values())

    def _load_plan_metadata(self, metadata_path: Path) -> Optional[PlanMetadata]:
        """Load and parse plan metadata file"""
        with open(metadata_path, 'r') as f:
            data = json.load(f)

        # Find corresponding Python module
        base_name = metadata_path.stem.replace("_metadata", "")
        python_module_path = metadata_path.parent / f"{base_name}_tasks.py"

        if not python_module_path.exists():
            self.logger.error(f"Python module not found: {python_module_path}")
            return None

        return PlanMetadata(
            plan_name=data["plan_name"],
            plan_version=data["plan_version"],
            project=data["project"],
            metadata_path=metadata_path,
            python_module_path=python_module_path,
            phases=data["phases"],
            current_status=data["current_status"],
            hardware_requirements=data.get("hardware_requirements", {}),
            blocking_conditions=self._extract_blocking_conditions(data)
        )

    def _extract_blocking_conditions(self, data: Dict) -> List[str]:
        """Extract plan-level blocking conditions (not phase-level)"""
        # Only return plan-level blocking conditions
        # Phase-level blocking is handled during phase filtering
        return data.get("blocking_conditions", [])

    def load_plan_tasks(self, plan_name: str) -> List[J5AWorkAssignment]:
        """
        Load all tasks from a specific plan

        Args:
            plan_name: Name of the plan to load

        Returns:
            List of J5AWorkAssignment objects
        """
        if plan_name not in self.plans:
            self.logger.error(f"Plan not found: {plan_name}")
            return []

        plan = self.plans[plan_name]

        try:
            # Dynamically import the Python module
            spec = importlib.util.spec_from_file_location(
                plan.python_module_path.stem,
                plan.python_module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Call the create function (assumes create_phase*_tasks() naming)
            if hasattr(module, 'create_phase1_tasks'):
                tasks = module.create_phase1_tasks()
            elif hasattr(module, 'create_tasks'):
                tasks = module.create_tasks()
            else:
                self.logger.error(f"No task creation function found in {plan.python_module_path}")
                return []

            # Cache tasks
            for task in tasks:
                self.all_tasks[task.task_id] = task

            self.logger.info(f"✅ Loaded {len(tasks)} tasks from {plan_name}")
            return tasks

        except Exception as e:
            self.logger.error(f"Failed to load tasks from {plan_name}: {e}")
            return []

    def get_executable_tasks(self,
                            max_tokens: Optional[int] = None,
                            max_ram_gb: Optional[float] = None,
                            thermal_state: Optional[str] = None,
                            plan_filter: Optional[str] = None) -> List[J5AWorkAssignment]:
        """
        Get filtered and ordered list of executable tasks

        Filters by:
        - Resource constraints (tokens, RAM, thermal)
        - Blocking conditions
        - Dependencies
        - Phase status

        Args:
            max_tokens: Maximum tokens available
            max_ram_gb: Maximum RAM available (GB)
            thermal_state: Current thermal state
            plan_filter: Only include tasks from this plan

        Returns:
            Ordered list of tasks ready for execution
        """
        if not self.plans:
            self.discover_plans()

        executable = []

        for plan_name, plan in self.plans.items():
            if plan_filter and plan_name != plan_filter:
                continue

            # Check plan-level blocking conditions (only at plan level, not phase level)
            if plan.blocking_conditions:
                self.logger.info(f"⏸️  Plan '{plan_name}' has blocking conditions:")
                for condition in plan.blocking_conditions:
                    self.logger.info(f"   - {condition}")
                continue

            self.logger.info(f"🔍 Processing plan: {plan_name}")

            # Load tasks if not already loaded
            if not any(task.task_id.startswith(plan.project) for task in self.all_tasks.values()):
                self.load_plan_tasks(plan_name)

            # Get tasks for each ready phase
            for phase in plan.phases:
                if phase["status"] not in ["ready", "in_progress"]:
                    continue

                # Check phase dependencies
                if not self._phase_dependencies_satisfied(phase, plan):
                    continue

                # Get tasks from phase
                phase_tasks = self._get_phase_tasks(phase, plan_name)

                # Filter by dependencies
                phase_tasks = self._filter_by_dependencies(phase_tasks)

                # Filter by resources
                if max_tokens or max_ram_gb or thermal_state:
                    phase_tasks = self._filter_by_resources(
                        phase_tasks,
                        max_tokens,
                        max_ram_gb,
                        thermal_state
                    )

                executable.extend(phase_tasks)

        # Order tasks by priority and dependencies
        ordered = self._order_tasks(executable)

        self.logger.info(f"📊 Executable tasks: {len(ordered)}")
        return ordered

    def _phase_dependencies_satisfied(self, phase: Dict, plan: PlanMetadata) -> bool:
        """Check if phase dependencies are satisfied"""
        dependencies = phase.get("dependencies", [])

        if not dependencies:
            return True

        # Check if dependent phases are completed
        for dep_phase_id in dependencies:
            status = plan.current_status.get(dep_phase_id, "waiting")
            if status != "completed":
                return False

        return True

    def _get_phase_tasks(self, phase: Dict, plan_name: str) -> List[J5AWorkAssignment]:
        """Get tasks from a specific phase"""
        phase_task_ids = [task["task_id"] for task in phase.get("tasks", [])]

        tasks = []
        for task_id in phase_task_ids:
            if task_id in self.all_tasks:
                task = self.all_tasks[task_id]
                # Update task with metadata estimates
                self._enrich_task_with_metadata(task, phase)
                tasks.append(task)

        return tasks

    def _enrich_task_with_metadata(self, task: J5AWorkAssignment, phase: Dict):
        """Add metadata resource estimates to task"""
        # Find task metadata
        task_meta = next(
            (t for t in phase.get("tasks", []) if t["task_id"] == task.task_id),
            None
        )

        if task_meta:
            # Register resource estimate with resource manager
            self.resource_manager.allocate_task_resources(
                task.task_id,
                TaskResourceEstimate(
                    task_id=task.task_id,
                    estimated_tokens=task_meta.get("estimated_tokens", 5000),
                    estimated_ram_gb=task_meta.get("estimated_ram_gb", 0.5),
                    estimated_duration_minutes=task_meta.get("estimated_duration_minutes", 10),
                    thermal_risk=task_meta.get("thermal_risk", "low")
                )
            )

    def _filter_by_dependencies(self, tasks: List[J5AWorkAssignment]) -> List[J5AWorkAssignment]:
        """Filter out tasks with unsatisfied dependencies"""
        # For now, simple implementation - return all
        # Future: build dependency graph and filter
        return tasks

    def _filter_by_resources(self,
                            tasks: List[J5AWorkAssignment],
                            max_tokens: Optional[int],
                            max_ram_gb: Optional[float],
                            thermal_state: Optional[str]) -> List[J5AWorkAssignment]:
        """Filter tasks by resource constraints"""
        filtered = []

        for task in tasks:
            # Check if task can execute with current resources
            can_execute, reason = self.resource_manager.can_execute_task(task.task_id)

            if can_execute:
                filtered.append(task)
            else:
                self.logger.debug(f"Filtering out {task.task_id}: {reason}")

        return filtered

    def _order_tasks(self, tasks: List[J5AWorkAssignment]) -> List[J5AWorkAssignment]:
        """
        Order tasks by priority and dependencies

        Scoring:
        - CRITICAL: 100
        - HIGH: 75
        - NORMAL: 50
        - LOW: 25
        """
        priority_scores = {
            Priority.CRITICAL: 100,
            Priority.HIGH: 75,
            Priority.NORMAL: 50,
            Priority.LOW: 25
        }

        def score_task(task: J5AWorkAssignment) -> int:
            base_score = priority_scores.get(task.priority, 50)

            # Boost foundation tasks (no dependencies)
            # (Future: check actual dependencies)

            return base_score

        tasks.sort(key=score_task, reverse=True)
        return tasks

    def get_plan_summary(self) -> Dict:
        """Get summary of all discovered plans"""
        summary = {
            "total_plans": len(self.plans),
            "plans": []
        }

        for plan_name, plan in self.plans.items():
            plan_summary = {
                "name": plan.plan_name,
                "project": plan.project,
                "version": plan.plan_version,
                "phases": len(plan.phases),
                "status": plan.current_status,
                "blocking_conditions": plan.blocking_conditions
            }
            summary["plans"].append(plan_summary)

        return summary

    def update_plan_status(self, plan_name: str, completed_tasks: List[str], failed_tasks: List[str]):
        """Update plan metadata with execution results"""
        if plan_name not in self.plans:
            return

        plan = self.plans[plan_name]

        # Load current metadata
        with open(plan.metadata_path, 'r') as f:
            data = json.load(f)

        # Update execution history
        if "execution_history" not in data:
            data["execution_history"] = []

        data["execution_history"].append({
            "date": datetime.now().isoformat(),
            "tasks_completed": completed_tasks,
            "tasks_failed": failed_tasks
        })

        # Update current status
        data["current_status"]["tasks_completed"].extend(completed_tasks)
        data["current_status"]["tasks_failed"].extend(failed_tasks)

        # Calculate progress
        total_tasks = sum(len(phase.get("tasks", [])) for phase in data["phases"])
        completed_count = len(data["current_status"]["tasks_completed"])
        progress = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        data["current_status"]["overall_progress"] = f"{progress:.1f}%"

        # Update last execution
        data["current_status"]["last_execution"] = datetime.now().isoformat()

        # Save updated metadata
        with open(plan.metadata_path, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"📊 Updated plan status: {plan_name} ({progress:.1f}% complete)")


if __name__ == "__main__":
    """Test plan manager"""
    import logging
    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing J5A Plan Manager")
    print("=" * 80)

    # Create plan manager
    plan_manager = J5APlanManager()

    # Discover plans
    print("\n📋 Discovering plans...")
    plans = plan_manager.discover_plans()

    if plans:
        print(f"✅ Found {len(plans)} plan(s)")

        # Get plan summary
        summary = plan_manager.get_plan_summary()
        print("\n📊 Plan Summary:")
        print(json.dumps(summary, indent=2))

        # Get executable tasks
        print("\n🎯 Getting executable tasks...")
        executable_tasks = plan_manager.get_executable_tasks()

        print(f"\n✅ Found {len(executable_tasks)} executable tasks:")
        for i, task in enumerate(executable_tasks, 1):
            print(f"   {i}. {task.task_id}: {task.task_name}")
            print(f"      Priority: {task.priority.name}")

    else:
        print("❌ No plans discovered")

    print("\n" + "=" * 80)
    print("✅ Plan manager test complete")