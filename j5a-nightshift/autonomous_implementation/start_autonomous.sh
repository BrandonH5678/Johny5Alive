#!/usr/bin/env bash
#
# Launch autonomous worker in background
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="logs/autonomous_run_$(date '+%Y%m%d_%H%M%S').log"

echo "=========================================="
echo "J5A Autonomous Worker - Background Launch"
echo "=========================================="
echo ""
echo "Pre-approved tasks:"
python3 manage_approvals.py status
echo ""
echo "Starting worker in background..."
echo "Log file: $LOG_FILE"
echo ""

# Launch worker in background
nohup python3 worker.py > "$LOG_FILE" 2>&1 &
WORKER_PID=$!

echo "✅ Worker started (PID: $WORKER_PID)"
echo ""
echo "Monitor progress:"
echo "  tail -f $LOG_FILE"
echo ""
echo "Check status:"
echo "  python3 manage_approvals.py status"
echo "  cat progress/current_state.json | jq '.completed_tasks | length'"
echo ""
echo "Worker will run until:"
echo "  - All pre-approved tasks complete"
echo "  - Encounters a task requiring approval"
echo "  - Encounters an error"
echo ""
echo "Safe travels! The worker will keep building while you're away."
echo "=========================================="
