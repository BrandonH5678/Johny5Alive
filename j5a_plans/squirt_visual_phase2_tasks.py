#!/usr/bin/env python3
"""
Squirt Visual Design Extension - Phase 2 J5A Work Assignments
Integration with existing Squirt systems
"""

from datetime import datetime
from pathlib import Path
from j5a_work_assignment import (
    J5AWorkAssignment,
    Priority,
    OutputSpecification,
    QuantitativeMeasure,
    TestOracle,
    EscalationPolicy
)

# Base path for Squirt
SQUIRT_PATH = Path("/home/johnny5/Squirt")

def create_phase2_tasks():
    """Create all Phase 2 work assignments"""

    tasks = []

    # ===== TASK 2.1: Thermal Safety Integration =====
    task_2_1 = J5AWorkAssignment(
        task_id="squirt_visual_2_1",
        task_name="Integrate visual processing with thermal safety",
        domain="system_development",
        description="Create thermal coordinator for visual tasks integrated with existing thermal_safety_manager",
        assigned_date=datetime.now(),
        priority=Priority.HIGH,  # Safety-critical

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "thermal_coordinator.py",
                format="Python",
                description="Thermal safety coordinator for visual tasks",
                min_size_bytes=1000,
                quality_checks=["valid_python", "imports_work", "thermal_checks_functional"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "thermal_integration_works": QuantitativeMeasure("thermal_tests_pass", 1.0, "==", "%"),
            "blocks_when_hot": QuantitativeMeasure("blocks_at_critical_temp", 1.0, "==", "boolean"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Thermal integration validation",
            description="Verify thermal safety integration works",
            expected_behavior="Blocks visual tasks when CPU temp exceeds thresholds",
            validation_method="Test thermal checks at various temperatures",
            test_cases=[
                {"cpu_temp": 70, "task_type": "concept", "expected": "allowed"},
                {"cpu_temp": 85, "task_type": "concept", "expected": "blocked"},
                {"cpu_temp": 76, "task_type": "cad", "expected": "allowed"},
                {"cpu_temp": 80, "task_type": "cad", "expected": "blocked"}
            ]
        ),

        approved_architectures=["ThermalSafetyManager"],
        forbidden_patterns=[
            r"import os.*system",  # No system calls
            r"subprocess\.call",  # Use subprocess.run
        ],

        rollback_plan="rm -f visual/thermal_coordinator.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=True,  # Safety-critical
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_2_1)

    # ===== TASK 2.2: Business Hours Coordination =====
    task_2_2 = J5AWorkAssignment(
        task_id="squirt_visual_2_2",
        task_name="Coordinate visual tasks with business hours",
        domain="system_development",
        description="Create business coordinator to defer visual tasks during LibreOffice business hours",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "business_coordinator.py",
                format="Python",
                description="Business hours coordinator for visual tasks",
                min_size_bytes=800,
                quality_checks=["valid_python", "imports_work", "business_hours_logic_works"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "business_hours_respected": QuantitativeMeasure("business_hours_tests_pass", 1.0, "==", "%"),
            "priority_override_works": QuantitativeMeasure("high_priority_allowed", 1.0, "==", "boolean"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Business hours validation",
            description="Verify business hours coordination works",
            expected_behavior="Low priority visual tasks deferred during business hours, high priority allowed",
            validation_method="Test coordination during and outside business hours",
            test_cases=[
                {"time": "2024-09-30 14:00", "day": "Monday", "priority": "normal", "expected": "deferred"},
                {"time": "2024-09-30 14:00", "day": "Monday", "priority": "high", "expected": "allowed"},
                {"time": "2024-09-30 20:00", "day": "Monday", "priority": "normal", "expected": "allowed"},
                {"time": "2024-09-30 14:00", "day": "Saturday", "priority": "normal", "expected": "allowed"}
            ]
        ),

        approved_architectures=["LibreOfficeCoordinator"],
        forbidden_patterns=[],

        rollback_plan="rm -f visual/business_coordinator.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_2_2)

    # ===== TASK 2.3: Queue Integration =====
    task_2_3 = J5AWorkAssignment(
        task_id="squirt_visual_2_3",
        task_name="Implement visual task queue manager",
        domain="system_development",
        description="Create queue manager for visual tasks with thermal/business coordination",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "visual_queue_manager.py",
                format="Python",
                description="Queue manager for visual processing tasks",
                min_size_bytes=1500,
                quality_checks=["valid_python", "imports_work", "queue_operations_work"]
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual_queue.json",
                format="JSON",
                description="Persistent queue storage",
                min_size_bytes=2,
                schema={"queue": list}
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "queue_operations_work": QuantitativeMeasure("queue_tests_pass", 1.0, "==", "%"),
            "persistence_works": QuantitativeMeasure("queue_survives_restart", 1.0, "==", "boolean"),
            "integration_works": QuantitativeMeasure("thermal_business_checks_enforced", 1.0, "==", "boolean"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Queue manager validation",
            description="Verify queue manager operations work correctly",
            expected_behavior="Tasks enqueued, retrieved in priority order, persist across restarts",
            validation_method="Enqueue tasks, retrieve, restart, verify persistence",
            test_cases=[
                {"operation": "enqueue_task", "expected": "success"},
                {"operation": "get_next_task", "expected": "task_returned"},
                {"operation": "mark_complete", "expected": "status_updated"},
                {"operation": "restart_and_load", "expected": "queue_restored"}
            ]
        ),

        approved_architectures=["VoiceQueueManager"],
        forbidden_patterns=[],

        rollback_plan="rm -f visual/visual_queue_manager.py visual_queue.json",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_2_3)

    # ===== TASK 2.4: Voice Input Integration =====
    task_2_4 = J5AWorkAssignment(
        task_id="squirt_visual_2_4",
        task_name="Integrate visual commands with voice processing",
        domain="system_development",
        description="Create voice command parser for visual task detection and queueing",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "voice_visual_commands.py",
                format="Python",
                description="Voice command parser for visual tasks",
                min_size_bytes=1200,
                quality_checks=["valid_python", "imports_work", "pattern_matching_works"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "voice_parsing_works": QuantitativeMeasure("voice_parse_tests_pass", 1.0, "==", "%"),
            "pattern_detection": QuantitativeMeasure("visual_commands_detected", 0.9, ">=", "%"),
            "queue_integration": QuantitativeMeasure("tasks_enqueued_from_voice", 1.0, "==", "boolean"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Voice integration validation",
            description="Verify voice command parsing and task creation",
            expected_behavior="Voice commands like 'generate CAD' detected and enqueued as tasks",
            validation_method="Test parsing with various voice command patterns",
            test_cases=[
                {"text": "generate a CAD model for pipe fitting", "expected": "cad_task"},
                {"text": "show me a concept render of the layout", "expected": "concept_task"},
                {"text": "add a pergola to the photo", "expected": "ar_task"},
                {"text": "prepare invoice for client", "expected": "no_visual_task"}
            ]
        ),

        approved_architectures=["voice_engine", "VoiceQueueManager"],
        forbidden_patterns=[],

        rollback_plan="rm -f visual/voice_visual_commands.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_2_4)

    # ===== TASK 2.5: Phase 2 Testing =====
    task_2_5 = J5AWorkAssignment(
        task_id="squirt_visual_2_5",
        task_name="Create Phase 2 integration test suite",
        domain="system_development",
        description="Comprehensive tests for Phase 2 integration components",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "tests" / "test_visual_integration.py",
                format="Python",
                description="Phase 2 integration test suite",
                min_size_bytes=2000,
                quality_checks=["valid_python", "tests_discoverable", "all_tests_pass"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "all_tests_pass": QuantitativeMeasure("test_pass_rate", 1.0, "==", "%"),
            "coverage": QuantitativeMeasure("code_coverage", 0.8, ">=", "%"),
            "integration_verified": QuantitativeMeasure("cross_component_tests_pass", 1.0, "==", "%"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Integration test suite validation",
            description="Verify all Phase 2 integration tests pass",
            expected_behavior="All integration components tested, 80%+ coverage",
            validation_method="Run pytest with coverage",
            test_cases=[
                {"component": "thermal_coordinator", "expected": "tests_pass"},
                {"component": "business_coordinator", "expected": "tests_pass"},
                {"component": "visual_queue_manager", "expected": "tests_pass"},
                {"component": "voice_visual_commands", "expected": "tests_pass"},
                {"integration": "thermal_queue", "expected": "tests_pass"},
                {"integration": "voice_queue", "expected": "tests_pass"}
            ]
        ),

        approved_architectures=["pytest"],
        forbidden_patterns=[
            r"@pytest\.mark\.skip",  # No skipping tests
            r"pass\s*#\s*TODO",  # No incomplete tests
        ],

        rollback_plan="rm -f tests/test_visual_integration.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=False  # Keep tests even if some fail initially
        )
    )
    tasks.append(task_2_5)

    return tasks


if __name__ == "__main__":
    """Generate Phase 2 tasks for J5A queue"""

    tasks = create_phase2_tasks()

    print("=" * 80)
    print("Squirt Visual Design Extension - Phase 2 Tasks")
    print("=" * 80)
    print(f"\nGenerated {len(tasks)} tasks for J5A queue:\n")

    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task.task_id}: {task.task_name}")
        print(f"   Priority: {task.priority.name}")
        print(f"   Expected outputs: {len(task.expected_outputs)}")
        print(f"   Success criteria: {len(task.success_criteria)}")
        print()

    print("=" * 80)
    print("Ready to load into J5A queue manager")
    print("=" * 80)