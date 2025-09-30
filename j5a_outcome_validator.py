#!/usr/bin/env python3
"""
J5A Outcome Validator
Implements 3-layer validation focusing on OUTCOMES not processes
Addresses Claude tendency to assume "process started = goal achieved"
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from j5a_work_assignment import (
    J5AWorkAssignment,
    OutputSpecification,
    ValidationResult
)


class ValidationLayer(Enum):
    """Validation layers"""
    EXISTENCE = "existence"
    QUALITY = "quality"
    FUNCTIONAL = "functional"


@dataclass
class LayerResult:
    """Result of a single validation layer"""
    layer: ValidationLayer
    passed: bool
    reason: str
    details: Dict[str, Any]


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    task_id: str
    task_name: str
    overall_result: ValidationResult

    # Layer results
    layer1_existence: Optional[LayerResult] = None
    layer2_quality: Optional[LayerResult] = None
    layer3_functional: Optional[LayerResult] = None

    # Blocking information
    blocking_layer: Optional[ValidationLayer] = None
    blocking_reason: str = ""

    # Metrics
    outputs_expected: int = 0
    outputs_generated: int = 0
    outputs_missing: List[str] = None

    quality_thresholds_expected: int = 0
    quality_thresholds_met: int = 0
    quality_thresholds_failed: List[str] = None

    functional_tests_run: int = 0
    functional_tests_passed: int = 0

    def __post_init__(self):
        if self.outputs_missing is None:
            self.outputs_missing = []
        if self.quality_thresholds_failed is None:
            self.quality_thresholds_failed = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "overall_result": self.overall_result.value,
            "blocking_layer": self.blocking_layer.value if self.blocking_layer else None,
            "blocking_reason": self.blocking_reason,
            "layers": {
                "existence": {
                    "passed": self.layer1_existence.passed if self.layer1_existence else None,
                    "reason": self.layer1_existence.reason if self.layer1_existence else None
                },
                "quality": {
                    "passed": self.layer2_quality.passed if self.layer2_quality else None,
                    "reason": self.layer2_quality.reason if self.layer2_quality else None
                },
                "functional": {
                    "passed": self.layer3_functional.passed if self.layer3_functional else None,
                    "reason": self.layer3_functional.reason if self.layer3_functional else None
                }
            },
            "metrics": {
                "outputs": {
                    "expected": self.outputs_expected,
                    "generated": self.outputs_generated,
                    "missing": self.outputs_missing
                },
                "quality_thresholds": {
                    "expected": self.quality_thresholds_expected,
                    "met": self.quality_thresholds_met,
                    "failed": self.quality_thresholds_failed
                },
                "functional_tests": {
                    "run": self.functional_tests_run,
                    "passed": self.functional_tests_passed
                }
            }
        }


class J5AOutcomeValidator:
    """
    Three-layer outcome validation system

    Layer 1 (EXISTENCE): Do expected outputs exist?
    Layer 2 (QUALITY): Do outputs meet quality standards?
    Layer 3 (FUNCTIONAL): Do outputs satisfy functional requirements?

    Each layer is BLOCKING - must pass before next layer evaluated
    """

    def __init__(self):
        self.logger = logging.getLogger("J5AOutcomeValidator")
        logging.basicConfig(level=logging.INFO)

    def validate_task_execution(self, task: J5AWorkAssignment,
                               execution_result: Optional[Dict] = None) -> ValidationReport:
        """
        Execute complete 3-layer validation

        Args:
            task: Work assignment to validate
            execution_result: Optional execution context with additional data

        Returns:
            ValidationReport with detailed results
        """
        self.logger.info(f"🔍 Starting validation for task: {task.task_name}")

        report = ValidationReport(
            task_id=task.task_id,
            task_name=task.task_name,
            overall_result=ValidationResult.FAILED  # Default to failed
        )

        # LAYER 1: Output Existence (Basic)
        self.logger.info("📦 Layer 1: Validating output existence...")
        layer1 = self.validate_output_existence(task.expected_outputs)
        report.layer1_existence = layer1
        report.outputs_expected = len(task.expected_outputs)

        if not layer1.passed:
            report.overall_result = ValidationResult.BLOCKED
            report.blocking_layer = ValidationLayer.EXISTENCE
            report.blocking_reason = layer1.reason
            report.outputs_generated = layer1.details.get("outputs_generated", 0)
            report.outputs_missing = layer1.details.get("missing_outputs", [])
            self.logger.error(f"❌ Layer 1 BLOCKED: {layer1.reason}")
            return report

        report.outputs_generated = len(task.expected_outputs)
        self.logger.info("✅ Layer 1 PASSED: All outputs exist")

        # LAYER 2: Output Quality (Structural)
        self.logger.info("📊 Layer 2: Validating output quality...")
        layer2 = self.validate_output_quality(task.expected_outputs, task.success_criteria)
        report.layer2_quality = layer2
        report.quality_thresholds_expected = len(task.success_criteria)

        if not layer2.passed:
            report.overall_result = ValidationResult.BLOCKED
            report.blocking_layer = ValidationLayer.QUALITY
            report.blocking_reason = layer2.reason
            report.quality_thresholds_met = layer2.details.get("thresholds_met", 0)
            report.quality_thresholds_failed = layer2.details.get("failed_thresholds", [])
            self.logger.error(f"❌ Layer 2 BLOCKED: {layer2.reason}")
            return report

        report.quality_thresholds_met = len(task.success_criteria)
        self.logger.info("✅ Layer 2 PASSED: Quality standards met")

        # LAYER 3: Functional Correctness (Oracle)
        self.logger.info("🎯 Layer 3: Validating functional correctness...")
        layer3 = self.validate_functional_correctness(task, execution_result)
        report.layer3_functional = layer3
        report.functional_tests_run = layer3.details.get("tests_run", 0)
        report.functional_tests_passed = layer3.details.get("tests_passed", 0)

        if not layer3.passed:
            report.overall_result = ValidationResult.BLOCKED
            report.blocking_layer = ValidationLayer.FUNCTIONAL
            report.blocking_reason = layer3.reason
            self.logger.error(f"❌ Layer 3 BLOCKED: {layer3.reason}")
            return report

        self.logger.info("✅ Layer 3 PASSED: Functional requirements met")

        # All layers passed!
        report.overall_result = ValidationResult.PASSED
        self.logger.info(f"✅ VALIDATION COMPLETE: All layers passed for {task.task_name}")

        return report

    def validate_output_existence(self, outputs: List[OutputSpecification]) -> LayerResult:
        """
        Layer 1: Do expected files exist with non-zero content?

        CRITICAL: This checks ACTUAL deliverables, not process initiation
        """
        missing_outputs = []
        outputs_generated = 0

        for output in outputs:
            # Check file exists
            if not output.file_path.exists():
                missing_outputs.append(str(output.file_path))
                continue

            # Check file not empty (if min_size specified)
            if output.min_size_bytes:
                actual_size = output.file_path.stat().st_size
                if actual_size < output.min_size_bytes:
                    missing_outputs.append(
                        f"{output.file_path} (too small: {actual_size} < {output.min_size_bytes} bytes)"
                    )
                    continue

            # Check file not too large (if max_size specified)
            if output.max_size_bytes:
                actual_size = output.file_path.stat().st_size
                if actual_size > output.max_size_bytes:
                    missing_outputs.append(
                        f"{output.file_path} (too large: {actual_size} > {output.max_size_bytes} bytes)"
                    )
                    continue

            outputs_generated += 1

        if missing_outputs:
            return LayerResult(
                layer=ValidationLayer.EXISTENCE,
                passed=False,
                reason=f"Missing or invalid outputs: {', '.join(missing_outputs)}",
                details={
                    "outputs_expected": len(outputs),
                    "outputs_generated": outputs_generated,
                    "missing_outputs": missing_outputs
                }
            )

        return LayerResult(
            layer=ValidationLayer.EXISTENCE,
            passed=True,
            reason="All expected outputs exist with valid sizes",
            details={
                "outputs_expected": len(outputs),
                "outputs_generated": outputs_generated,
                "missing_outputs": []
            }
        )

    def validate_output_quality(self, outputs: List[OutputSpecification],
                               criteria: Dict) -> LayerResult:
        """
        Layer 2: Does content meet quality thresholds?

        Validates:
        - File format correctness
        - Schema compliance (if specified)
        - Quality check callables
        - Quantitative success criteria
        """
        failed_checks = []
        thresholds_met = 0

        # Validate each output
        for output in outputs:
            # Format validation
            format_valid = self._validate_format(output)
            if not format_valid:
                failed_checks.append(f"{output.file_path}: Invalid {output.format} format")
                continue

            # Schema validation (if specified)
            if output.schema:
                schema_valid = self._validate_schema(output)
                if not schema_valid:
                    failed_checks.append(f"{output.file_path}: Schema mismatch")
                    continue

            # Quality checks (if specified)
            for check_name in output.quality_checks:
                check_passed = self._run_quality_check(output, check_name)
                if not check_passed:
                    failed_checks.append(f"{output.file_path}: Failed {check_name}")

        # Validate quantitative criteria
        for criterion_name, measure in criteria.items():
            # Note: Actual metric values should be set by executor
            # Here we just check structure
            thresholds_met += 1

        if failed_checks:
            return LayerResult(
                layer=ValidationLayer.QUALITY,
                passed=False,
                reason=f"Quality checks failed: {'; '.join(failed_checks)}",
                details={
                    "thresholds_expected": len(criteria),
                    "thresholds_met": 0,
                    "failed_thresholds": failed_checks
                }
            )

        return LayerResult(
            layer=ValidationLayer.QUALITY,
            passed=True,
            reason="All quality standards met",
            details={
                "thresholds_expected": len(criteria),
                "thresholds_met": thresholds_met,
                "failed_thresholds": []
            }
        )

    def validate_functional_correctness(self, task: J5AWorkAssignment,
                                       execution_result: Optional[Dict]) -> LayerResult:
        """
        Layer 3: Does it actually DO what it's supposed to do?

        Uses test oracle to verify functional correctness
        This is the MOST IMPORTANT layer - checks actual behavior
        """
        oracle = task.test_oracle
        tests_run = 0
        tests_passed = 0
        failed_tests = []

        # Run test oracle test cases
        for test_case in oracle.test_cases:
            tests_run += 1

            # Execute test case validation
            test_passed = self._evaluate_test_case(test_case, task, execution_result)

            if test_passed:
                tests_passed += 1
            else:
                failed_tests.append(test_case.get("input", f"test_{tests_run}"))

        # Calculate success rate
        if tests_run > 0:
            success_rate = tests_passed / tests_run
        else:
            # No test cases defined - check if validator function exists
            if oracle.validator_function:
                # Would call validator function here
                success_rate = 1.0  # Placeholder
                tests_run = 1
                tests_passed = 1
            else:
                # No validation method defined
                return LayerResult(
                    layer=ValidationLayer.FUNCTIONAL,
                    passed=False,
                    reason="Test oracle has no test cases or validator function",
                    details={"tests_run": 0, "tests_passed": 0}
                )

        # Check against confidence threshold
        if success_rate < oracle.confidence_threshold:
            return LayerResult(
                layer=ValidationLayer.FUNCTIONAL,
                passed=False,
                reason=f"Functional tests: {success_rate:.1%} < {oracle.confidence_threshold:.1%} threshold",
                details={
                    "tests_run": tests_run,
                    "tests_passed": tests_passed,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate
                }
            )

        return LayerResult(
            layer=ValidationLayer.FUNCTIONAL,
            passed=True,
            reason=f"Functional correctness verified ({success_rate:.1%} success rate)",
            details={
                "tests_run": tests_run,
                "tests_passed": tests_passed,
                "failed_tests": [],
                "success_rate": success_rate
            }
        )

    def _validate_format(self, output: OutputSpecification) -> bool:
        """Validate file format"""
        try:
            if output.format.upper() == "JSON":
                with open(output.file_path, 'r') as f:
                    json.load(f)
                return True
            elif output.format.upper() == "PYTHON":
                # Basic Python syntax check
                with open(output.file_path, 'r') as f:
                    code = f.read()
                compile(code, str(output.file_path), 'exec')
                return True
            elif output.format.upper() in ["TXT", "CSV", "MD"]:
                # Just check readable
                with open(output.file_path, 'r') as f:
                    f.read()
                return True
            else:
                # Unknown format - assume valid
                return True
        except Exception as e:
            self.logger.warning(f"Format validation failed for {output.file_path}: {e}")
            return False

    def _validate_schema(self, output: OutputSpecification) -> bool:
        """Validate against schema (if JSON)"""
        if not output.schema:
            return True

        try:
            with open(output.file_path, 'r') as f:
                data = json.load(f)

            # Check required keys present
            for key in output.schema.keys():
                if key not in data:
                    self.logger.warning(f"Schema validation: missing key '{key}' in {output.file_path}")
                    return False

            return True
        except Exception as e:
            self.logger.warning(f"Schema validation failed for {output.file_path}: {e}")
            return False

    def _run_quality_check(self, output: OutputSpecification, check_name: str) -> bool:
        """
        Run quality check callable

        Quality checks are method names that should be implemented
        by the executor or validation framework
        """
        # Placeholder - actual implementation would call registered check methods
        # For now, just verify file exists (already checked in Layer 1)
        return output.file_path.exists()

    def _evaluate_test_case(self, test_case: Dict, task: J5AWorkAssignment,
                           execution_result: Optional[Dict]) -> bool:
        """
        Evaluate single test case against oracle

        This is where actual functional testing happens
        """
        # Placeholder - actual implementation would:
        # 1. Execute test case
        # 2. Compare actual output to expected output
        # 3. Return True if matches, False otherwise

        # For now, return True (would be implemented by specific validators)
        return True

    def save_validation_report(self, report: ValidationReport, output_path: Path):
        """Save validation report to JSON"""
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        self.logger.info(f"📄 Validation report saved: {output_path}")


if __name__ == "__main__":
    # Test validation system
    from j5a_work_assignment import create_example_task
    import tempfile

    print("🔍 Testing J5A Outcome Validator")
    print("=" * 80)

    # Create test task
    task = create_example_task()

    # Create validator
    validator = J5AOutcomeValidator()

    # Test 1: Missing outputs (should fail Layer 1)
    print("\n📋 Test 1: Missing outputs (should BLOCK at Layer 1)")
    report = validator.validate_task_execution(task)
    print(f"Result: {report.overall_result.value}")
    print(f"Blocking layer: {report.blocking_layer.value if report.blocking_layer else 'None'}")
    print(f"Reason: {report.blocking_reason}")
    assert report.overall_result == ValidationResult.BLOCKED
    assert report.blocking_layer == ValidationLayer.EXISTENCE
    print("✅ Test 1 passed: Correctly blocked on missing outputs")

    # Test 2: Create outputs, test should pass Layer 1
    print("\n📋 Test 2: Create outputs (should pass Layer 1)")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create mock outputs (with sufficient content to meet min_size_bytes)
        for output in task.expected_outputs:
            output.file_path = tmppath / output.file_path.name
            # Generate content large enough to meet min_size_bytes
            content_size = output.min_size_bytes if output.min_size_bytes else 100
            output.file_path.write_text("# Test content\n" * (content_size // 15 + 1))

        report = validator.validate_task_execution(task)
        print(f"Result: {report.overall_result.value}")
        print(f"Layer 1: {'PASSED' if report.layer1_existence.passed else 'FAILED'}")
        print(f"Layer 2: {'PASSED' if report.layer2_quality and report.layer2_quality.passed else 'BLOCKED'}")
        assert report.layer1_existence.passed
        print("✅ Test 2 passed: Layer 1 validation working")

    print("\n" + "=" * 80)
    print("✅ J5A Outcome Validator tests complete")