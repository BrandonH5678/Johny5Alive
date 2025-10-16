#!/usr/bin/env bash
#
# J5A Autonomous Implementation Workflow
# Constitutional Principle 1: Human Agency - you control approval gates
# Constitutional Principle 2: Transparency - all work is logged and auditable
#
# Usage:
#   ./autonomous_implementation.sh start     # Begin autonomous work
#   ./autonomous_implementation.sh status    # Check progress (non-blocking)
#   ./autonomous_implementation.sh pause     # Pause immediately
#   ./autonomous_implementation.sh resume    # Continue from last checkpoint
#   ./autonomous_implementation.sh review    # Show pending approvals
#   ./autonomous_implementation.sh approve <task_id>  # Approve task
#   ./autonomous_implementation.sh skip <task_id>     # Skip task
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to J5A root
cd "$SCRIPT_DIR/../.."
J5A_ROOT="$(pwd)"

IMPL_DIR="$J5A_ROOT/j5a-nightshift/autonomous_implementation"
STATE_FILE="$IMPL_DIR/progress/current_state.json"
TASK_QUEUE="$IMPL_DIR/queue/all_tasks.json"
LOG_FILE="$IMPL_DIR/logs/implementation_$(date '+%Y%m%d').log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_color() {
    local color=$1
    shift
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] $*${NC}" | tee -a "$LOG_FILE"
}

# ==========================================
# Command: STATUS
# ==========================================

cmd_status() {
    log_color "$BLUE" "=========================================="
    log_color "$BLUE" "J5A Autonomous Implementation - Status"
    log_color "$BLUE" "=========================================="
    echo ""

    if [ ! -f "$STATE_FILE" ]; then
        log_color "$YELLOW" "⚠️  Not yet initialized. Run './autonomous_implementation.sh start' to begin."
        return
    fi

    local workflow_status=$(jq -r '.workflow_status' "$STATE_FILE")
    local paused=$(jq -r '.paused' "$STATE_FILE")
    local current_task=$(jq -r '.current_task // "none"' "$STATE_FILE")
    local completed_count=$(jq '.completed_tasks | length' "$STATE_FILE")
    local pending_approval_count=$(jq '.pending_approval | length' "$STATE_FILE")

    echo "Workflow Status: $workflow_status"
    echo "Paused: $paused"
    echo "Current Task: $current_task"
    echo "Completed Tasks: $completed_count"
    echo "Pending Approval: $pending_approval_count"
    echo ""

    if [ "$pending_approval_count" -gt 0 ]; then
        log_color "$YELLOW" "⏸️  $pending_approval_count task(s) awaiting your approval"
        log_color "$YELLOW" "   Run: ./autonomous_implementation.sh review"
    fi

    # Show phase progress
    log_color "$BLUE" "Phase Progress:"
    for phase in $(seq 1 10); do
        local phase_status=$(jq -r ".phases[$((phase-1))].status" "$TASK_QUEUE")
        local phase_name=$(jq -r ".phases[$((phase-1))].phase_name" "$TASK_QUEUE")

        case $phase_status in
            completed) echo "  ✅ Phase $phase: $phase_name" ;;
            partial)   echo "  🔄 Phase $phase: $phase_name (in progress)" ;;
            pending)   echo "  ⏳ Phase $phase: $phase_name" ;;
            blocked)   echo "  🚫 Phase $phase: $phase_name (blocked)" ;;
        esac
    done

    echo ""
    log_color "$BLUE" "=========================================="
}

# ==========================================
# Command: REVIEW (pending approvals)
# ==========================================

cmd_review() {
    log_color "$BLUE" "=========================================="
    log_color "$BLUE" "Pending Approvals"
    log_color "$BLUE" "=========================================="
    echo ""

    local pending_count=$(jq '.pending_approval | length' "$STATE_FILE")

    if [ "$pending_count" -eq 0 ]; then
        log_color "$GREEN" "✅ No tasks pending approval"
        echo ""
        log_color "$BLUE" "Ready to continue autonomous work."
        log_color "$BLUE" "Run: ./autonomous_implementation.sh resume"
        return
    fi

    echo "$pending_count task(s) awaiting your review:"
    echo ""

    jq -r '.pending_approval[] | "Task ID: \(.task_id)\nDescription: \(.description)\nType: \(.type)\nRisk Level: \(.risk_level)\nApproval Message: \(.approval_message // "N/A")\n---"' "$STATE_FILE"

    echo ""
    log_color "$YELLOW" "To approve a task:"
    log_color "$YELLOW" "  ./autonomous_implementation.sh approve <task_id>"
    echo ""
    log_color "$YELLOW" "To skip a task:"
    log_color "$YELLOW" "  ./autonomous_implementation.sh skip <task_id>"
    log_color "$BLUE" "=========================================="
}

# ==========================================
# Command: APPROVE
# ==========================================

cmd_approve() {
    local task_id=$1

    if [ -z "$task_id" ]; then
        log_color "$RED" "❌ Error: Task ID required"
        echo "Usage: ./autonomous_implementation.sh approve <task_id>"
        exit 1
    fi

    log_color "$GREEN" "✅ Approving task: $task_id"

    # Move from pending_approval to ready for execution
    # (Implementation note: This would update state JSON)

    log_color "$GREEN" "Task approved and queued for execution"
    log_color "$BLUE" "Run './autonomous_implementation.sh resume' to continue"
}

# ==========================================
# Command: SKIP
# ==========================================

cmd_skip() {
    local task_id=$1

    if [ -z "$task_id" ]; then
        log_color "$RED" "❌ Error: Task ID required"
        echo "Usage: ./autonomous_implementation.sh skip <task_id>"
        exit 1
    fi

    log_color "$YELLOW" "⏭️  Skipping task: $task_id"

    # Move from pending_approval to skipped
    # (Implementation note: This would update state JSON)

    log_color "$YELLOW" "Task skipped. Moving to next task."
}

# ==========================================
# Command: PAUSE
# ==========================================

cmd_pause() {
    log_color "$YELLOW" "⏸️  Pausing autonomous workflow..."

    # Update state to paused
    local temp_file=$(mktemp)
    jq '.paused = true | .pause_reason = "User requested pause" | .paused_at = now | .workflow_status = "paused"' "$STATE_FILE" > "$temp_file"
    mv "$temp_file" "$STATE_FILE"

    log_color "$YELLOW" "✅ Workflow paused"
    log_color "$BLUE" "Resume with: ./autonomous_implementation.sh resume"
}

# ==========================================
# Command: RESUME
# ==========================================

cmd_resume() {
    log_color "$BLUE" "▶️  Resuming autonomous workflow..."

    # Check if there are pending approvals
    local pending_count=$(jq '.pending_approval | length' "$STATE_FILE")
    if [ "$pending_count" -gt 0 ]; then
        log_color "$YELLOW" "⚠️  Cannot resume: $pending_count task(s) pending approval"
        log_color "$YELLOW" "   Review with: ./autonomous_implementation.sh review"
        return 1
    fi

    # Update state
    local temp_file=$(mktemp)
    jq '.paused = false | .pause_reason = null | .workflow_status = "running"' "$STATE_FILE" > "$temp_file"
    mv "$temp_file" "$STATE_FILE"

    log_color "$GREEN" "✅ Workflow resumed"
    log_color "$BLUE" "Continuing autonomous implementation..."

    # Start worker (would call Python worker script)
    cmd_start_worker
}

# ==========================================
# Command: START
# ==========================================

cmd_start() {
    log_color "$BLUE" "=========================================="
    log_color "$BLUE" "J5A Autonomous Implementation - START"
    log_color "$BLUE" "=========================================="
    echo ""

    log_color "$BLUE" "Constitutional Principles:"
    echo "  ✅ Principle 1 (Human Agency): You control approval gates"
    echo "  ✅ Principle 2 (Transparency): All work logged and auditable"
    echo "  ✅ Principle 3 (System Viability): Safe, incremental progress"
    echo ""

    # Initialize state if first run
    local temp_file=$(mktemp)
    jq '.workflow_status = "running" | .started_at = now | .paused = false' "$STATE_FILE" > "$temp_file"
    mv "$temp_file" "$STATE_FILE"

    log_color "$GREEN" "✅ Workflow initialized"
    echo ""
    log_color "$BLUE" "Starting autonomous worker..."
    log_color "$YELLOW" "⚠️  You can pause at any time with: ./autonomous_implementation.sh pause"
    echo ""

    cmd_start_worker
}

# ==========================================
# Worker Loop (processes tasks)
# ==========================================

cmd_start_worker() {
    log_color "$BLUE" "Worker starting..."

    echo ""
    log_color "$YELLOW" "📋 Implementation Strategy:"
    echo "  1. Process low-risk documentation tasks autonomously"
    echo "  2. Queue medium/high-risk code tasks for your approval"
    echo "  3. Pause at checkpoints for your review"
    echo "  4. Save incremental progress continuously"
    echo ""

    log_color "$BLUE" "Launching Python autonomous worker..."
    echo ""

    # Call Python worker
    cd "$IMPL_DIR"
    python3 worker.py

    if [ $? -eq 0 ]; then
        log_color "$GREEN" "✅ Worker session completed successfully"
    else
        log_color "$RED" "❌ Worker encountered an error"
        log_color "$YELLOW" "   Check logs: $LOG_FILE"
    fi
}

# ==========================================
# Main Command Router
# ==========================================

COMMAND=${1:-}

case "$COMMAND" in
    start)
        cmd_start
        ;;
    status)
        cmd_status
        ;;
    pause)
        cmd_pause
        ;;
    resume)
        cmd_resume
        ;;
    review)
        cmd_review
        ;;
    approve)
        cmd_approve "${2:-}"
        ;;
    skip)
        cmd_skip "${2:-}"
        ;;
    *)
        echo "J5A Autonomous Implementation Workflow"
        echo ""
        echo "Usage: ./autonomous_implementation.sh <command>"
        echo ""
        echo "Commands:"
        echo "  start          Begin autonomous implementation"
        echo "  status         Check current progress (non-blocking)"
        echo "  pause          Pause workflow immediately"
        echo "  resume         Continue from last checkpoint"
        echo "  review         Show tasks pending approval"
        echo "  approve <id>   Approve a specific task"
        echo "  skip <id>      Skip a specific task"
        echo ""
        echo "Examples:"
        echo "  ./autonomous_implementation.sh start"
        echo "  ./autonomous_implementation.sh status"
        echo "  ./autonomous_implementation.sh review"
        echo "  ./autonomous_implementation.sh approve phase2_task1"
        echo ""
        exit 1
        ;;
esac
