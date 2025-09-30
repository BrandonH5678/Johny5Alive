"""
J5A Work Assignment: Harmonize Intelligent Model Selection Across J5A
Task definitions for overnight/background execution
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TestOracle:
    """Defines how to validate task completion"""
    validation_commands: List[str]
    expected_outputs: List[str]
    quality_criteria: Dict[str, any]


@dataclass
class J5AWorkAssignment:
    """Complete specification for J5A overnight task"""
    task_id: str
    task_name: str
    domain: str  # system_development, documentation, validation, integration
    description: str
    priority: Priority
    risk_level: RiskLevel

    # Outputs and validation
    expected_outputs: List[str]
    success_criteria: Dict[str, any]
    test_oracle: TestOracle

    # Resource requirements
    estimated_tokens: int
    estimated_ram_gb: float
    estimated_duration_minutes: int
    thermal_risk: str  # low, medium, high

    # Dependencies and rollback
    dependencies: List[str]  # List of task_ids that must complete first
    blocking_conditions: List[str]
    rollback_plan: str

    # Context
    implementation_notes: Optional[str] = None


def create_harmonize_model_selection_tasks() -> List[J5AWorkAssignment]:
    """
    Create task definitions for harmonizing intelligent model selection across J5A
    """
    tasks = []

    # ============================================================================
    # PHASE 1: Update J5A Context Injection
    # ============================================================================

    task_1_1 = J5AWorkAssignment(
        task_id="harmonize_model_1_1",
        task_name="Add IntelligentModelSelector to J5A CLAUDE.md",
        domain="documentation",
        description="Insert IntelligentModelSelector auto-injection section into J5A CLAUDE.md before existing overnight task protocols",
        priority=Priority.HIGH,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/CLAUDE.md",
            "/home/johnny5/Johny5Alive/CLAUDE.md.backup"
        ],

        success_criteria={
            "intelligent_model_section_present": True,
            "section_before_line": 150,  # Must be prominent in auto-injection
            "red_flags_updated": True,
            "example_code_included": True,
            "consistent_with_squirt_sherlock": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -n 'IntelligentModelSelector' /home/johnny5/Johny5Alive/CLAUDE.md",
                "grep -n '🤖 INTELLIGENT MODEL SELECTION' /home/johnny5/Johny5Alive/CLAUDE.md",
                "grep -A 10 'RED FLAGS' /home/johnny5/Johny5Alive/CLAUDE.md | grep -i 'model.*selection'",
            ],
            expected_outputs=[
                "Multiple IntelligentModelSelector references found",
                "Section appears before line 150",
                "RED FLAGS include model selection violations"
            ],
            quality_criteria={
                "min_intelligent_model_references": 5,
                "example_code_blocks": 2,
                "red_flag_items": 3
            }
        ),

        estimated_tokens=12000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=30,
        thermal_risk="low",

        dependencies=[],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Johny5Alive/CLAUDE.md from CLAUDE.md.backup",

        implementation_notes="""
        Add section modeled after Squirt/Sherlock CLAUDE.md patterns:

        ## 🤖 INTELLIGENT MODEL SELECTION (MANDATORY FOR J5A OVERNIGHT TASKS)

        ### MANDATORY AUTO-INJECTION: Audio/ML Processing Tasks

        **BEFORE Any Overnight Task with Audio/ML Processing:**
        **CRITICAL CONSTRAINTS (Auto-Inject):**
        - **🤖 INTELLIGENT MODEL SELECTION**: ALWAYS use IntelligentModelSelector - NEVER hard-code model choice
        - **Memory Limit**: 3.0GB safe threshold for J5A coordination overhead
        - **System Viability**: Completion > Quality (85% complete beats 95% crash)
        - **Cross-System Impact**: Model selection affects Squirt/Sherlock resource allocation

        Include RED FLAGS and correct implementation patterns.
        """
    )
    tasks.append(task_1_1)

    # ============================================================================
    # PHASE 2: Update J5A Operator Manual
    # ============================================================================

    task_2_1 = J5AWorkAssignment(
        task_id="harmonize_model_2_1",
        task_name="Add Model Selection Checkpoint to J5A Operator Manual",
        domain="documentation",
        description="Insert Checkpoint 0.5: Model Selection Validation between Checkpoint 0 and 1 in JOHNY5_AI_OPERATOR_MANUAL.md",
        priority=Priority.HIGH,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md",
            "/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md.backup"
        ],

        success_criteria={
            "checkpoint_0_5_added": True,
            "blocking_gate_marked": True,
            "validation_commands_provided": True,
            "critical_failure_section_updated": True,
            "consistent_with_existing_checkpoints": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -n 'Checkpoint 0.5.*Model Selection' /home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md",
                "grep -A 20 'Checkpoint 0.5' /home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md | grep 'BLOCKING GATE'",
                "grep -A 10 'CRITICAL FAILURE INDICATORS' /home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md | grep -i 'model.*selection'",
            ],
            expected_outputs=[
                "Checkpoint 0.5 found in document",
                "BLOCKING GATE marker present",
                "Model selection in failure indicators"
            ],
            quality_criteria={
                "checkpoint_gate_checklist_items": 4,
                "validation_command_examples": 3,
                "failure_response_defined": True
            }
        ),

        estimated_tokens=10000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=20,
        thermal_risk="low",

        dependencies=["harmonize_model_1_1"],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md from backup",

        implementation_notes="""
        Insert between existing Checkpoint 0 and Checkpoint 1:

        **Checkpoint 0.5: Model Selection Validation (MANDATORY - BLOCKING GATE)**
        **GATE KEEPER**: Must validate intelligent model selection for audio/ML tasks BEFORE queuing
        - [ ] **IntelligentModelSelector Usage Verified** - All audio/ML tasks use constraint-aware selection
        - [ ] **Hard-Coded Models Detected** - No tasks with hard-coded tiny/small/medium/large-v3
        - [ ] **RAM Constraints Validated** - Selected models fit within 3.0GB safe threshold
        - [ ] **System Viability Priority** - Completion prioritized over theoretical "best quality"

        **MANDATORY VALIDATION:**
        ```bash
        python3 src/j5a_model_selection_validator.py task_definition.json
        # GATE KEEPER: Must pass validation OR task queuing BLOCKED
        ```

        **FAILURE RESPONSE**: If model selection validation fails, task BLOCKED until corrected
        """
    )
    tasks.append(task_2_1)

    # ============================================================================
    # PHASE 3: Create Model Selection Validator Tool
    # ============================================================================

    task_3_1 = J5AWorkAssignment(
        task_id="harmonize_model_3_1",
        task_name="Create j5a_model_selection_validator.py",
        domain="system_development",
        description="Implement model selection validation tool to scan task definitions for hard-coded models and RAM constraint violations",
        priority=Priority.HIGH,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/src/j5a_model_selection_validator.py"
        ],

        success_criteria={
            "detects_hard_coded_models": True,
            "validates_ram_constraints": True,
            "integrates_with_queue_manager": True,
            "provides_clear_error_messages": True,
            "test_mode_functional": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 /home/johnny5/Johny5Alive/src/j5a_model_selection_validator.py --test-mode",
                "python3 -c 'from src.j5a_model_selection_validator import ModelSelectionValidator; v = ModelSelectionValidator(); print(v.validate_task({\"uses_audio\": True, \"model\": \"large-v3\"}))'",
            ],
            expected_outputs=[
                "Test mode passes all cases",
                "Hard-coded model detection works",
                "IntelligentModelSelector usage approved"
            ],
            quality_criteria={
                "test_cases_passed": 6,  # 3 positive, 3 negative
                "false_positive_rate": 0.0,
                "false_negative_rate": 0.0
            }
        ),

        estimated_tokens=8000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=25,
        thermal_risk="low",

        dependencies=["harmonize_model_2_1"],
        blocking_conditions=[],

        rollback_plan="Remove /home/johnny5/Johny5Alive/src/j5a_model_selection_validator.py",

        implementation_notes="""
        Implementation requirements:

        1. ModelSelectionValidator class with methods:
           - validate_task(task_definition: dict) -> ValidationResult
           - detect_hard_coded_models(code: str) -> List[str]
           - validate_ram_constraints(model_name: str, available_ram_gb: float) -> bool
           - check_intelligent_selector_usage(code: str) -> bool

        2. Scan task definitions for:
           - whisper.load_model("tiny"|"small"|"medium"|"large-v3")
           - Hard-coded model strings
           - Missing IntelligentModelSelector import/usage

        3. Validation logic:
           - Audio/ML tasks MUST use IntelligentModelSelector
           - Model memory requirements < 3.0GB (J5A safe threshold)
           - Provide actionable error messages

        4. Test mode with sample tasks:
           - Positive: IntelligentModelSelector usage (should pass)
           - Negative: Hard-coded "large-v3" (should fail)
           - Negative: Model requiring 4GB RAM (should fail)
        """
    )
    tasks.append(task_3_1)

    # ============================================================================
    # PHASE 4: Integration Testing
    # ============================================================================

    task_4_1 = J5AWorkAssignment(
        task_id="harmonize_model_4_1",
        task_name="Integration test model selection validation",
        domain="validation",
        description="Test validator with sample task definitions and confirm integration with overnight queue manager",
        priority=Priority.HIGH,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/tests/model_selection_validation_results.json"
        ],

        success_criteria={
            "positive_tests_passed": True,
            "negative_tests_failed_correctly": True,
            "queue_manager_integration_works": True,
            "no_false_positives": True,
            "no_false_negatives": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -m pytest tests/test_model_selection_validator.py -v",
                "cat tests/model_selection_validation_results.json | jq '.tests_passed'",
            ],
            expected_outputs=[
                "All tests passed",
                "test_results.json shows 100% success"
            ],
            quality_criteria={
                "total_tests": 6,
                "tests_passed": 6,
                "tests_failed": 0,
                "integration_functional": True
            }
        ),

        estimated_tokens=5000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=15,
        thermal_risk="low",

        dependencies=["harmonize_model_3_1"],
        blocking_conditions=[],

        rollback_plan="N/A (test-only task, no production changes)",

        implementation_notes="""
        Test cases:

        1. POSITIVE: Task with IntelligentModelSelector
           - Expected: PASS

        2. POSITIVE: Non-audio task (no model selection needed)
           - Expected: PASS

        3. NEGATIVE: Task with hard-coded whisper.load_model("large-v3")
           - Expected: FAIL with clear error message

        4. NEGATIVE: Task selecting model requiring 4GB RAM
           - Expected: FAIL with RAM constraint violation

        5. NEGATIVE: Audio task without IntelligentModelSelector
           - Expected: FAIL with missing selector error

        6. INTEGRATION: Queue manager rejects invalid task
           - Expected: Task blocked from queuing

        Document all results in JSON format with pass/fail status and error messages.
        """
    )
    tasks.append(task_4_1)

    return tasks


if __name__ == "__main__":
    tasks = create_harmonize_model_selection_tasks()
    print(f"Created {len(tasks)} tasks for Harmonize Intelligent Model Selection")
    for task in tasks:
        print(f"  - {task.task_id}: {task.task_name} ({task.priority.value}, {task.risk_level.value})")
