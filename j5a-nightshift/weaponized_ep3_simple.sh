#!/usr/bin/env bash
#
# Weaponized Episode 91 - Simplified Direct Download
# Uses known audio URL from RSS feed
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Logging setup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_DIR="ops/logs"
LOG_FILE="$LOG_DIR/weaponized_ep91_simple_${TIMESTAMP}.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# Configuration
OUTPUT_DIR="artifacts/nightshift/2025-10-13/weaponized"
AUDIO_URL="https://www.podtrac.com/pts/redirect.mp3/pdst.fm/e/prfx.byspotify.com/e/pscrb.fm/rss/p/mgln.ai/e/p721018/mgln.ai/e/1468/chrt.fm/track/B175B2/traffic.megaphone.fm/CAD5885902773.mp3?updated=1679773194"
AUDIO_FILE="$OUTPUT_DIR/episode_91.mp3"
CLAUDE_QUEUE="/home/johnny5/Johny5Alive/queue/claude/2025-10-13.jsonl"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$CLAUDE_QUEUE")"

log "=========================================="
log "Weaponized Ep 91 - Sherlock Pipeline"
log "=========================================="
log ""
log "Episode: The Pentagon's Top UFO Hunter"
log "Guest: John 'Jay' Stratton"
log "Published: Feb 7, 2023"
log ""

#
# PHASE 1: DOWNLOAD
#
log "PHASE 1: Audio Download"
log "------------------------"
log "URL: $AUDIO_URL"
log "Destination: $AUDIO_FILE"
log ""

if [ -f "$AUDIO_FILE" ]; then
    EXISTING_SIZE=$(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE" 2>/dev/null)
    log "⚠️  File already exists ($EXISTING_SIZE bytes)"
    log "Skipping download..."
else
    log "Downloading with curl..."
    curl -L --retry 5 --retry-delay 2 --progress-bar \
        -o "$AUDIO_FILE" "$AUDIO_URL" 2>&1 | tee -a "$LOG_FILE"

    if [ $? -ne 0 ] || [ ! -f "$AUDIO_FILE" ]; then
        log_error "Download failed"
        exit 1
    fi

    AUDIO_SIZE=$(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE" 2>/dev/null)
    AUDIO_SIZE_MB=$(echo "scale=2; $AUDIO_SIZE / 1024 / 1024" | bc)
    log "✅ Download complete: ${AUDIO_SIZE_MB} MB"
fi

log ""

#
# PHASE 2: WHISPER DIARIZATION
#
log "PHASE 2: Whisper Diarization (Background)"
log "------------------------------------------"

WHISPER_LOG="$LOG_DIR/whisper_ep91_${TIMESTAMP}.log"

# Check if whisper is already running
if [ -f "$OUTPUT_DIR/whisper.pid" ]; then
    OLD_PID=$(cat "$OUTPUT_DIR/whisper.pid")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        log "⚠️  Whisper already running (PID: $OLD_PID)"
        log "Skipping whisper launch..."
        WHISPER_PID=$OLD_PID
    else
        log "Starting Whisper Large v3..."
        nohup whisper "$AUDIO_FILE" \
            --model large-v3 \
            --language en \
            --task transcribe \
            --output_dir "$OUTPUT_DIR" \
            --output_format txt \
            --output_format json \
            --output_format srt \
            --verbose True \
            > "$WHISPER_LOG" 2>&1 &

        WHISPER_PID=$!
        echo "$WHISPER_PID" > "$OUTPUT_DIR/whisper.pid"
        log "✅ Whisper started (PID: $WHISPER_PID)"
    fi
else
    log "Starting Whisper Large v3..."
    nohup whisper "$AUDIO_FILE" \
        --model large-v3 \
        --language en \
        --task transcribe \
        --output_dir "$OUTPUT_DIR" \
        --output_format txt \
        --output_format json \
        --output_format srt \
        --verbose True \
        > "$WHISPER_LOG" 2>&1 &

    WHISPER_PID=$!
    echo "$WHISPER_PID" > "$OUTPUT_DIR/whisper.pid"
    log "✅ Whisper started (PID: $WHISPER_PID)"
fi

log "Whisper log: $WHISPER_LOG"
log ""

#
# PHASE 3: CLAUDE QUEUE HANDOFF
#
log "PHASE 3: Claude Queue Handoff"
log "------------------------------"

CLAUDE_TASK_TEMPLATE="/home/johnny5/Johny5Alive/queue/claude/weaponized_ep91_sherlock_analysis_template.json"

if [ -f "$CLAUDE_TASK_TEMPLATE" ]; then
    # Check if task already queued
    if [ -f "$CLAUDE_QUEUE" ] && grep -q "weaponized-ep91-sherlock-analysis" "$CLAUDE_QUEUE" 2>/dev/null; then
        log "⚠️  Claude task already queued"
    else
        jq -c '.' "$CLAUDE_TASK_TEMPLATE" >> "$CLAUDE_QUEUE"
        log "✅ Claude task queued to: $CLAUDE_QUEUE"
    fi
else
    log "⚠️  Template not found: $CLAUDE_TASK_TEMPLATE"
fi

log ""

#
# SUMMARY
#
log "=========================================="
log "Pipeline Execution Complete"
log "=========================================="
log "Download:     ✅ COMPLETE"
log "Diarization:  🔄 BACKGROUND (PID: $WHISPER_PID)"
log "Claude Queue: ✅ QUEUED"
log ""
log "Expected Outputs:"
log "  - Audio:      $AUDIO_FILE"
log "  - Transcript: ${OUTPUT_DIR}/episode_91.txt"
log "  - JSON:       ${OUTPUT_DIR}/episode_91.json"
log "  - SRT:        ${OUTPUT_DIR}/episode_91.srt"
log ""
log "Monitor:"
log "  tail -f $WHISPER_LOG"
log "  ps aux | grep $WHISPER_PID"
log ""
log "Full log: $LOG_FILE"
log "=========================================="
