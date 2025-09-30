# J5A Plans Directory

## Purpose

This directory contains **implementation plans** that J5A can analyze and execute during overnight sessions.

## Structure

Each plan includes:

1. **Implementation Plan**: High-level strategy and phase breakdown (`.md` file)
2. **Task Definitions**: Executable J5AWorkAssignment specifications (`.py` file)
3. **Task Metadata**: Machine-readable task properties (`.json` file)

## J5A Plan Selection Process

During overnight sessions, J5A:

1. **Scans `j5a_plans/` directory** for available plans
2. **Reads task metadata** to understand dependencies, resource requirements
3. **Checks resource constraints** (tokens, RAM, thermal)
4. **Prioritizes tasks** based on:
   - Priority level (CRITICAL > HIGH > NORMAL > LOW)
   - Dependencies (foundation tasks before dependent tasks)
   - Risk level (low-risk first)
   - Resource availability
5. **Executes tasks** with full validation pipeline
6. **Checkpoints progress** to resume across sessions

## Current Plans

### Squirt Visual Design Extension

**Files:**
- `VISUAL_DESIGN_IMPLEMENTATION_PLAN.md` - 4-phase implementation strategy
- `squirt_visual_phase1_tasks.py` - Phase 1 task definitions
- `squirt_visual_phase1_metadata.json` - Machine-readable task properties

**Status:** Ready for execution
**Phases:**
- Phase 1: Foundation (6 tasks, ~33k tokens, LOW RISK)
- Phase 2: Integration (5 tasks, ~40k tokens, MEDIUM RISK)
- Phase 3: Processing Engines (BLOCKED until 16GB RAM upgrade)
- Phase 4: Advanced Features (4 tasks, ~30k tokens, LOW RISK)

## Plan Format Specification

### Implementation Plan (Markdown)

```markdown
# [Project Name] Implementation Plan

## Overview
Brief description and goals

## Phases
### Phase 1: [Name]
- **Status**: Ready / Blocked / In Progress / Complete
- **Risk Level**: LOW / MEDIUM / HIGH
- **Dependencies**: None / Phase X complete
- **Estimated Tokens**: X,XXX
- **Tasks**: List of task IDs

### Phase 2: [Name]
...

## Dependencies
- External dependencies
- Hardware requirements
- Blocking conditions
```

### Task Definitions (Python)

```python
from j5a_work_assignment import J5AWorkAssignment, Priority

def create_phase_tasks():
    tasks = []

    task = J5AWorkAssignment(
        task_id="unique_id",
        task_name="Human-readable name",
        domain="system_development",
        description="What this task does",
        priority=Priority.NORMAL,
        expected_outputs=[...],
        success_criteria={...},
        test_oracle=TestOracle(...),
        rollback_plan="How to undo",
        ...
    )
    tasks.append(task)

    return tasks
```

### Task Metadata (JSON)

```json
{
  "plan_name": "Squirt Visual Extension",
  "plan_version": "1.0",
  "created": "2024-09-30",
  "phases": [
    {
      "phase_id": "phase_1",
      "phase_name": "Foundation",
      "status": "ready",
      "risk_level": "low",
      "dependencies": [],
      "blocking_conditions": [],
      "estimated_tokens": 33000,
      "estimated_duration_hours": 0.5,
      "tasks": [
        {
          "task_id": "squirt_visual_1_1",
          "task_name": "Create folder structure",
          "priority": "normal",
          "estimated_tokens": 3000,
          "estimated_ram_gb": 0.2,
          "estimated_duration_minutes": 5,
          "thermal_risk": "low",
          "dependencies": [],
          "outputs": [
            "/home/johnny5/Squirt/visual/__init__.py",
            "/home/johnny5/Squirt/memory/__init__.py"
          ]
        }
      ]
    }
  ]
}
```

## Task Selection Algorithm

J5A uses this decision tree:

```
1. Load all plans from j5a_plans/
2. Filter by blocking conditions:
   - Check hardware requirements
   - Check dependency completion
   - Check resource availability
3. Build dependency graph:
   - Tasks with no dependencies first
   - Tasks with satisfied dependencies next
   - Blocked tasks deferred
4. Score each task:
   - Priority weight: CRITICAL=100, HIGH=75, NORMAL=50, LOW=25
   - Risk penalty: LOW=0, MEDIUM=-10, HIGH=-25
   - Resource fit: +10 if fits current budget
5. Sort by score (highest first)
6. Execute in order until resource limit reached
7. Checkpoint remaining tasks
```

## Adding New Plans

### Step 1: Create Implementation Plan

```bash
# Create markdown plan
vim j5a_plans/NEW_PROJECT_PLAN.md
```

### Step 2: Define Tasks

```bash
# Create task definitions
vim j5a_plans/new_project_tasks.py
```

### Step 3: Generate Metadata

```bash
# Run metadata generator
python3 j5a_plan_metadata_generator.py new_project_tasks.py
# Creates: new_project_metadata.json
```

### Step 4: Validate Plan

```bash
# Validate plan structure
python3 j5a_plan_validator.py j5a_plans/new_project_metadata.json
```

### Step 5: Load into Queue (Optional)

```bash
# Manually load tasks immediately
python3 -c "
from j5a_queue_manager import J5AQueueManager
from j5a_plans.new_project_tasks import create_tasks

queue = J5AQueueManager()
for task in create_tasks():
    queue.add_task(task)
"

# OR let J5A discover and load automatically during overnight run
```

## Plan Discovery and Execution

### Automatic Discovery

J5A overnight executor can automatically:

```python
from j5a_plan_manager import J5APlanManager

# Create plan manager
plan_manager = J5APlanManager(plans_dir="j5a_plans")

# Discover available plans
plans = plan_manager.discover_plans()

# Get executable tasks (filtered by constraints)
executable_tasks = plan_manager.get_executable_tasks(
    max_tokens=140000,
    max_ram_gb=2.4,
    thermal_state="safe"
)

# Execute tasks
executor.execute_task_list(executable_tasks)
```

## Status Tracking

Plans track status in metadata:

```json
{
  "execution_history": [
    {
      "date": "2024-09-30",
      "tasks_completed": ["squirt_visual_1_1", "squirt_visual_1_2"],
      "tasks_failed": [],
      "checkpoint": "j5a_checkpoint_20240930.json"
    }
  ],
  "current_status": {
    "phase_1": "in_progress",
    "phase_2": "waiting",
    "phase_3": "blocked",
    "phase_4": "waiting"
  }
}
```

## Best Practices

1. **Modular Phases**: Break work into small, independent phases
2. **Clear Dependencies**: Document what must complete first
3. **Conservative Estimates**: Overestimate tokens/time/RAM
4. **Low-Risk First**: Start with foundation tasks
5. **Rollback Plans**: Always define how to undo changes
6. **Test Oracles**: Define exact success criteria
7. **Blocking Conditions**: Explicitly state hardware/dependency requirements

## Plan Lifecycle

```
Created → Ready → Queued → Executing → Checkpointed → Resumed → Completed
                    ↓
                 Blocked (waiting for resources/dependencies)
```

---

**J5A Plans**: Intelligent task planning and execution for overnight automation.