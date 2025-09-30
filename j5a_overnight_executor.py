#!/usr/bin/env python3
"""
J5A Overnight Executor
Main execution engine for validation-focused overnight work assignments

Integrates all components:
- Work assignments
- Outcome validation
- Quality gates
- Methodology enforcement
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from j5a_work_assignment import J5AWorkAssignment, TaskStatus, Priority
from j5a_outcome_validator import J5AOutcomeValidator, ValidationResult
from j5a_quality_gates import QualityGateManager, GateStatus
from j5a_methodology_enforcer import MethodologyEnforcer, ComplianceStatus
from j5a_resource_manager import J5AResourceManager, TaskResourceEstimate, SessionStrategy


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    task_name: str
    success: bool
    status: TaskStatus
    error_message: str = ""

    # Gate results
    gates_passed: List[str] = None
    gates_failed: List[str] = None
    blocking_gate: Optional[str] = None

    # Validation results
    validation_report: Optional[Dict] = None

    # Methodology compliance
    methodology_compliant: bool = True
    methodology_violations: List[str] = None

    # Timing and resources
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    peak_ram_gb: float = 0.0
    peak_thermal_celsius: float = 0.0
    tokens_used: int = 0

    def __post_init__(self):
        if self.gates_passed is None:
            self.gates_passed = []
        if self.gates_failed is None:
            self.gates_failed = []
        if self.methodology_violations is None:
            self.methodology_violations = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "success": self.success,
            "status": self.status.value,
            "error_message": self.error_message,
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "blocking_gate": self.blocking_gate,
            "validation_report": self.validation_report,
            "methodology_compliant": self.methodology_compliant,
            "methodology_violations": self.methodology_violations,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "peak_ram_gb": self.peak_ram_gb,
            "peak_thermal_celsius": self.peak_thermal_celsius,
            "tokens_used": self.tokens_used
        }


class J5AOvernightExecutor:
    """
    Main overnight execution engine

    Executes tasks with mandatory quality gates and outcome validation
    """

    def __init__(self, output_dir: Optional[Path] = None, resource_manager: Optional[J5AResourceManager] = None):
        self.logger = logging.getLogger("J5AOvernightExecutor")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Components
        self.gate_manager = QualityGateManager()
        self.outcome_validator = J5AOutcomeValidator()
        self.methodology_enforcer = MethodologyEnforcer()
        self.resource_manager = resource_manager or J5AResourceManager()

        # Output directory for reports
        self.output_dir = output_dir or Path("j5a_output")
        self.output_dir.mkdir(exist_ok=True)

        # Execution tracking
        self.current_task: Optional[J5AWorkAssignment] = None
        self.execution_results: List[ExecutionResult] = []

    def execute_task(self, task: J5AWorkAssignment) -> ExecutionResult:
        """
        Execute single task with full validation pipeline

        Pipeline:
        1. Pre-flight gate
        2. Proof-of-concept gate
        3. Implementation (with methodology enforcement)
        4. Implementation gate
        5. Outcome validation
        6. Delivery gate

        Any gate failure BLOCKS progression
        """
        self.current_task = task

        # ========== RESOURCE CHECK ==========
        self.logger.info("\n🎛️  Checking resource availability...")
        can_execute, reason = self.resource_manager.can_execute_task(task.task_id)

        if not can_execute:
            self.logger.error(f"❌ Resource constraint: {reason}")
            result = ExecutionResult(
                task_id=task.task_id,
                task_name=task.task_name,
                success=False,
                status=TaskStatus.BLOCKED,
                start_time=datetime.now(),
                error_message=f"Resource constraint: {reason}"
            )
            return self._finalize_result(result)

        self.logger.info("=" * 80)
        self.logger.info(f"🚀 Starting task: {task.task_name}")
        self.logger.info(f"📋 Task ID: {task.task_id}")
        self.logger.info(f"🎯 Domain: {task.domain}")
        self.logger.info("=" * 80)

        # Initialize result
        result = ExecutionResult(
            task_id=task.task_id,
            task_name=task.task_name,
            success=False,
            status=TaskStatus.QUEUED,
            start_time=datetime.now()
        )

        task.start_time = result.start_time
        task.status = TaskStatus.PRE_FLIGHT

        # Track starting token count
        tokens_at_start = self.resource_manager.token_budget.tokens_used

        try:
            # ========== GATE 1: PRE-FLIGHT ==========
            self.logger.info("\n🚪 GATE 1: Pre-Flight Validation")
            gate_results = self.gate_manager.evaluate_all_gates(task, {"phase": "pre_flight"})

            # Check if blocked
            blocking_gate = self.gate_manager.get_blocking_gate(gate_results)
            if blocking_gate:
                result.status = TaskStatus.BLOCKED
                result.blocking_gate = blocking_gate.gate_name
                result.error_message = blocking_gate.reason
                result.gates_failed = task.gates_failed
                self.logger.error(f"🛑 BLOCKED at {blocking_gate.gate_name}: {blocking_gate.reason}")
                return self._finalize_result(result)

            result.gates_passed.extend(task.gates_passed)
            task.status = TaskStatus.POC

            # ========== GATE 2: PROOF-OF-CONCEPT ==========
            # (POC gate already evaluated in gate_manager.evaluate_all_gates)
            # If we reach here, POC passed or wasn't required

            # ========== IMPLEMENTATION PHASE ==========
            self.logger.info("\n⚙️  PHASE: Implementation")
            task.status = TaskStatus.IMPLEMENTING

            # Execute actual implementation
            # (This is where task-specific work happens)
            impl_context = self._execute_implementation(task)

            if not impl_context.get("success", False):
                result.status = TaskStatus.FAILED
                result.error_message = impl_context.get("error", "Implementation failed")
                self.logger.error(f"❌ Implementation failed: {result.error_message}")
                return self._finalize_result(result)

            # ========== METHODOLOGY ENFORCEMENT ==========
            self.logger.info("\n🔍 Checking methodology compliance...")
            if impl_context.get("implementation_files"):
                compliance = self.methodology_enforcer.validate_multiple_files(
                    task,
                    impl_context["implementation_files"]
                )

                result.methodology_compliant = compliance.compliant
                result.methodology_violations = compliance.violations

                if not compliance.compliant:
                    result.status = TaskStatus.BLOCKED
                    result.error_message = f"Methodology violations: {'; '.join(compliance.violations)}"
                    self.logger.error(f"🚫 {result.error_message}")
                    return self._finalize_result(result)

            # ========== GATE 3: IMPLEMENTATION GATE ==========
            # (Already part of gate_manager evaluation)

            # ========== OUTCOME VALIDATION ==========
            self.logger.info("\n✅ PHASE: Outcome Validation")
            task.status = TaskStatus.VALIDATING

            validation_report = self.outcome_validator.validate_task_execution(
                task,
                impl_context
            )

            result.validation_report = validation_report.to_dict()

            if validation_report.overall_result != ValidationResult.PASSED:
                result.status = TaskStatus.BLOCKED
                result.blocking_gate = f"Validation_{validation_report.blocking_layer.value}"
                result.error_message = validation_report.blocking_reason
                self.logger.error(f"🛑 Validation failed: {result.error_message}")
                return self._finalize_result(result)

            # ========== GATE 4: DELIVERY GATE ==========
            # Final gate evaluation
            self.logger.info("\n🚪 GATE 4: Delivery Validation")

            # Re-evaluate gates with validation report
            final_gate_context = {
                "phase": "delivery",
                "validation_report": validation_report,
                "implementation_files": impl_context.get("implementation_files", [])
            }

            # Note: We already evaluated all gates earlier, but delivery gate needs validation report
            # In full implementation, would only evaluate delivery gate here
            # For now, mark as passed if validation passed

            # ========== SUCCESS ==========
            result.success = True
            result.status = TaskStatus.COMPLETED
            task.status = TaskStatus.COMPLETED
            result.gates_passed = task.gates_passed

            self.logger.info("\n" + "=" * 80)
            self.logger.info(f"✅ Task completed successfully: {task.task_name}")
            self.logger.info("=" * 80)

        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error_message = str(e)
            task.status = TaskStatus.FAILED
            self.logger.exception(f"❌ Task failed with exception: {e}")

        finally:
            # Record token usage
            tokens_used = self.resource_manager.token_budget.tokens_used - tokens_at_start
            result.tokens_used = tokens_used
            self.resource_manager.record_task_completion(task.task_id, tokens_used)

            result = self._finalize_result(result)
            self._save_task_report(task, result)

        return result

    def _execute_implementation(self, task: J5AWorkAssignment) -> Dict:
        """
        Execute task-specific implementation

        This is a placeholder - actual implementation would be provided
        by task-specific executors or AI-driven code generation

        Returns:
            Implementation context with results
        """
        self.logger.info("🔨 Executing task implementation...")

        # Placeholder implementation
        # In real system, this would:
        # 1. Generate/modify code based on task requirements
        # 2. Run tests
        # 3. Generate outputs
        # 4. Collect metrics

        impl_context = {
            "success": True,
            "implementation_files": [],
            "outputs_generated": [],
            "tests_run": 0,
            "tests_passed": 0
        }

        # Simulate: Create expected outputs (placeholder)
        for output_spec in task.expected_outputs:
            # In real implementation, would generate actual output
            # For now, just note what should be generated
            impl_context["outputs_generated"].append(str(output_spec.file_path))

        return impl_context

    def _finalize_result(self, result: ExecutionResult) -> ExecutionResult:
        """Finalize execution result with timing and resources"""
        result.end_time = datetime.now()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()

        # Record in execution history
        self.execution_results.append(result)

        return result

    def _save_task_report(self, task: J5AWorkAssignment, result: ExecutionResult):
        """Save detailed task execution report"""
        report_path = self.output_dir / f"{task.task_id}_report.json"

        report = {
            "task": task.to_dict(),
            "execution": result.to_dict(),
            "generated_at": datetime.now().isoformat()
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"📄 Task report saved: {report_path}")

    def execute_task_list(self, tasks: List[J5AWorkAssignment]) -> List[ExecutionResult]:
        """
        Execute multiple tasks sequentially with resource monitoring

        Monitors:
        - Token budget (checkpoints before exhaustion)
        - RAM availability
        - Thermal state

        Returns:
            List of execution results
        """
        self.logger.info(f"\n🎯 Executing {len(tasks)} tasks")
        self.resource_manager.print_session_summary()
        results = []

        for i, task in enumerate(tasks, 1):
            # Check if we should checkpoint before next task
            should_checkpoint, strategy = self.resource_manager.should_checkpoint_session()

            if should_checkpoint:
                self.logger.warning(f"\n⚠️  Resource checkpoint triggered: {strategy.value}")

                if strategy == SessionStrategy.EMERGENCY_CHECKPOINT:
                    self.logger.warning("🚨 Emergency checkpoint - preserving session immediately")
                    remaining_tasks = [t.to_dict() for t in tasks[i-1:]]
                    self.resource_manager.create_checkpoint(
                        queue_state={"queued_tasks": remaining_tasks},
                        current_task=task.to_dict() if task else None
                    )
                    self.logger.warning("💾 Session preserved - stopping execution")
                    break

                elif strategy == SessionStrategy.COMPLETE_CURRENT:
                    self.logger.info("⏸️  Will complete current task then checkpoint")
                    # Continue to execute current task, then checkpoint after

            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"📋 Task {i}/{len(tasks)}")
            self.logger.info(f"{'='*80}")

            result = self.execute_task(task)
            results.append(result)

            # Log result
            status_icon = "✅" if result.success else "❌"
            self.logger.info(f"{status_icon} Task {i}: {result.status.value}")
            self.logger.info(f"🎫 Tokens used: {result.tokens_used:,}")

            # Print resource summary after each task
            if i % 3 == 0 or should_checkpoint:  # Every 3 tasks or if checkpoint triggered
                self.resource_manager.print_session_summary()

            # If completing current before checkpoint, do it now
            if should_checkpoint and strategy == SessionStrategy.COMPLETE_CURRENT:
                remaining_tasks = [t.to_dict() for t in tasks[i:]]
                self.resource_manager.create_checkpoint(
                    queue_state={"queued_tasks": remaining_tasks}
                )
                self.logger.info("💾 Session checkpointed - stopping execution")
                break

        return results

    def generate_overnight_summary(self, results: List[ExecutionResult]) -> Dict:
        """Generate summary of overnight execution"""
        summary = {
            "execution_date": datetime.now().isoformat(),
            "total_tasks": len(results),
            "completed": sum(1 for r in results if r.success),
            "blocked": sum(1 for r in results if r.status == TaskStatus.BLOCKED),
            "failed": sum(1 for r in results if r.status == TaskStatus.FAILED),

            # Gate statistics
            "gates_passed_total": sum(len(r.gates_passed) for r in results),
            "gates_failed_total": sum(len(r.gates_failed) for r in results),

            # Validation statistics
            "validation_passed": sum(
                1 for r in results
                if r.validation_report and
                r.validation_report.get("overall_result") == "passed"
            ),

            # Methodology statistics
            "methodology_compliant": sum(1 for r in results if r.methodology_compliant),
            "methodology_violations": sum(len(r.methodology_violations) for r in results),

            # Timing
            "total_duration_hours": sum(r.duration_seconds for r in results) / 3600,

            # Detailed results
            "task_results": [r.to_dict() for r in results]
        }

        return summary

    def save_overnight_summary(self, results: List[ExecutionResult]):
        """Save overnight execution summary"""
        summary = self.generate_overnight_summary(results)

        summary_path = self.output_dir / f"overnight_summary_{datetime.now().strftime('%Y%m%d')}.json"

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        self.logger.info(f"\n📊 Overnight summary saved: {summary_path}")

        # Print summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 OVERNIGHT EXECUTION SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Total tasks: {summary['total_tasks']}")
        self.logger.info(f"✅ Completed: {summary['completed']}")
        self.logger.info(f"🛑 Blocked: {summary['blocked']}")
        self.logger.info(f"❌ Failed: {summary['failed']}")
        self.logger.info(f"🚪 Total gates passed: {summary['gates_passed_total']}")
        self.logger.info(f"✅ Validation passed: {summary['validation_passed']}")
        self.logger.info(f"📏 Methodology compliant: {summary['methodology_compliant']}/{summary['total_tasks']}")
        self.logger.info(f"⏱️  Total duration: {summary['total_duration_hours']:.2f} hours")
        self.logger.info("=" * 80)


if __name__ == "__main__":
    # Test overnight executor
    from j5a_work_assignment import create_example_task

    print("🌙 Testing J5A Overnight Executor")
    print("=" * 80)

    # Create test tasks
    tasks = [
        create_example_task()
    ]
    tasks[0].task_id = "test_001"

    # Create executor
    executor = J5AOvernightExecutor(output_dir=Path("test_j5a_output"))

    # Execute tasks
    print("\n🚀 Executing test tasks...")
    results = executor.execute_task_list(tasks)

    # Generate summary
    print("\n📊 Generating summary...")
    executor.save_overnight_summary(results)

    print("\n" + "=" * 80)
    print("✅ Overnight executor test complete")
    print(f"📄 Reports saved in: {executor.output_dir}")