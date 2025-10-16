#!/bin/bash
# Auto-Process Next Episode: Dylan Borland EP39 after Jay Stratton EP91 completes
# Monitors current Whisper and automatically starts next transcription

CURRENT_WHISPER_PID=6341  # Jay Stratton EP91
BORLAND_AUDIO="/home/johnny5/Johny5Alive/j5a-nightshift/artifacts/nightshift/2025-10-13/weaponized/ep39_borland/episode_39_dylan_borland_part2.mp3"
BORLAND_OUTPUT_DIR="/home/johnny5/Johny5Alive/j5a-nightshift/artifacts/nightshift/2025-10-13/weaponized/ep39_borland"
LOG_FILE="/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/auto_process_next_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Auto-Process Next Episode Monitor Started"
log "=========================================="
log "Current: Jay Stratton EP91 (PID $CURRENT_WHISPER_PID)"
log "Next: Dylan Borland EP39"
log "Log: $LOG_FILE"
log ""

# Verify current Whisper is running
if ! ps -p $CURRENT_WHISPER_PID > /dev/null 2>&1; then
    log "❌ ERROR: Current Whisper process (PID $CURRENT_WHISPER_PID) not running"
    log "Starting Borland transcription immediately..."

    # Start immediately if EP91 already finished
    log "Executing: whisper $BORLAND_AUDIO --model large-v3 ..."

    /usr/bin/python3 /home/johnny5/.local/bin/whisper \
        "$BORLAND_AUDIO" \
        --model large-v3 \
        --language en \
        --task transcribe \
        --output_dir "$BORLAND_OUTPUT_DIR" \
        --output_format txt \
        --output_format json \
        --output_format srt \
        --verbose True \
        > "$BORLAND_OUTPUT_DIR/whisper_output.log" 2>&1 &

    BORLAND_PID=$!
    echo $BORLAND_PID > "$BORLAND_OUTPUT_DIR/whisper.pid"

    log "✅ Dylan Borland Whisper started (PID: $BORLAND_PID)"
    log "Monitor: tail -f $BORLAND_OUTPUT_DIR/whisper_output.log"
    exit 0
fi

log "✅ Current Whisper confirmed running"
log "CPU: $(ps -p $CURRENT_WHISPER_PID -o %cpu --no-headers)%"
log "Memory: $(ps -p $CURRENT_WHISPER_PID -o %mem --no-headers)%"
log ""

# Monitor completion
log "Monitoring Jay Stratton EP91 Whisper completion..."
log "Checking every 2 minutes..."
log ""

CHECK_COUNT=0
while ps -p $CURRENT_WHISPER_PID > /dev/null 2>&1; do
    sleep 120  # Check every 2 minutes
    CHECK_COUNT=$((CHECK_COUNT + 1))

    # Log status every 30 minutes (15 checks)
    if [ $((CHECK_COUNT % 15)) -eq 0 ]; then
        ELAPSED=$((CHECK_COUNT * 2))
        log "Still monitoring... (${ELAPSED} minutes elapsed)"
        if ps -p $CURRENT_WHISPER_PID > /dev/null 2>&1; then
            log "  EP91 CPU: $(ps -p $CURRENT_WHISPER_PID -o %cpu --no-headers)%"
            log "  EP91 Memory: $(ps -p $CURRENT_WHISPER_PID -o %mem --no-headers)%"
        fi
    fi
done

log ""
log "=========================================="
log "✅ Jay Stratton EP91 Whisper COMPLETED!"
log "=========================================="
log ""

# Wait 10 seconds to ensure clean completion and file writes
log "Waiting 10 seconds for file system sync..."
sleep 10

# Verify EP91 transcripts were created
EP91_DIR="/home/johnny5/Johny5Alive/j5a-nightshift/artifacts/nightshift/2025-10-13/weaponized"
if [ -f "$EP91_DIR/episode_91.txt" ]; then
    log "✅ EP91 transcript confirmed: episode_91.txt"
    EP91_SIZE=$(stat -c%s "$EP91_DIR/episode_91.txt")
    log "   Size: $((EP91_SIZE / 1024)) KB"
else
    log "⚠️  WARNING: EP91 transcript not found at expected location"
    log "   Searching for output files..."
    find "$EP91_DIR" -name "*.txt" -mmin -5 -ls >> "$LOG_FILE" 2>&1
fi

log ""
log "=========================================="
log "Starting Dylan Borland EP39 Transcription"
log "=========================================="
log ""
log "Audio: $BORLAND_AUDIO"
log "Output: $BORLAND_OUTPUT_DIR"
log "Model: large-v3"
log ""

# Verify Borland audio exists
if [ ! -f "$BORLAND_AUDIO" ]; then
    log "❌ ERROR: Borland audio file not found: $BORLAND_AUDIO"
    exit 1
fi

log "Audio size: $(stat -c%s "$BORLAND_AUDIO" | awk '{printf "%.1f MB", $1/1024/1024}')"
log ""
log "Starting Whisper..."

# Start Borland transcription
/usr/bin/python3 /home/johnny5/.local/bin/whisper \
    "$BORLAND_AUDIO" \
    --model large-v3 \
    --language en \
    --task transcribe \
    --output_dir "$BORLAND_OUTPUT_DIR" \
    --output_format txt \
    --output_format json \
    --output_format srt \
    --verbose True \
    > "$BORLAND_OUTPUT_DIR/whisper_output.log" 2>&1 &

BORLAND_PID=$!
echo $BORLAND_PID > "$BORLAND_OUTPUT_DIR/whisper.pid"

# Verify process started
sleep 3
if ps -p $BORLAND_PID > /dev/null 2>&1; then
    log "✅ Dylan Borland Whisper started successfully!"
    log "   PID: $BORLAND_PID"
    log "   CPU: $(ps -p $BORLAND_PID -o %cpu --no-headers)%"
    log "   Memory: $(ps -p $BORLAND_PID -o %mem --no-headers)%"
    log ""
    log "Monitor progress:"
    log "  tail -f $BORLAND_OUTPUT_DIR/whisper_output.log"
    log "  ps -p $BORLAND_PID"
    log ""
    log "When complete, transcripts will be at:"
    log "  $BORLAND_OUTPUT_DIR/episode_39_dylan_borland_part2.txt"
    log "  $BORLAND_OUTPUT_DIR/episode_39_dylan_borland_part2.json"
    log "  $BORLAND_OUTPUT_DIR/episode_39_dylan_borland_part2.srt"
else
    log "❌ ERROR: Failed to start Borland Whisper process"
    log "Check logs: $BORLAND_OUTPUT_DIR/whisper_output.log"
    exit 1
fi

log ""
log "=========================================="
log "Auto-Process Monitor Complete"
log "=========================================="
log "Dylan Borland EP39 transcription is now running"
log "Claude intelligence extraction will auto-queue when complete"
log ""

# Note about Claude queue
log "📋 Reminder: Claude job already queued at:"
log "   /home/johnny5/Johny5Alive/queue/claude/2025-10-13.jsonl"
log "   - Dylan Borland EP39 intelligence analysis"
log "   - Will process automatically when transcripts are ready"
log ""

exit 0
