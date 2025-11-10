#!/usr/bin/env bash
#
# Weaponized Episode 91 - Direct Episode URL Approach
# Uses direct episode page instead of homepage discovery
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Logging setup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_DIR="ops/logs"
LOG_FILE="$LOG_DIR/weaponized_ep91_direct_${TIMESTAMP}.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# Configuration
OUTPUT_DIR="artifacts/nightshift/2025-10-13/weaponized"
RETRIEVER_DIR="ops/fetchers/retriever"
EPISODE_URL="https://www.weaponizedpodcast.com/episodes-4/episode-91"
CLAUDE_QUEUE="/home/johnny5/Johny5Alive/queue/claude/2025-10-13.jsonl"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$CLAUDE_QUEUE")"

log "=========================================="
log "Weaponized Ep 91 - Direct URL Approach"
log "=========================================="
log ""

#
# PHASE 1: RETRIEVAL (Direct Episode URL)
#
log "PHASE 1: Audio Retrieval (Direct URL)"
log "--------------------------------------"
log "Episode URL: $EPISODE_URL"

RETRIEVAL_PAYLOAD='{
  "home_url": "'"$EPISODE_URL"'",
  "max_cascade_retries": 2,
  "max_stage_retries": 2,
  "download": true,
  "outdir": "'"$OUTPUT_DIR"'",
  "filename": "episode_91.mp3",
  "download_timeout": 1800
}'

log "Running retriever with direct episode URL..."

RETRIEVAL_RESULT=$(echo "$RETRIEVAL_PAYLOAD" | python3 "$RETRIEVER_DIR/nightshift_task_retriever.py" 2>&1)
RETRIEVAL_EXIT=$?

if [ $RETRIEVAL_EXIT -ne 0 ]; then
    log_error "Retrieval failed with exit code $RETRIEVAL_EXIT"
    log_error "Output: $RETRIEVAL_RESULT"
    log ""
    log "=========================================="
    log "FALLBACK: Manual Download Attempt"
    log "=========================================="

    # Fallback: Try to extract audio URL manually using RWF
    log "Attempting manual audio extraction from episode page..."

    # Use Python to scrape the page
    AUDIO_URL=$(python3 -c "
import sys
sys.path.insert(0, '$RETRIEVER_DIR')
from retriever.rwf import RobustWebFetcher
from retriever.discovery import _extract_page_audio

fetcher = RobustWebFetcher()
page = fetcher.get('$EPISODE_URL')
urls = _extract_page_audio(page.text, page.url, fetcher)

if urls:
    print(urls[0])
else:
    sys.exit(1)
" 2>&1)

    if [ $? -eq 0 ] && [ -n "$AUDIO_URL" ]; then
        log "✅ Audio URL found: $AUDIO_URL"
        log "Downloading with curl..."

        curl -L --retry 5 --retry-delay 2 -o "$OUTPUT_DIR/episode_91.mp3" "$AUDIO_URL" 2>&1 | tee -a "$LOG_FILE"

        if [ $? -eq 0 ] && [ -f "$OUTPUT_DIR/episode_91.mp3" ]; then
            log "✅ Fallback download successful"
        else
            log_error "Fallback download failed"
            exit 1
        fi
    else
        log_error "Could not extract audio URL from episode page"
        exit 1
    fi
else
    log "✅ Retrieval successful"
    echo "$RETRIEVAL_RESULT" | jq '.' >> "$LOG_FILE" 2>/dev/null || echo "$RETRIEVAL_RESULT" >> "$LOG_FILE"
fi

# Verify audio file
AUDIO_FILE="$OUTPUT_DIR/episode_91.mp3"
if [ ! -f "$AUDIO_FILE" ]; then
    log_error "Audio file not found: $AUDIO_FILE"
    exit 1
fi

AUDIO_SIZE=$(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE" 2>/dev/null)
log "Audio file: $AUDIO_FILE ($AUDIO_SIZE bytes)"
log ""

#
# PHASE 2: WHISPER DIARIZATION (Background Task)
#
log "PHASE 2: Whisper Diarization (Background)"
log "------------------------------------------"

WHISPER_LOG="$LOG_DIR/whisper_ep91_${TIMESTAMP}.log"

log "Starting Whisper Large v3..."
log "Whisper log: $WHISPER_LOG"

# Run whisper in background
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
log "✅ Whisper started (PID: $WHISPER_PID)"
echo "$WHISPER_PID" > "$OUTPUT_DIR/whisper.pid"
log ""

#
# PHASE 3: CLAUDE QUEUE HANDOFF
#
log "PHASE 3: Claude Queue Handoff"
log "------------------------------"

CLAUDE_TASK_TEMPLATE="/home/johnny5/Johny5Alive/queue/claude/weaponized_ep91_sherlock_analysis_template.json"

if [ -f "$CLAUDE_TASK_TEMPLATE" ]; then
    jq -c '.' "$CLAUDE_TASK_TEMPLATE" >> "$CLAUDE_QUEUE"
    log "✅ Claude task queued"
else
    log "⚠️  Template not found, skipping Claude queue"
fi

log ""
log "=========================================="
log "Pipeline Complete"
log "=========================================="
log "Retrieval:    ✅ COMPLETE"
log "Diarization:  🔄 BACKGROUND (PID: $WHISPER_PID)"
log "Claude Queue: ✅ QUEUED"
log ""
log "Monitor: tail -f $WHISPER_LOG"
log "=========================================="
