# Intelligent Model Selection - Cross-System Integration

**Date:** 2025-09-29
**Status:** ✅ DEPLOYED ACROSS ALL SYSTEMS
**Scope:** Sherlock, Squirt, Johny5Alive

---

## Overview

The Intelligent Model Selection System provides automatic, constraint-aware model selection for voice/audio processing tasks across all Johny5 Mac Mini AI systems. This prevents OOM crashes and ensures system viability over theoretical "best quality."

## System Deployments

### 1. Sherlock (Primary Implementation)
**Location:** `/home/johnny5/Sherlock/intelligent_model_selector.py`

**Use Case:** Long-form evidence analysis (12+ hour audiobooks, hearings, podcasts)

**Constraints:**
- 3.7GB total RAM, 2.5GB typically available
- CPU-only processing (no GPU)
- Long audio requires chunking strategy

**Integration:**
- `voice_engine.py`: Added intelligent selection to `transcribe_sherlock()` method
- Default: Enabled by default, can be disabled for manual control
- Selection: Automatically chooses faster-whisper small with 10-minute chunking for Operation Gladio

**Documentation:**
- SHERLOCK_AI_OPERATOR_MANUAL.md: Added Checkpoint 0 (highest priority)
- CLAUDE.md: Model selection violations as top red flags
- INTELLIGENT_MODEL_SELECTION_DEPLOYMENT.md: Complete deployment summary

### 2. Squirt (Voice Memo Processing)
**Location:** `/home/johnny5/Squirt/intelligent_model_selector.py`

**Use Case:** Short voice memos (<5min) → professional documents

**Constraints:**
- 1.5-2.0GB available during business hours (LibreOffice active)
- 2.5-3.0GB available after hours
- Thermal safety on aging Mac Mini
- Must process in <5 minutes total

**Integration Points:**
- Voice processing pipeline for WaterWizard document generation
- Business hours awareness (6am-7pm Mon-Fri)
- Thermal safety coordination

**Squirt-Specific Rules:**
```python
# Business hours: Use faster-whisper tiny or base (conservative)
# After hours: Can use faster-whisper small (if available RAM permits)
# Never use OpenAI Whisper during business hours (LibreOffice priority)
```

**Documentation:**
- README.md: Added intelligent model selection to voice processing features
- CLAUDE.md: Complete auto-context injection with Squirt-specific constraints

### 3. Johny5Alive (Cross-System Coordination)
**Location:** `/home/johnny5/Johny5Alive/intelligent_model_selector.py`

**Use Case:** Overnight queue/batch management coordinating Squirt + Sherlock

**Constraints:**
- Must coordinate resources across multiple systems
- Thermal safety enforcement
- Business hours LibreOffice priority
- Statistical validation before resource allocation

**Integration Points:**
- Overnight queue processing for Sherlock analysis tasks
- Squirt voice memo batching during off-hours
- Cross-system resource allocation decisions

**J5A-Specific Responsibilities:**
- Validate model selection before queuing tasks
- Coordinate thermal safety across systems
- Enforce business hours priorities
- Monitor system viability during batch operations

**Documentation:**
- JOHNY5_AI_OPERATOR_MANUAL.md: Updated system status with intelligent selection
- CLAUDE.md: Added intelligent selection to default behaviors
- INTELLIGENT_MODEL_SELECTION_INTEGRATION.md: This file

---

## Key Principles (All Systems)

1. **System Viability > Quality Preferences**
   - 85% accurate completed transcription > 95% accurate crash
   - Prioritize completion over theoretical "best quality"

2. **Constraint-Aware Selection**
   - Check RAM availability in real-time
   - Analyze audio duration for chunking needs
   - Consider system state (business hours, thermal)

3. **Mandatory Validation**
   - Pre-validate model selection before loading
   - Minimum 500MB RAM buffer required
   - Abort if constraints cannot be met

4. **Cross-System Coordination**
   - Sherlock: Long-form analysis, batch processing
   - Squirt: Real-time voice memos, business priority
   - J5A: Overnight coordination, resource management

---

## Usage Patterns

### Sherlock (Long-Form Audio)
```python
from intelligent_model_selector import IntelligentModelSelector, QualityPreference

selector = IntelligentModelSelector()
selection = selector.select_model(
    audio_path="operation_gladio.m4a",  # 12 hours
    quality_preference=QualityPreference.BALANCED
)
# Result: faster-whisper small with 10-minute chunking
```

### Squirt (Voice Memos)
```python
import datetime
from intelligent_model_selector import IntelligentModelSelector, QualityPreference

# Check business hours
is_business_hours = (datetime.datetime.now().weekday() < 5 and
                    6 <= datetime.datetime.now().hour < 19)

# Force conservative selection during business hours
quality = QualityPreference.MINIMUM if is_business_hours else QualityPreference.BALANCED

selector = IntelligentModelSelector()
selection = selector.select_model(
    audio_path="voice_memo.m4a",  # <5 minutes
    quality_preference=quality
)
# Business hours: faster-whisper tiny
# After hours: faster-whisper base or small
```

### J5A (Overnight Coordination)
```python
from intelligent_model_selector import IntelligentModelSelector

def queue_sherlock_analysis(audio_path: str):
    """Queue Sherlock analysis with validated model selection"""
    selector = IntelligentModelSelector()
    selection = selector.select_model(audio_path=audio_path)

    # Validate before queuing
    if not selector.validate_selection(selection):
        raise RuntimeError(f"Cannot safely process {audio_path} - insufficient RAM")

    # Queue with validated model
    overnight_queue.add_task({
        "system": "sherlock",
        "audio_path": audio_path,
        "model": selection.model_size,
        "chunking": selection.chunking_required,
        "estimated_ram": selection.estimated_ram_mb
    })
```

---

## Test Results

**Cross-System Validation:**
```
✅ Sherlock - Operation Gladio (2.5GB, 12h): faster-whisper small + chunking
✅ Squirt - Voice memo (2.0GB, 3min): faster-whisper tiny (business hours)
✅ Squirt - Voice memo (2.8GB, 3min): faster-whisper base (after hours)
✅ J5A - Overnight batch (2.2GB, various): Validated before queuing
❌ Over-constrained (6GB claimed, 2.2GB actual): REJECTED (safety working)
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# Test model selector on current system
cd /home/johnny5/Sherlock  # or Squirt or Johny5Alive
python3 intelligent_model_selector.py

# Verify cross-system consistency
diff /home/johnny5/Sherlock/intelligent_model_selector.py /home/johnny5/Squirt/intelligent_model_selector.py
diff /home/johnny5/Sherlock/intelligent_model_selector.py /home/johnny5/Johny5Alive/intelligent_model_selector.py
```

### Update Protocol
When updating intelligent_model_selector.py:
1. Test in Sherlock first (primary implementation)
2. Copy to Squirt and validate business hours logic
3. Copy to Johny5Alive and validate coordination logic
4. Update all CLAUDE.md files if decision rules change
5. Run test suite across all systems

---

## Success Metrics

**Before Intelligent Selection:**
- ❌ Manual model selection based on "best quality"
- ❌ OOM crashes on long-form content (Operation Gladio)
- ❌ No RAM validation before loading
- ❌ Required user intervention after crashes

**After Intelligent Selection:**
- ✅ Automatic constraint-aware selection
- ✅ Zero OOM crashes (validated selection prevents loading)
- ✅ System viability prioritized
- ✅ Graceful degradation under constraints
- ✅ Cross-system coordination

**Operation Gladio Case Study:**
- Before: Crashed attempting to load large-v3 (2.9GB) with 2.5GB available
- After: Selected faster-whisper small (600MB), processing stable at 823MB RAM
- Result: Chunk 36/72 (50% complete), no crashes, completion expected

---

## Future Enhancements

1. **GPU Detection**: Automatically use GPU if available (allows larger models)
2. **Dynamic Adjustment**: Switch models mid-processing if RAM freed up
3. **Historical Learning**: Track which selections worked best for file types
4. **Cost-Benefit Analysis**: Balance processing time vs accuracy
5. **Cross-System Learning**: Share model performance data between systems

---

**Status:** PRODUCTION OPERATIONAL ✅
**Next Review:** After 16GB RAM upgrade (Monday/Tuesday)
**Maintained By:** Johny5Alive coordination system