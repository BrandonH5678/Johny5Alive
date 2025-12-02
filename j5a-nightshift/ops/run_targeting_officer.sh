#!/bin/bash
#
# Targeting Officer Wrapper for Night Shift
# Runs daily sweep and logs to dedicated file
#
set -e

LOG_DIR="/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs"
LOG_FILE="$LOG_DIR/targeting_officer_$(date +%Y%m%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Run targeting officer with timestamp
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Targeting Officer sweep" >> "$LOG_FILE"

cd /home/johnny5/Sherlock
python3 src/sherlock_targeting_officer.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Targeting Officer completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Targeting Officer failed with exit code $EXIT_CODE" >> "$LOG_FILE"
    exit $EXIT_CODE
fi

exit 0
