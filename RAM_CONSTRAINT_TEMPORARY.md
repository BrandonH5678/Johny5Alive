# TEMPORARY RAM CONSTRAINT

**Status:** ACTIVE until RAM upgrade delivered
**Date Added:** 2025-10-01
**Added By:** User request (RAM upgrade kit delivery delayed)

---

## Constraint Overview

Until the RAM upgrade is installed (current: 3.7GB → target: 8GB+), J5A will **block multi-speaker audio research projects** that require intensive diarization and speaker separation processing.

### BLOCKED Content Types:
- ❌ **Podcasts** (multi-speaker conversations)
- ❌ **Interview series** (multi-speaker Q&A)
- ❌ **YouTube videos** (often multi-speaker)
- ❌ **Multi-speaker audio** (any format)

### ALLOWED Content Types:
- ✅ **Documents** (books, PDFs, text)
- ✅ **Books** (print media)
- ✅ **Single-speaker audio** (lectures, speeches)
- ✅ **Visual media** (images, photos)

---

## Implementation

### File Modified:
`/home/johnny5/Johny5Alive/src/overnight_queue_manager.py`

### Code Location:
- **Line 175-189:** RAM constraint configuration
- **Line 473-479:** Execution blocking logic
- **Line 654-700:** `_check_ram_constraint()` method

### Key Logic:
```python
# TEMPORARY: RAM upgrade constraint (remove after RAM upgrade delivered)
self.ram_upgrade_pending = True
self.blocked_content_types = [
    "podcast",
    "interview_series",
    "youtube",  # Often multi-speaker
    "multi_speaker_audio"
]
```

---

## Current Queue Impact

**Total Sherlock packages in queue:** 35

### Blocked by RAM Constraint: 3
1. **American Alchemy Interviews with Danny Sheehan** (youtube, Priority 2)
2. **American Alchemy with Harald Malmgren** (youtube, Priority 2)
3. **Weaponized Podcast** (youtube, Priority 1) ⚠️ Critical priority

### Allowed to Execute: 32
- **10 Priority 1 (Critical)** packages including:
  - Imminent — Luis Elizondo (document)
  - Hal Puthoff (composite)
  - Henry Kissinger (composite)
  - George H. W. Bush (composite)
  - Allen Dulles (composite)
  - And 5 more...

- **22 Priority 2-3** packages

---

## How It Works

### 1. Task Queuing
When Targeting Officer submits packages to J5A queue, they are stored normally.

### 2. Execution Attempt
When J5A attempts to execute a task:

```
1. Update status to IN_PROGRESS
2. Check RAM constraint ← NEW STEP
   - If blocked content type → DEFER task
   - Log: "⚠️ RAM CONSTRAINT: Blocking {type} - requires RAM upgrade"
3. Continue with validation checkpoints (if allowed)
4. Execute task (if allowed)
```

### 3. Deferred Status
Blocked tasks get status `DEFERRED` and will be automatically retried on next queue processing cycle (but will continue to be blocked until constraint is removed).

---

## Architecture Analysis

### Single Manager Design ✅

**Q: Is there overlap between overnight executor and queue manager?**

**A: NO - They are the SAME file.**

- **File:** `/home/johnny5/Johny5Alive/src/overnight_queue_manager.py`
- **Class:** `J5AOvernightQueueManager`
- **Functions:** Both queuing AND execution

The constraint was added **ONLY ONCE** in this single manager class.

**Key Methods:**
- `queue_task()` - Add tasks to queue
- `process_overnight_queue()` - Execute tasks from queue
- `_process_single_task()` - Process individual task (includes RAM check)
- `_check_ram_constraint()` - NEW: RAM constraint enforcement

**Result:** Clean, well-organized single-responsibility design. No duplication needed.

---

## How to Remove Constraint (When RAM Upgrade Arrives)

### Option 1: Quick Toggle (30 seconds)

Edit `/home/johnny5/Johny5Alive/src/overnight_queue_manager.py`:

**Find line 177:**
```python
self.ram_upgrade_pending = True
```

**Change to:**
```python
self.ram_upgrade_pending = False
```

**Save and restart J5A.** All content types now allowed.

### Option 2: Complete Removal (5 minutes)

1. **Remove configuration (lines 175-189):**
   ```python
   # Delete this entire block:
   # TEMPORARY: RAM upgrade constraint...
   self.ram_upgrade_pending = True
   self.blocked_content_types = [...]
   self.allowed_content_types = [...]
   ```

2. **Remove execution check (lines 473-479):**
   ```python
   # Delete this block:
   # TEMPORARY: RAM upgrade constraint check
   if not self._check_ram_constraint(task_def):
       ...
   ```

3. **Remove method (lines 654-700):**
   ```python
   # Delete entire method:
   def _check_ram_constraint(self, task_def: TaskDefinition) -> bool:
       ...
   ```

4. **Save and restart J5A.**

---

## Testing the Constraint

### Verify Blocked Packages:
```bash
cd /home/johnny5/Johny5Alive
python3 test_ram_constraint.py
```

**Expected output:**
```
🚫 BLOCKED (Multi-speaker audio): 3
✅ ALLOWED (Document/print/visual): 32
```

### Check J5A Logs:
```bash
tail -f j5a_queue_manager.log | grep "RAM CONSTRAINT"
```

**Expected when blocked task attempted:**
```
⚠️ RAM CONSTRAINT: Blocking youtube package - requires RAM upgrade
```

---

## Package-Specific Impact

### High-Priority Blocked:
1. **Weaponized Podcast** (Priority 1)
   - Target: UAP disclosure content
   - Hosts: Jeremy Corbell & George Knapp
   - **Action:** Will auto-execute when RAM constraint removed

### Can Execute Now (Priority 1):
- Imminent book (Luis Elizondo) - Document research
- Allen Dulles - Composite research (Wikipedia, Google, archives)
- James Angleton - Composite research
- Hal Puthoff - Composite research
- All other Priority 1 composite/document packages

---

## Timeline

**Current RAM:** 3.7GB total
**Target RAM:** 8GB+ (upgrade kit delayed)
**Constraint Duration:** Until upgrade installed
**Affected Packages:** 3 (2 Priority 2, 1 Priority 1)
**Available Packages:** 32 can execute immediately

**When upgrade arrives:**
1. Install RAM
2. Set `ram_upgrade_pending = False` (line 177)
3. Restart J5A
4. All 35 packages will be eligible for execution

---

## Related Files

- **Queue Manager:** `src/overnight_queue_manager.py` (constraint implemented here)
- **Test Script:** `test_ram_constraint.py` (analyze queue impact)
- **Queue Directory:** `queue/sherlock_pkg_*.json` (35 packages waiting)
- **This Document:** `RAM_CONSTRAINT_TEMPORARY.md` (removal instructions)

---

**Last Updated:** 2025-10-01
**Status:** Active constraint, ready to remove when RAM upgrade arrives
