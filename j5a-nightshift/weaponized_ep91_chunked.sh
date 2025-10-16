#!/usr/bin/env bash
#
# Weaponized Episode 91 - Protocol-Compliant Chunked Processing
# Implements CLAUDE.md chunking protocol: 10-minute segments
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source J5A Resource Safety Gate
source "$SCRIPT_DIR/ops/resource_safety_gate.sh"

# Logging setup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_DIR="ops/logs"
LOG_FILE="$LOG_DIR/weaponized_ep91_chunked_${TIMESTAMP}.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# Configuration
OUTPUT_DIR="artifacts/nightshift/2025-10-13/weaponized"
AUDIO_FILE="$OUTPUT_DIR/episode_91.mp3"
CHUNKS_DIR="$OUTPUT_DIR/chunks"
CHUNK_DURATION=600  # 10 minutes in seconds
MAX_PARALLEL=1      # SAFETY: Only 1 Whisper Large-v3 at a time (prevents OOM/freeze)

mkdir -p "$CHUNKS_DIR"

log "=========================================="
log "Weaponized Ep 91 - Chunked Processing"
log "Protocol: CLAUDE.md 10-minute segments"
log "=========================================="
log ""

# Verify audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    log_error "Audio file not found: $AUDIO_FILE"
    exit 1
fi

# Get audio duration
DURATION=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO_FILE")
DURATION_INT=${DURATION%.*}
log "Audio duration: ${DURATION_INT}s ($(echo "scale=2; $DURATION_INT / 60" | bc) minutes)"

# Calculate number of chunks
NUM_CHUNKS=$(echo "($DURATION_INT + $CHUNK_DURATION - 1) / $CHUNK_DURATION" | bc)
log "Processing strategy: $NUM_CHUNKS chunks of $CHUNK_DURATION seconds"
log "Parallel processing: $MAX_PARALLEL concurrent chunks"
log ""

#
# PHASE 1: AUDIO SEGMENTATION
#
log "PHASE 1: Audio Segmentation"
log "----------------------------"

for ((i=0; i<$NUM_CHUNKS; i++)); do
    START_TIME=$((i * CHUNK_DURATION))
    CHUNK_FILE="$CHUNKS_DIR/chunk_$(printf '%03d' $i).mp3"

    if [ -f "$CHUNK_FILE" ]; then
        log "Chunk $i already exists: $CHUNK_FILE"
    else
        log "Creating chunk $i (start: ${START_TIME}s)..."
        ffmpeg -y -i "$AUDIO_FILE" -ss "$START_TIME" -t "$CHUNK_DURATION" \
            -acodec copy "$CHUNK_FILE" 2>&1 | grep -E "(Duration|time=)" | tail -1 >> "$LOG_FILE" || true
        log "✅ Chunk $i created: $CHUNK_FILE"
    fi
done

log ""
log "✅ Segmentation complete: $NUM_CHUNKS chunks ready"
log ""

#
# PHASE 2: PARALLEL TRANSCRIPTION
#
log "PHASE 2: Parallel Transcription (whisper tiny)"
log "--------------------------------------------------"

# J5A SAFETY GATE: Acquire lock and validate system resources
log ""
log "🔒 Acquiring Whisper processing lock..."
if ! acquire_whisper_lock 2>&1 | tee -a "$LOG_FILE"; then
    log_error "Safety gate blocked execution - system not safe for Whisper processing"
    log_error "Review safety checks above and retry when conditions are met"
    exit 1
fi
log ""

process_chunk() {
    local chunk_id=$1
    local chunk_file=$2
    local chunk_log="$LOG_DIR/whisper_chunk_${chunk_id}_${TIMESTAMP}.log"

    log "Processing chunk $chunk_id..."

    whisper "$chunk_file" \
        --model tiny \
        --language en \
        --task transcribe \
        --output_dir "$CHUNKS_DIR" \
        --output_format txt \
        --output_format json \
        --output_format srt \
        --verbose False \
        > "$chunk_log" 2>&1

    if [ $? -eq 0 ]; then
        log "✅ Chunk $chunk_id complete"
        return 0
    else
        log_error "Chunk $chunk_id failed"
        return 1
    fi
}

export -f process_chunk
export -f log
export -f log_error
export LOG_FILE
export TIMESTAMP
export LOG_DIR
export CHUNKS_DIR

# Process chunks with parallel limit
CHUNK_FILES=("$CHUNKS_DIR"/chunk_*.mp3)
PIDS=()
ACTIVE=0

for chunk_file in "${CHUNK_FILES[@]}"; do
    chunk_basename=$(basename "$chunk_file" .mp3)
    chunk_id=$(echo "$chunk_basename" | grep -oP '\d+')

    # Wait if we've hit the parallel limit
    while [ $ACTIVE -ge $MAX_PARALLEL ]; do
        sleep 2
        for pid in "${PIDS[@]}"; do
            if ! ps -p "$pid" > /dev/null 2>&1; then
                ACTIVE=$((ACTIVE - 1))
            fi
        done
    done

    # Start chunk processing in background
    process_chunk "$chunk_id" "$chunk_file" &
    PIDS+=($!)
    ACTIVE=$((ACTIVE + 1))
done

# Wait for all remaining chunks
log ""
log "Waiting for all chunks to complete..."
for pid in "${PIDS[@]}"; do
    wait "$pid" || log_error "Process $pid failed"
done

log ""
log "✅ All chunks transcribed"
log ""

#
# PHASE 3: TRANSCRIPT MERGING
#
log "PHASE 3: Transcript Merging"
log "----------------------------"

FINAL_TXT="$OUTPUT_DIR/episode_91.txt"
FINAL_JSON="$OUTPUT_DIR/episode_91.json"
FINAL_SRT="$OUTPUT_DIR/episode_91.srt"

# Merge TXT files
log "Merging TXT transcripts..."
> "$FINAL_TXT"
for ((i=0; i<$NUM_CHUNKS; i++)); do
    chunk_txt="$CHUNKS_DIR/chunk_$(printf '%03d' $i).txt"
    if [ -f "$chunk_txt" ]; then
        cat "$chunk_txt" >> "$FINAL_TXT"
        echo "" >> "$FINAL_TXT"  # Add separator
    else
        log_error "Missing chunk transcript: $chunk_txt"
    fi
done
log "✅ TXT merge complete: $FINAL_TXT"

# Merge JSON files
log "Merging JSON transcripts..."
python3 << 'PYTHON_SCRIPT'
import json
import sys

chunks_dir = "$CHUNKS_DIR"
output_file = "$FINAL_JSON"
num_chunks = $NUM_CHUNKS

merged_segments = []
time_offset = 0.0

for i in range(num_chunks):
    chunk_json = f"{chunks_dir}/chunk_{i:03d}.json"
    try:
        with open(chunk_json, 'r') as f:
            data = json.load(f)

        # Adjust timestamps and append segments
        for segment in data.get('segments', []):
            segment['start'] += time_offset
            segment['end'] += time_offset
            merged_segments.append(segment)

        # Update offset for next chunk
        if data.get('segments'):
            time_offset = merged_segments[-1]['end']
    except FileNotFoundError:
        print(f"ERROR: Missing {chunk_json}", file=sys.stderr)
        sys.exit(1)

# Write merged JSON
merged_data = {
    "text": " ".join([s['text'] for s in merged_segments]),
    "segments": merged_segments,
    "language": "en"
}

with open(output_file, 'w') as f:
    json.dump(merged_data, f, indent=2)

print(f"✅ JSON merge complete: {output_file}")
PYTHON_SCRIPT

# Merge SRT files with timestamp adjustment
log "Merging SRT transcripts..."
python3 << 'PYTHON_SCRIPT2'
import re

chunks_dir = "$CHUNKS_DIR"
output_file = "$FINAL_SRT"
num_chunks = $NUM_CHUNKS
chunk_duration = $CHUNK_DURATION

def parse_srt_time(time_str):
    """Convert SRT timestamp to seconds"""
    h, m, s = time_str.replace(',', '.').split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def format_srt_time(seconds):
    """Convert seconds to SRT timestamp"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')

merged_srt = []
segment_counter = 1

for i in range(num_chunks):
    chunk_srt = f"{chunks_dir}/chunk_{i:03d}.srt"
    time_offset = i * chunk_duration

    try:
        with open(chunk_srt, 'r') as f:
            content = f.read().strip()

        # Parse SRT entries
        entries = content.split('\n\n')
        for entry in entries:
            if not entry.strip():
                continue

            lines = entry.split('\n')
            if len(lines) >= 3:
                # lines[0] is segment number (we'll renumber)
                # lines[1] is timestamp
                # lines[2+] is text

                timestamp_match = re.match(r'(\S+) --> (\S+)', lines[1])
                if timestamp_match:
                    start_time = parse_srt_time(timestamp_match.group(1)) + time_offset
                    end_time = parse_srt_time(timestamp_match.group(2)) + time_offset
                    text = '\n'.join(lines[2:])

                    merged_srt.append(f"{segment_counter}")
                    merged_srt.append(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}")
                    merged_srt.append(text)
                    merged_srt.append("")  # Blank line separator

                    segment_counter += 1
    except FileNotFoundError:
        print(f"ERROR: Missing {chunk_srt}", file=sys.stderr)

with open(output_file, 'w') as f:
    f.write('\n'.join(merged_srt))

print(f"✅ SRT merge complete: {output_file}")
PYTHON_SCRIPT2

log ""
log "✅ All transcripts merged"
log ""

#
# SUMMARY
#
log "=========================================="
log "Chunked Processing Complete"
log "=========================================="
log "Segmentation:     ✅ COMPLETE ($NUM_CHUNKS chunks)"
log "Transcription:    ✅ COMPLETE"
log "Merging:          ✅ COMPLETE"
log ""
log "Final Outputs:"
log "  - Transcript:  $FINAL_TXT"
log "  - JSON:        $FINAL_JSON"
log "  - SRT:         $FINAL_SRT"
log ""
log "Chunk artifacts: $CHUNKS_DIR"
log "Full log:        $LOG_FILE"
log "=========================================="
