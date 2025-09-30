# J5A Token Management Guide

## Overview

J5A Resource Manager balances **Claude token budget**, **RAM availability**, and **thermal safety** to prevent hitting the 5-hour session limit while maintaining system stability.

## Problem Statement

Claude Code sessions have a ~200,000 token limit (~5 hours). Without management:
- ❌ Sessions terminate mid-task when token budget exhausted
- ❌ Lost work and context when hitting limit unexpectedly
- ❌ No coordination with RAM (3.7GB) or thermal constraints (2012 Mac Mini)

## Solution: Integrated Resource Management

The `J5AResourceManager` provides:

1. **Token Budget Tracking**: Monitors usage, estimates remaining time
2. **Session Checkpointing**: Preserves state before token exhaustion
3. **Resource Coordination**: Balances tokens, RAM, and thermal state
4. **Task Planning**: Allocates token budgets across task queue

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   J5A Resource Manager                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Token Budget    │  │ RAM Monitor      │  │  Thermal   │ │
│  │                 │  │                  │  │  Safety    │ │
│  │ • 200k limit    │  │ • 3.7GB total    │  │  Manager   │ │
│  │ • Usage track   │  │ • 2.4GB target   │  │            │ │
│  │ • Burn rate     │  │ • Availability   │  │ • CPU temp │ │
│  │ • Checkpoints   │  │   checks         │  │ • States   │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Session Checkpoint System                   │   │
│  │  • EMERGENCY_CHECKPOINT: <10k tokens remaining        │   │
│  │  • COMPLETE_CURRENT: <30k tokens, finish task         │   │
│  │  • Preserves queue state for resumption               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Token Budget Tracking

### Budget Structure

```python
class ClaudeTokenBudget:
    MAX_SESSION_TOKENS = 200,000      # ~5 hour limit
    tokens_used: int                  # Current usage
    emergency_reserve: int = 10,000   # For checkpointing
    tokens_per_task_estimate: int = 5,000
```

### Key Metrics

- **Tokens Remaining**: `200,000 - tokens_used - emergency_reserve`
- **Burn Rate**: `tokens_used / session_hours`
- **Time Remaining**: `tokens_remaining / burn_rate`
- **Usage Percentage**: `(tokens_used / 200,000) * 100`

## Resource Monitoring

### Before Each Task

```python
# Check all resource constraints
can_execute, reason = resource_manager.can_execute_task(task_id)

# Blocks if:
# - Tokens remaining < 15,000 (critical)
# - RAM available < 1.5GB (critical)
# - Thermal state = CRITICAL or EMERGENCY
# - Tokens remaining < 30,000 (warning)
# - RAM available < 2.0GB (warning)
```

### During Execution

```python
# Track token usage per task
tokens_at_start = resource_manager.token_budget.tokens_used
# ... execute task ...
tokens_used = current_tokens - tokens_at_start
resource_manager.record_task_completion(task_id, tokens_used)
```

### After Task Completion

```python
# Every 3 tasks or when checkpointing triggered
resource_manager.print_session_summary()

# Shows:
# - Session duration
# - Token budget (used/remaining, burn rate)
# - RAM status
# - Thermal state
# - Limiting resource
```

## Checkpoint Strategies

### 1. Emergency Checkpoint (<10k tokens)

```python
if tokens_remaining < 10,000:
    strategy = SessionStrategy.EMERGENCY_CHECKPOINT
    # Immediately save state and stop
    resource_manager.create_checkpoint(
        queue_state={"queued_tasks": remaining_tasks},
        current_task=current_task
    )
    break  # Stop execution
```

### 2. Complete Current Task (<30k tokens)

```python
if tokens_remaining < 30,000:
    strategy = SessionStrategy.COMPLETE_CURRENT
    # Finish current task, then checkpoint
    execute_task(task)
    resource_manager.create_checkpoint(...)
    break  # Stop execution
```

### 3. Thermal Emergency

```python
if thermal_state in ["critical", "emergency"]:
    strategy = SessionStrategy.EMERGENCY_CHECKPOINT
    # Immediate checkpoint regardless of tokens
    resource_manager.create_checkpoint(...)
    break
```

## Checkpoint Format

Saved to `j5a_checkpoint.json`:

```json
{
  "created_at": "2024-09-30T10:45:00",
  "session_start": "2024-09-30T08:00:00",
  "tokens_used": 180000,
  "session_hours": 2.75,
  "queue_state": {
    "queued_tasks": [
      {"task_id": "squirt_visual_1_4", ...},
      {"task_id": "squirt_visual_1_5", ...},
      {"task_id": "squirt_visual_1_6", ...}
    ]
  },
  "current_task": {"task_id": "squirt_visual_1_3", ...},
  "resource_snapshot": {
    "tokens_remaining": 10000,
    "ram_available_gb": 2.1,
    "cpu_temp": 78.5,
    "thermal_state": "warm"
  },
  "reason": "Token budget preservation"
}
```

## Integration with Overnight Executor

### Initialization

```python
# Create resource manager with constraints
resource_manager = J5AResourceManager(
    max_ram_gb=3.7,
    target_available_ram_gb=2.4
)

# Create executor with resource manager
executor = J5AOvernightExecutor(
    output_dir=Path("j5a_output"),
    resource_manager=resource_manager
)
```

### Task Execution with Monitoring

```python
# Execute task list (automatically monitors resources)
results = executor.execute_task_list(tasks)

# Executor will:
# 1. Check resources before each task
# 2. Track token usage per task
# 3. Print summaries every 3 tasks
# 4. Checkpoint when approaching limits
# 5. Stop execution if resources exhausted
```

## Token Allocation Planning

### Pre-Execution Planning

```python
# Estimate tokens for task queue
plan = resource_manager.get_token_allocation_plan(task_queue)

# Returns:
{
  "available_tokens": 140000,
  "tasks_can_execute": [
    {"task_id": "task_1", "tokens": 5000, "minutes": 10},
    {"task_id": "task_2", "tokens": 5000, "minutes": 10},
    # ... 28 more tasks
  ],
  "tasks_deferred": [
    {"task_id": "task_30", "reason": "insufficient_tokens"}
  ],
  "estimated_completion_time": "5h 0m"
}
```

### Task Resource Estimates

```python
# Define task resource requirements
resource_manager.allocate_task_resources(
    task_id="squirt_visual_1_3",
    estimate=TaskResourceEstimate(
        task_id="squirt_visual_1_3",
        estimated_tokens=5000,        # Conservative estimate
        estimated_ram_gb=0.5,         # ChromaDB setup
        estimated_duration_minutes=10,
        thermal_risk="low"            # No heavy processing
    )
)
```

## Usage Examples

### Example 1: Normal Execution

```python
resource_manager = J5AResourceManager()
executor = J5AOvernightExecutor(resource_manager=resource_manager)

# Execute Phase 1 tasks (6 tasks × 5k tokens = 30k tokens)
tasks = create_phase1_tasks()
results = executor.execute_task_list(tasks)

# Output:
# 🎛️  J5A RESOURCE MANAGER - SESSION SUMMARY
# ⏱️  Session Duration: 0.5h
# 🎫 Token Budget:
#    Used: 32,000 / 200,000 (16.0%)
#    Remaining: 158,000
#    Burn rate: 64,000 tokens/hour
#    Est. time remaining: 2.5h
# ✅ Can continue: True
```

### Example 2: Approaching Token Limit

```python
# After several task batches, approaching limit
# Session duration: 4.2h
# Tokens used: 175,000

# Before next task:
can_execute, reason = resource_manager.can_execute_task("task_35")
# Returns: (False, "Insufficient tokens (15,000 remaining, need ~5,000)")

# Executor automatically checkpoints:
should_checkpoint, strategy = resource_manager.should_checkpoint_session()
# Returns: (True, SessionStrategy.COMPLETE_CURRENT)

# Checkpoint created:
# 💾 Session checkpoint saved: j5a_checkpoint.json
#    Session duration: 4.2h
#    Tokens used: 175,000
#    Tasks remaining: 15
```

### Example 3: Thermal Emergency

```python
# CPU temp rises to 92°C during processing

# Resource check fails:
can_execute, reason = resource_manager.can_execute_task("task_10")
# Returns: (False, "Thermal constraint: critical (92.0°C)")

# Emergency checkpoint triggered:
# ⚠️  Resource checkpoint triggered: emergency_checkpoint
# 🚨 Emergency checkpoint - preserving session immediately
# 💾 Session preserved - stopping execution
```

## Session Resumption (Future)

When checkpoints are created, future J5A runs can resume:

```python
# Load checkpoint from previous session
checkpoint = resource_manager.load_checkpoint()

if checkpoint:
    # Resume from checkpoint
    remaining_tasks = checkpoint["queue_state"]["queued_tasks"]
    # ... reconstruct J5AWorkAssignment objects ...
    executor.execute_task_list(remaining_tasks)
```

## Best Practices

### 1. Conservative Token Estimates

Default 5,000 tokens per task is conservative:
- Simple tasks (file creation): ~2,000 tokens
- Medium tasks (code generation): ~5,000 tokens
- Complex tasks (multi-file refactoring): ~10,000 tokens

### 2. Task Batching

Group related tasks to maximize efficiency:
- Phase 1 (6 tasks): Foundation setup (~30k tokens)
- Phase 2 (5 tasks): Integration (~25k tokens)
- Can execute ~40 simple tasks per session

### 3. Monitoring Frequency

Print summaries strategically:
- Every 3 tasks (default)
- After checkpoint warnings
- At phase boundaries

### 4. Emergency Reserve

Keep 10,000 token reserve for:
- Checkpoint creation
- Error handling
- Session cleanup

## Integration with Squirt Visual Extension

### Phase 1 Token Budget

```
Task 1.1: Create folder structure        ~3,000 tokens
Task 1.2: Define Pydantic schemas        ~5,000 tokens
Task 1.3: Set up ChromaDB                ~6,000 tokens
Task 1.4: Implement validators           ~7,000 tokens
Task 1.5: Install dependencies           ~4,000 tokens
Task 1.6: Create test suite              ~8,000 tokens
                                         ─────────────
Total Phase 1:                           ~33,000 tokens
```

Can complete Phase 1 with 16.5% of token budget.

### Multi-Phase Execution

With 200k token budget:
- Phase 1: ~33k tokens (foundation)
- Phase 2: ~40k tokens (integration)
- Phase 3: BLOCKED (requires RAM upgrade)
- Phase 4: ~30k tokens (advanced features)
- **Contingency**: ~97k tokens (for errors, retries, validation)

## Troubleshooting

### "Token budget exhausted"

**Cause**: Used >190,000 tokens (including reserve)
**Solution**: Checkpoint created automatically, resume in new session

### "Insufficient tokens for task"

**Cause**: Task estimate + current usage > budget
**Solution**: Task deferred, included in checkpoint for next session

### "Thermal constraint"

**Cause**: CPU temp >85°C (critical) or >90°C (emergency)
**Solution**:
1. Implement external cooling
2. Reduce system load
3. Wait for temps to drop
4. Resume from checkpoint

### "Insufficient RAM"

**Cause**: Available RAM <1.5GB
**Solution**:
1. Close other applications
2. Wait for memory to free
3. Reduce task RAM estimates
4. Process in smaller batches

## Metrics and Logging

### Session Log

All resource snapshots logged to `j5a_session_log.json`:

```json
{"timestamp": "2024-09-30T08:15:00", "tokens": {"used": 5000, "remaining": 185000}, ...}
{"timestamp": "2024-09-30T08:25:00", "tokens": {"used": 10000, "remaining": 180000}, ...}
```

### Task Reports

Each task execution includes resource metrics:

```json
{
  "task_id": "squirt_visual_1_3",
  "tokens_used": 5234,
  "duration_seconds": 45.2,
  "peak_ram_gb": 2.1,
  "peak_thermal_celsius": 76.5
}
```

## Future Enhancements

1. **Machine Learning**: Learn actual token usage per task type
2. **Adaptive Estimates**: Adjust estimates based on historical data
3. **Multi-Session Planning**: Span work across multiple sessions
4. **Priority-Based Allocation**: Allocate more tokens to critical tasks
5. **External Monitoring**: Web dashboard for resource tracking

---

## Quick Reference

### Key Constants

```python
MAX_SESSION_TOKENS = 200,000
EMERGENCY_RESERVE = 10,000
DEFAULT_TOKENS_PER_TASK = 5,000
CRITICAL_TOKEN_THRESHOLD = 15,000
WARNING_TOKEN_THRESHOLD = 30,000
```

### Key Methods

```python
# Resource checking
resource_manager.can_execute_task(task_id) → (bool, str)
resource_manager.get_resource_snapshot() → ResourceSnapshot

# Token tracking
resource_manager.allocate_task_resources(task_id, estimate)
resource_manager.record_task_completion(task_id, tokens_used)

# Checkpointing
resource_manager.should_checkpoint_session() → (bool, SessionStrategy)
resource_manager.create_checkpoint(queue_state, current_task)
resource_manager.load_checkpoint() → Optional[Dict]

# Reporting
resource_manager.print_session_summary()
resource_manager.get_session_summary() → Dict
```

---

**J5A Token Management**: Intelligent resource coordination for uninterrupted overnight execution.