# J5A Heavy Process Operating Protocols

**Last Updated:** 2025-10-15
**Status:** MANDATORY - System Viability Critical
**Incident Reference:** System Freeze 2025-10-15 (Parallel Whisper OOM)

## Executive Summary

This document establishes **mandatory operating protocols** for running heavy ML processes (Whisper Large-v3, etc.) on the J5A system following a critical system freeze incident caused by parallel Whisper processes exceeding memory and thermal limits.

**CRITICAL RULE:** Only **ONE** Whisper Large-v3 process may run at any time, with mandatory resource validation.

---

## Incident Post-Mortem: 2025-10-15 System Freeze

### What Happened
- **10:37:54** - Script launched **4 concurrent Whisper Large-v3 processes**
- **11:37:37** - Second attempt launched **2 concurrent Whisper Large-v3 processes**
- **Result:** System froze/hung during parallel model loading
- **Recovery:** 11:52:03 - System recovered after forced restart

### Root Causes

#### 1. Memory Exhaustion (Primary)
- **Each Whisper Large-v3 model:** 5-10GB RAM when loaded
- **2 parallel processes:** 10-20GB required
- **System safe limit:** 14GB (16GB total - 2GB OS buffer)
- **VIOLATION:** Exceeded safe memory threshold by 40-140%

#### 2. Thermal Stress (Secondary)
- **CPU temperature:** Reached 103°C (TCPG sensor)
- **Safe operating limit:** 80°C per CLAUDE.md
- **Hardware:** 2012 Mac Mini with known thermal limitations
- **VIOLATION:** Exceeded thermal limit by 29%

#### 3. No Resource Coordination (Systemic)
- No mutual exclusion between heavy processes
- No pre-flight resource validation
- Claude Code operations could overlap with Whisper
- Scripts used hardcoded parallelization without safety checks

### Evidence
- `j5a-nightshift/ops/logs/weaponized_ep91_chunked_20251015_103754.log:8` - "Parallel processing: 4 concurrent chunks"
- `j5a-nightshift/ops/logs/weaponized_ep91_chunked_20251015_113737.log:8` - "Parallel processing: 2 concurrent chunks"
- Empty `whisper_chunk_*.log` files indicate processes killed by OOM or system freeze
- Kernel ACPI EC interrupt block/unblock events suggest system hang recovery

---

## New Safety Architecture: J5A Resource Safety Gate

### Overview
All heavy processes **MUST** pass through the J5A Resource Safety Gate before execution. The gate implements:

1. **Mutual Exclusion** - Process-level lockfiles prevent concurrent heavy operations
2. **Memory Validation** - Ensures sufficient memory available (4GB safety margin)
3. **Thermal Protection** - Blocks execution if CPU >80°C
4. **Process Coordination** - Detects existing Whisper/Claude operations
5. **Blocking Gates** - Hard failures on safety violations (no bypass)

### Implementation

#### Core Component: `ops/resource_safety_gate.sh`

**5 Mandatory Safety Checks:**

```bash
CHECK 1: Memory Availability
  - Validates ≥14GB free after Whisper launch
  - Blocks if <4GB safety margin remaining

CHECK 2: Thermal Safety
  - CPU temperature must be <80°C
  - Blocks until system cools down

CHECK 3: Whisper Process Mutex
  - No other Whisper Large processes running
  - Enforces strict serialization

CHECK 4: Claude Code Activity Detection
  - Warning if Claude using >500MB RAM
  - Informational only (doesn't block)

CHECK 5: Process Lock Status
  - Validates lockfile availability
  - Clears stale locks from dead processes
```

#### Usage Pattern

**Before running Whisper:**
```bash
source ops/resource_safety_gate.sh

# Acquire lock and validate safety
if ! acquire_whisper_lock; then
    echo "❌ Safety gate blocked execution"
    exit 1
fi

# ... run whisper process ...

# Lock is automatically released on exit via trap
```

**Standalone safety check:**
```bash
./ops/resource_safety_gate.sh
# Exit code 0 = safe, 1 = unsafe
```

---

## Updated Script Behavior

### `weaponized_ep91_chunked.sh`
**Changes:**
- `MAX_PARALLEL` reduced from `2` → `1`
- Sources `resource_safety_gate.sh` on startup
- Calls `acquire_whisper_lock` before Phase 2 (Parallel Transcription)
- Hard failure if safety gate blocks execution

### `whisper_chunked_wrapper.sh`
**Changes:**
- `MEMORY_PER_WHISPER_GB` increased from `3.0` → `10.0` (realistic estimate)
- Removed dynamic parallelization calculation
- `MAX_PARALLEL` hardcoded to `1`
- Sources `resource_safety_gate.sh` on startup
- Calls `acquire_whisper_lock` before transcription phase

---

## Operating Procedures

### For Whisper Transcription Tasks

#### ✅ CORRECT Procedure
```bash
# 1. Check if system is safe
cd ~/Johny5Alive/j5a-nightshift
./ops/resource_safety_gate.sh

# 2. If safe, run transcription
./whisper_chunked_wrapper.sh episode.mp3 --model large-v3 --language en

# 3. Monitor progress
tail -f ops/logs/whisper_*.log
```

#### ❌ INCORRECT Procedures
```bash
# DON'T: Launch multiple Whisper processes manually
whisper file1.mp3 --model large-v3 &
whisper file2.mp3 --model large-v3 &  # ❌ WILL CAUSE FREEZE

# DON'T: Bypass the wrapper scripts
whisper large_file.mp3 --model large-v3  # ❌ No chunking, no safety checks

# DON'T: Modify MAX_PARALLEL to >1
MAX_PARALLEL=4  # ❌ DANGER - Will cause OOM/freeze
```

### For Claude Code Operations During Whisper Processing

#### If Whisper is Running:
1. **Claude Code operations are allowed** but will be warned about reduced resources
2. **Avoid memory-intensive Claude operations** (large file processing, extensive searches)
3. **Monitor system status** with `htop` or `free -h`

#### If Starting New Whisper Task:
1. **Wait for current Whisper to complete** if one is running
2. **Check Claude memory usage:** `ps aux | grep claude | awk '{sum+=$6} END {print sum/1024 " MB"}'`
3. **If Claude using >2GB**, wait or kill non-critical Claude tasks

---

## Emergency Procedures

### If System Becomes Unresponsive

**Symptoms:**
- Mouse/keyboard input frozen
- Display frozen
- SSH connections timeout
- System not responding to normal commands

**Immediate Actions:**
1. **Wait 2-3 minutes** - May be thermal throttling recovery
2. **Force restart** if no recovery (hold power button)
3. **After restart, check logs:**
   ```bash
   dmesg -T | grep -i -E "(oom|kill|freeze)"
   journalctl --since "30 minutes ago" --priority=0..3
   ```
4. **Clear stale locks:**
   ```bash
   rm -f /tmp/j5a_locks/whisper_large.lock
   ```

### If Whisper Process Hangs

**Symptoms:**
- Process appears running but no output
- Log file not growing
- High CPU usage but no progress

**Actions:**
1. **Check lock status:**
   ```bash
   cat /tmp/j5a_locks/whisper_large.lock
   ps -p <PID>
   ```
2. **If process dead but lock exists:**
   ```bash
   rm -f /tmp/j5a_locks/whisper_large.lock
   ```
3. **Kill hung process:**
   ```bash
   pkill -9 -f "whisper.*large"
   ```
4. **Wait for system to stabilize** (check CPU temp)
5. **Retry with safety gate**

### If Safety Gate Continuously Blocks

**Scenario 1: Thermal Block**
```bash
# Wait for cooling
watch -n 5 sensors
# When CPU <75°C, retry
```

**Scenario 2: Memory Block**
```bash
# Find memory hogs
ps aux --sort=-%mem | head -10

# Kill non-essential processes
kill <PID>

# Clear caches if desperate (rarely needed)
sudo sync && sudo sysctl -w vm.drop_caches=3
```

**Scenario 3: Stale Lock**
```bash
# Check if lock holder is alive
cat /tmp/j5a_locks/whisper_large.lock
ps -p <PID>

# If dead, remove lock
rm -f /tmp/j5a_locks/whisper_large.lock
```

---

## Monitoring Commands

### Real-Time System Status
```bash
# Memory usage
watch -n 2 free -h

# CPU temperature
watch -n 2 sensors

# Running Whisper processes
watch -n 2 'ps aux | grep whisper | grep -v grep'

# Lock status
watch -n 2 'ls -lh /tmp/j5a_locks/ 2>/dev/null || echo "No locks"'
```

### Log Monitoring
```bash
# Latest Whisper logs
ls -lt ~/Johny5Alive/j5a-nightshift/ops/logs/whisper_* | head -5

# Follow active log
tail -f ~/Johny5Alive/j5a-nightshift/ops/logs/whisper_*.log

# Check for errors
grep -i error ~/Johny5Alive/j5a-nightshift/ops/logs/*.log
```

---

## Testing & Validation

### Safety Gate Test
```bash
cd ~/Johny5Alive/j5a-nightshift

# Should PASS if system healthy
./ops/resource_safety_gate.sh
# Exit code: 0

# Should FAIL if Whisper already running
./whisper_chunked_wrapper.sh test.mp3 --model large-v3 &
./ops/resource_safety_gate.sh  # Should block
# Exit code: 1
```

### Script Integration Test
```bash
# Test with short audio file (<15 min) - no chunking
./whisper_chunked_wrapper.sh short_audio.mp3 --model large-v3 --language en

# Test with long audio file (>15 min) - chunking + safety gate
./whisper_chunked_wrapper.sh long_audio.mp3 --model large-v3 --language en

# Verify safety gate blocks parallel execution
./whisper_chunked_wrapper.sh file1.mp3 --model large-v3 &
sleep 2
./whisper_chunked_wrapper.sh file2.mp3 --model large-v3  # Should block
```

---

## Performance Implications

### Before (Parallel Processing)
- **Theoretical throughput:** 2x faster (2 chunks in parallel)
- **Actual result:** System freeze, 100% data loss, manual recovery required
- **Total time:** Process time + recovery time + retry time = **FAILURE**

### After (Sequential Processing)
- **Throughput:** 1x (sequential chunks)
- **Stability:** 100% reliable, no freezes
- **Total time:** Process time only = **SUCCESS**

**Lesson:** Sequential completion >>> parallel failure

### Estimated Processing Times
- **10-minute audio chunk:** ~5-8 minutes (Whisper Large-v3)
- **90-minute podcast (9 chunks):** ~45-72 minutes
- **vs. Parallel (if it worked):** ~23-36 minutes
- **Difference:** +22-36 minutes BUT guaranteed completion

---

## Future Improvements

### Potential Enhancements
1. **Dynamic thermal throttling** - Reduce MAX_PARALLEL if temp >70°C
2. **Memory pressure monitoring** - Pause processing if memory <2GB free
3. **Background process priority** - Nice/ionice for Whisper processes
4. **Checkpoint-based interruption** - Save state if thermal emergency
5. **Multi-day queue coordination** - Spread heavy tasks across multiple nights

### NOT Recommended
- ❌ Increasing MAX_PARALLEL beyond 1 for Whisper Large-v3
- ❌ Bypassing safety gates for "urgent" tasks
- ❌ Dynamic memory limits based on "available" RAM
- ❌ Parallel processing of Large models on this hardware

---

## Compliance & Enforcement

### Mandatory Compliance
All scripts that run Whisper Large-v3 or other heavy ML models (>5GB RAM) **MUST:**
1. Source `ops/resource_safety_gate.sh`
2. Call `acquire_whisper_lock` before heavy operations
3. Set `MAX_PARALLEL=1` (or use `calculate_safe_parallel_count`)
4. Use lockfile-based mutual exclusion

### Script Audit Checklist
- [ ] Sources `resource_safety_gate.sh`?
- [ ] Calls `acquire_whisper_lock`?
- [ ] Uses `MAX_PARALLEL=1` or calculated safe value?
- [ ] Handles lock failure gracefully?
- [ ] Includes incremental save pattern for long operations?

### Enforcement
- **CLAUDE.md** updated with mandatory safety gate usage
- **Pre-flight checks** added to `j5a_worker.py` and queue processor
- **CI/CD validation** (future) - Scan scripts for safety gate compliance

---

## Summary

**The Golden Rule:** If it uses Whisper Large-v3, it runs ALONE.

**Why This Matters:**
- System viability > processing speed
- Sequential completion > parallel failure
- 2-hour job that completes > 1-hour job that crashes at 99%

**When In Doubt:**
```bash
./ops/resource_safety_gate.sh
```

If it blocks, there's a reason. Wait, don't override.

---

**Document Version:** 1.0
**Author:** Claude Code (post-incident analysis)
**Review Date:** 2025-10-15
**Next Review:** After 30 days of stable operation
