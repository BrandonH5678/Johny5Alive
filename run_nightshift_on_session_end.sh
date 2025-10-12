#!/bin/bash
# Run Night Shift when Claude Code session ends
# This script is designed to be triggered when token budget exhausts

set -e

NIGHTSHIFT_DIR="/home/johnny5/Johny5Alive/j5a-nightshift"
LOG_FILE="/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/session_end_run_$(date +%Y%m%d_%H%M%S).log"

echo "========================================"  | tee -a "$LOG_FILE"
echo "NIGHT SHIFT - SESSION END TRIGGER"       | tee -a "$LOG_FILE"
echo "Started: $(date)"                        | tee -a "$LOG_FILE"
echo "========================================"  | tee -a "$LOG_FILE"
echo ""                                         | tee -a "$LOG_FILE"

# Change to nightshift directory
cd "$NIGHTSHIFT_DIR"

# Run pre-flight check
echo "Running pre-flight check..." | tee -a "$LOG_FILE"
if ! ./ops/pre_flight_check.sh >> "$LOG_FILE" 2>&1; then
    echo "❌ Pre-flight check failed" | tee -a "$LOG_FILE"
    exit 1
fi
echo "✅ Pre-flight check passed" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run Night Shift with timeout protection (30 minutes max)
echo "Starting Night Shift processing (30 min timeout)..." | tee -a "$LOG_FILE"
if timeout 1800 python3 process_nightshift_queue.py >> "$LOG_FILE" 2>&1; then
    echo "✅ Night Shift completed successfully" | tee -a "$LOG_FILE"
    exit_code=0
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "⚠️  Night Shift timed out after 30 minutes" | tee -a "$LOG_FILE"
    else
        echo "❌ Night Shift failed with exit code: $exit_code" | tee -a "$LOG_FILE"
    fi
fi

# Generate summary
echo "" | tee -a "$LOG_FILE"
echo "Generating summary..." | tee -a "$LOG_FILE"
python3 ops/nightshift_summary.py >> "$LOG_FILE" 2>&1 || true

echo "" | tee -a "$LOG_FILE"
echo "========================================"  | tee -a "$LOG_FILE"
echo "NIGHT SHIFT RUN COMPLETE"                | tee -a "$LOG_FILE"
echo "Ended: $(date)"                          | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE"                          | tee -a "$LOG_FILE"
echo "========================================"  | tee -a "$LOG_FILE"

exit $exit_code
