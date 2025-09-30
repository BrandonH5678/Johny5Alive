# Propagate Incremental Save Pattern to Squirt and Sherlock Implementation Plan

## Overview

**Goal:** Propagate the Incremental Save Pattern principle (learned from Operation Gladio Sept 2024) to Squirt and Sherlock systems to prevent catastrophic data loss from crashes during long-running processes.

**Priority:** CRITICAL
**Risk Level:** LOW (documentation + pattern implementation)
**Estimated Tokens:** 45,000
**Estimated Duration:** 2.5 hours

## Background: Operation Gladio Lesson

**Critical Design Principle Learned (Sept 2024):**
> "Any long-running process that accumulates data in memory MUST save intermediate results incrementally."

**Why This Matters:**
- Operation Gladio: 17+ hours of transcription work at risk in volatile memory
- System crash at 99% complete = 100% data loss
- Power loss, thermal shutdown, OOM crash all cause total failure
- Incremental saves = Resume from last checkpoint (minimal loss)

---

## Current State Analysis

### What Works
- ✅ J5A CLAUDE.md: Incremental Save Pattern documented (Sept 2024)
- ✅ J5A has learned the lesson and documented the principle
- ✅ Pattern includes when-to-apply rules and implementation requirements

### What's Missing
- ❌ **Squirt:** No incremental save pattern in voice queue processing
- ❌ **Squirt:** Voice processing accumulates results in memory before saving
- ❌ **Sherlock:** Long-form audio transcription (12+ hour audiobooks) at risk
- ❌ **Sherlock:** No checkpoint mechanism for multi-hour processing tasks

### Gap Impact
- **Squirt Risk:** Voice queue batch processing could lose all results on crash
- **Sherlock Risk:** 17+ hour audiobook transcription vulnerable to 100% data loss
- **System Viability:** Violates "completion > quality" principle by risking incomplete work

---

## Implementation Phases

### Phase 1: Squirt Voice Queue Checkpoint System (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** None
**Estimated Tokens:** 18,000
**Estimated Duration:** 1 hour

**Tasks:**
1. Update Squirt CLAUDE.md with Incremental Save Pattern auto-injection
2. Update Squirt AI Operator Manual with checkpoint requirements
3. Implement CheckpointManager for voice_queue_manager.py
4. Add incremental save after each voice memo processing
5. Add checkpoint manifest tracking for resume capability

**Expected Outputs:**
- `/home/johnny5/Squirt/CLAUDE.md` (updated with incremental save pattern)
- `/home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md` (checkpoint protocols added)
- `/home/johnny5/Squirt/src/voice_checkpoint_manager.py` (new module)
- `/home/johnny5/Squirt/src/voice_queue_manager.py` (checkpoint integration)

**Success Criteria:**
- Voice queue saves results after each memo (not batch at end)
- Checkpoint manifest tracks completed memos
- Resume capability functional after simulated crash
- Zero data loss for completed voice memos

**Implementation Pattern:**
```python
# ❌ WRONG: Current Squirt voice queue (accumulate in memory)
results = []
for voice_memo in queue:
    result = process_voice_memo(voice_memo)
    results.append(result)  # RISK: All work lost on crash
save_all_results(results)  # Single point of failure

# ✅ CORRECT: Incremental checkpoint saves
checkpoint_mgr = VoiceCheckpointManager()
for voice_memo in queue:
    result = process_voice_memo(voice_memo)
    checkpoint_mgr.save_result(voice_memo.id, result)  # Immediately persisted
    checkpoint_mgr.update_manifest(voice_memo.id, status="complete")
```

---

### Phase 2: Sherlock Audio Transcription Checkpoints (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 1 complete (for pattern consistency)
**Estimated Tokens:** 20,000
**Estimated Duration:** 1 hour

**Tasks:**
1. Update Sherlock CLAUDE.md with Incremental Save Pattern auto-injection
2. Update Sherlock AI Operator Manual with checkpoint protocols
3. Implement AudioTranscriptionCheckpointManager
4. Add chunk-based checkpoint saves for long-form audio
5. Implement resume-from-checkpoint for interrupted transcriptions

**Expected Outputs:**
- `/home/johnny5/Sherlock/CLAUDE.md` (updated with incremental save pattern)
- `/home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md` (checkpoint protocols)
- `/home/johnny5/Sherlock/audio_transcription_checkpoint_manager.py` (new module)
- `/home/johnny5/Sherlock/voice_engine.py` (checkpoint integration)

**Success Criteria:**
- Long-form audio saves transcription after each chunk (10-minute segments)
- Checkpoint manifest tracks completed chunks with timestamps
- Resume capability functional - can restart from last checkpoint
- Operation Gladio scenario prevented (17+ hours recoverable)

**Implementation Pattern:**
```python
# ❌ WRONG: Current risk for long-form audio
all_transcripts = []
for chunk in audio_chunks:  # 100+ chunks for 17-hour audiobook
    transcript = transcribe_chunk(chunk)
    all_transcripts.append(transcript)  # RISK: Hours of work in volatile memory
save_complete_transcript(all_transcripts)  # Crash before this = 100% loss

# ✅ CORRECT: Incremental chunk checkpoint saves
checkpoint_mgr = AudioTranscriptionCheckpointManager(audiobook_id="gladio_001")
for i, chunk in enumerate(audio_chunks):
    transcript = transcribe_chunk(chunk)
    checkpoint_mgr.save_chunk_transcript(i, transcript)  # Persist immediately
    checkpoint_mgr.update_progress(chunks_complete=i+1)

# Resume capability
if checkpoint_mgr.has_checkpoint(audiobook_id):
    last_chunk = checkpoint_mgr.get_last_completed_chunk()
    audio_chunks = audio_chunks[last_chunk+1:]  # Resume from interruption
```

---

### Phase 3: Documentation Propagation (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 1 and 2 complete
**Estimated Tokens:** 5,000
**Estimated Duration:** 20 minutes

**Tasks:**
1. Create cross-reference in J5A documentation pointing to Squirt/Sherlock implementations
2. Document when-to-apply rules for each system
3. Add incremental save pattern to J5A methodology enforcement checklist
4. Update J5A validation gates to check for incremental saves in long-running tasks

**Expected Outputs:**
- `/home/johnny5/Johny5Alive/CLAUDE.md` (cross-references updated)
- `/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md` (enforcement checklist)

**Success Criteria:**
- J5A documentation references Squirt/Sherlock implementations
- When-to-apply rules documented for each system
- J5A validation gates include incremental save pattern checks
- Consistent pattern across all three systems

---

### Phase 4: Validation and Testing (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 3 complete
**Estimated Tokens:** 2,000
**Estimated Duration:** 10 minutes

**Tasks:**
1. Create test scenario: Simulated crash during Squirt voice queue processing
2. Verify resume-from-checkpoint for voice queue
3. Create test scenario: Simulated crash during Sherlock long-form transcription
4. Verify chunk recovery and resume capability
5. Document validation results

**Expected Outputs:**
- Test results confirming zero data loss for completed work
- Resume capability validation documentation

**Success Criteria:**
- Squirt voice queue recovers all completed memos after simulated crash
- Sherlock long-form transcription resumes from last completed chunk
- No duplicate processing of already-completed work
- Checkpoint overhead < 5% of total processing time

---

## Dependencies

**External:**
- None (pattern implementation, not external libraries)

**Blocking Conditions:**
- None (all prerequisites satisfied)

**Hardware Requirements:**
- Standard disk space for checkpoint files (minimal - JSON/text)

---

## When to Apply Incremental Save Pattern

**Squirt:**
- ✅ Voice queue batch processing (>10 memos)
- ✅ Multi-input document generation sequences
- ⚠️ Single voice memo processing (NOT needed - completes in <5 min)

**Sherlock:**
- ✅ Long-form audio transcription (>1 hour runtime)
- ✅ Large audiobook processing (Operation Gladio: 17+ hours)
- ✅ Batch evidence analysis (>50 items)
- ⚠️ Single short audio clip (NOT needed - completes quickly)

**General Rules (from J5A):**
- ✅ Process runtime > 1 hour
- ✅ Data accumulation > 100 MB
- ✅ Work is chunked/segmented (>10 chunks)
- ✅ Re-processing has significant cost (time/compute/money)

---

## Rollback Plan

**If checkpoint system causes issues:**
1. Revert CLAUDE.md updates for Squirt/Sherlock
2. Revert AI Operator Manual updates
3. Remove checkpoint manager modules
4. Restore original processing logic (non-incremental)
5. Document rollback reason and blockers

**Recovery Strategy:**
- Checkpoint saves are additive (append-only)
- Rollback removes checkpoint logic but preserves existing functionality
- No data loss from rollback (checkpoint files remain as backup)

---

## Test Oracle

**Validation Criteria:**

1. **Squirt Voice Queue Test:**
   ```bash
   # Start voice queue with 20 memos
   python3 /home/johnny5/Squirt/src/voice_queue_manager.py --process-batch test_batch_20
   # Kill process after 10 memos complete
   # Resume and verify: 10 already complete, 10 remaining processed
   ```

2. **Sherlock Long-Form Audio Test:**
   ```bash
   # Start 2-hour audiobook transcription
   python3 /home/johnny5/Sherlock/voice_engine.py --process long_audiobook.aaxc
   # Kill process after 30 minutes (25% complete)
   # Resume and verify: Starts from chunk 15, not chunk 0
   ```

3. **Checkpoint Overhead Test:**
   ```bash
   # Measure processing time with and without checkpoints
   # Verify overhead < 5% of total processing time
   ```

**Quality Metrics:**
- Zero data loss for completed work
- Resume capability functional
- Checkpoint overhead < 5%
- No duplicate processing

---

## Notes

- **Critical Priority:** Prevents catastrophic data loss (17+ hours work at risk)
- **Low Risk:** Additive checkpoint system, doesn't modify core processing
- **High Value:** Enables long-running processes that were previously too risky
- **Operation Gladio Prevention:** Directly addresses real failure scenario

---

**Plan Status:** Ready for J5A overnight execution
**Created:** 2025-09-30
**Version:** 1.0
**Origin:** Operation Gladio lesson learned (Sept 2024)
