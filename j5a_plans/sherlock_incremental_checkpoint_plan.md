# Sherlock Incremental Checkpoint Saving - Implementation Plan

**Project:** Sherlock Audio Transcription Enhancement
**Priority:** HIGH (prevents data loss)
**Risk Level:** LOW (improves reliability)
**Created:** 2024-09-30

## Problem Statement

**Current Risk:**
Operation Gladio demonstrated a critical vulnerability: 17+ hours of transcription work stored in volatile process memory. If the process crashes, system fails, or power is lost, all progress is lost.

**Root Cause:**
The `process_gladio_fast_small.py` script accumulates all chunk transcriptions in memory and only saves to disk after ALL chunks complete. This violates the principle of incremental persistence.

## Design Principle: Incremental Save Pattern

**Core Principle:**
> Any long-running process involving significant data accumulation or computation MUST save intermediate results incrementally to prevent catastrophic data loss from system failure, crashes, or interruptions.

### When to Apply

Apply incremental saving when:
- ✅ Process runtime > 1 hour
- ✅ Data accumulation in memory > 100 MB
- ✅ Work is chunked/segmented
- ✅ Individual chunks have value independently
- ✅ Re-processing has significant cost (time/compute/money)

### Pattern Structure

```python
# ❌ WRONG: Accumulate everything, save at end
results = []
for chunk in chunks:
    result = process(chunk)
    results.append(result)  # Stored in volatile memory
save_all(results)  # Single point of failure

# ✅ CORRECT: Save after each chunk
for chunk in chunks:
    result = process(chunk)
    save_incremental(result)  # Persisted immediately
    mark_complete(chunk.id)  # Track progress
```

### Implementation Requirements

1. **Checkpoint Files**: Each chunk saves to its own file
2. **Progress Tracking**: Manifest file tracks completed chunks
3. **Resume Capability**: Can restart from last completed chunk
4. **Atomic Writes**: Use temp files + rename for crash safety
5. **Validation**: Verify saved data before marking complete

## Operation Gladio Fix

### Current Architecture (Vulnerable)

```
Process Flow:
1. Load model
2. Chunk audio into 72 pieces
3. FOR each chunk:
   - Transcribe
   - Store in memory (all_results list)
4. AFTER ALL chunks: Save to disk  ← SINGLE POINT OF FAILURE
```

**Risk:** 17 hours of work lost if process dies at 99%

### Proposed Architecture (Resilient)

```
Process Flow:
1. Load model
2. Chunk audio into 72 pieces
3. Check progress manifest (resume if exists)
4. FOR each incomplete chunk:
   - Transcribe
   - SAVE to chunk_NNN.json (atomic write)
   - UPDATE progress manifest
   - Store in memory for final assembly
5. Assemble complete transcript from saved chunks
6. Save final combined transcript
```

**Benefits:**
- ✅ Crash at any point: Resume from last saved chunk
- ✅ Can sample transcriptions during processing
- ✅ Progress visible externally
- ✅ Minimal overhead (~1-2 seconds per chunk)

## Implementation Tasks

### Task 1: Create Checkpoint Manager

**File:** `sherlock_checkpoint_manager.py`

```python
class TranscriptionCheckpointManager:
    """Manage incremental saving of transcription chunks"""

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.manifest_file = checkpoint_dir / "progress_manifest.json"
        self.checkpoint_dir.mkdir(exist_ok=True)

    def save_chunk(self, chunk_id: int, result: dict):
        """Save chunk transcription atomically"""
        chunk_file = self.checkpoint_dir / f"chunk_{chunk_id:03d}.json"
        temp_file = chunk_file.with_suffix('.tmp')

        # Write to temp file first
        with open(temp_file, 'w') as f:
            json.dump(result, f, indent=2)

        # Atomic rename
        temp_file.rename(chunk_file)

        # Update progress manifest
        self._update_manifest(chunk_id)

    def get_completed_chunks(self) -> set:
        """Return set of completed chunk IDs"""
        if not self.manifest_file.exists():
            return set()

        with open(self.manifest_file) as f:
            manifest = json.load(f)

        return set(manifest.get('completed_chunks', []))

    def load_chunk(self, chunk_id: int) -> Optional[dict]:
        """Load saved chunk transcription"""
        chunk_file = self.checkpoint_dir / f"chunk_{chunk_id:03d}.json"
        if not chunk_file.exists():
            return None

        with open(chunk_file) as f:
            return json.load(f)

    def assemble_transcript(self, num_chunks: int) -> str:
        """Assemble complete transcript from saved chunks"""
        transcript_parts = []

        for i in range(1, num_chunks + 1):
            chunk_data = self.load_chunk(i)
            if chunk_data and 'text' in chunk_data:
                transcript_parts.append(chunk_data['text'])

        return "\n\n".join(transcript_parts)

    def _update_manifest(self, chunk_id: int):
        """Update progress manifest"""
        if self.manifest_file.exists():
            with open(self.manifest_file) as f:
                manifest = json.load(f)
        else:
            manifest = {'completed_chunks': [], 'last_update': None}

        if chunk_id not in manifest['completed_chunks']:
            manifest['completed_chunks'].append(chunk_id)
            manifest['completed_chunks'].sort()

        manifest['last_update'] = datetime.now().isoformat()

        # Atomic write
        temp_file = self.manifest_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        temp_file.rename(self.manifest_file)
```

**Success Criteria:**
- Chunks save atomically (temp file + rename)
- Manifest tracks all completed chunks
- Can load any previously saved chunk
- Can assemble complete transcript from chunks

### Task 2: Modify Gladio Processor

**File:** `process_gladio_fast_small.py` (modifications)

**Changes:**

1. Add checkpoint manager initialization:
```python
def __init__(self, db_path: str = "gladio_intelligence.db"):
    self.db = GladioEvidenceDatabase(db_path)

    # Add checkpoint manager
    self.checkpoint_mgr = TranscriptionCheckpointManager(
        Path("audiobooks/operation_gladio/checkpoints")
    )
```

2. Modify chunk processing loop:
```python
# Check which chunks are already completed
completed = self.checkpoint_mgr.get_completed_chunks()
self.logger.info(f"📂 Found {len(completed)} previously completed chunks")

for i, chunk in enumerate(chunks, 1):
    # Skip if already completed
    if i in completed:
        self.logger.info(f"⏭️  Skipping chunk {i} (already completed)")
        result = self.checkpoint_mgr.load_chunk(i)
    else:
        # Process chunk
        result = self.transcribe_chunk(chunk, i)

        # SAVE IMMEDIATELY after transcription
        if "text" in result:
            self.checkpoint_mgr.save_chunk(i, result)
            self.logger.info(f"💾 Checkpoint saved: chunk {i}")

    all_results.append(result)

    if "text" in result:
        full_transcript.append(result["text"])
```

3. Final assembly uses checkpoints:
```python
# Assemble transcript from checkpoints (redundant but safe)
complete_transcript = self.checkpoint_mgr.assemble_transcript(len(chunks))

# Also save from memory for validation
memory_transcript = "\n\n".join(full_transcript)

# Verify they match
if complete_transcript == memory_transcript:
    self.logger.info("✅ Checkpoint transcript matches memory transcript")
else:
    self.logger.warning("⚠️  Checkpoint/memory mismatch - using checkpoint version")
    complete_transcript = complete_transcript  # Use checkpoint (safer)
```

**Success Criteria:**
- Script can resume from any point
- Checkpoints saved after each chunk
- No data loss on crash/interrupt
- Minimal performance overhead (<5%)

### Task 3: Create Recovery Script

**File:** `recover_gladio_from_checkpoints.py`

```python
#!/usr/bin/env python3
"""
Recover Operation Gladio transcription from checkpoints
Use this if the main process crashes
"""

from pathlib import Path
from sherlock_checkpoint_manager import TranscriptionCheckpointManager

def recover_transcript():
    """Recover complete transcript from checkpoint files"""

    checkpoint_dir = Path("audiobooks/operation_gladio/checkpoints")

    if not checkpoint_dir.exists():
        print("❌ No checkpoint directory found")
        return

    manager = TranscriptionCheckpointManager(checkpoint_dir)
    completed = manager.get_completed_chunks()

    print(f"📊 Found {len(completed)} completed chunks:")
    print(f"   Chunks: {sorted(completed)}")

    # Determine expected total
    expected_chunks = 72  # For Operation Gladio

    if len(completed) == expected_chunks:
        print("✅ All chunks complete!")
    else:
        missing = set(range(1, expected_chunks + 1)) - completed
        print(f"⚠️  Missing {len(missing)} chunks: {sorted(missing)}")

    # Assemble what we have
    print("\n📝 Assembling transcript from checkpoints...")
    transcript = manager.assemble_transcript(expected_chunks)

    # Save recovered transcript
    output_file = "audiobooks/operation_gladio/operation_gladio_transcript_RECOVERED.txt"
    with open(output_file, 'w') as f:
        f.write(transcript)

    print(f"✅ Recovered transcript saved: {output_file}")
    print(f"📊 Characters: {len(transcript):,}")
    print(f"📊 Words: {len(transcript.split()):,}")

if __name__ == "__main__":
    recover_transcript()
```

**Success Criteria:**
- Can recover partial transcripts
- Shows which chunks are missing
- Works even if process died mid-chunk

### Task 4: Add to J5A Methodology

**File:** `j5a_methodology_enforcer.py` (add new check)

Add to forbidden patterns detection:

```python
class IncrementalSaveViolation:
    """Detect lack of incremental saving in long-running processes"""

    patterns = [
        # Accumulation without incremental save
        r'results\s*=\s*\[\].*for.*in.*results\.append.*\n(?!.*save)',

        # Large loop without checkpoint
        r'for\s+\w+\s+in\s+range\([0-9]{3,}\).*\n(?!.*checkpoint|save)',
    ]

    def check(self, code: str, task: J5AWorkAssignment) -> List[str]:
        """Check if code accumulates data without incremental saves"""
        violations = []

        # If task is long-running and processes chunks
        if 'chunk' in code.lower() and 'for' in code:
            has_loop = re.search(r'for\s+.*\s+in\s+', code)
            has_save_in_loop = re.search(r'for.*\n.*(?:save|checkpoint|persist)', code, re.MULTILINE)

            if has_loop and not has_save_in_loop:
                violations.append(
                    "Long-running chunk processing without incremental saves detected. "
                    "Add checkpoint saving after each chunk to prevent data loss."
                )

        return violations
```

**Success Criteria:**
- J5A detects missing incremental saves
- Warns during code review
- Blocks tasks with high data loss risk

## Estimated Resources

**Tokens:** ~15,000
**Time:** 2-3 hours
**RAM:** <100 MB additional
**Risk:** LOW (improves reliability)

## Rollback Plan

If checkpoint implementation causes issues:
1. Original script still works (checkpoints optional)
2. Can disable checkpointing with flag
3. Can process without checkpoint manager
4. No changes to output format

## Benefits

### Immediate
- ✅ Can recover from crashes
- ✅ Can sample during processing
- ✅ Progress visible externally
- ✅ Reduced anxiety during long runs

### Long-term
- ✅ Pattern applies to all chunked processing
- ✅ J5A learns to enforce incremental saves
- ✅ Reduces risk for all future operations
- ✅ Better resource utilization (can pause/resume)

## General Principle for J5A

**Rule:** Incremental Save Pattern
**Category:** Risk Management / Data Persistence
**Priority:** MANDATORY for long-running processes

**Detection Criteria:**
```python
if (estimated_runtime > 1_hour OR
    data_accumulation > 100_MB OR
    chunk_count > 10):
    REQUIRE: incremental_checkpoint_saving()
```

**Implementation Checklist:**
- [ ] Each chunk saves to individual file
- [ ] Progress manifest tracks completion
- [ ] Atomic writes (temp + rename)
- [ ] Resume capability from manifest
- [ ] Recovery script available
- [ ] Validation of saved data

**Enforcement:**
- J5A methodology enforcer checks for pattern
- Quality gate blocks tasks without incremental saves
- Test oracle verifies resume capability
- Documentation includes recovery procedures

---

**Status:** Ready for implementation
**Next Action:** Create J5A work assignment
**Dependencies:** None (applies to existing systems)