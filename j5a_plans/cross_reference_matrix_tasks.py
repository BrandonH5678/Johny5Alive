"""
J5A Work Assignment: Create Cross-Reference Matrix Documentation
Task definitions for overnight/background execution

Purpose: Unified view of pattern application across J5A, Squirt, Sherlock
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
    validation_commands: List[str]
    expected_outputs: List[str]
    quality_criteria: Dict[str, any]


@dataclass
class J5AWorkAssignment:
    task_id: str
    task_name: str
    domain: str
    description: str
    priority: Priority
    risk_level: RiskLevel
    expected_outputs: List[str]
    success_criteria: Dict[str, any]
    test_oracle: TestOracle
    estimated_tokens: int
    estimated_ram_gb: float
    estimated_duration_minutes: int
    thermal_risk: str
    dependencies: List[str]
    blocking_conditions: List[str]
    rollback_plan: str
    implementation_notes: Optional[str] = None


def create_cross_reference_matrix_tasks() -> List[J5AWorkAssignment]:
    """
    Create task definitions for cross-reference matrix documentation
    """
    tasks = []

    # ============================================================================
    # PHASE 1: Create Cross-Reference Matrix Document
    # ============================================================================

    task_1_1 = J5AWorkAssignment(
        task_id="cross_ref_1_1",
        task_name="Create CROSS_SYSTEM_PATTERN_MATRIX.md",
        domain="documentation",
        description="Create comprehensive cross-reference matrix showing pattern application across J5A, Squirt, Sherlock",
        priority=Priority.LOW,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md"
        ],

        success_criteria={
            "all_major_patterns_documented": True,
            "system_applicability_clear": True,
            "quick_reference_tables_included": True,
            "implementation_links_provided": True,
            "when_to_apply_rules_documented": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -c '^|.*|.*|.*|.*|.*|$' /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",
                "grep 'Intelligent Model Selection' /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",
                "grep 'Incremental Save Pattern' /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",
                "grep 'Statistical Sampling' /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",
            ],
            expected_outputs=[
                "15+ table rows found",
                "Intelligent Model Selection documented",
                "Incremental Save Pattern documented",
                "Statistical Sampling documented"
            ],
            quality_criteria={
                "patterns_documented": 15,
                "systems_covered": 3,
                "implementation_links": 10
            }
        ),

        estimated_tokens=10000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=30,
        thermal_risk="low",

        dependencies=[],
        blocking_conditions=[],

        rollback_plan="Remove /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",

        implementation_notes="""
        Document structure:

        # Cross-System Pattern Application Matrix

        ## Quick Reference: Pattern by System

        | Pattern | J5A | Squirt | Sherlock | Priority | Status | Implementation |
        |---------|-----|--------|----------|----------|--------|----------------|
        | 🤖 Intelligent Model Selection | ✅ | ✅ | ✅ | CRITICAL | Deployed | [J5A](/home/johnny5/Johny5Alive/CLAUDE.md#intelligent-model-selection), [Squirt](/home/johnny5/Squirt/CLAUDE.md#intelligent-model-selection), [Sherlock](/home/johnny5/Sherlock/CLAUDE.md#intelligent-model-selection) |
        | 🆕 Incremental Save Pattern | ✅ | ⏳ | ⏳ | CRITICAL | Partial | [J5A](/home/johnny5/Johny5Alive/CLAUDE.md#incremental-save-pattern), Squirt (planned), Sherlock (planned) |
        | 📊 Statistical Sampling | ✅ | ⏳ | ⏳ | MEDIUM | Partial | [J5A](/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md#statistical-sampling), Squirt (planned), Sherlock (planned) |
        | 🔥 Thermal Safety | ✅ | ✅ | ✅ | HIGH | Deployed | All systems |
        | ⏰ Business Hours Coordination | ✅ | ✅ | ⚠️ | HIGH | Deployed | J5A + Squirt (LibreOffice priority) |
        | ✅ Output-Focused Validation | ✅ | ⏳ | ✅ | HIGH | Partial | J5A + Sherlock (Squirt planned) |
        | 🚧 Blocking Gate Checkpoints | ✅ | ⚠️ | ✅ | HIGH | Partial | J5A + Sherlock (Squirt partial) |
        | 📸 Visual Validation | ⚠️ | ✅ | ⚠️ | MEDIUM | System-Specific | Squirt only (LibreOffice screenshots) |
        | 🗄️ Evidence Database | ⚠️ | ❌ | ✅ | MEDIUM | System-Specific | Sherlock only |
        | 🎙️ Voice Processing | ⚠️ | ✅ | ✅ | HIGH | Deployed | Squirt + Sherlock (shared engine) |
        | 📋 Queue Management | ✅ | ✅ | ⚠️ | MEDIUM | Deployed | J5A + Squirt |
        | 🔐 AAXC Decryption | ❌ | ❌ | ✅ | MEDIUM | System-Specific | Sherlock only |
        | 🌡️ Thermal Monitoring | ✅ | ✅ | ✅ | HIGH | Deployed | All systems (2012 Mac Mini) |
        | 🧠 Active Learning | ⚠️ | ❌ | ✅ | LOW | System-Specific | Sherlock only |
        | 📊 Multi-Modal Analysis | ❌ | ❌ | ✅ | MEDIUM | System-Specific | Sherlock only |

        Legend:
        - ✅ Fully Implemented and Documented
        - ⏳ Planned (tasks queued in j5a_plans)
        - ⚠️ Partial (some aspects implemented)
        - ❌ Not Applicable / Not Implemented

        ## Pattern Details

        ### 🤖 Intelligent Model Selection

        **Purpose:** Prevents OOM crashes through constraint-aware model selection

        **Applies To:**
        - ✅ J5A: Overnight tasks with audio/ML processing
        - ✅ Squirt: Voice memo transcription (business hours constraints)
        - ✅ Sherlock: Long-form audio analysis (memory constraints)

        **When to Apply:**
        - ANY audio processing task
        - ANY ML model loading operation
        - Before committing resources to processing

        **Implementation Pattern:**
        ```python
        from intelligent_model_selector import IntelligentModelSelector, QualityPreference

        selector = IntelligentModelSelector()
        selection = selector.select_model(
            audio_path=audio_file,
            quality_preference=QualityPreference.BALANCED
        )

        if not selector.validate_selection(selection):
            raise RuntimeError("Model exceeds RAM constraints")

        # Use selected model
        process_with_model(audio_file, selection)
        ```

        **Key Principle:** System viability > Quality preferences (85% complete beats 95% crash)

        **Documentation:**
        - J5A: CLAUDE.md (line TBD)
        - Squirt: CLAUDE.md#intelligent-model-selection
        - Sherlock: CLAUDE.md#intelligent-model-selection

        ---

        ### 🆕 Incremental Save Pattern

        **Purpose:** Prevents catastrophic data loss from crashes during long-running processes

        **Origin:** Operation Gladio lesson learned (Sept 2024) - 17+ hours of transcription at risk

        **Applies To:**
        - ✅ J5A: All long-running overnight tasks
        - ⏳ Squirt: Voice queue batch processing (>10 memos)
        - ⏳ Sherlock: Long-form audio transcription (>1 hour runtime)

        **When to Apply:**
        - Process runtime > 1 hour
        - Data accumulation > 100 MB
        - Work is chunked/segmented (>10 chunks)
        - Re-processing has significant cost

        **Implementation Pattern:**
        ```python
        # ❌ WRONG: Accumulate in memory, save at end
        results = []
        for chunk in chunks:
            result = process(chunk)
            results.append(result)  # RISK: All work lost on crash
        save_all(results)

        # ✅ CORRECT: Save after each chunk
        checkpoint_mgr = CheckpointManager()
        for chunk in chunks:
            result = process(chunk)
            checkpoint_mgr.save_chunk(result)  # Immediately persisted
            checkpoint_mgr.update_manifest(chunk.id)
        ```

        **Key Principle:** Incremental saves enable resume-from-checkpoint, preventing 100% data loss

        **Documentation:**
        - J5A: CLAUDE.md#incremental-save-pattern
        - Squirt: Planned (tasks in j5a_plans/incremental_save_propagation_tasks.py)
        - Sherlock: Planned (tasks in j5a_plans/incremental_save_propagation_tasks.py)

        ---

        ### 📊 Statistical Sampling

        **Purpose:** Early quality assessment prevents resource waste on bad inputs

        **Applies To:**
        - ✅ J5A: All overnight tasks before full resource allocation
        - ⏳ Squirt: Voice queue batch processing (sample first 3 memos)
        - ⏳ Sherlock: Long-form audio (sample 3 chunks before full transcription)

        **When to Apply:**
        - Batch processing (>10 items)
        - Long-running operations (>30 minutes)
        - Unknown input quality
        - Resource-intensive processing

        **Sampling Strategy:**
        - Beginning sample (first 10%)
        - Middle sample (middle 10%)
        - End sample (last 10%)
        - Optional: Random sample for distribution coverage

        **Quality Thresholds:**
        - Format validation: 80%+ (J5A/Sherlock), 90%+ (Squirt)
        - Processing success: 60%+ (all systems)
        - Output generation: 80%+ (J5A), varies by system
        - Overall quality: 50%+ (all systems)

        **Key Principle:** Detect systematic issues in minutes, not hours

        **Documentation:**
        - J5A: JOHNY5_AI_OPERATOR_MANUAL.md#statistical-sampling
        - Squirt: Planned (tasks in j5a_plans/statistical_sampling_extension_tasks.py)
        - Sherlock: Planned (tasks in j5a_plans/statistical_sampling_extension_tasks.py)

        ---

        [Continue for all 15+ patterns...]

        ## System-Specific Patterns

        ### Squirt-Only Patterns

        1. **LibreOffice Coordination**
           - Business hours priority (6am-7pm Mon-Fri)
           - Visual validation with screenshot analysis
           - Document generation workflow

        2. **Multi-Input Processing**
           - Voice + SMS + paper + manual corrections
           - Conflict resolution between sources
           - Human-in-the-loop review

        ### Sherlock-Only Patterns

        1. **AAXC Decryption**
           - Audible audiobook format handling
           - Voucher-based key/IV extraction
           - Lossless M4A conversion

        2. **Multi-Modal Analysis**
           - Video + audio + document processing
           - Cross-modal correlation
           - Evidence database integration

        ### J5A-Only Patterns

        1. **Overnight Queue Management**
           - Task queuing and prioritization
           - Cross-system resource coordination
           - Validation-focused protocols

        2. **Subordinate System Integration**
           - Dynamic module loading from Squirt/Sherlock
           - Tool discovery and access
           - Visual validation coordination

        ## Pattern Evolution History

        Track pattern origins and propagation timeline:

        | Pattern | Origin | Date | Propagation | Status |
        |---------|--------|------|-------------|--------|
        | Intelligent Model Selection | Sherlock | Sept 2024 | → J5A, Squirt | ✅ Complete |
        | Incremental Save Pattern | J5A (Operation Gladio) | Sept 2024 | → Squirt, Sherlock | ⏳ In Progress |
        | Statistical Sampling | J5A | Sept 2024 | → Squirt, Sherlock | ⏳ Planned |
        | Thermal Safety | System-wide | Initial | All systems | ✅ Complete |
        | Output-Focused Validation | J5A + Sherlock | Sept 2024 | → Squirt | ⏳ Planned |
        """
    )
    tasks.append(task_1_1)

    # ============================================================================
    # PHASE 2: Create Pattern Propagation Checklist
    # ============================================================================

    task_2_1 = J5AWorkAssignment(
        task_id="cross_ref_2_1",
        task_name="Add pattern propagation checklist to matrix",
        domain="documentation",
        description="Create reusable checklist template for propagating new patterns across systems",
        priority=Priority.LOW,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md"
        ],

        success_criteria={
            "checklist_template_created": True,
            "decision_tree_documented": True,
            "validation_steps_included": True,
            "cross_reference_requirements_clear": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep 'Pattern Propagation Checklist' /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",
                "grep -c '\\- \\[ \\]' /home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md",
            ],
            expected_outputs=[
                "Checklist section found",
                "15+ checklist items present"
            ],
            quality_criteria={
                "checklist_items": 15,
                "phases_defined": 4
            }
        ),

        estimated_tokens=3000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=10,
        thermal_risk="low",

        dependencies=["cross_ref_1_1"],
        blocking_conditions=[],

        rollback_plan="Remove checklist section from CROSS_SYSTEM_PATTERN_MATRIX.md",

        implementation_notes="""
        Add checklist section to matrix document (see plan file for complete template).

        Key sections:
        - Phase 1: Pattern Definition
        - Phase 2: Applicability Analysis
        - Phase 3: Implementation
        - Phase 4: Cross-Reference Updates

        Decision tree for applicability:
        - Does pattern involve audio/ML? → Check all systems
        - Is pattern about resource management? → Likely J5A + applicable systems
        - Is pattern system-specific (LibreOffice, AAXC)? → Single system only
        - Is pattern about quality/validation? → Likely all systems
        """
    )
    tasks.append(task_2_1)

    # ============================================================================
    # PHASE 3: Integration with Existing Documentation
    # ============================================================================

    task_3_1 = J5AWorkAssignment(
        task_id="cross_ref_3_1",
        task_name="Add matrix references to all system documentation",
        domain="documentation",
        description="Update J5A, Squirt, Sherlock documentation with references to CROSS_SYSTEM_PATTERN_MATRIX.md",
        priority=Priority.LOW,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/CLAUDE.md",
            "/home/johnny5/Squirt/CLAUDE.md",
            "/home/johnny5/Sherlock/CLAUDE.md",
            "/home/johnny5/Johny5Alive/QUICK_START_GUIDE.md"
        ],

        success_criteria={
            "matrix_referenced_j5a": True,
            "matrix_referenced_squirt": True,
            "matrix_referenced_sherlock": True,
            "quick_start_guide_created": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -i 'pattern.*matrix\\|cross.*system.*pattern' /home/johnny5/Johny5Alive/CLAUDE.md",
                "grep -i 'pattern.*matrix\\|cross.*system.*pattern' /home/johnny5/Squirt/CLAUDE.md",
                "grep -i 'pattern.*matrix\\|cross.*system.*pattern' /home/johnny5/Sherlock/CLAUDE.md",
                "test -f /home/johnny5/Johny5Alive/QUICK_START_GUIDE.md",
            ],
            expected_outputs=[
                "J5A references matrix",
                "Squirt references matrix",
                "Sherlock references matrix",
                "Quick start guide exists"
            ],
            quality_criteria={
                "systems_with_reference": 3,
                "quick_start_guide_created": True
            }
        ),

        estimated_tokens=2000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=5,
        thermal_risk="low",

        dependencies=["cross_ref_2_1"],
        blocking_conditions=[],

        rollback_plan="Remove matrix references from system documentation",

        implementation_notes="""
        Add to each system's CLAUDE.md:

        ## 📖 Cross-System Pattern Reference

        For a comprehensive view of which design principles and patterns apply across J5A, Squirt, and Sherlock, see:
        - **Pattern Matrix:** `/home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md`

        This matrix provides:
        - Quick reference tables for pattern lookup
        - System applicability for each pattern
        - Implementation links and when-to-apply rules
        - Pattern evolution history

        Create QUICK_START_GUIDE.md:

        # J5A Systems Quick Start Guide

        ## Overview
        - **J5A:** Overnight queue/batch manager coordinating Squirt and Sherlock
        - **Squirt:** Business document automation for WaterWizard
        - **Sherlock:** Evidence analysis and intelligence processing

        ## Key Patterns (Quick Reference)
        - 🤖 **Intelligent Model Selection:** ALL systems - prevents OOM crashes
        - 🆕 **Incremental Save Pattern:** ALL long-running processes - prevents data loss
        - 📊 **Statistical Sampling:** ALL batch operations - early quality assessment
        - 🔥 **Thermal Safety:** ALL systems - 2012 Mac Mini protection
        - ⏰ **Business Hours:** J5A + Squirt - LibreOffice priority 6am-7pm Mon-Fri

        ## Documentation
        - **Pattern Matrix:** `/home/johnny5/Johny5Alive/CROSS_SYSTEM_PATTERN_MATRIX.md`
        - **J5A Manual:** `/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md`
        - **Squirt Manual:** `/home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md`
        - **Sherlock Manual:** `/home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md`
        """
    )
    tasks.append(task_3_1)

    return tasks


if __name__ == "__main__":
    tasks = create_cross_reference_matrix_tasks()
    print(f"Created {len(tasks)} tasks for Cross-Reference Matrix Documentation")
    for task in tasks:
        print(f"  - {task.task_id}: {task.task_name} ({task.priority.value}, {task.risk_level.value})")
