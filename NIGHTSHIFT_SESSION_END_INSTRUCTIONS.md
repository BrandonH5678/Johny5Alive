# Night Shift - Session End Execution Instructions

**Purpose:** Run Night Shift when Claude Code session ends (token exhaustion)

## What Was Prepared

### 1. Session-End Trigger Script
**Location:** `/home/johnny5/Johny5Alive/run_nightshift_on_session_end.sh`
- Runs pre-flight checks
- Executes Night Shift with 30-minute timeout protection
- Generates summary report
- Comprehensive logging

### 2. Fixed Systemd Service Configuration
**Location:** `/home/johnny5/Johny5Alive/j5a-nightshift/j5a-nightshift.service.fixed`

**Key Fixes:**
- Moved `StartLimitIntervalSec` to `[Unit]` section (was causing warning)
- Added 30-minute timeout protection (`TimeoutStartSec=1800`)
- Added timeout wrapper to ExecStart
- Made summary step optional (won't fail if errors)

### 3. Complete Setup and Run Script
**Location:** `/home/johnny5/Johny5Alive/setup_and_run_nightshift.sh`

**What It Does:**
1. Installs fixed systemd service configuration
2. Checks Ollama is running (starts if needed)
3. Runs Night Shift queue processor manually
4. Captures all output with comprehensive logging

## How to Run When Session Ends

### Option 1: Recommended - Complete Setup and Run
```bash
sudo /home/johnny5/Johny5Alive/setup_and_run_nightshift.sh
```

This will:
- Fix the systemd service for future runs
- Run Night Shift immediately
- Show all output in terminal

### Option 2: Simple Session-End Trigger
```bash
/home/johnny5/Johny5Alive/run_nightshift_on_session_end.sh
```

This will:
- Run Night Shift with current configuration
- Log to timestamped file in `ops/logs/`

### Option 3: Manual Systemd Service (After Installing Fix)
```bash
# Install fixed service (requires sudo)
sudo cp /home/johnny5/Johny5Alive/j5a-nightshift/j5a-nightshift.service.fixed /etc/systemd/system/j5a-nightshift.service
sudo systemctl daemon-reload

# Run via systemd
sudo systemctl start j5a-nightshift.service

# Check status
systemctl status j5a-nightshift.service
```

## Expected Behavior

### What Will Happen
1. **Pre-flight check** - Verifies Ollama is running
2. **Job processing** - Processes 10 test jobs from `nightshift_jobs.json`
3. **Local LLM usage** - Uses qwen2.5:7b via Ollama (no API calls)
4. **Summary generation** - Creates completion report

### Success Criteria
- ≥85% jobs complete (9/10 or better)
- All summaries have ≥3 citations
- Processing time <30 min total
- No thermal events (CPU <80°C)
- No OOM errors

### Logs and Output
- **Systemd logs:** `/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/systemd.log`
- **Session-end logs:** `/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/session_end_run_*.log`
- **Output files:** `/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs/*.md`

## Known Issues and Workarounds

### Issue: Script Hangs on Job Processing
**Symptom:** Process timeout after 30 minutes
**Cause:** Ollama LLM inference may be slow on CPU-only hardware
**Workaround:** Timeout protection in place - job will be killed and next one attempted

### Issue: Systemd Service Still Fails
**Symptom:** Service exits with code 1
**Cause:** Configuration not yet updated
**Solution:** Run Option 1 (setup_and_run_nightshift.sh) to install fix

### Issue: No Jobs Processed
**Symptom:** "0 jobs completed"
**Check:**
1. Ollama running: `curl http://localhost:11434/api/version`
2. Input files exist: `ls /home/johnny5/Johny5Alive/j5a-nightshift/ops/inbox/`
3. Jobs file valid: `cat /home/johnny5/Johny5Alive/j5a-nightshift/ops/queue/nightshift_jobs.json`

## Debugging

### View Real-Time Logs
```bash
# Systemd logs
tail -f /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/systemd.log

# Session-end logs (get latest)
tail -f /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/session_end_run_*.log
```

### Check Ollama Status
```bash
# Is Ollama running?
curl http://localhost:11434/api/version

# Is model available?
ollama list | grep qwen2.5

# Test model
ollama run qwen2.5:7b-instruct-q4_K_M "Hello"
```

### Manual Test Run
```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift
python3 process_nightshift_queue.py 1  # Process just 1 job
```

## What Happens Next

### If Successful (≥85% success rate)
1. Review output quality in `ops/outputs/`
2. Check validation results
3. Analyze processing metrics
4. Plan production deployment (nightly runs)

### If Unsuccessful (<85% success rate)
1. Review failure logs
2. Identify common failure patterns
3. Optimize prompts for local 7B LLM
4. Adjust chunk sizes or validation criteria
5. Iterate and re-test

## Future Automation

Once Night Shift proves successful:

### Enable Nightly Systemd Timer
```bash
# Timer already configured for 7:00 PM daily
sudo systemctl enable j5a-nightshift.timer
sudo systemctl start j5a-nightshift.timer

# Check next run time
systemctl list-timers | grep nightshift
```

### Monitor Production Runs
```bash
# View completion summary
cat /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/nightshift_summary_*.txt

# Check success rates over time
grep "Phase 1 Success Rate" /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/systemd.log
```

---

**Created:** 2025-10-11
**Purpose:** Session-end Night Shift execution trigger
**Status:** Ready to run when Claude Code session ends
