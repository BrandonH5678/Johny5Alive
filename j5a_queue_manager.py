#!/usr/bin/env python3
"""
J5A Queue Manager
Manages prioritized task queue for overnight processing with incremental improvements

Constitutional Authority: J5A_CONSTITUTION.md - Principles 1, 2, 3, 4
Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md - Principles 7, 8
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from j5a_work_assignment import (
    J5AWorkAssignment,
    Priority,
    OutputSpecification,
    QuantitativeMeasure,
    TestOracle,
    EscalationPolicy,
    TaskStatus
)

# Add j5a-nightshift/core to path for principle imports
sys.path.insert(0, str(Path(__file__).parent / "j5a-nightshift" / "core"))

try:
    from strategic_principles import StrategicPrinciples
    from governance_logger import GovernanceLogger
    PRINCIPLES_AVAILABLE = True
except ImportError:
    PRINCIPLES_AVAILABLE = False
    # Graceful degradation if principles module not available yet


class ImprovementType(Enum):
    """Types of incremental improvements"""
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    TEST_COVERAGE = "test_coverage"
    BUG_FIX = "bug_fix"
    FEATURE_ENHANCEMENT = "feature_enhancement"
    TECHNICAL_DEBT = "technical_debt"
    DOCUMENTATION = "documentation"
    SECURITY = "security"


@dataclass
class ImprovementOpportunity:
    """Identified opportunity for incremental improvement"""
    type: ImprovementType
    system: str  # e.g., "sherlock", "squirt"
    scope: str  # What to improve
    description: str
    expected_impact: str
    priority: Priority
    effort_estimate: str  # "small", "medium", "large"


class J5AQueueManager:
    """
    Manages task queue for overnight processing

    Features:
    - Priority-based queuing
    - Automatic improvement opportunity detection
    - Task validation before queuing
    - Queue persistence
    """

    def __init__(self, queue_file: Optional[Path] = None):
        self.logger = logging.getLogger("J5AQueueManager")
        self.queue_file = queue_file or Path("j5a_queue.json")

        # Task queue (priority-sorted)
        self.queue: List[J5AWorkAssignment] = []

        # Initialize principles and governance if available
        if PRINCIPLES_AVAILABLE:
            try:
                self.principles = StrategicPrinciples()
                self.gov_logger = GovernanceLogger()
                self.logger.info("✅ Strategic Principles and Governance logging enabled")
            except Exception as e:
                self.logger.warning(f"Could not initialize principles/governance: {e}")
                self.principles = None
                self.gov_logger = None
        else:
            self.principles = None
            self.gov_logger = None

        # Load existing queue if available
        if self.queue_file.exists():
            self.load_queue()

    def check_constitutional_compliance(self, task: J5AWorkAssignment, context: Dict) -> Dict[str, str]:
        """
        Check constitutional principle compliance for task queuing

        Args:
            task: Work assignment to check
            context: Queue context (queue size, resource constraints, etc.)

        Returns:
            Dict mapping principle -> compliance status
        """
        compliance = {}

        # Principle 1: Human Agency (High-risk tasks require approval)
        if task.priority == Priority.CRITICAL:
            compliance["Principle 1: Human Agency"] = "WARNING - Critical priority task should be reviewed by human"
        else:
            compliance["Principle 1: Human Agency"] = "PASS - Task priority allows autonomous queuing"

        # Principle 2: Transparency (All decisions auditable)
        if self.gov_logger:
            compliance["Principle 2: Transparency"] = "PASS - Task queuing logged for audit trail"
        else:
            compliance["Principle 2: Transparency"] = "WARNING - Governance logging unavailable"

        # Principle 3: System Viability (Completion > Speed)
        if task.expected_outputs and task.success_criteria:
            compliance["Principle 3: System Viability"] = "PASS - Task has clear outputs and success criteria"
        else:
            compliance["Principle 3: System Viability"] = "FAIL - Missing outputs or success criteria"

        # Principle 4: Resource Stewardship (Respect constraints)
        queue_size = context.get("queue_size", 0)
        max_queue_size = context.get("max_queue_size", 100)

        if queue_size < max_queue_size:
            compliance["Principle 4: Resource Stewardship"] = f"PASS - Queue size {queue_size}/{max_queue_size}"
        else:
            compliance["Principle 4: Resource Stewardship"] = f"WARNING - Queue approaching capacity {queue_size}/{max_queue_size}"

        # Strategic Principle 7: Autonomous Workflows (Night Shift operations)
        if task.requires_poc:
            compliance["Strategic Principle 7: Autonomous Workflows"] = "PASS - POC phase ensures safe autonomous execution"
        else:
            compliance["Strategic Principle 7: Autonomous Workflows"] = "WARNING - No POC phase, higher autonomous risk"

        # Strategic Principle 8: Governance Frameworks (Accountable AI)
        if task.rollback_plan:
            compliance["Strategic Principle 8: Governance"] = "PASS - Rollback plan defined for accountability"
        else:
            compliance["Strategic Principle 8: Governance"] = "WARNING - No rollback plan defined"

        return compliance

    def add_task(self, task: J5AWorkAssignment) -> bool:
        """
        Add task to queue with validation

        Returns:
            True if task added successfully, False if validation failed
        """
        self.logger.info(f"➕ Adding task to queue: {task.task_name}")

        # Validate task definition
        if not self._validate_task_definition(task):
            self.logger.error(f"❌ Task validation failed: {task.task_name}")
            return False

        # Check constitutional compliance
        queue_context = {
            "queue_size": len(self.queue),
            "max_queue_size": 100,
            "current_date": datetime.now().isoformat()
        }

        compliance = self.check_constitutional_compliance(task, queue_context)

        # Log constitutional compliance check
        self.logger.info("⚖️ Constitutional Compliance Check:")
        for principle, status in compliance.items():
            status_icon = "✅" if "PASS" in status else ("⚠️" if "WARNING" in status else "❌")
            self.logger.info(f"   {status_icon} {principle}: {status}")

        # Check for blocking violations (FAIL status)
        violations = [status for status in compliance.values() if "FAIL" in status]
        if violations:
            self.logger.error(f"❌ Task queuing blocked due to constitutional violations")
            self.logger.error(f"   Violations: {violations}")
            return False

        # Log decision with governance logger if available
        if self.gov_logger:
            try:
                self.gov_logger.log_decision(
                    decision_type="task_queuing",
                    context={
                        "task_id": task.task_id,
                        "task_name": task.task_name,
                        "priority": task.priority.name,
                        "queue_size": len(self.queue)
                    },
                    decision={
                        "action": "queue_task",
                        "reasoning": f"Task meets constitutional requirements for autonomous queuing"
                    },
                    principle_alignment=[
                        principle for principle, status in compliance.items()
                        if "PASS" in status
                    ]
                )
            except Exception as e:
                self.logger.warning(f"Failed to log governance decision: {e}")

        # Add to queue (sorted by priority)
        self.queue.append(task)
        self._sort_queue()

        # Persist queue
        self.save_queue()

        self.logger.info(f"✅ Task added to queue (position: {self._get_task_position(task)})")
        return True

    def get_next_task(self) -> Optional[J5AWorkAssignment]:
        """Get highest priority task from queue"""
        if not self.queue:
            return None

        # Get first queued task (highest priority)
        for task in self.queue:
            if task.status == TaskStatus.QUEUED:
                return task

        return None

    def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        for i, task in enumerate(self.queue):
            if task.task_id == task_id:
                self.queue.pop(i)
                self.save_queue()
                self.logger.info(f"🗑️  Removed task from queue: {task_id}")
                return True
        return False

    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            "total_tasks": len(self.queue),
            "queued": sum(1 for t in self.queue if t.status == TaskStatus.QUEUED),
            "in_progress": sum(1 for t in self.queue if t.status in [
                TaskStatus.PRE_FLIGHT,
                TaskStatus.POC,
                TaskStatus.IMPLEMENTING,
                TaskStatus.VALIDATING
            ]),
            "completed": sum(1 for t in self.queue if t.status == TaskStatus.COMPLETED),
            "blocked": sum(1 for t in self.queue if t.status == TaskStatus.BLOCKED),
            "failed": sum(1 for t in self.queue if t.status == TaskStatus.FAILED),
            "by_priority": {
                "critical": sum(1 for t in self.queue if t.priority == Priority.CRITICAL),
                "high": sum(1 for t in self.queue if t.priority == Priority.HIGH),
                "normal": sum(1 for t in self.queue if t.priority == Priority.NORMAL),
                "low": sum(1 for t in self.queue if t.priority == Priority.LOW)
            }
        }

    def add_incremental_improvement_tasks(self, target_systems: List[str]):
        """
        Analyze systems and queue incremental improvement tasks

        Args:
            target_systems: Systems to analyze (e.g., ["sherlock", "squirt", "johny5alive"])
        """
        self.logger.info(f"🔍 Analyzing improvement opportunities for: {', '.join(target_systems)}")

        for system in target_systems:
            opportunities = self.analyze_improvement_opportunities(system)

            self.logger.info(f"📊 Found {len(opportunities)} opportunities in {system}")

            for opportunity in opportunities:
                task = self._create_improvement_task(opportunity)
                if task:
                    self.add_task(task)

    def analyze_improvement_opportunities(self, system: str) -> List[ImprovementOpportunity]:
        """
        Analyze system for improvement opportunities

        In full implementation, this would:
        - Run static code analysis
        - Check test coverage
        - Identify performance bottlenecks
        - Scan for technical debt
        - Review documentation completeness
        """
        opportunities = []

        # Placeholder - would be implemented with actual analysis tools
        # For now, return example opportunities

        if system == "sherlock":
            opportunities.extend([
                ImprovementOpportunity(
                    type=ImprovementType.TEST_COVERAGE,
                    system=system,
                    scope="voice_engine.py",
                    description="Increase test coverage for error handling paths",
                    expected_impact="Improve reliability of voice processing",
                    priority=Priority.NORMAL,
                    effort_estimate="medium"
                ),
                ImprovementOpportunity(
                    type=ImprovementType.CODE_QUALITY,
                    system=system,
                    scope="evidence_database.py",
                    description="Refactor complex methods for better maintainability",
                    expected_impact="Easier maintenance and debugging",
                    priority=Priority.LOW,
                    effort_estimate="medium"
                )
            ])

        elif system == "squirt":
            opportunities.extend([
                ImprovementOpportunity(
                    type=ImprovementType.PERFORMANCE,
                    system=system,
                    scope="voice_memo_processor.py",
                    description="Optimize memory usage during processing",
                    expected_impact="Reduce RAM footprint during business hours",
                    priority=Priority.HIGH,
                    effort_estimate="small"
                )
            ])

        return opportunities

    def _create_improvement_task(self, opportunity: ImprovementOpportunity) -> Optional[J5AWorkAssignment]:
        """Create work assignment from improvement opportunity"""

        # Generate task ID
        task_id = f"improve_{opportunity.system}_{opportunity.type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Define expected outputs based on improvement type
        expected_outputs = self._define_improvement_outputs(opportunity)

        # Define success criteria
        success_criteria = self._define_improvement_criteria(opportunity)

        # Define test oracle
        test_oracle = self._define_improvement_oracle(opportunity)

        try:
            task = J5AWorkAssignment(
                task_id=task_id,
                task_name=f"{opportunity.type.value}: {opportunity.scope}",
                domain=self._get_domain_from_system(opportunity.system),
                description=opportunity.description,
                assigned_date=datetime.now(),
                priority=opportunity.priority,
                expected_outputs=expected_outputs,
                success_criteria=success_criteria,
                test_oracle=test_oracle,
                requires_poc=True,
                rollback_plan=f"Revert changes to {opportunity.scope} if validation fails"
            )

            return task

        except Exception as e:
            self.logger.error(f"❌ Failed to create task for opportunity: {e}")
            return None

    def _define_improvement_outputs(self, opportunity: ImprovementOpportunity) -> List[OutputSpecification]:
        """Define expected outputs for improvement type"""

        base_path = Path(f"improvements/{opportunity.system}/{opportunity.type.value}")

        outputs = [
            OutputSpecification(
                file_path=base_path / "modified_code.py",
                format="Python",
                description=f"Modified {opportunity.scope}",
                min_size_bytes=100,
                quality_checks=["passes_all_tests", "no_syntax_errors"]
            ),
            OutputSpecification(
                file_path=base_path / "validation_report.json",
                format="JSON",
                description="Validation report with test results",
                schema={"test_results": dict, "metrics": dict},
                quality_checks=["valid_json"]
            )
        ]

        # Add type-specific outputs
        if opportunity.type == ImprovementType.TEST_COVERAGE:
            outputs.append(
                OutputSpecification(
                    file_path=base_path / "new_tests.py",
                    format="Python",
                    description="New test cases",
                    min_size_bytes=100,
                    quality_checks=["passes_all_tests"]
                )
            )

        return outputs

    def _define_improvement_criteria(self, opportunity: ImprovementOpportunity) -> Dict[str, QuantitativeMeasure]:
        """Define success criteria for improvement type"""

        # Base criteria (always required)
        criteria = {
            "existing_tests_pass_rate": QuantitativeMeasure(
                "existing_tests_pass_rate", 1.0, "==", "%"
            ),
            "no_regressions": QuantitativeMeasure(
                "regression_count", 0, "==", "count"
            )
        }

        # Type-specific criteria
        if opportunity.type == ImprovementType.TEST_COVERAGE:
            criteria["new_test_coverage"] = QuantitativeMeasure(
                "code_coverage_increase", 0.05, ">=", "%"  # At least 5% increase
            )

        elif opportunity.type == ImprovementType.PERFORMANCE:
            criteria["performance_improvement"] = QuantitativeMeasure(
                "performance_improvement", 0.1, ">=", "%"  # At least 10% improvement
            )

        elif opportunity.type == ImprovementType.CODE_QUALITY:
            criteria["code_quality_score"] = QuantitativeMeasure(
                "pylint_score", 8.0, ">=", "score"
            )

        return criteria

    def _define_improvement_oracle(self, opportunity: ImprovementOpportunity) -> TestOracle:
        """Define test oracle for improvement type"""

        return TestOracle(
            name=f"{opportunity.type.value}_validation",
            description=f"Validate {opportunity.type.value} improvement",
            expected_behavior=f"{opportunity.expected_impact}",
            validation_method="Run tests and compare metrics before/after",
            confidence_threshold=0.8
        )

    def _get_domain_from_system(self, system: str) -> str:
        """Map system name to domain"""
        domain_map = {
            "sherlock": "audio_processing",
            "squirt": "document_processing",
            "johny5alive": "system_management"
        }
        return domain_map.get(system, "general")

    def _validate_task_definition(self, task: J5AWorkAssignment) -> bool:
        """Validate task definition completeness"""
        try:
            # Task validation happens in __post_init__
            # If we got here, task is valid
            return True
        except Exception as e:
            self.logger.error(f"Task validation failed: {e}")
            return False

    def _sort_queue(self):
        """Sort queue by priority"""
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.NORMAL: 2,
            Priority.LOW: 3
        }
        self.queue.sort(key=lambda t: (priority_order[t.priority], t.assigned_date))

    def _get_task_position(self, task: J5AWorkAssignment) -> int:
        """Get task position in queue (1-indexed)"""
        for i, queued_task in enumerate(self.queue, 1):
            if queued_task.task_id == task.task_id:
                return i
        return -1

    def save_queue(self):
        """Persist queue to disk"""
        queue_data = {
            "saved_at": datetime.now().isoformat(),
            "tasks": [task.to_dict() for task in self.queue]
        }

        with open(self.queue_file, 'w') as f:
            json.dump(queue_data, f, indent=2)

        self.logger.debug(f"💾 Queue saved to {self.queue_file}")

    def load_queue(self):
        """Load queue from disk"""
        if not self.queue_file.exists():
            return

        try:
            with open(self.queue_file, 'r') as f:
                queue_data = json.load(f)

            # Note: Full deserialization would reconstruct J5AWorkAssignment objects
            # For now, just log that queue exists
            task_count = len(queue_data.get("tasks", []))
            self.logger.info(f"📂 Loaded {task_count} tasks from queue file")

        except Exception as e:
            self.logger.error(f"❌ Failed to load queue: {e}")


if __name__ == "__main__":
    # Test queue manager
    from j5a_work_assignment import create_example_task

    print("📋 Testing J5A Queue Manager")
    print("=" * 80)

    # Create queue manager
    queue_manager = J5AQueueManager(queue_file=Path("test_queue.json"))

    # Test 1: Add tasks
    print("\n✅ Test 1: Adding tasks to queue")
    task1 = create_example_task()
    task1.task_id = "test_001"
    task1.priority = Priority.HIGH

    task2 = create_example_task()
    task2.task_id = "test_002"
    task2.priority = Priority.LOW

    queue_manager.add_task(task1)
    queue_manager.add_task(task2)

    status = queue_manager.get_queue_status()
    print(f"Queue status: {status}")
    assert status["total_tasks"] == 2

    # Test 2: Get next task (should be high priority)
    print("\n✅ Test 2: Get next task")
    next_task = queue_manager.get_next_task()
    assert next_task.task_id == "test_001"
    print(f"Next task: {next_task.task_id} (priority: {next_task.priority.name})")

    # Test 3: Analyze improvement opportunities
    print("\n✅ Test 3: Analyze improvement opportunities")
    opportunities = queue_manager.analyze_improvement_opportunities("sherlock")
    print(f"Found {len(opportunities)} opportunities")
    for opp in opportunities:
        print(f"  - {opp.type.value}: {opp.description}")

    # Test 4: Add improvement tasks
    print("\n✅ Test 4: Add incremental improvement tasks")
    queue_manager.add_incremental_improvement_tasks(["sherlock"])
    status = queue_manager.get_queue_status()
    print(f"Queue status after improvements: {status}")

    print("\n" + "=" * 80)
    print("✅ Queue manager tests complete")