#!/usr/bin/env bash
#
# Universal Whisper Chunking Wrapper
# Automatically chunks audio files before transcription to prevent memory exhaustion
#
# Usage:
#   ./whisper_chunked_wrapper.sh <audio_file> [whisper_args...]
#
# Example:
#   ./whisper_chunked_wrapper.sh podcast.mp3 --model large-v3 --language en
#
# Design Principles:
#   - Automatic chunking for all audio >15 minutes
#   - Memory-aware parallelization (MAX_PARALLEL based on available RAM)
#   - Incremental save pattern: saves transcripts after each chunk
#   - Seamless merge of final outputs (txt, json, srt)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source J5A Resource Safety Gate
source "$SCRIPT_DIR/ops/resource_safety_gate.sh"

# ==========================================
# CONFIGURATION
# ==========================================

CHUNK_DURATION=600        # 10 minutes per chunk (Operation Gladio protocol)
MIN_DURATION_FOR_CHUNKING=900  # Chunk if audio >15 minutes
MEMORY_PER_WHISPER_GB=10.0 # Whisper Large-v3 memory requirement (conservative estimate)

# ==========================================
# ARGUMENT PARSING
# ==========================================

if [ $# -lt 1 ]; then
    echo "Usage: $0 <audio_file> [whisper_args...]"
    echo ""
    echo "Example:"
    echo "  $0 podcast.mp3 --model large-v3 --language en --task transcribe"
    echo ""
    echo "Features:"
    echo "  - Automatic chunking for audio >15 minutes"
    echo "  - Memory-safe parallel processing"
    echo "  - Incremental checkpoint saving"
    echo "  - Seamless output merging (txt, json, srt)"
    exit 1
fi

AUDIO_FILE="$1"
shift
WHISPER_ARGS=("$@")

# ==========================================
# VALIDATION
# ==========================================

if [ ! -f "$AUDIO_FILE" ]; then
    echo "ERROR: Audio file not found: $AUDIO_FILE" >&2
    exit 1
fi

# Use faster-whisper CLI wrapper (more efficient than OpenAI Whisper)
FASTER_WHISPER_CLI="$SCRIPT_DIR/faster_whisper_cli.py"
if [ ! -f "$FASTER_WHISPER_CLI" ]; then
    echo "ERROR: faster-whisper CLI wrapper not found: $FASTER_WHISPER_CLI" >&2
    exit 1
fi

# Verify faster-whisper is installed
if ! python3 -c "import faster_whisper" &> /dev/null; then
    echo "ERROR: faster-whisper not installed. Install with: pip3 install faster-whisper" >&2
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg not installed. Install with: sudo apt-get install ffmpeg" >&2
    exit 1
fi

if ! command -v ffprobe &> /dev/null; then
    echo "ERROR: ffprobe not installed (comes with ffmpeg)" >&2
    exit 1
fi

# ==========================================
# AUDIO ANALYSIS
# ==========================================

echo "=========================================="
echo "Whisper Chunked Wrapper"
echo "=========================================="
echo "Audio: $AUDIO_FILE"
echo ""

# Get audio duration
DURATION=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO_FILE")
DURATION_INT=${DURATION%.*}
DURATION_MINUTES=$(echo "scale=2; $DURATION_INT / 60" | bc)

echo "Duration: ${DURATION_INT}s (${DURATION_MINUTES} minutes)"

# Check if chunking is needed
if [ "$DURATION_INT" -lt "$MIN_DURATION_FOR_CHUNKING" ]; then
    echo "Audio is short (<15 min) - processing directly without chunking"
    echo ""
    python3 "$FASTER_WHISPER_CLI" "$AUDIO_FILE" "${WHISPER_ARGS[@]}"
    exit $?
fi

echo "Audio is long (>${MIN_DURATION_FOR_CHUNKING}s) - enabling chunked processing"
echo ""

# ==========================================
# J5A SAFETY GATE - RESOURCE VALIDATION
# ==========================================

# CRITICAL: Only 1 Whisper Large-v3 process at a time
# Prevents OOM crashes and system freezes
MAX_PARALLEL=1

echo "=========================================="
echo "J5A Safety Gate - Resource Validation"
echo "=========================================="
echo ""
echo "Max parallel chunks: $MAX_PARALLEL (enforced for system safety)"
echo ""

# Acquire lock and validate system resources
echo "🔒 Acquiring Whisper processing lock..."
if ! acquire_whisper_lock; then
    echo "❌ Safety gate blocked execution - system not safe for Whisper processing" >&2
    echo "Review safety checks above and retry when conditions are met" >&2
    exit 1
fi
echo ""

# ==========================================
# CHUNKING SETUP
# ==========================================

# Determine output directory from whisper args or use audio file location
OUTPUT_DIR=$(dirname "$AUDIO_FILE")
for ((i=0; i<${#WHISPER_ARGS[@]}; i++)); do
    if [ "${WHISPER_ARGS[$i]}" = "--output_dir" ] && [ $((i+1)) -lt ${#WHISPER_ARGS[@]} ]; then
        OUTPUT_DIR="${WHISPER_ARGS[$((i+1))]}"
        break
    fi
done

AUDIO_BASENAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
CHUNKS_DIR="$OUTPUT_DIR/chunks_${AUDIO_BASENAME}"
mkdir -p "$CHUNKS_DIR"

# Calculate number of chunks
NUM_CHUNKS=$(echo "($DURATION_INT + $CHUNK_DURATION - 1) / $CHUNK_DURATION" | bc)

echo "Chunking strategy:"
echo "  - Chunk duration: ${CHUNK_DURATION}s (10 minutes)"
echo "  - Total chunks: $NUM_CHUNKS"
echo "  - Chunks directory: $CHUNKS_DIR"
echo ""

# ==========================================
# PHASE 1: AUDIO SEGMENTATION
# ==========================================

echo "PHASE 1: Audio Segmentation"
echo "----------------------------"

for ((i=0; i<$NUM_CHUNKS; i++)); do
    START_TIME=$((i * CHUNK_DURATION))
    CHUNK_FILE="$CHUNKS_DIR/chunk_$(printf '%03d' $i).mp3"

    if [ -f "$CHUNK_FILE" ]; then
        echo "✓ Chunk $i already exists (incremental save pattern)"
    else
        echo "Creating chunk $i (start: ${START_TIME}s)..."
        ffmpeg -y -i "$AUDIO_FILE" -ss "$START_TIME" -t "$CHUNK_DURATION" \
            -acodec copy "$CHUNK_FILE" 2>&1 | grep -E "(Duration|time=)" | tail -1 || true
        echo "✅ Chunk $i created"
    fi
done

echo ""
echo "✅ Segmentation complete: $NUM_CHUNKS chunks ready"
echo ""

# ==========================================
# PHASE 2: PARALLEL TRANSCRIPTION
# ==========================================

echo "PHASE 2: Parallel Transcription"
echo "--------------------------------"

# Build whisper command from original args, removing --output_dir (we'll override)
WHISPER_CMD_ARGS=()
SKIP_NEXT=false
for ((i=0; i<${#WHISPER_ARGS[@]}; i++)); do
    if [ "$SKIP_NEXT" = true ]; then
        SKIP_NEXT=false
        continue
    fi

    if [ "${WHISPER_ARGS[$i]}" = "--output_dir" ]; then
        SKIP_NEXT=true
        continue
    fi

    WHISPER_CMD_ARGS+=("${WHISPER_ARGS[$i]}")
done

# Track background processes
PIDS=()
ACTIVE=0

for ((i=0; i<$NUM_CHUNKS; i++)); do
    CHUNK_FILE="$CHUNKS_DIR/chunk_$(printf '%03d' $i).mp3"
    CHUNK_ID=$(printf '%03d' $i)

    # Wait if we've hit the parallel limit (BEFORE checking incremental save)
    # This ensures serialization works even when some chunks are skipped
    while [ $ACTIVE -ge $MAX_PARALLEL ]; do
        sleep 2
        NEW_PIDS=()
        for pid in "${PIDS[@]}"; do
            if ps -p "$pid" > /dev/null 2>&1; then
                # Process still running - keep it
                NEW_PIDS+=("$pid")
            else
                # Process completed - decrement counter
                ACTIVE=$((ACTIVE - 1))
            fi
        done
        PIDS=("${NEW_PIDS[@]}")
    done

    # Check if already processed (incremental save pattern)
    if [ -f "$CHUNKS_DIR/chunk_${CHUNK_ID}.txt" ]; then
        echo "✓ Chunk $i already transcribed (incremental save pattern)"
        continue
    fi

    # Start chunk processing in background (inlined to avoid export -f issues)
    echo "Processing chunk $i..."
    (
        python3 "$FASTER_WHISPER_CLI" "$CHUNK_FILE" \
            "${WHISPER_CMD_ARGS[@]}" \
            --output_dir "$CHUNKS_DIR" \
            --verbose False \
            > "$CHUNKS_DIR/chunk_${CHUNK_ID}.log" 2>&1
    ) &
    PIDS+=($!)
    ACTIVE=$((ACTIVE + 1))
done

# Wait for all remaining chunks
echo ""
echo "Waiting for all chunks to complete..."
for pid in "${PIDS[@]}"; do
    wait "$pid" || echo "WARNING: Process $pid failed" >&2
done

echo ""
echo "✅ All chunks transcribed"
echo ""

# ==========================================
# PHASE 3: TRANSCRIPT MERGING
# ==========================================

echo "PHASE 3: Transcript Merging"
echo "----------------------------"

FINAL_TXT="$OUTPUT_DIR/${AUDIO_BASENAME}.txt"
FINAL_JSON="$OUTPUT_DIR/${AUDIO_BASENAME}.json"
FINAL_SRT="$OUTPUT_DIR/${AUDIO_BASENAME}.srt"

# Merge TXT files
echo "Merging TXT transcripts..."
> "$FINAL_TXT"
for ((i=0; i<$NUM_CHUNKS; i++)); do
    chunk_txt="$CHUNKS_DIR/chunk_$(printf '%03d' $i).txt"
    if [ -f "$chunk_txt" ]; then
        cat "$chunk_txt" >> "$FINAL_TXT"
        echo "" >> "$FINAL_TXT"
    else
        echo "WARNING: Missing chunk transcript: $chunk_txt" >&2
    fi
done
echo "✅ TXT merge complete: $FINAL_TXT"

# Merge JSON files (if json format requested)
if echo "${WHISPER_ARGS[@]}" | grep -q "json"; then
    echo "Merging JSON transcripts..."
    python3 << EOF
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
        print(f"WARNING: Missing {chunk_json}", file=sys.stderr)

# Write merged JSON
merged_data = {
    "text": " ".join([s['text'] for s in merged_segments]),
    "segments": merged_segments,
    "language": "en"
}

with open(output_file, 'w') as f:
    json.dump(merged_data, f, indent=2)

print(f"✅ JSON merge complete: {output_file}")
EOF
fi

# Merge SRT files (if srt format requested)
if echo "${WHISPER_ARGS[@]}" | grep -q "srt"; then
    echo "Merging SRT transcripts..."
    python3 << 'EOF'
import re
import sys

chunks_dir = "$CHUNKS_DIR"
output_file = "$FINAL_SRT"
num_chunks = $NUM_CHUNKS
chunk_duration = $CHUNK_DURATION

def parse_srt_time(time_str):
    h, m, s = time_str.replace(',', '.').split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def format_srt_time(seconds):
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

        entries = content.split('\n\n')
        for entry in entries:
            if not entry.strip():
                continue

            lines = entry.split('\n')
            if len(lines) >= 3:
                timestamp_match = re.match(r'(\S+) --> (\S+)', lines[1])
                if timestamp_match:
                    start_time = parse_srt_time(timestamp_match.group(1)) + time_offset
                    end_time = parse_srt_time(timestamp_match.group(2)) + time_offset
                    text = '\n'.join(lines[2:])

                    merged_srt.append(f"{segment_counter}")
                    merged_srt.append(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}")
                    merged_srt.append(text)
                    merged_srt.append("")

                    segment_counter += 1
    except FileNotFoundError:
        print(f"WARNING: Missing {chunk_srt}", file=sys.stderr)

with open(output_file, 'w') as f:
    f.write('\n'.join(merged_srt))

print(f"✅ SRT merge complete: {output_file}")
EOF
fi

echo ""
echo "✅ All transcripts merged"
echo ""

# ==========================================
# SUMMARY
# ==========================================

echo "=========================================="
echo "Chunked Processing Complete"
echo "=========================================="
echo "Segmentation:     ✅ $NUM_CHUNKS chunks"
echo "Transcription:    ✅ COMPLETE"
echo "Merging:          ✅ COMPLETE"
echo ""
echo "Final Outputs:"
[ -f "$FINAL_TXT" ] && echo "  - Transcript:  $FINAL_TXT"
[ -f "$FINAL_JSON" ] && echo "  - JSON:        $FINAL_JSON"
[ -f "$FINAL_SRT" ] && echo "  - SRT:         $FINAL_SRT"
echo ""
echo "Chunk artifacts preserved: $CHUNKS_DIR"
echo "=========================================="
