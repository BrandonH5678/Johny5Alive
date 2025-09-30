#!/usr/bin/env python3
"""
Squirt Visual Design Extension - Phase 4 J5A Work Assignments
Advanced Features and Polish
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

def create_phase4_tasks():
    """Create all Phase 4 work assignments"""

    tasks = []

    # ===== TASK 4.1: Prompt Template System =====
    task_4_1 = J5AWorkAssignment(
        task_id="squirt_visual_4_1",
        task_name="Implement YAML-based prompt template system",
        domain="system_development",
        description="Create template engine for prompts with constraint injection",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "prompts" / "template_engine.py",
                format="Python",
                description="Prompt template engine",
                min_size_bytes=1000,
                quality_checks=["valid_python", "imports_work", "templates_work"]
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "prompts" / "templates.yaml",
                format="YAML",
                description="Prompt templates for various scenarios",
                min_size_bytes=500
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "templates_load": QuantitativeMeasure("yaml_templates_valid", 1.0, "==", "boolean"),
            "constraint_injection": QuantitativeMeasure("constraints_injected", 1.0, "==", "%"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Template system validation",
            description="Verify template system works",
            expected_behavior="Templates load, constraints inject, prompts generate",
            validation_method="Load templates, inject constraints, validate output",
            test_cases=[
                {"template": "landscape", "constraints": ["modern", "low_maintenance"], "expected": "prompt_with_constraints"},
                {"template": "hardscape", "constraints": ["durable", "pergola"], "expected": "prompt_with_constraints"}
            ]
        ),

        approved_architectures=["pyyaml"],
        forbidden_patterns=[],

        rollback_plan="rm -f visual/prompts/template_engine.py visual/prompts/templates.yaml",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_4_1)

    # ===== TASK 4.2: Metadata Enhancement =====
    task_4_2 = J5AWorkAssignment(
        task_id="squirt_visual_4_2",
        task_name="Implement comprehensive metadata tracking",
        domain="system_development",
        description="Track all inputs, outputs, constraints for every visual task",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "metadata.py",
                format="Python",
                description="Metadata tracking system",
                min_size_bytes=1500,
                quality_checks=["valid_python", "imports_work", "metadata_capture_works"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "captures_all_fields": QuantitativeMeasure("metadata_completeness", 1.0, "==", "%"),
            "integrates_with_memory": QuantitativeMeasure("vector_store_integration", 1.0, "==", "boolean"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Metadata system validation",
            description="Verify metadata tracking captures all fields",
            expected_behavior="All task inputs/outputs tracked, stored in vector DB",
            validation_method="Generate task, verify metadata completeness",
            test_cases=[
                {"task_type": "cad", "expected": "metadata_complete"},
                {"task_type": "concept", "expected": "metadata_complete"},
                {"metadata_query": "similar_tasks", "expected": "results_found"}
            ]
        ),

        approved_architectures=["ChromaDB"],
        forbidden_patterns=[],

        rollback_plan="rm -f visual/metadata.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_4_2)

    # ===== TASK 4.3: ControlNet Integration =====
    task_4_3 = J5AWorkAssignment(
        task_id="squirt_visual_4_3",
        task_name="Implement ControlNet for guided generation",
        domain="system_development",
        description="Add ControlNet support for AR compositing guidance",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "sd" / "controlnet_engine.py",
                format="Python",
                description="ControlNet integration for guided generation",
                min_size_bytes=1500,
                quality_checks=["valid_python", "imports_work", "controlnet_works"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "controlnet_loads": QuantitativeMeasure("controlnet_model_loads", 1.0, "==", "boolean"),
            "guided_generation": QuantitativeMeasure("guided_generation_works", 1.0, "==", "%"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="ControlNet validation",
            description="Verify ControlNet guided generation works",
            expected_behavior="ControlNet loads, guides generation based on input",
            validation_method="Generate with ControlNet guidance, validate output",
            test_cases=[
                {"guidance": "depth_map", "expected": "controlled_generation"},
                {"guidance": "edge_map", "expected": "controlled_generation"}
            ]
        ),

        approved_architectures=["diffusers", "controlnet"],
        forbidden_patterns=[],

        rollback_plan="rm -f visual/sd/controlnet_engine.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_4_3)

    # ===== TASK 4.4: Visual Operator Manual =====
    task_4_4 = J5AWorkAssignment(
        task_id="squirt_visual_4_4",
        task_name="Create Visual Workflows Operator Manual",
        domain="documentation",
        description="Comprehensive documentation for visual design workflows",
        assigned_date=datetime.now(),
        priority=Priority.LOW,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "VISUAL_WORKFLOWS_OPERATOR_MANUAL.md",
                format="Markdown",
                description="Complete visual workflows documentation",
                min_size_bytes=5000
            )
        ],

        success_criteria={
            "completeness": QuantitativeMeasure("sections_complete", 1.0, "==", "%"),
            "examples_included": QuantitativeMeasure("workflow_examples", 5, ">=", "count"),
            "troubleshooting": QuantitativeMeasure("troubleshooting_section_exists", 1.0, "==", "boolean")
        },

        test_oracle=TestOracle(
            name="Documentation validation",
            description="Verify operator manual is complete",
            expected_behavior="All workflows documented with examples",
            validation_method="Review manual for completeness",
            test_cases=[
                {"section": "concept_generation", "expected": "documented"},
                {"section": "cad_generation", "expected": "documented"},
                {"section": "ar_mockups", "expected": "documented"},
                {"section": "troubleshooting", "expected": "documented"}
            ]
        ),

        approved_architectures=[],
        forbidden_patterns=[],

        rollback_plan="rm -f VISUAL_WORKFLOWS_OPERATOR_MANUAL.md",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=False
        )
    )
    tasks.append(task_4_4)

    return tasks


if __name__ == "__main__":
    """Generate Phase 4 tasks for J5A queue"""

    tasks = create_phase4_tasks()

    print("=" * 80)
    print("Squirt Visual Design Extension - Phase 4 Tasks")
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