#!/bin/bash
# Auto-resume Dylan Borland Whisper after Jay Stratton completes
# Monitors PID 15561 (Jay Stratton) and resumes PID 37348 (Dylan Borland) when complete

STRATTON_PID=15561
BORLAND_PID=37348
LOG_FILE="/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/auto_resume_borland.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "==========================================
log "Auto-Resume Monitor Started"
log "=========================================="
log "Monitoring Jay Stratton (PID $STRATTON_PID)"
log "Will resume Dylan Borland (PID $BORLAND_PID) when complete"
log ""

# Check if processes exist
if ! ps -p $STRATTON_PID > /dev/null 2>&1; then
    log "❌ ERROR: Jay Stratton process (PID $STRATTON_PID) not running"
    log "Dylan Borland already paused - manually resume with: kill -CONT $BORLAND_PID"
    exit 1
fi

if ! ps -p $BORLAND_PID > /dev/null 2>&1; then
    log "❌ ERROR: Dylan Borland process (PID $BORLAND_PID) not found"
    exit 1
fi

# Verify Borland is paused
BORLAND_STATE=$(ps -p $BORLAND_PID -o state --no-headers | tr -d ' ')
if [ "$BORLAND_STATE" != "T" ]; then
    log "⚠️  WARNING: Dylan Borland process not in stopped state (state: $BORLAND_STATE)"
    log "Pausing now..."
    kill -STOP $BORLAND_PID
    sleep 1
fi

log "✅ Dylan Borland process confirmed paused"
log ""

# Monitor Jay Stratton completion
log "Monitoring Jay Stratton process..."
while ps -p $STRATTON_PID > /dev/null 2>&1; do
    sleep 60  # Check every minute
done

log ""
log "=========================================="
log "✅ Jay Stratton process completed!"
log "=========================================="
log ""

# Wait 5 seconds to ensure clean completion
sleep 5

# Resume Dylan Borland
log "Resuming Dylan Borland Whisper (PID $BORLAND_PID)..."
if ps -p $BORLAND_PID > /dev/null 2>&1; then
    kill -CONT $BORLAND_PID
    sleep 2

    # Verify resumed
    BORLAND_STATE=$(ps -p $BORLAND_PID -o state --no-headers | tr -d ' ')
    if [ "$BORLAND_STATE" = "R" ] || [ "$BORLAND_STATE" = "S" ]; then
        log "✅ Dylan Borland process resumed successfully"
        log "CPU usage: $(ps -p $BORLAND_PID -o %cpu --no-headers)"
        log "Memory usage: $(ps -p $BORLAND_PID -o %mem --no-headers)"
        log ""
        log "Monitor progress: tail -f ops/logs/whisper_ep39_borland_20251014_113531.log"
    else
        log "⚠️  WARNING: Dylan Borland state: $BORLAND_STATE (expected R or S)"
    fi
else
    log "❌ ERROR: Dylan Borland process no longer exists"
    exit 1
fi

log ""
log "=========================================="
log "Auto-Resume Monitor Complete"
log "=========================================="
