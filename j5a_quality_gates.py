#!/usr/bin/env python3
"""
J5A Quality Gates System
Implements mandatory blocking checkpoints that prevent progression
until specific criteria are met

Addresses Claude tendency to abandon rigorous protocols under difficulty
"""

import logging
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from j5a_work_assignment import J5AWorkAssignment


class GateStatus(Enum):
    """Quality gate evaluation result"""
    PASSED = "passed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class GateResult:
    """Result of quality gate evaluation"""
    gate_name: str
    status: GateStatus
    reason: str
    details: Dict[str, Any]
    blocking: bool = True  # If True, task cannot proceed past this gate


class QualityGate(ABC):
    """
    Base class for quality gates
    All gates are BLOCKING by default - task cannot proceed if gate fails
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"QualityGate.{name}")

    @abstractmethod
    def evaluate(self, task: J5AWorkAssignment, context: Optional[Dict] = None) -> GateResult:
        """
        Evaluate if task can proceed past this gate

        Args:
            task: Work assignment being evaluated
            context: Optional additional context (execution state, etc.)

        Returns:
            GateResult indicating pass/block/fail
        """
        pass

    def block(self, reason: str, details: Optional[Dict] = None) -> GateResult:
        """Helper to create blocking result"""
        return GateResult(
            gate_name=self.name,
            status=GateStatus.BLOCKED,
            reason=reason,
            details=details or {},
            blocking=True
        )

    def fail(self, reason: str, details: Optional[Dict] = None) -> GateResult:
        """Helper to create failure result"""
        return GateResult(
            gate_name=self.name,
            status=GateStatus.FAILED,
            reason=reason,
            details=details or {},
            blocking=True
        )

    def passed(self, reason: str, details: Optional[Dict] = None) -> GateResult:
        """Helper to create pass result"""
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            reason=reason,
            details=details or {},
            blocking=False
        )


class PreFlightGate(QualityGate):
    """
    Gate 1: Pre-Flight Validation
    Validates system readiness and task definition completeness

    BLOCKS if:
    - Task definition incomplete
    - System resources insufficient
    - Business hours conflict
    """

    def __init__(self):
        super().__init__("PreFlight")

    def evaluate(self, task: J5AWorkAssignment, context: Optional[Dict] = None) -> GateResult:
        """Validate task can start"""
        self.logger.info(f"🔍 Evaluating pre-flight for task: {task.task_name}")

        # Check 1: Task definition completeness
        if not task.expected_outputs:
            return self.block("Task missing expected_outputs definition")

        if not task.success_criteria:
            return self.block("Task missing success_criteria definition")

        if not task.test_oracle:
            return self.block("Task missing test_oracle definition")

        # Check 2: RAM availability
        ram_available_gb = psutil.virtual_memory().available / (1024**3)
        if ram_available_gb < task.max_ram_gb:
            return self.block(
                f"Insufficient RAM: {ram_available_gb:.2f}GB available < {task.max_ram_gb:.2f}GB required",
                {"ram_available_gb": ram_available_gb, "ram_required_gb": task.max_ram_gb}
            )

        # Check 3: Thermal safety
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                cpu_temp = max([t.current for sensor_temps in temps.values() for t in sensor_temps])
                if cpu_temp > task.max_thermal_celsius:
                    return self.block(
                        f"CPU temperature too high: {cpu_temp}°C > {task.max_thermal_celsius}°C threshold",
                        {"cpu_temp_celsius": cpu_temp, "threshold_celsius": task.max_thermal_celsius}
                    )
        except Exception as e:
            self.logger.warning(f"Could not check CPU temperature: {e}")

        # Check 4: Business hours compliance (if required)
        if task.requires_business_hours_clear:
            # Would check if LibreOffice is running, current time is business hours, etc.
            # For now, just pass
            pass

        # Check 5: Validation samples exist (if POC required)
        if task.requires_poc and not task.validation_samples:
            return self.block(
                "Task requires POC but no validation_samples provided",
                {"requires_poc": True, "validation_samples_count": 0}
            )

        self.logger.info("✅ Pre-flight checks passed")
        return self.passed(
            "System ready for task execution",
            {
                "ram_available_gb": ram_available_gb,
                "ram_required_gb": task.max_ram_gb,
                "validation_samples": len(task.validation_samples)
            }
        )


class ProofOfConceptGate(QualityGate):
    """
    Gate 2: Proof-of-Concept Validation
    Requires small-scale test BEFORE full implementation

    BLOCKS if:
    - POC test not defined
    - POC test fails
    - POC does not generate expected outputs (even at small scale)

    This is CRITICAL - prevents wasting resources on approaches that won't work
    """

    def __init__(self):
        super().__init__("ProofOfConcept")

    def evaluate(self, task: J5AWorkAssignment, context: Optional[Dict] = None) -> GateResult:
        """Validate POC before full implementation"""
        self.logger.info(f"🧪 Evaluating proof-of-concept for task: {task.task_name}")

        # Check if POC required
        if not task.requires_poc:
            self.logger.info("ℹ️  POC not required for this task")
            return self.passed("POC not required", {"poc_required": False})

        # Check POC test provided
        if not task.validation_samples:
            return self.block(
                "POC required but no validation_samples provided",
                {"validation_samples_count": 0}
            )

        # Execute POC test
        poc_result = self._execute_poc(task, context)

        if not poc_result["success"]:
            return self.block(
                f"POC test failed: {poc_result['failure_reason']}",
                poc_result
            )

        # Verify POC generated expected outputs (at small scale)
        missing_outputs = poc_result.get("missing_outputs", [])
        if missing_outputs:
            return self.block(
                f"POC did not generate expected outputs: {', '.join(missing_outputs)}",
                poc_result
            )

        self.logger.info("✅ Proof-of-concept validated")
        return self.passed(
            "POC successful - may proceed to full implementation",
            poc_result
        )

    def _execute_poc(self, task: J5AWorkAssignment, context: Optional[Dict]) -> Dict:
        """
        Execute proof-of-concept test

        This should run a small-scale version of the task to validate approach
        """
        # Placeholder implementation - would be customized per task domain
        # For now, just verify validation samples exist

        poc_result = {
            "success": True,
            "validation_samples_tested": len(task.validation_samples),
            "outputs_generated": [],
            "missing_outputs": [],
            "failure_reason": None
        }

        # Check each validation sample exists
        for sample in task.validation_samples:
            if not sample.exists():
                poc_result["success"] = False
                poc_result["failure_reason"] = f"Validation sample not found: {sample}"
                break

        return poc_result


class ImplementationGate(QualityGate):
    """
    Gate 3: Implementation Validation
    Validates code quality, test passage, and methodology compliance

    BLOCKS if:
    - Existing tests fail (ANY regression)
    - New tests fail
    - Code quality below standards
    - Forbidden patterns detected
    """

    def __init__(self):
        super().__init__("Implementation")

    def evaluate(self, task: J5AWorkAssignment, context: Optional[Dict] = None) -> GateResult:
        """Validate implementation quality"""
        self.logger.info(f"⚙️  Evaluating implementation for task: {task.task_name}")

        implementation_details = {}

        # Check 1: Existing tests pass (100% required - NO REGRESSIONS)
        if context and "existing_tests" in context:
            test_result = self._run_existing_tests(context["existing_tests"])
            implementation_details["existing_tests"] = test_result

            if test_result["pass_rate"] < 1.0:
                return self.block(
                    f"Existing tests failed: {test_result['failed_count']} failures (REGRESSION)",
                    test_result
                )

        # Check 2: New tests pass (100% required)
        if context and "new_tests" in context:
            test_result = self._run_new_tests(context["new_tests"])
            implementation_details["new_tests"] = test_result

            if test_result["pass_rate"] < 1.0:
                return self.block(
                    f"New tests failed: {test_result['failed_count']} failures",
                    test_result
                )

        # Check 3: Code quality standards
        if context and "implementation_files" in context:
            quality_result = self._check_code_quality(context["implementation_files"])
            implementation_details["code_quality"] = quality_result

            if not quality_result["meets_standards"]:
                return self.block(
                    f"Code quality below standards: {quality_result['issues']}",
                    quality_result
                )

        # Check 4: Methodology compliance (checked by MethodologyEnforcer)
        if context and "methodology_check" in context:
            methodology_result = context["methodology_check"]
            implementation_details["methodology"] = methodology_result

            if not methodology_result["compliant"]:
                return self.block(
                    f"Methodology violation: {methodology_result['violations']}",
                    methodology_result
                )

        self.logger.info("✅ Implementation validated")
        return self.passed(
            "Implementation meets all quality standards",
            implementation_details
        )

    def _run_existing_tests(self, test_suite: str) -> Dict:
        """Run existing test suite to check for regressions"""
        # Placeholder - would actually run tests
        return {
            "pass_rate": 1.0,
            "passed_count": 0,
            "failed_count": 0,
            "tests_run": 0
        }

    def _run_new_tests(self, test_suite: str) -> Dict:
        """Run new test suite"""
        # Placeholder - would actually run tests
        return {
            "pass_rate": 1.0,
            "passed_count": 0,
            "failed_count": 0,
            "tests_run": 0
        }

    def _check_code_quality(self, files: List[Path]) -> Dict:
        """Check code quality standards"""
        # Placeholder - would run linters, check complexity, etc.
        return {
            "meets_standards": True,
            "issues": []
        }


class DeliveryGate(QualityGate):
    """
    Gate 4: Delivery Validation
    Final validation before marking task complete

    BLOCKS if:
    - Any expected output missing
    - Any success criterion not met
    - Functional tests fail
    - Rollback plan not documented

    This is the FINAL checkpoint - ensures ACTUAL OUTCOMES achieved
    """

    def __init__(self):
        super().__init__("Delivery")

    def evaluate(self, task: J5AWorkAssignment, context: Optional[Dict] = None) -> GateResult:
        """Final validation before completion"""
        self.logger.info(f"🚀 Evaluating delivery for task: {task.task_name}")

        delivery_details = {}

        # Check 1: All expected outputs exist
        missing_outputs = []
        for output in task.expected_outputs:
            if not output.file_path.exists():
                missing_outputs.append(str(output.file_path))

        if missing_outputs:
            return self.block(
                f"Missing expected outputs: {', '.join(missing_outputs)}",
                {"missing_outputs": missing_outputs}
            )

        delivery_details["outputs_generated"] = len(task.expected_outputs)

        # Check 2: Success criteria met
        criteria_met = task.evaluate_success_criteria()
        delivery_details["success_criteria_met"] = criteria_met
        delivery_details["actual_metrics"] = task.actual_metrics

        if not criteria_met:
            unmet_criteria = []
            for name, measure in task.success_criteria.items():
                if name in task.actual_metrics:
                    actual = task.actual_metrics[name]
                    if not measure.evaluate(actual):
                        unmet_criteria.append(
                            f"{name}: {actual} {measure.comparison} {measure.threshold} (FAILED)"
                        )
                else:
                    unmet_criteria.append(f"{name}: NOT MEASURED")

            return self.block(
                f"Success criteria not met: {'; '.join(unmet_criteria)}",
                {"unmet_criteria": unmet_criteria}
            )

        # Check 3: Functional correctness (via outcome validator)
        if context and "validation_report" in context:
            validation = context["validation_report"]
            delivery_details["validation"] = validation

            if validation.overall_result != "passed":
                return self.block(
                    f"Functional validation failed: {validation.blocking_reason}",
                    {"validation_report": validation.to_dict()}
                )

        # Check 4: Rollback plan documented
        if not task.rollback_plan:
            self.logger.warning("⚠️  No rollback plan documented")
            delivery_details["rollback_plan"] = False
        else:
            delivery_details["rollback_plan"] = True

        self.logger.info("✅ Delivery validated - task complete")
        return self.passed(
            "All deliverables generated, success criteria met, validation passed",
            delivery_details
        )


class QualityGateManager:
    """
    Manages quality gate execution
    Enforces sequential evaluation with blocking
    """

    def __init__(self):
        self.logger = logging.getLogger("QualityGateManager")
        self.gates = [
            PreFlightGate(),
            ProofOfConceptGate(),
            ImplementationGate(),
            DeliveryGate()
        ]

    def evaluate_all_gates(self, task: J5AWorkAssignment,
                          context: Optional[Dict] = None) -> List[GateResult]:
        """
        Evaluate all gates sequentially

        STOPS at first blocking gate

        Returns:
            List of gate results (stops at first block)
        """
        results = []
        context = context or {}

        for gate in self.gates:
            self.logger.info(f"🚪 Evaluating gate: {gate.name}")

            result = gate.evaluate(task, context)
            results.append(result)

            # Record in task
            if result.status == GateStatus.PASSED:
                task.mark_gate_passed(gate.name)
            else:
                task.mark_gate_failed(gate.name, result.reason)

            # Stop at first blocking gate
            if result.blocking and result.status != GateStatus.PASSED:
                self.logger.error(f"🛑 BLOCKED at gate: {gate.name} - {result.reason}")
                break

        return results

    def get_blocking_gate(self, results: List[GateResult]) -> Optional[GateResult]:
        """Get first blocking gate (if any)"""
        for result in results:
            if result.blocking and result.status != GateStatus.PASSED:
                return result
        return None


if __name__ == "__main__":
    # Test quality gates
    from j5a_work_assignment import create_example_task

    print("🚪 Testing J5A Quality Gates")
    print("=" * 80)

    # Create test task
    task = create_example_task()

    # Create gate manager
    manager = QualityGateManager()

    # Test gate evaluation
    print("\n📋 Evaluating quality gates...")
    results = manager.evaluate_all_gates(task)

    print(f"\n📊 Results:")
    for result in results:
        status_icon = "✅" if result.status == GateStatus.PASSED else "❌"
        print(f"{status_icon} {result.gate_name}: {result.status.value}")
        print(f"   Reason: {result.reason}")

    blocking = manager.get_blocking_gate(results)
    if blocking:
        print(f"\n🛑 BLOCKED at: {blocking.gate_name}")
        print(f"   Reason: {blocking.reason}")
    else:
        print("\n✅ All gates passed!")

    print("\n" + "=" * 80)
    print("✅ Quality gates test complete")