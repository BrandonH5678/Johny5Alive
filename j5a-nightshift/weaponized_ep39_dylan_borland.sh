#!/usr/bin/env bash
#
# Weaponized Episode 39 - Dylan Borland Part 2
# Sherlock Intelligence Extraction Pipeline
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Logging setup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_DIR="ops/logs"
LOG_FILE="$LOG_DIR/weaponized_ep39_borland_${TIMESTAMP}.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# Configuration
OUTPUT_DIR="artifacts/nightshift/2025-10-13/weaponized/ep39_borland"
AUDIO_URL="https://www.podtrac.com/pts/redirect.mp3/pdst.fm/e/prfx.byspotify.com/e/pscrb.fm/rss/p/mgln.ai/e/p721018/mgln.ai/e/1468/chrt.fm/track/B175B2/traffic.megaphone.fm/IMP3237728966.mp3?updated=1759469815"
AUDIO_FILE="$OUTPUT_DIR/episode_39_dylan_borland_part2.mp3"
CLAUDE_QUEUE="/home/johnny5/Johny5Alive/queue/claude/2025-10-13.jsonl"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$CLAUDE_QUEUE")"

log "=========================================="
log "Weaponized Ep 39 - Sherlock Pipeline"
log "=========================================="
log ""
log "Episode: Dylan Borland Unloads - The Truth About Legacy UFO Programs : PART 2"
log "Guest: Dylan Borland (UAP Whistleblower)"
log "Published: Oct 3, 2025"
log ""

#
# PHASE 1: DOWNLOAD
#
log "PHASE 1: Audio Download"
log "------------------------"

if [ -f "$AUDIO_FILE" ]; then
    EXISTING_SIZE=$(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE" 2>/dev/null)
    log "⚠️  File already exists ($EXISTING_SIZE bytes)"
    log "Skipping download..."
else
    log "Downloading Dylan Borland Part 2..."
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

WHISPER_LOG="$LOG_DIR/whisper_ep39_borland_${TIMESTAMP}.log"

if [ -f "$OUTPUT_DIR/whisper.pid" ]; then
    OLD_PID=$(cat "$OUTPUT_DIR/whisper.pid")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        log "⚠️  Whisper already running (PID: $OLD_PID)"
        log "Skipping whisper launch..."
        WHISPER_PID=$OLD_PID
    else
        log "Starting Whisper Large v3..."
        nohup /home/johnny5/.local/bin/whisper "$AUDIO_FILE" \
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
    nohup /home/johnny5/.local/bin/whisper "$AUDIO_FILE" \
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

# Create custom Sherlock analysis task for Dylan Borland
CLAUDE_TASK=$(cat <<EOF
{
  "id": "2025-10-13T21:00:00Z-weaponized-ep39-borland-sherlock",
  "type": "analysis",
  "priority": "high",
  "sherlock_metadata": {
    "package_id": "weaponized_ep39_borland_20251013",
    "target_name": "Weaponized Episode 39 - Dylan Borland Part 2",
    "evidence_type": "transcript_audio",
    "source_credibility": "high",
    "analysis_depth": "comprehensive",
    "cross_reference": true
  },
  "inputs": [
    "$OUTPUT_DIR/episode_39_dylan_borland_part2.txt",
    "$OUTPUT_DIR/episode_39_dylan_borland_part2.json"
  ],
  "deliverables": [
    "artifacts/claude/2025-10-13/sherlock/borland_ep39_overview.json",
    "artifacts/claude/2025-10-13/sherlock/borland_ep39_claims.json",
    "artifacts/claude/2025-10-13/sherlock/borland_ep39_entities.json",
    "artifacts/claude/2025-10-13/sherlock/borland_ep39_timeline.json",
    "artifacts/claude/2025-10-13/sherlock/borland_ep39_evidence_gaps.json",
    "artifacts/claude/2025-10-13/reports/borland_ep39_intelligence_summary.md"
  ],
  "constraints": {
    "max_tokens": 60000,
    "style": "intelligence_analysis",
    "citations": true,
    "speaker_attribution": true,
    "cross_reference_sherlock_db": true,
    "fact_vs_speculation": true
  },
  "notes": "Sherlock Intelligence Analysis: Dylan Borland UAP Whistleblower testimony PART 2. Extract all claims about legacy UFO programs, defense contractors, government witnesses, and Congressional testimony. Identify key individuals, organizations, and programs. Build timeline of events. Note speaker attribution (Jeremy Corbell, George Knapp, Dylan Borland). Cross-reference with existing Sherlock evidence database. Distinguish verifiable facts from speculation. Flag claims requiring corroboration. Focus on Borland's specific allegations about UFO retrieval programs and government secrecy."
}
EOF
)

if grep -q "weaponized-ep39-borland-sherlock" "$CLAUDE_QUEUE" 2>/dev/null; then
    log "⚠️  Claude task already queued"
else
    echo "$CLAUDE_TASK" | jq -c '.' >> "$CLAUDE_QUEUE"
    log "✅ Claude task queued"
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
log "  - Transcript: ${OUTPUT_DIR}/episode_39_dylan_borland_part2.txt"
log "  - JSON:       ${OUTPUT_DIR}/episode_39_dylan_borland_part2.json"
log "  - SRT:        ${OUTPUT_DIR}/episode_39_dylan_borland_part2.srt"
log ""
log "Monitor: tail -f $WHISPER_LOG"
log "Full log: $LOG_FILE"
log "=========================================="
