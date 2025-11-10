# Phoenix Coordination & Fix Plan
## Critical Findings and Implementation Strategy

**Date:** 2025-10-23
**System:** Phoenix Autonomous Testing Agent
**Mission:** Debug Night Shift to achieve 5 consecutive successful runs
**Status:** ACTIVE - Implementing coordination fixes

---

## EXECUTIVE SUMMARY

Strategic assessment revealed critical architectural issues in Phoenix's current implementation:

1. **✅ GOOD NEWS:** Wrapper script bugs FIXED (transcription phase working)
2. **❌ CRITICAL BUG:** Phoenix/Night Shift coordination conflict (both trigger processing)
3. **❌ MISSING:** Diarization and merge stage validation
4. **❌ LIMITED:** Novel failure detection capabilities

**This document captures the fix plan and coordination protocol to resolve these issues.**

---

## PART 1: CRITICAL FINDINGS FROM STRATEGIC ASSESSMENT

### Finding #1: Phoenix/Night Shift Overlap Creates Conflicts

**Problem:**
```
19:00: systemd timer triggers Night Shift (autonomous)
19:00: Phoenix ALSO monitors Night Shift
19:05: Night Shift starts processing
19:05: Phoenix tries to "test" Night Shift by STARTING ANOTHER INSTANCE
       ↓
    CONFLICT: Two Night Shift processes competing for resources
```

**Root Cause:** Phoenix was designed to TEST Night Shift by RUNNING it, but Night Shift is ALSO running on its own schedule. These dual triggers create race conditions and resource conflicts.

**Impact:**
- Production runs interfered with
- Test runs contaminated by production
- Unclear which process owns which episode
- Resource contention when both run simultaneously

### Finding #2: Incomplete Stage Validation

**Current Phoenix Validation:**
- ✅ Download stage
- ✅ Chunk stage
- ✅ Transcribe stage
- ❌ Diarize stage (NOT CHECKED)
- ❌ Merge stage (NOT CHECKED)
- ❌ Correct stage (NOT CHECKED)
- ❌ Evidence ingest stage (NOT CHECKED)

**Evidence:** Episode 26eede804a89d769
- ✅ Chunking: WORKED (13 chunks)
- ✅ Transcription: WORKED (100KB transcript)
- ❌ Diarization: FAILED (no diarization file)
- ❌ Merge: NEVER REACHED
- **Phoenix would have marked this as "SUCCESS" because transcription completed!**

### Finding #3: Limited Novel Failure Detection

**Current Phoenix Capabilities:**
- Pattern matching against known failures
- If pattern not in database → ask human

**Missing Capabilities:**
- Timing anomaly detection (process taking too long)
- Resource anomaly detection (CPU/memory patterns wrong)
- Output quality anomalies (file sizes suspicious)
- Cascade failure detection (early stage issues causing downstream problems)
- Silent failure detection (process completes but produces garbage)

### Finding #4: Successful Manual Processing Architecture Exists

**Evidence from EP3 Pipeline (`ep3_intelligence_pipeline.py`):**
```
PROVEN WORKING ORDER:
1. Audio segmentation (chunking)
2. Diarization (speaker identification)
3. Transcription (speech-to-text)
4. Merge (combine speaker labels + transcript)
5. Correction (content-logic fixes)
6. Evidence ingestion

KEY INSIGHT: Diarization BEFORE transcription!
```

**Current Night Shift attempts diarization AFTER transcription on FULL audio → OOM failure**

---

## PART 2: COORDINATION PROTOCOL (Phoenix ↔ Night Shift)

### Principle: CLEAR SEPARATION OF CONCERNS

```
NIGHT SHIFT DOMAIN:
- Scheduled production processing (nightly 19:00)
- Real episode queue management
- Lightweight decision-making (Ollama/Qwen)
- 7-stage pipeline execution
- PRODUCTION MODE ONLY

PHOENIX DOMAIN:
- Isolated test runs (NOT production episodes)
- Failure pattern analysis
- Complex debugging decisions (Claude/Beyond RAG)
- Fix strategy development
- TEST MODE ONLY

NO OVERLAP ALLOWED
```

### Two Operating Modes

#### Mode 1: PASSIVE MONITORING (During Production Hours)

**When:** Night Shift has scheduled run imminent or active
**Phoenix Behavior:**
```python
def passive_monitoring_mode():
    """
    Phoenix observes production runs WITHOUT triggering them
    """

    # 1. Check if production run imminent (<30 min) or active
    if self._is_production_run_imminent() or self._is_production_run_active():
        logger.info("🔍 PASSIVE MODE: Observing production run")

        # 2. Monitor logs in real-time (read-only)
        self._tail_night_shift_logs()

        # 3. Detect failures passively
        failure = self._detect_failure_from_logs()

        # 4. If failure detected, record for later analysis
        if failure:
            self._record_failure_for_analysis(failure)

        # 5. DO NOT TRIGGER NEW RUNS
        # 6. DO NOT EDIT FILES DURING PRODUCTION

        return "OBSERVATION_COMPLETE"
```

**Key Point:** Phoenix becomes a WATCHER, not an ACTOR during production.

#### Mode 2: ACTIVE TEST MODE (During Off-Hours)

**When:** No production runs scheduled/active, Phoenix can safely test
**Phoenix Behavior:**
```python
def active_test_mode():
    """
    Phoenix actively tests Night Shift with isolated runs
    """

    # 1. Acquire exclusive test lock
    if not self._acquire_test_lock():
        return "BLOCKED: Another test in progress"

    # 2. Apply pending fixes from previous cycle
    self._apply_pending_fixes()

    # 3. Select test episode (NOT from production queue)
    test_episode = self._select_test_episode()
    # Options: replay failed episode, use dedicated test episode, etc.

    # 4. Trigger ISOLATED test run
    #    - Use systemd-run (not systemctl start)
    #    - Set PHOENIX_TEST_MODE=true environment variable
    #    - Run single episode, not full queue
    result = subprocess.run([
        'systemd-run',
        '--unit=phoenix-test-run',
        '--setenv=PHOENIX_TEST_MODE=true',
        '--setenv=TEST_EPISODE_ID=' + test_episode,
        '--',
        'python3',
        '/home/johnny5/Sherlock/nightshift_podcast_processor.py',
        '--test-mode',
        '--episode', test_episode
    ])

    # 5. ACTIVELY monitor execution
    monitor_result = self._active_monitor_test_run(
        expected_stages=['download', 'chunk', 'diarize', 'transcribe', 'merge', 'correct', 'ingest'],
        timeout_per_stage={'download': 120, 'chunk': 180, 'diarize': 600, ...}
    )

    # 6. Analyze results and decide next action
    if monitor_result.success:
        self._record_success()
        self._release_test_lock()
        return "SUCCESS"
    else:
        fix_strategy = self._reason_about_failure(monitor_result)
        self._apply_auto_fix(fix_strategy)
        self._release_test_lock()
        return "RETRY_WITH_FIX"
```

### Lock Mechanism

```python
class PhoenixTestLock:
    """
    Prevents conflicts between Phoenix test runs and production
    """

    LOCK_FILE = "/tmp/phoenix_test_mode.lock"

    def acquire_test_lock(self) -> bool:
        """
        Acquire exclusive lock for testing
        """

        # Check if production run imminent
        if self._is_production_run_imminent(minutes=30):
            logger.warning("❌ Cannot acquire lock: Production run in <30 min")
            return False

        # Check if production currently active
        if self._is_night_shift_active():
            logger.warning("❌ Cannot acquire lock: Night Shift currently running")
            return False

        # Check if another Phoenix test active
        if os.path.exists(self.LOCK_FILE):
            with open(self.LOCK_FILE, 'r') as f:
                lock_data = json.load(f)

            # Check if lock is stale (>2 hours old)
            lock_age = (datetime.now() - datetime.fromisoformat(lock_data['acquired_at'])).total_seconds()
            if lock_age < 7200:  # 2 hours
                logger.warning(f"❌ Cannot acquire lock: Test in progress (PID {lock_data['pid']})")
                return False
            else:
                logger.info("🔓 Removing stale lock")
                os.remove(self.LOCK_FILE)

        # Acquire lock
        lock_data = {
            'pid': os.getpid(),
            'acquired_at': datetime.now().isoformat(),
            'purpose': 'phoenix_test_mode'
        }

        with open(self.LOCK_FILE, 'w') as f:
            json.dump(lock_data, f)

        logger.info("🔒 Test lock acquired")
        return True

    def release_test_lock(self):
        """Release lock after test completes"""
        if os.path.exists(self.LOCK_FILE):
            os.remove(self.LOCK_FILE)
            logger.info("🔓 Test lock released")
```

---

## PART 3: NOVEL FAILURE DETECTION METHODS

### Method 1: Timing Anomaly Detection

```python
class TimingAnomalyDetector:
    """
    Detect when stages take abnormally long
    Uses statistical process control (SPC)
    """

    def __init__(self):
        self.historical_times = self._load_historical_times()

    def detect_anomaly(self, stage: str, elapsed_time: float) -> Optional[Anomaly]:
        """
        Detect if elapsed time is outside normal range
        """

        stage_times = self.historical_times.get(stage, [])

        if len(stage_times) < 10:
            # Not enough history - can't detect anomalies yet
            return None

        mean = statistics.mean(stage_times)
        stdev = statistics.stdev(stage_times)

        # 3-sigma rule: 99.7% of values within 3 standard deviations
        lower_bound = max(0, mean - (3 * stdev))
        upper_bound = mean + (3 * stdev)

        if elapsed_time > upper_bound:
            return Anomaly(
                type='TIMING_SLOW',
                stage=stage,
                observed=elapsed_time,
                expected_range=(lower_bound, upper_bound),
                severity='HIGH' if elapsed_time > upper_bound * 1.5 else 'MEDIUM',
                message=f"{stage} taking {elapsed_time:.1f}s (expected {mean:.1f}±{stdev:.1f}s)"
            )

        if elapsed_time < lower_bound:
            # Suspiciously FAST - might indicate skipped work
            return Anomaly(
                type='TIMING_FAST',
                stage=stage,
                observed=elapsed_time,
                expected_range=(lower_bound, upper_bound),
                severity='MEDIUM',
                message=f"{stage} completed in {elapsed_time:.1f}s (expected {mean:.1f}±{stdev:.1f}s) - suspiciously fast!"
            )

        return None
```

### Method 2: Resource Usage Anomaly Detection

```python
class ResourceAnomalyDetector:
    """
    Detect abnormal CPU/memory patterns during processing
    """

    def detect_resource_anomaly(self, stage: str, cpu_percent: float, mem_percent: float) -> Optional[Anomaly]:
        """
        Each stage has expected resource usage patterns
        """

        expected_patterns = {
            'download': {'cpu': (5, 30), 'mem': (10, 30)},      # Network I/O
            'chunk': {'cpu': (20, 60), 'mem': (10, 30)},        # CPU-bound
            'diarize': {'cpu': (80, 100), 'mem': (30, 60)},     # CPU + memory intensive
            'transcribe': {'cpu': (80, 100), 'mem': (40, 70)},  # Very intensive
            'merge': {'cpu': (5, 20), 'mem': (5, 20)},          # Light processing
            'correct': {'cpu': (10, 40), 'mem': (10, 30)},      # Moderate
            'ingest': {'cpu': (5, 20), 'mem': (5, 20)}          # Database I/O
        }

        expected = expected_patterns.get(stage)
        if not expected:
            return None

        cpu_min, cpu_max = expected['cpu']
        mem_min, mem_max = expected['mem']

        # Check if outside expected ranges
        if cpu_percent < cpu_min * 0.5:
            return Anomaly(
                type='CPU_UNDERUTILIZATION',
                stage=stage,
                observed={'cpu': cpu_percent, 'mem': mem_percent},
                expected={'cpu': expected['cpu'], 'mem': expected['mem']},
                severity='MEDIUM',
                message=f"{stage} using only {cpu_percent:.1f}% CPU (expected {cpu_min}-{cpu_max}%) - may be stalled"
            )

        if mem_percent > mem_max * 1.2:
            return Anomaly(
                type='MEMORY_LEAK',
                stage=stage,
                observed={'cpu': cpu_percent, 'mem': mem_percent},
                expected={'cpu': expected['cpu'], 'mem': expected['mem']},
                severity='HIGH',
                message=f"{stage} using {mem_percent:.1f}% memory (expected {mem_min}-{mem_max}%) - possible memory leak"
            )

        return None
```

### Method 3: Output Quality Anomaly Detection

```python
class OutputAnomalyDetector:
    """
    Detect when output files are suspicious
    """

    def detect_output_anomaly(self, stage: str, output_path: str) -> Optional[Anomaly]:
        """
        Validate output files match expected characteristics
        """

        # Check 1: File exists
        if not os.path.exists(output_path):
            return Anomaly(
                type='MISSING_OUTPUT',
                stage=stage,
                observed=None,
                expected=output_path,
                severity='CRITICAL',
                message=f"{stage} did not produce expected output: {output_path}"
            )

        # Check 2: File size reasonable
        file_size = os.path.getsize(output_path)

        # Get historical file sizes for this stage
        historical_sizes = self.db.get_output_sizes(stage, last_n=50)

        if historical_sizes:
            mean_size = statistics.mean(historical_sizes)
            stdev_size = statistics.stdev(historical_sizes)

            min_expected = max(0, mean_size - (3 * stdev_size))
            max_expected = mean_size + (3 * stdev_size)

            if file_size < min_expected or file_size > max_expected:
                return Anomaly(
                    type='FILE_SIZE_ANOMALY',
                    stage=stage,
                    observed=file_size,
                    expected=(min_expected, max_expected),
                    severity='HIGH',
                    message=f"{output_path} is {file_size} bytes (expected {mean_size:.0f}±{stdev_size:.0f})"
                )

        # Check 3: Content validation (for text files)
        if output_path.endswith('.txt'):
            return self._validate_text_content(output_path, stage)

        # Check 4: JSON validity (for JSON files)
        if output_path.endswith('.json'):
            return self._validate_json_content(output_path, stage)

        return None

    def _validate_text_content(self, file_path: str, stage: str) -> Optional[Anomaly]:
        """
        Check if text file has reasonable content
        """

        with open(file_path, 'r') as f:
            content = f.read()

        # Heuristic checks
        words = content.split()
        chars = len(content)

        if len(words) == 0:
            return Anomaly(
                type='EMPTY_OUTPUT',
                stage=stage,
                observed=0,
                expected='>0 words',
                severity='CRITICAL',
                message=f"{file_path} is empty!"
            )

        # Check character-to-word ratio (typical English: 4-6 chars/word)
        ratio = chars / len(words) if len(words) > 0 else 0

        if ratio < 3 or ratio > 20:
            return Anomaly(
                type='SUSPICIOUS_CONTENT',
                stage=stage,
                observed=ratio,
                expected=(4, 6),
                severity='MEDIUM',
                message=f"{file_path} has unusual char/word ratio: {ratio:.1f} (expected 4-6)"
            )

        return None

    def _validate_json_content(self, file_path: str, stage: str) -> Optional[Anomaly]:
        """
        Check if JSON file is valid and has expected structure
        """

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return Anomaly(
                type='INVALID_JSON',
                stage=stage,
                observed=str(e),
                expected='Valid JSON',
                severity='CRITICAL',
                message=f"{file_path} is not valid JSON: {e}"
            )

        # Stage-specific structure checks
        if stage == 'diarize' and 'segments' not in data:
            return Anomaly(
                type='MISSING_JSON_FIELD',
                stage=stage,
                observed=list(data.keys()),
                expected=['segments'],
                severity='HIGH',
                message=f"Diarization JSON missing 'segments' field"
            )

        return None
```

### Method 4: Cascade Failure Detection

```python
class CascadeFailureDetector:
    """
    Detect when early-stage issues cause downstream problems
    """

    def detect_cascade(self, stage_results: List[StageResult]) -> Optional[CascadeFailure]:
        """
        Analyze stage results for causal chains
        """

        for i, stage in enumerate(stage_results):
            # Check if stage "succeeded" but with suspicious quality
            if stage.status == 'success' and stage.quality_score < 0.5:

                # Look at downstream stages
                downstream_stages = stage_results[i+1:]

                for downstream in downstream_stages:
                    if downstream.status == 'failed':
                        # Likely cascade: early low-quality output caused downstream failure
                        return CascadeFailure(
                            root_stage=stage.name,
                            root_issue=f"Low quality output (score={stage.quality_score:.2f})",
                            affected_stage=downstream.name,
                            evidence={
                                'root_output_size': stage.output_size,
                                'downstream_error': downstream.error_message
                            },
                            message=f"{stage.name} produced low-quality output, causing {downstream.name} to fail"
                        )

        return None
```

---

## PART 4: FULL PIPELINE STAGE VALIDATION

### Current Gap: Stages 4-7 Not Validated

**Need to add validation for:**

```python
class FullPipelineValidator:
    """
    Validate ALL 7 stages of Night Shift pipeline
    """

    def validate_episode_processing(self, episode_id: str) -> ValidationResult:
        """
        Comprehensive validation across all stages
        """

        processing_dir = f"/home/johnny5/Sherlock/nightshift_processing/{episode_id}"

        stage_results = []

        # Stage 1: Download
        stage_results.append(self._validate_download(processing_dir))

        # Stage 2: Chunk
        stage_results.append(self._validate_chunking(processing_dir))

        # Stage 3: Diarization [NEW - WAS MISSING]
        stage_results.append(self._validate_diarization(processing_dir))

        # Stage 4: Transcription
        stage_results.append(self._validate_transcription(processing_dir))

        # Stage 5: Merge [NEW - WAS MISSING]
        stage_results.append(self._validate_merge(processing_dir))

        # Stage 6: Correction [NEW - WAS MISSING]
        stage_results.append(self._validate_correction(processing_dir))

        # Stage 7: Evidence Ingest [NEW - WAS MISSING]
        stage_results.append(self._validate_evidence_ingest(episode_id))

        # Cascade failure detection
        cascade = self.cascade_detector.detect_cascade(stage_results)

        all_passed = all(s.status == 'success' for s in stage_results)

        return ValidationResult(
            episode_id=episode_id,
            all_stages_passed=all_passed,
            stage_results=stage_results,
            cascade_failure=cascade,
            overall_quality_score=self._calculate_quality_score(stage_results)
        )

    def _validate_diarization(self, processing_dir: str) -> StageResult:
        """
        Validate diarization stage produced valid output
        """

        diarization_file = f"{processing_dir}/diarization.json"

        # Check 1: File exists
        if not os.path.exists(diarization_file):
            return StageResult(
                stage='diarization',
                status='failed',
                error_message='Diarization file not found',
                quality_score=0.0
            )

        # Check 2: Valid JSON
        try:
            with open(diarization_file, 'r') as f:
                diarization = json.load(f)
        except json.JSONDecodeError as e:
            return StageResult(
                stage='diarization',
                status='failed',
                error_message=f'Invalid JSON: {e}',
                quality_score=0.0
            )

        # Check 3: Has segments
        if 'segments' not in diarization or len(diarization['segments']) == 0:
            return StageResult(
                stage='diarization',
                status='failed',
                error_message='No speaker segments found',
                quality_score=0.0
            )

        # Check 4: Speaker IDs present
        speakers = set(seg.get('speaker') for seg in diarization['segments'])
        if None in speakers or len(speakers) == 0:
            return StageResult(
                stage='diarization',
                status='failed',
                error_message='Speaker IDs missing or invalid',
                quality_score=0.5
            )

        # Success with quality score
        quality_score = min(1.0, len(speakers) / 3.0)  # Expect 2-3 speakers typically

        return StageResult(
            stage='diarization',
            status='success',
            quality_score=quality_score,
            metadata={
                'num_segments': len(diarization['segments']),
                'num_speakers': len(speakers),
                'speakers': list(speakers)
            }
        )

    def _validate_merge(self, processing_dir: str) -> StageResult:
        """
        Validate merge stage combined transcript + speaker labels
        """

        merged_file = f"{processing_dir}/attributed_transcript.txt"

        if not os.path.exists(merged_file):
            return StageResult(
                stage='merge',
                status='failed',
                error_message='Merged transcript not found',
                quality_score=0.0
            )

        with open(merged_file, 'r') as f:
            content = f.read()

        # Check for speaker labels in format "Speaker X:" or "[Speaker X]"
        import re
        speaker_labels = re.findall(r'(Speaker \w+:|\\[Speaker \w+\\])', content)

        if len(speaker_labels) == 0:
            return StageResult(
                stage='merge',
                status='failed',
                error_message='No speaker labels found in merged transcript',
                quality_score=0.0
            )

        return StageResult(
            stage='merge',
            status='success',
            quality_score=1.0,
            metadata={
                'file_size': os.path.getsize(merged_file),
                'speaker_labels_count': len(speaker_labels)
            }
        )
```

---

## PART 5: IMPLEMENTATION PRIORITY

### Immediate (This Session)

1. **✅ Create Documentation** (DONE)
   - Kaizen architecture
   - Phoenix coordination plan

2. **🔄 Implement Coordination Protocol** (NEXT)
   - Test mode lock mechanism
   - Production run detection
   - Passive vs active monitoring modes

3. **🔄 Extend Stage Validation**
   - Add diarization validation
   - Add merge validation
   - Add cascade failure detection

4. **🔄 Basic Novel Failure Detection**
   - Timing anomaly detector
   - Output existence checks

### Near-Term (Next Session)

5. **Advanced Novel Failure Detection**
   - Resource usage patterns
   - Output quality analysis
   - Log pattern analysis

6. **Night Shift Test Mode Awareness**
   - Check PHOENIX_TEST_MODE env var
   - Enhanced logging under test

7. **End-to-End Testing**
   - Full Phoenix test cycle
   - Validation with real episode

---

## PART 6: SUCCESS CRITERIA

**Phoenix coordination is successful when:**

1. ✅ **No Production Conflicts**
   - Phoenix never triggers during scheduled Night Shift runs
   - Production runs complete uninterrupted
   - Test runs isolated from production queue

2. ✅ **Full Pipeline Validation**
   - All 7 stages validated (not just first 3)
   - Episode 26eede804a89d769 would be correctly marked as FAILED
   - Diarization failures detected and reported

3. ✅ **Novel Failure Detection**
   - At least 3 types of anomalies detected automatically
   - Timing, output, and cascade failures caught

4. ✅ **Proper Handoff to Auto-Fix**
   - Failures correctly analyzed
   - Fix strategies proposed
   - Iteration loop functional

---

## CONCLUSION

These fixes address the critical architectural gaps discovered in the strategic assessment. Once implemented, Phoenix will:

- ✅ Coordinate properly with Night Shift (no conflicts)
- ✅ Validate ALL pipeline stages (not just first 3)
- ✅ Detect novel failures through multiple methods
- ✅ Provide accurate success/failure reporting
- ✅ Enable proper handoff to Kaizen when debugging complete

**Next Step:** Implement coordination protocol and extended stage validation.

---

**Document Status:** ✅ ANALYSIS COMPLETE
**Implementation Status:** Ready to execute
**Priority:** CRITICAL - Fixes core Phoenix functionality

**Document Owner:** Claude (Phoenix Architect)
**Review Date:** 2025-10-23
