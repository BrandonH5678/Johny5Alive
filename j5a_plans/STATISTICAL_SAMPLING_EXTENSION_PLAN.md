# Extend Statistical Sampling to Squirt and Sherlock Implementation Plan

## Overview

**Goal:** Extend J5A's statistical sampling validation methodology (3-segment stratified sampling) to Squirt and Sherlock systems to enable early quality assessment and resource allocation decisions.

**Priority:** MEDIUM
**Risk Level:** LOW
**Estimated Tokens:** 40,000
**Estimated Duration:** 2 hours

## Background: J5A Statistical Sampling Philosophy

**Core Validation Philosophy:**
> "Statistical sampling validates processing viability BEFORE resource allocation to prevent waste of system resources."

**3-Segment Stratified Sampling:**
- **Beginning sample:** First 10% of input data
- **Middle sample:** Middle 10% of input data
- **End sample:** Final 10% of input data
- **Random sample:** Additional random selection for distribution coverage

**Quality Thresholds (J5A Standard):**
- **Format Validation:** 80%+ samples must have valid format
- **Processing Success:** 60%+ samples must process successfully
- **Output Generation:** 80%+ samples must generate expected outputs
- **Overall Quality:** Average quality score ≥50%

---

## Current State Analysis

### What Works
- ✅ J5A: Complete statistical sampling validation system implemented
- ✅ J5A: 3-segment stratified sampling with blocking gate checkpoints
- ✅ J5A: Quality thresholds prevent resource waste

### What's Missing
- ❌ **Squirt:** No statistical validation of voice processing accuracy
- ❌ **Squirt:** Batch processing starts without quality assessment
- ❌ **Sherlock:** No early-stage evidence quality validation
- ❌ **Sherlock:** Long-form audio starts without viability check

### Gap Impact
- **Squirt Risk:** Process 100 voice memos before discovering systematic quality issues
- **Sherlock Risk:** Commit 17 hours to audiobook before realizing format incompatibility
- **Resource Waste:** Full resource allocation without quality viability assessment

---

## Implementation Phases

### Phase 1: Squirt Voice Processing Statistical Validation (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** None
**Estimated Tokens:** 15,000
**Estimated Duration:** 45 minutes

**Tasks:**
1. Create SquirtVoiceQualityValidator module
2. Implement 3-sample voice memo validation (beginning, middle, end of queue)
3. Add quality thresholds: transcription accuracy, content extraction, format success
4. Integrate with voice queue manager as pre-processing gate
5. Document statistical sampling in Squirt AI Operator Manual

**Expected Outputs:**
- `/home/johnny5/Squirt/src/voice_quality_validator.py`
- `/home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md` (statistical validation section)
- Test results demonstrating early quality detection

**Success Criteria:**
- 3-sample validation completes in <5 minutes
- Detects systematic quality issues before batch processing
- Provides actionable feedback on quality concerns
- Integrates with existing voice queue workflow

**Sampling Strategy for Squirt:**
```python
# Voice Queue Statistical Sampling
queue_size = len(voice_memos)
samples = {
    "beginning": voice_memos[0:2],        # First 2 memos
    "middle": voice_memos[queue_size//2:queue_size//2+2],  # Middle 2 memos
    "end": voice_memos[-2:],              # Last 2 memos
}

# Quality Assessment
for category, memos in samples.items():
    for memo in memos:
        result = process_voice_memo(memo)
        quality_metrics[category].append({
            "transcription_accuracy": estimate_accuracy(result),
            "content_extraction_success": check_extracted_fields(result),
            "format_valid": validate_audio_format(memo),
        })

# Viability Decision
if avg_transcription_accuracy < 0.70:
    raise QualityGateFailure("Voice quality insufficient for batch processing")
if content_extraction_success_rate < 0.60:
    raise QualityGateFailure("Content extraction patterns not viable")
```

---

### Phase 2: Sherlock Evidence Quality Statistical Validation (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 1 complete (for pattern consistency)
**Estimated Tokens:** 18,000
**Estimated Duration:** 1 hour

**Tasks:**
1. Create SherlockEvidenceQualityValidator module
2. Implement 3-segment audio chunk validation for long-form content
3. Add quality thresholds: audio format, transcription viability, entity extraction
4. Integrate with voice engine as pre-transcription gate
5. Document statistical sampling in Sherlock AI Operator Manual

**Expected Outputs:**
- `/home/johnny5/Sherlock/evidence_quality_validator.py`
- `/home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md` (statistical validation section)
- Operation Gladio scenario validation results

**Success Criteria:**
- 3-chunk validation completes in <10 minutes (30 seconds per chunk)
- Detects format incompatibility before full transcription
- Predicts transcription viability with 85%+ accuracy
- Prevents Operation Gladio scenario (17 hours wasted on bad input)

**Sampling Strategy for Sherlock:**
```python
# Long-Form Audio Statistical Sampling
audio_duration = get_audio_duration(audio_file)
chunk_duration = 600  # 10 minutes per chunk

sample_chunks = {
    "beginning": extract_chunk(audio_file, start=0, duration=chunk_duration),
    "middle": extract_chunk(audio_file, start=audio_duration//2, duration=chunk_duration),
    "end": extract_chunk(audio_file, start=audio_duration-chunk_duration, duration=chunk_duration),
}

# Quality Assessment
for position, chunk in sample_chunks.items():
    result = transcribe_chunk(chunk)
    quality_metrics[position].append({
        "audio_format_valid": validate_audio_format(chunk),
        "transcription_success": result.success,
        "transcription_quality": estimate_wer(result),  # Word Error Rate
        "entity_extraction_viable": extract_entities(result.text) > 0,
    })

# Viability Decision
if format_success_rate < 0.80:
    raise QualityGateFailure("Audio format issues detected - abort before full processing")
if transcription_success_rate < 0.60:
    raise QualityGateFailure("Transcription viability insufficient")
if avg_transcription_quality < 0.50:
    raise QualityGateFailure("Expected transcription quality below acceptable threshold")
```

---

### Phase 3: Documentation and Integration (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 2 complete
**Estimated Tokens:** 5,000
**Estimated Duration:** 15 minutes

**Tasks:**
1. Update Squirt CLAUDE.md with statistical sampling auto-injection
2. Update Sherlock CLAUDE.md with statistical sampling auto-injection
3. Cross-reference J5A statistical validation methodology
4. Document quality threshold standards across systems

**Expected Outputs:**
- `/home/johnny5/Squirt/CLAUDE.md` (statistical sampling section)
- `/home/johnny5/Sherlock/CLAUDE.md` (statistical sampling section)
- Cross-references to J5A validation methodology

**Success Criteria:**
- Statistical sampling documented in all three systems
- Quality thresholds consistent across systems
- Cross-references enable pattern reuse
- When-to-apply rules clearly documented

---

### Phase 4: Validation and Testing (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 3 complete
**Estimated Tokens:** 2,000
**Estimated Duration:** 10 minutes

**Tasks:**
1. Test Squirt voice queue with known-bad audio samples
2. Verify early detection prevents full batch processing
3. Test Sherlock with incompatible audio format
4. Verify early detection prevents 17-hour waste scenario
5. Document validation results and quality gate effectiveness

**Expected Outputs:**
- Test results confirming early quality detection
- Resource savings measurements
- False positive/negative rates

**Success Criteria:**
- Quality gates correctly block bad inputs
- No false positives (good inputs blocked)
- Early detection saves >90% of potential wasted resources
- Quality predictions accurate within 15%

---

## Dependencies

**External:**
- None (uses existing voice processing infrastructure)

**Blocking Conditions:**
- None (additive validation, doesn't modify core processing)

**Hardware Requirements:**
- Additional 5-10 minutes processing time for validation samples
- Minimal RAM overhead (<100MB for sample processing)

---

## Quality Thresholds by System

### Squirt Voice Processing
- **Format Validation:** 90%+ samples must have valid audio format
- **Transcription Success:** 70%+ samples must transcribe successfully
- **Content Extraction:** 60%+ samples must extract required business fields
- **Overall Quality:** Average transcription confidence ≥0.70

**Rationale:** Higher thresholds for business-critical document generation

### Sherlock Evidence Analysis
- **Format Validation:** 80%+ samples must have valid audio format
- **Transcription Success:** 60%+ samples must transcribe successfully
- **Entity Extraction:** 30%+ samples must extract meaningful entities
- **Overall Quality:** Average quality score ≥0.50

**Rationale:** More tolerant for research/analysis use cases, prioritize viability over perfection

### J5A Overnight Tasks (Reference)
- **Format Validation:** 80%+ format success required
- **Processing Success:** 60%+ processing success required
- **Output Generation:** 80%+ output generation success required
- **Overall Quality:** Average quality score ≥50%

---

## Rollback Plan

**If statistical validation causes issues:**
1. Disable validation gates in Squirt voice queue manager
2. Disable validation gates in Sherlock voice engine
3. Remove validator modules
4. Restore original processing logic
5. Document rollback reason and performance data

**Recovery Strategy:**
- Validation is optional gate (can be disabled)
- No changes to core processing logic
- Rollback removes validation overhead but preserves functionality

---

## Test Oracle

**Validation Criteria:**

1. **Squirt Voice Queue Quality Gate Test:**
   ```bash
   # Create test queue with 3 good + 7 bad audio files
   python3 /home/johnny5/Squirt/src/voice_queue_manager.py --queue test_mixed_quality
   # Expected: Quality gate detects issues, blocks full processing
   # Verify: Only 3 samples processed, not all 10
   ```

2. **Sherlock Long-Form Audio Quality Gate Test:**
   ```bash
   # Test with incompatible audio format (simulated Operation Gladio scenario)
   python3 /home/johnny5/Sherlock/voice_engine.py --process bad_format_audiobook.aaxc
   # Expected: Quality gate detects format issues in <10 minutes
   # Verify: Aborts before 17-hour full processing
   ```

3. **Resource Savings Measurement:**
   ```bash
   # Compare resource usage: with vs without quality gates
   # Expected: >90% resource savings when bad inputs detected early
   ```

**Quality Metrics:**
- Early detection accuracy: 85%+
- False positive rate: <5%
- Resource savings: >90% for bad inputs
- Validation overhead: <5% for good inputs

---

## Notes

- **Medium Priority:** Important for efficiency but not blocking production
- **Low Risk:** Additive validation, doesn't modify core processing
- **High Value:** Prevents resource waste from processing bad inputs
- **Quick Wins:** Detects systematic issues early (minutes vs hours)

**Real-World Impact:**
- **Squirt:** Detect voice quality issues in first 3 memos, not after processing 100
- **Sherlock:** Detect format incompatibility in 10 minutes, not after 17 hours
- **J5A:** Already has this capability, extending to subordinate systems

---

**Plan Status:** Ready for J5A overnight execution
**Created:** 2025-09-30
**Version:** 1.0
