#!/usr/bin/env bash
#
# Weaponized Episode 91 - Sherlock Intelligence Extraction Pipeline
# Executes: Retrieval → Whisper Diarization → Claude Queue
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Logging setup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_DIR="ops/logs"
LOG_FILE="$LOG_DIR/weaponized_ep91_pipeline_${TIMESTAMP}.log"
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
CLAUDE_QUEUE="queue/claude/2025-10-13.jsonl"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$CLAUDE_QUEUE")"

log "=========================================="
log "Weaponized Ep 91 - Sherlock Pipeline"
log "=========================================="
log ""

#
# PHASE 1: RETRIEVAL
#
log "PHASE 1: Audio Retrieval"
log "-------------------------"

RETRIEVAL_PAYLOAD='{
  "home_url": "https://www.weaponizedpodcast.com",
  "prefer_epnum": 91,
  "max_cascade_retries": 3,
  "max_stage_retries": 2,
  "download": true,
  "outdir": "'"$OUTPUT_DIR"'",
  "filename": "episode_91.mp3",
  "download_timeout": 1800
}'

log "Running Night Shift Retriever..."
log "Payload: $RETRIEVAL_PAYLOAD"

RETRIEVAL_RESULT=$(echo "$RETRIEVAL_PAYLOAD" | python3 "$RETRIEVER_DIR/nightshift_task_retriever.py" 2>&1)
RETRIEVAL_EXIT=$?

if [ $RETRIEVAL_EXIT -ne 0 ]; then
    log_error "Retrieval failed with exit code $RETRIEVAL_EXIT"
    log_error "Output: $RETRIEVAL_RESULT"
    exit 1
fi

log "✅ Retrieval successful"
echo "$RETRIEVAL_RESULT" | jq '.' >> "$LOG_FILE" 2>/dev/null || echo "$RETRIEVAL_RESULT" >> "$LOG_FILE"

# Extract downloaded file path
AUDIO_FILE="$OUTPUT_DIR/episode_91.mp3"
if [ ! -f "$AUDIO_FILE" ]; then
    log_error "Downloaded audio file not found: $AUDIO_FILE"
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

TRANSCRIPT_PREFIX="$OUTPUT_DIR/ep91_transcript_diarized"
WHISPER_LOG="$LOG_DIR/whisper_ep91_${TIMESTAMP}.log"

# Check if whisper is available
if ! command -v whisper &> /dev/null; then
    log_error "OpenAI Whisper not found. Install with: pip3 install openai-whisper"
    exit 1
fi

log "Starting Whisper Large v3 with speaker diarization..."
log "Output prefix: $TRANSCRIPT_PREFIX"
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
log "Background process running - check log: $WHISPER_LOG"
log ""

# Save PID for monitoring
echo "$WHISPER_PID" > "$OUTPUT_DIR/whisper.pid"

#
# PHASE 3: CLAUDE QUEUE HANDOFF (Conditional)
#
log "PHASE 3: Claude Queue Handoff"
log "------------------------------"

log "Creating Claude Queue task for Sherlock analysis..."

# Use the template and append to today's JSONL
CLAUDE_TASK_TEMPLATE="/home/johnny5/Johny5Alive/queue/claude/weaponized_ep91_sherlock_analysis_template.json"

if [ ! -f "$CLAUDE_TASK_TEMPLATE" ]; then
    log_error "Claude task template not found: $CLAUDE_TASK_TEMPLATE"
    exit 1
fi

# Convert to single-line JSONL and append
jq -c '.' "$CLAUDE_TASK_TEMPLATE" >> "/home/johnny5/Johny5Alive/$CLAUDE_QUEUE"

log "✅ Claude task queued to: $CLAUDE_QUEUE"
log ""

#
# SUMMARY
#
log "=========================================="
log "Pipeline Execution Summary"
log "=========================================="
log "Phase 1 (Retrieval):    ✅ COMPLETE"
log "Phase 2 (Diarization):  🔄 BACKGROUND (PID: $WHISPER_PID)"
log "Phase 3 (Claude Queue): ✅ QUEUED"
log ""
log "Expected Outputs:"
log "  - Audio:      $AUDIO_FILE"
log "  - Transcript: ${TRANSCRIPT_PREFIX}.txt"
log "  - JSON:       ${TRANSCRIPT_PREFIX}.json"
log "  - SRT:        ${TRANSCRIPT_PREFIX}.srt"
log ""
log "Monitor diarization progress:"
log "  tail -f $WHISPER_LOG"
log ""
log "Check Whisper status:"
log "  ps aux | grep $WHISPER_PID"
log ""
log "Full pipeline log: $LOG_FILE"
log "=========================================="
