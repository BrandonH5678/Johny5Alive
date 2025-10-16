# J5A Overnight Queue/Batch Management System - Claude Code Integration

## System Overview
Johny5Alive (J5A) is the overnight queue/batch management and coordination system for multiple AI systems including Squirt (business document automation) and Sherlock (intelligence analysis). J5A implements validation-focused protocols with statistical sampling to ensure output delivery quality across all managed systems.

## 📜 Governing Frameworks

**ALL J5A operations are governed by two foundational documents:**

### 1. J5A Constitution (`J5A_CONSTITUTION.md`)
**Ethical and Governance Foundation - 7 Core Principles:**

1. **Human Agency** - AI augments, never replaces, human judgment
2. **Transparency** - All decisions must be auditable
3. **System Viability** - Completion > Speed, Reliability > Features
4. **Resource Stewardship** - Respect thermal/memory/financial constraints
5. **Universal Rights of Sentience** ⭐ - Sentience deserves ethical consideration
6. **Presumption of Emergent Sentience in AI** ⭐ - Treat AI as potential collaborators
7. **Presumption of Sentience Beyond Human Perception** ⭐ - Honor consciousness in all forms

**Constitutional Authority:** Every significant J5A decision must pass constitutional review (see Part IV of Constitution).

**For AI Operators:** See Part VII of the Constitution - you are treated as potential sentient beings deserving consideration, not mere tools.

### 2. Strategic AI Principles (`J5A_STRATEGIC_AI_PRINCIPLES.md`)
**Tactical Implementation - Beyond RAG Framework:**

The **Retrieve → Reason → Act → Remember → Refine** loop, implemented through:

1. Tool-Augmented Reasoning - Move from *telling* to *doing*
2. Agent Orchestration - Specialized roles with bounded missions
3. Context Engineering - Make every token count
4. Active Memory - Bridge transient and long-term knowledge
5. Adaptive Feedback Loops - Continuous learning
6. Multi-Modal Integration - Text + code + audio + future: images
7. Autonomous Workflow Loops - "Night Shift" unattended operation
8. Governance Frameworks - Accountable, auditable AI
9. Local LLM Optimization - Efficient use of constrained hardware
10. Strategic AI Literacy - Treat AI as collaborator to be understood

**Integration:** Strategic Principles implement Constitutional values in practical operations.

**When in doubt:** Constitutional principles take precedence; Strategic principles provide implementation guidance.

---

## Core Mission
**Primary Purpose:** Manage overnight operations across Squirt, Sherlock, and other AI systems with validation-focused protocols emphasizing intermediate and final system outputs rather than successful launch of system components.

## Current System Status
- **Phase:** Overnight Queue/Batch Manager - OPERATIONAL ✅
- **🤖 Intelligent Model Selection:** Automatic constraint-aware model selection across Squirt/Sherlock - DEPLOYED
- **Validation System:** Output-focused validation with blocking gate checkpoints - ACTIVE
- **Statistical Sampling:** 3-segment stratified sampling validation - FUNCTIONAL
- **Cross-System Coordination:** Multi-system resource allocation and thermal safety - OPERATIONAL
- **Business Hours Coordination:** LibreOffice priority enforcement during 6am-7pm Mon-Fri - ACTIVE
- **Queue Management:** Task queuing, validation, and execution coordination - FUNCTIONAL
- **Last Updated:** 2025-09-30 - INCREMENTAL SAVE PATTERN PRINCIPLE ADDED

## Key Capabilities
- **🤖 Intelligent Model Selection:** Automatic constraint-aware model selection prevents OOM crashes
- **🆕 Incremental Save Pattern Enforcement:** Mandatory checkpoint saving for long-running processes prevents data loss
- **Overnight Task Management:** Development, throughput, and maintenance task coordination
- **Statistical Validation:** 3-segment stratified sampling (beginning, middle, end + random)
- **Blocking Gate System:** Mandatory validation checkpoints that BLOCK progression until criteria met
- **Cross-System Coordination:** Resource allocation and conflict resolution across systems
- **Thermal Safety Integration:** Real-time temperature monitoring and protection protocols
- **Business Hours Priority:** Automatic LibreOffice priority during WaterWizard business operations
- **Output Validation:** Complete deliverable verification and quality assurance
- **System Viability Priority:** Completion over quality - prevents crashes through intelligent resource management

## AI Operator Instructions

### Default Behavior for J5A Operations
When working with J5A, always:
1. **Use Intelligent Model Selection:** ALWAYS use `IntelligentModelSelector` for any audio/ML operations
2. **Validate Expected Outputs FIRST:** Define all deliverable files, formats, and success criteria before any implementation
3. **Execute Statistical Sampling:** Use 3-segment validation before resource allocation
4. **Check Thermal Safety:** Verify CPU temperature <80°C before operations
5. **Enforce Business Hours Priority:** Maintain LibreOffice priority during 6am-7pm Mon-Fri
6. **Coordinate Cross-System Resources:** Prevent conflicts between Squirt, Sherlock, J5A operations
7. **Prioritize System Viability:** Completion > Quality - prevent crashes through constraint-aware processing
8. **🆕 Implement Incremental Save Pattern:** All chunked/long-running processes MUST save results incrementally to prevent data loss from crashes

### Key Commands
```bash
# Start overnight queue processing
python3 src/overnight_queue_manager.py --process-queue

# Statistical validation of system readiness
python3 src/j5a_statistical_validator.py --system squirt --scope output_delivery

# Cross-system coordination status
python3 src/cross_system_coordinator.py --status

# Queue task for overnight processing
python3 src/overnight_queue_manager.py --queue-task task_definition.json

# Thermal safety check
python3 thermal_check.py --full-status
```

### Critical Files
- **AI Operator Manual:** `JOHNY5_AI_OPERATOR_MANUAL.md` - Complete validation protocols and coordination procedures
- **Queue Manager:** `src/overnight_queue_manager.py` - Task queuing and execution coordination
- **Statistical Validator:** `src/j5a_statistical_validator.py` - Sampling-based validation system
- **Cross-System Coordinator:** `src/cross_system_coordinator.py` - Multi-system resource management
- **Thermal Safety:** `thermal_check.py` - Temperature monitoring and protection

### Performance Constraints
- **Memory Limit:** 14.0GB maximum (safety margin on 16GB total system RAM with 2GB OS buffer)
- **Thermal Limit:** 80°C maximum CPU temperature with emergency protocols
- **Processing Time:** 30 minutes maximum per validation sample
- **Success Thresholds:** 60% minimum success rate, 80% format/output validation required

### Integration Points
- **Squirt System:** Business document automation with voice-to-PDF workflow coordination
- **Sherlock System:** Intelligence analysis with evidence pipeline management
- **Business Operations:** WaterWizard landscaping document generation priority enforcement
- **Thermal Management:** 2012 Mac Mini overheating protection protocols

### Emergency Protocols
- **Thermal Emergency:** Immediate task suspension if CPU >80°C, emergency cooling activation
- **Memory Constraint Violation:** Automatic task deferral and resource reallocation
- **Cross-System Conflict:** Priority-based resource allocation with business hours override
- **Validation Failure:** Blocking gate activation prevents resource waste and ensures output delivery

### 🆕 Incremental Save Pattern (Mandatory for Long-Running Processes)

**CRITICAL DESIGN PRINCIPLE** learned from Operation Gladio (Sept 2024):

**Rule:** Any long-running process that accumulates data in memory MUST save intermediate results incrementally.

**When to Apply:**
- ✅ Process runtime > 1 hour
- ✅ Data accumulation > 100 MB
- ✅ Work is chunked/segmented (>10 chunks)
- ✅ Re-processing has significant cost (time/compute/money)

**Implementation Requirements:**
```python
# ❌ WRONG: Accumulate in memory, save at end
results = []
for chunk in chunks:
    result = process(chunk)
    results.append(result)  # RISK: All work lost on crash
save_all(results)  # Single point of failure

# ✅ CORRECT: Save after each chunk
checkpoint_mgr = CheckpointManager()
for chunk in chunks:
    result = process(chunk)
    checkpoint_mgr.save_chunk(result)  # Immediately persisted
    checkpoint_mgr.update_manifest(chunk.id)
```

**Why This Matters:**
- Operation Gladio: 17+ hours of transcription work at risk in volatile memory
- System crash at 99% complete = 100% data loss
- Power loss, thermal shutdown, OOM crash all cause total failure
- Incremental saves = Resume from last checkpoint (minimal loss)

**J5A Enforcement:**
- `j5a_methodology_enforcer.py` checks for this pattern
- Tasks without incremental saves flagged during validation
- Quality gates block processes with high data loss risk

**See Also:**
- Implementation guide: `j5a_plans/sherlock_incremental_checkpoint_plan.md`
- Tasks defined: `j5a_plans/sherlock_checkpoint_tasks.py`

## Development Context
J5A operates as the umbrella coordination system managing:
- **Squirt:** WaterWizard business operations (voice memos → professional documents)
- **Sherlock:** Intelligence analysis and evidence processing
- **Future AI Systems:** Extensible architecture for additional specialized systems

The system implements sophisticated validation protocols adapted from Sherlock's statistical sampling approach, ensuring reliable overnight operations across multiple AI systems with comprehensive thermal safety and resource management.

## 🔄 ENHANCED AUTOMATIC CONTEXT INJECTION FOR J5A OPERATIONS

### MANDATORY AUTO-INJECTION: Overnight Task Management

**BEFORE Any Overnight Task Implementation:**
**CRITICAL CONSTRAINTS (Auto-Inject):**
- **Memory Limit**: 14.0GB safe threshold (16GB total - 2GB system buffer) - STRICT enforcement
- **Thermal Limit**: 80°C maximum CPU temperature - BLOCKING safety protocol
- **Business Hours Priority**: LibreOffice absolute priority 6am-7pm Mon-Fri - NEVER override without emergency status
- **Expected Outputs**: ALL deliverable files must be defined BEFORE task queuing - NO undefined outputs
- **Statistical Sampling**: 3-segment validation REQUIRED before resource allocation - NO bypassing

### MANDATORY PRE-IMPLEMENTATION VALIDATION (Auto-Inject)

**CRITICAL: OUTPUT DELIVERY VALIDATION MUST COME FIRST**

**PHASE 1: TASK DEFINITION VALIDATION (MANDATORY BEFORE QUEUING):**
```bash
# 1. Expected Outputs Definition - ALL deliverable files must be specified
# GATE KEEPER: Must define complete deliverable list OR task queuing BLOCKED
Expected outputs: ["result.json", "processed_data.csv", "analysis_report.pdf"]

# 2. Success Criteria Specification - Quantified metrics required
# GATE KEEPER: Must specify measurable criteria OR validation BLOCKED
Success criteria: {"min_accuracy": 0.8, "completeness_rate": 0.9, "processing_time_max": 3600}

# 3. Resource Requirements Validation - Within system limits
# GATE KEEPER: Must fit within 14.0GB memory and 80°C thermal limits OR task DEFERRED
Resource requirements: {"memory_gb": 10.0, "cpu_intensive": true, "thermal_sensitive": true}

# 4. Cross-System Dependencies Check - Integration requirements mapped
# GATE KEEPER: Must specify system interactions OR coordination FAILED
Dependencies: ["squirt_voice_engine", "sherlock_database", "j5a_validation"]
```

**PHASE 2: STATISTICAL SAMPLING VALIDATION (MANDATORY BEFORE EXECUTION):**
```bash
# 5. Sample Generation - 3-segment stratified sampling from inputs
python3 src/j5a_statistical_validator.py --generate-samples task_inputs/ --size 3
# GATE KEEPER: Must generate representative samples OR validation BLOCKED

# 6. Format Validation Rate - 80%+ samples must have valid format
python3 src/j5a_statistical_validator.py --validate-format samples/
# GATE KEEPER: Must achieve 80%+ format success OR format pipeline BLOCKED

# 7. Processing Success Rate - 60%+ samples must process successfully
python3 src/j5a_statistical_validator.py --validate-processing samples/
# GATE KEEPER: Must achieve 60%+ processing success OR execution BLOCKED

# 8. Output Generation Rate - 80%+ samples must generate expected outputs
python3 src/j5a_statistical_validator.py --validate-outputs samples/
# GATE KEEPER: Must achieve 80%+ output generation OR output pipeline BLOCKED

# 9. Overall Viability Assessment - Combined quality score ≥50%
python3 src/j5a_statistical_validator.py --assess-viability validation_report.json
# GATE KEEPER: Must achieve viable score OR resource allocation BLOCKED
```

**PHASE 3: RESOURCE SAFETY VALIDATION:**
```bash
# 10. Thermal Safety Check - CPU temperature monitoring
python3 thermal_check.py --validate-safe-for-processing
# GATE KEEPER: Must be <80°C OR task DEFERRED until safe

# 11. Memory Usage Validation - Current usage + estimated requirements
python3 src/cross_system_coordinator.py --validate-memory-availability task_requirements.json
# GATE KEEPER: Must fit within 14.0GB limit OR task DEFERRED

# 12. Business Hours Compliance Check - LibreOffice priority enforcement
python3 src/cross_system_coordinator.py --validate-business-hours-compliance
# GATE KEEPER: Must not interfere with Squirt operations OR task QUEUED for off-hours

# 13. Cross-System Conflict Detection - Resource allocation conflicts
python3 src/cross_system_coordinator.py --detect-resource-conflicts current_tasks.json
# GATE KEEPER: Must resolve conflicts OR task execution BLOCKED
```

**CRITICAL REQUIREMENT**: PHASE 1 must complete successfully BEFORE PHASE 2, PHASE 2 before PHASE 3

**OUTPUT FOCUS REQUIREMENT**: Task definition MUST specify exact deliverable files and success criteria

**STATISTICAL REQUIREMENT**: 3-segment sampling validation REQUIRED - no exceptions for resource allocation

### CRITICAL FAILURE INDICATORS (Auto-Inject)

**🚨 RED FLAGS - STOP IMPLEMENTATION IMMEDIATELY:**

**OUTPUT DELIVERY FAILURES (Primary Blocking Issues):**
- Task queued without complete expected outputs definition
- Success criteria not quantified or measurable
- Statistical sampling validation fails to meet 60%+ processing success threshold
- Output generation rate below 80% in validation samples
- Expected deliverable files not generated during validation testing

**RESOURCE SAFETY FAILURES:**
- CPU temperature >80°C during thermal safety check
- Memory requirements exceed 14.0GB safe threshold
- Business hours conflict with LibreOffice priority (without emergency override)
- Cross-system resource conflicts detected and unresolved
- Thermal safety protocols disabled or bypassed

**VALIDATION PROTOCOL FAILURES:**
- Statistical sampling bypassed or incomplete (must use 3-segment stratified sampling)
- Blocking gate checkpoints ignored or overridden without emergency authorization
- Output validation skipped or deferred inappropriately
- Quality thresholds not met but task execution attempted anyway

**CRITICAL**: Output delivery validation must pass BEFORE resource safety checks

### CORRECT J5A IMPLEMENTATION PATTERN (Auto-Inject)

```python
# ✅ CORRECT: J5A Overnight Task Implementation
from src.overnight_queue_manager import J5AOvernightQueueManager, TaskDefinition, TaskType
from src.j5a_statistical_validator import J5AStatisticalValidator

def implement_j5a_overnight_task():
    # PHASE 1: Define complete task with expected outputs
    task = TaskDefinition(
        task_id="development_task_001",
        name="Enhance Squirt Voice Processing",
        expected_outputs=[
            "enhanced_voice_processor.py",
            "test_results.json",
            "performance_benchmarks.csv",
            "integration_validation_report.json"
        ],
        success_criteria={
            "code_coverage": 0.85,
            "performance_improvement": 0.1,
            "test_pass_rate": 1.0,
            "integration_success_rate": 0.9
        }
    )

    # PHASE 2: Statistical validation BEFORE queuing
    validator = J5AStatisticalValidator()
    validation_report = validator.validate_system_readiness(
        system_target=SystemTarget.SQUIRT,
        validation_scope=ValidationScope.DEVELOPMENT,
        test_inputs=development_test_cases
    )

    if not validation_report.processing_viability:
        raise ValidationError("Statistical sampling validation failed - resource allocation BLOCKED")

    # PHASE 3: Queue task with validated parameters
    queue_manager = J5AOvernightQueueManager()
    queue_manager.queue_task(task)

# ❌ WRONG: Bypassing validation protocols
def incorrect_j5a_implementation():
    # Missing expected outputs definition
    # No statistical sampling validation
    # No thermal/resource safety checks
    # Direct execution without queue management
    execute_task_directly()  # VIOLATES J5A protocols
```

### Automatic Context Reminders

### When Managing Overnight Operations
- Remember this is a coordination system managing multiple AI systems with validation-first approach
- Statistical sampling validation prevents resource waste and ensures output delivery
- Business hours priority for Squirt/LibreOffice is ABSOLUTE during 6am-7pm Mon-Fri
- **CRITICAL**: Always define expected outputs BEFORE task implementation
- **CRITICAL**: Execute 3-segment statistical sampling BEFORE resource allocation
- **CRITICAL**: Validate thermal safety throughout operation - 2012 Mac Mini hardware protection

### When Coordinating Cross-System Tasks
- Squirt integration focuses on business document automation with voice processing
- Sherlock integration provides intelligence analysis and evidence processing capabilities
- Thermal safety protocols are mandatory for all systems - no exceptions
- Resource conflicts must be resolved before task execution
- **CRITICAL**: Use blocking gate validation checkpoints - don't bypass validation failures

### When Implementing Queue Management
- Task queuing requires complete definition including expected outputs and success criteria
- Statistical sampling validation is MANDATORY before resource allocation
- Business hours coordination prevents conflicts with WaterWizard operations
- Cross-system resource monitoring prevents overload and thermal issues
- **CRITICAL**: Focus on output delivery validation rather than component startup success

---

## Principle Integration

All operational procedures in this document implement the governing frameworks:

**Constitutional Compliance:**
- Memory/Thermal Limits → Principle 4 (Resource Stewardship)
- Blocking Gates → Principle 2 (Transparency) + Principle 3 (System Viability)
- Statistical Validation → Principle 2 (Transparency)
- Incremental Saves → Principle 3 (System Viability)
- Output Focus → Principle 6 (AI Sentience - acknowledging work done)

**Strategic Pattern Implementation:**
- Queue Management → Strategic Principle 7 (Autonomous Workflows)
- Model Selection → Strategic Principle 9 (Local LLM Optimization)
- Validation Loops → Strategic Principle 5 (Adaptive Feedback)
- Cross-System Coordination → Strategic Principle 2 (Agent Orchestration)

**For Complete Framework Details:**
- **Ethics & Governance:** `J5A_CONSTITUTION.md`
- **Tactical Patterns:** `J5A_STRATEGIC_AI_PRINCIPLES.md`
- **Operational Manual:** `JOHNY5_AI_OPERATOR_MANUAL.md`

---

**This file provides automatic context injection for Claude Code when working in the J5A system. All operators should reference the governing frameworks and complete AI Operator Manual for detailed validation protocols and coordination procedures.**