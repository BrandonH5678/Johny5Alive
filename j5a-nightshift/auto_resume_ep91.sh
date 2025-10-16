#!/usr/bin/env bash
#
# Auto-Resume Episode 91 Processing
# Waits for safe conditions, then launches chunked processing
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/ops/resource_safety_gate.sh"

LOG_FILE="ops/logs/auto_resume_ep91_$(date '+%Y%m%d_%H%M%S').log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Auto-Resume Episode 91 Processing"
log "=========================================="
log ""
log "Waiting for safe operating conditions..."
log "This may take a few minutes if Claude Code is active."
log ""

# Wait up to 15 minutes for safe conditions
MAX_WAIT=900
WAIT_INTERVAL=30
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if run_all_safety_checks > /dev/null 2>&1; then
        log ""
        log "✅ Safe conditions achieved after ${ELAPSED}s"
        log ""
        log "Launching weaponized_ep91_chunked.sh..."
        log ""

        # Execute the main script
        exec ./weaponized_ep91_chunked.sh
    fi

    log "  Waiting for resources... (${ELAPSED}s/${MAX_WAIT}s)"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

log ""
log "❌ Timeout: Safe conditions not achieved after ${MAX_WAIT}s"
log "Manual intervention required - check system status"
exit 1
