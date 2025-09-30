#!/usr/bin/env python3
"""
J5A Work Assignment Schema
Defines comprehensive task structure for overnight validation-focused work
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum


class Priority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class TaskStatus(Enum):
    """Task execution status"""
    QUEUED = "queued"
    PRE_FLIGHT = "pre_flight"
    POC = "proof_of_concept"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ValidationResult(Enum):
    """Validation outcome"""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class OutputSpecification:
    """
    Precise specification of expected output
    Enforces outcome-based validation (not process-based)
    """
    file_path: Path
    format: str  # e.g., "JSON", "CSV", "TXT", "Python"
    description: str

    # Schema validation
    schema: Optional[Dict] = None

    # Content validation
    min_size_bytes: Optional[int] = None
    max_size_bytes: Optional[int] = None

    # Quality checks (callables that return bool)
    quality_checks: List[str] = field(default_factory=list)  # Method names to call

    # Test oracle - sample expected output for validation
    sample_expected_output: Optional[Any] = None

    def __post_init__(self):
        """Ensure file_path is Path object"""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)


@dataclass
class QuantitativeMeasure:
    """
    Measurable success criterion with threshold
    """
    metric_name: str
    threshold: float
    comparison: str  # ">=", "<=", "==", ">", "<"
    unit: str = ""

    def evaluate(self, actual_value: float) -> bool:
        """Evaluate if actual value meets threshold"""
        if self.comparison == ">=":
            return actual_value >= self.threshold
        elif self.comparison == "<=":
            return actual_value <= self.threshold
        elif self.comparison == "==":
            return actual_value == self.threshold
        elif self.comparison == ">":
            return actual_value > self.threshold
        elif self.comparison == "<":
            return actual_value < self.threshold
        else:
            raise ValueError(f"Invalid comparison: {self.comparison}")


@dataclass
class TestOracle:
    """
    Defines ground truth for validation
    Answers: "How do we KNOW if this is correct?"
    """
    name: str
    description: str

    # Ground truth definition
    expected_behavior: str
    validation_method: str  # How to verify correctness

    # Executable validation
    validator_function: Optional[str] = None  # Method name to call

    # Sample test cases with known correct outputs
    test_cases: List[Dict[str, Any]] = field(default_factory=list)

    # Confidence threshold (e.g., 0.8 = 80% confidence required)
    confidence_threshold: float = 0.8


@dataclass
class EscalationPolicy:
    """
    Defines what happens when task fails/blocks
    """
    notify_immediately: bool = False
    max_retry_attempts: int = 0
    rollback_on_failure: bool = True
    human_intervention_required: bool = False
    escalation_message: str = ""


@dataclass
class J5AWorkAssignment:
    """
    Comprehensive task definition for J5A overnight work
    Enforces outcome-based validation and rigorous standards
    """
    # Basic identification
    task_id: str
    task_name: str
    domain: str  # e.g., "audio_processing", "database_operations"
    description: str
    assigned_date: datetime
    priority: Priority

    # CRITICAL: Expected outputs (outcome-focused)
    # MANDATORY - cannot be empty
    expected_outputs: List[OutputSpecification]

    # CRITICAL: Success criteria (quantified, measurable)
    # MANDATORY - must be measurable
    success_criteria: Dict[str, QuantitativeMeasure]

    # Test oracle (ground truth)
    test_oracle: TestOracle

    # Validation samples for POC testing
    validation_samples: List[Path] = field(default_factory=list)

    # Quality gate requirements
    requires_poc: bool = True  # Proof-of-concept required before full implementation
    requires_stratified_sampling: bool = True  # 3-segment sampling validation
    minimum_sampling_success_rate: float = 0.6  # 60% minimum

    # Methodology enforcement
    approved_architectures: List[str] = field(default_factory=list)  # Must use these
    forbidden_patterns: List[str] = field(default_factory=list)  # Must not use these
    extends_existing_class: Optional[str] = None  # If must extend existing architecture

    # Resource constraints
    max_ram_gb: float = 3.0  # Default safety threshold
    max_thermal_celsius: float = 80.0
    max_duration_hours: float = 8.0  # Overnight window

    # Business hours constraints
    requires_business_hours_clear: bool = False  # If needs LibreOffice priority cleared

    # Rollback and safety
    rollback_plan: str = ""
    failure_escalation: EscalationPolicy = field(default_factory=lambda: EscalationPolicy())

    # Execution tracking
    status: TaskStatus = TaskStatus.QUEUED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: str = ""

    # Validation results
    validation_results: Dict[str, Any] = field(default_factory=dict)
    gates_passed: List[str] = field(default_factory=list)
    gates_failed: List[str] = field(default_factory=list)
    blocking_gate: Optional[str] = None

    # Actual metrics achieved
    actual_metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task definition completeness"""
        # Ensure expected_outputs is not empty
        if not self.expected_outputs:
            raise ValueError("expected_outputs cannot be empty - must define what outputs are expected")

        # Ensure success_criteria is not empty
        if not self.success_criteria:
            raise ValueError("success_criteria cannot be empty - must define measurable success criteria")

        # Ensure test_oracle is provided
        if not self.test_oracle:
            raise ValueError("test_oracle required - must define how to verify correctness")

    def mark_gate_passed(self, gate_name: str):
        """Record quality gate passage"""
        if gate_name not in self.gates_passed:
            self.gates_passed.append(gate_name)

    def mark_gate_failed(self, gate_name: str, reason: str):
        """Record quality gate failure"""
        if gate_name not in self.gates_failed:
            self.gates_failed.append(gate_name)
        self.blocking_gate = gate_name
        self.error_message = reason
        self.status = TaskStatus.BLOCKED

    def record_metric(self, metric_name: str, value: float):
        """Record actual metric achieved"""
        self.actual_metrics[metric_name] = value

    def evaluate_success_criteria(self) -> bool:
        """
        Evaluate if all success criteria met
        Returns True only if ALL criteria pass
        """
        for criterion_name, measure in self.success_criteria.items():
            if criterion_name not in self.actual_metrics:
                return False  # Missing metric

            actual_value = self.actual_metrics[criterion_name]
            if not measure.evaluate(actual_value):
                return False  # Criterion not met

        return True  # All criteria met

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "domain": self.domain,
            "description": self.description,
            "assigned_date": self.assigned_date.isoformat(),
            "priority": self.priority.name,
            "status": self.status.value,
            "expected_outputs": [
                {
                    "file_path": str(o.file_path),
                    "format": o.format,
                    "description": o.description
                }
                for o in self.expected_outputs
            ],
            "success_criteria": {
                name: {
                    "metric": measure.metric_name,
                    "threshold": measure.threshold,
                    "comparison": measure.comparison,
                    "unit": measure.unit
                }
                for name, measure in self.success_criteria.items()
            },
            "test_oracle": {
                "name": self.test_oracle.name,
                "description": self.test_oracle.description,
                "expected_behavior": self.test_oracle.expected_behavior
            },
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "blocking_gate": self.blocking_gate,
            "actual_metrics": self.actual_metrics,
            "success_criteria_met": self.evaluate_success_criteria() if self.actual_metrics else None
        }


def create_example_task() -> J5AWorkAssignment:
    """
    Example task definition showing proper structure
    """
    return J5AWorkAssignment(
        task_id="dev_001",
        task_name="Improve Sherlock voice processing error handling",
        domain="audio_processing",
        description="Add comprehensive error handling and recovery to voice_engine.py",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        # Expected outputs - MANDATORY
        expected_outputs=[
            OutputSpecification(
                file_path=Path("voice_engine.py"),
                format="Python",
                description="Updated voice_engine.py with error handling",
                min_size_bytes=10000,  # Must not be empty
                quality_checks=["passes_all_tests", "no_syntax_errors", "pylint_score_above_8"]
            ),
            OutputSpecification(
                file_path=Path("tests/test_voice_engine_errors.py"),
                format="Python",
                description="New test suite for error handling",
                min_size_bytes=1000,
                quality_checks=["all_tests_pass"]
            ),
            OutputSpecification(
                file_path=Path("validation_report.json"),
                format="JSON",
                description="Validation report with test results",
                schema={"test_results": dict, "metrics": dict},
                quality_checks=["valid_json", "all_required_fields_present"]
            )
        ],

        # Success criteria - MANDATORY, measurable
        success_criteria={
            "existing_tests_pass_rate": QuantitativeMeasure("existing_tests_pass_rate", 1.0, "==", "%"),
            "new_tests_pass_rate": QuantitativeMeasure("new_tests_pass_rate", 1.0, "==", "%"),
            "code_coverage": QuantitativeMeasure("code_coverage", 0.85, ">=", "%"),
            "no_regressions": QuantitativeMeasure("regression_count", 0, "==", "count")
        },

        # Test oracle - how to verify correctness
        test_oracle=TestOracle(
            name="Error handling validation",
            description="Verify error handling works correctly",
            expected_behavior="System gracefully handles errors without crashes",
            validation_method="Run error injection tests and verify recovery",
            test_cases=[
                {"input": "corrupted_audio.wav", "expected": "error_handled_gracefully"},
                {"input": "missing_file.wav", "expected": "error_reported_clearly"}
            ]
        ),

        # Methodology enforcement
        approved_architectures=["VoiceEngineManager"],
        extends_existing_class="VoiceEngineManager",
        forbidden_patterns=[
            r"except:\s*pass",  # No silent error swallowing
            r"#\s*TODO.*error",  # No deferred error handling
        ],

        # Escalation policy
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True,
            human_intervention_required=False
        )
    )


if __name__ == "__main__":
    # Test task definition
    task = create_example_task()
    print(f"✅ Created example task: {task.task_name}")
    print(f"📊 Expected outputs: {len(task.expected_outputs)}")
    print(f"📈 Success criteria: {len(task.success_criteria)}")
    print(f"🎯 Test oracle: {task.test_oracle.name}")

    # Test validation
    print("\n🔍 Task definition validation:")
    try:
        # Should work - has all required fields
        print("✅ Task definition valid")
    except ValueError as e:
        print(f"❌ Task definition invalid: {e}")

    # Test incomplete task (should fail)
    print("\n🔍 Testing incomplete task (should fail):")
    try:
        incomplete = J5AWorkAssignment(
            task_id="bad_001",
            task_name="Bad task",
            domain="test",
            description="Missing required fields",
            assigned_date=datetime.now(),
            priority=Priority.LOW,
            expected_outputs=[],  # EMPTY - should fail
            success_criteria={},  # EMPTY - should fail
            test_oracle=None  # MISSING - should fail
        )
        print("❌ Should have failed but didn't!")
    except ValueError as e:
        print(f"✅ Correctly rejected incomplete task: {e}")