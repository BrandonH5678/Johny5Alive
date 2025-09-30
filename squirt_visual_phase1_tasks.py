#!/usr/bin/env python3
"""
Squirt Visual Design Extension - Phase 1 J5A Work Assignments
Foundation tasks with low risk, no system impact
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

def create_phase1_tasks():
    """Create all Phase 1 work assignments"""

    tasks = []

    # ===== TASK 1.1: Create Folder Structure =====
    task_1_1 = J5AWorkAssignment(
        task_id="squirt_visual_1_1",
        task_name="Create visual/ and memory/ folder structure",
        domain="system_development",
        description="Create folder structure for Squirt visual design extension with no impact on existing systems",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "__init__.py",
                format="Python",
                description="Visual module init file",
                min_size_bytes=0
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "prompts" / ".gitkeep",
                format="TXT",
                description="Prompts folder marker",
                min_size_bytes=0
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "memory" / "__init__.py",
                format="Python",
                description="Memory module init file",
                min_size_bytes=0
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "memory" / "design_registry.jsonl",
                format="JSONL",
                description="Design registry file",
                min_size_bytes=0
            )
        ],

        success_criteria={
            "folders_created": QuantitativeMeasure("folders_exist", 1.0, "==", "boolean"),
            "no_overwrites": QuantitativeMeasure("files_overwritten", 0, "==", "count"),
            "squirt_functional": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Folder structure validation",
            description="Verify all folders and files created without impact",
            expected_behavior="All folders exist, no existing files modified",
            validation_method="Check directory tree and run existing Squirt tests",
            test_cases=[
                {"check": "visual/ exists", "expected": True},
                {"check": "memory/ exists", "expected": True},
                {"check": "existing Squirt unchanged", "expected": True}
            ]
        ),

        approved_architectures=["Squirt"],
        forbidden_patterns=[
            r"rm -rf",  # No destructive operations
            r"git reset --hard",  # No git resets
        ],

        rollback_plan="Remove created folders: rm -rf visual/ memory/",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_1_1)

    # ===== TASK 1.2: Define Data Schemas =====
    task_1_2 = J5AWorkAssignment(
        task_id="squirt_visual_1_2",
        task_name="Define Pydantic data schemas for visual tasks",
        domain="system_development",
        description="Create data models for visual tasks and design memory",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "schemas" / "__init__.py",
                format="Python",
                description="Schemas module init",
                min_size_bytes=0
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "schemas" / "tasks.py",
                format="Python",
                description="Visual task schemas with Pydantic models",
                min_size_bytes=500,
                quality_checks=["valid_python", "imports_work", "models_instantiate"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "models_work": QuantitativeMeasure("model_tests_pass", 1.0, "==", "%"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Schema validation",
            description="Verify Pydantic models work correctly",
            expected_behavior="Models instantiate, validate inputs, reject invalid data",
            validation_method="Instantiate models with valid and invalid data",
            test_cases=[
                {"input": {"project_id": "test", "task_type": "cad", "params": {}}, "expected": "valid"},
                {"input": {"project_id": "", "task_type": "invalid"}, "expected": "validation_error"}
            ]
        ),

        approved_architectures=["Pydantic"],
        forbidden_patterns=[
            r"eval\(",  # No eval
            r"exec\(",  # No exec
        ],

        rollback_plan="Remove schemas folder",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_1_2)

    # ===== TASK 1.3: Vector DB Setup =====
    task_1_3 = J5AWorkAssignment(
        task_id="squirt_visual_1_3",
        task_name="Set up ChromaDB vector store for design memory",
        domain="system_development",
        description="Implement vector database for design context and history tracking",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "memory" / "vector_store.py",
                format="Python",
                description="Vector store implementation with ChromaDB",
                min_size_bytes=1000,
                quality_checks=["valid_python", "imports_work", "db_initializes"]
            ),
            OutputSpecification(
                file_path=SQUIRT_PATH / "memory" / "index" / ".gitkeep",
                format="TXT",
                description="Vector DB index folder marker",
                min_size_bytes=0
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "db_works": QuantitativeMeasure("db_tests_pass", 1.0, "==", "%"),
            "persistence": QuantitativeMeasure("data_survives_restart", 1.0, "==", "boolean"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Vector DB validation",
            description="Verify ChromaDB operations work correctly",
            expected_behavior="Can add designs, query similar, retrieve history, persist data",
            validation_method="Add design, query, verify results, restart DB, verify persistence",
            test_cases=[
                {"operation": "add_design", "expected": "success"},
                {"operation": "find_similar", "expected": "results_returned"},
                {"operation": "get_project_history", "expected": "history_returned"},
                {"operation": "restart_and_query", "expected": "data_persisted"}
            ]
        ),

        approved_architectures=["ChromaDB"],
        forbidden_patterns=[
            r"rm -rf.*memory",  # No deleting memory folder
            r"DROP TABLE",  # No SQL drops
        ],

        rollback_plan="Remove vector_store.py and memory/index/ folder",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_1_3)

    # ===== TASK 1.4: Validation Framework =====
    task_1_4 = J5AWorkAssignment(
        task_id="squirt_visual_1_4",
        task_name="Implement visual output validators",
        domain="system_development",
        description="Create validation functions for images and STL files",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "visual" / "validators.py",
                format="Python",
                description="Image and STL validation functions",
                min_size_bytes=2000,
                quality_checks=["valid_python", "imports_work", "validators_work"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "validators_work": QuantitativeMeasure("validation_tests_pass", 1.0, "==", "%"),
            "catches_invalid": QuantitativeMeasure("invalid_inputs_rejected", 1.0, "==", "%"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Validator validation",
            description="Verify validators catch invalid inputs",
            expected_behavior="Valid files pass, invalid files fail with clear messages",
            validation_method="Test with valid and invalid image/STL files",
            test_cases=[
                {"input": "nonexistent.png", "expected": "validation_failed"},
                {"input": "valid_image.png", "expected": "validation_passed"},
                {"input": "nonexistent.stl", "expected": "validation_failed"},
                {"input": "valid_model.stl", "expected": "validation_passed"}
            ]
        ),

        approved_architectures=["PIL", "trimesh"],
        forbidden_patterns=[
            r"os\.system",  # No system calls
            r"subprocess\.call",  # Use subprocess.run instead
        ],

        rollback_plan="Remove validators.py",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_1_4)

    # ===== TASK 1.5: Install Dependencies =====
    task_1_5 = J5AWorkAssignment(
        task_id="squirt_visual_1_5",
        task_name="Install Phase 1 dependencies",
        domain="system_development",
        description="Install required Python packages for Phase 1",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "requirements_visual_phase1.txt",
                format="TXT",
                description="Phase 1 dependencies list",
                min_size_bytes=50
            )
        ],

        success_criteria={
            "packages_installed": QuantitativeMeasure("import_errors", 0, "==", "count"),
            "no_conflicts": QuantitativeMeasure("dependency_conflicts", 0, "==", "count"),
            "existing_functional": QuantitativeMeasure("existing_imports_work", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Dependency validation",
            description="Verify all packages install without conflicts",
            expected_behavior="New packages importable, existing packages still work",
            validation_method="Import new packages, run existing tests",
            test_cases=[
                {"check": "import pydantic", "expected": "success"},
                {"check": "import chromadb", "expected": "success"},
                {"check": "import PIL", "expected": "success"},
                {"check": "import trimesh", "expected": "success"},
                {"check": "existing voice imports", "expected": "success"}
            ]
        ),

        approved_architectures=["pip", "venv"],
        forbidden_patterns=[
            r"pip install.*--force",  # No force installs
            r"pip uninstall",  # No uninstalling existing packages
        ],

        rollback_plan="pip uninstall pydantic chromadb pillow trimesh",
        failure_escalation=EscalationPolicy(
            notify_immediately=True,  # Dependency issues need attention
            max_retry_attempts=1,
            rollback_on_failure=True
        )
    )
    tasks.append(task_1_5)

    # ===== TASK 1.6: Comprehensive Tests =====
    task_1_6 = J5AWorkAssignment(
        task_id="squirt_visual_1_6",
        task_name="Create Phase 1 test suite",
        domain="system_development",
        description="Comprehensive tests for all Phase 1 components",
        assigned_date=datetime.now(),
        priority=Priority.NORMAL,

        expected_outputs=[
            OutputSpecification(
                file_path=SQUIRT_PATH / "tests" / "test_visual_foundation.py",
                format="Python",
                description="Phase 1 comprehensive test suite",
                min_size_bytes=1000,
                quality_checks=["valid_python", "tests_discoverable", "all_tests_pass"]
            )
        ],

        success_criteria={
            "valid_syntax": QuantitativeMeasure("syntax_errors", 0, "==", "count"),
            "all_tests_pass": QuantitativeMeasure("test_pass_rate", 1.0, "==", "%"),
            "coverage": QuantitativeMeasure("code_coverage", 0.8, ">=", "%"),
            "no_regressions": QuantitativeMeasure("existing_tests_pass", 1.0, "==", "%")
        },

        test_oracle=TestOracle(
            name="Test suite validation",
            description="Verify all tests pass and provide good coverage",
            expected_behavior="All Phase 1 components tested, 80%+ coverage",
            validation_method="Run pytest with coverage",
            test_cases=[
                {"component": "schemas", "expected": "tests_pass"},
                {"component": "vector_store", "expected": "tests_pass"},
                {"component": "validators", "expected": "tests_pass"}
            ]
        ),

        approved_architectures=["pytest"],
        forbidden_patterns=[
            r"@pytest\.mark\.skip",  # No skipping tests
            r"pass\s*#\s*TODO",  # No incomplete tests
        ],

        rollback_plan="Remove test file",
        failure_escalation=EscalationPolicy(
            notify_immediately=False,
            max_retry_attempts=2,
            rollback_on_failure=False  # Keep tests even if some fail initially
        )
    )
    tasks.append(task_1_6)

    return tasks


if __name__ == "__main__":
    """Generate Phase 1 tasks for J5A queue"""

    tasks = create_phase1_tasks()

    print("=" * 80)
    print("Squirt Visual Design Extension - Phase 1 Tasks")
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