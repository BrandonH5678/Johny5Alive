# Week 1: Automation & Monitoring Implementation Plan

**Goal**: Enable true autonomous overnight operation of Night Shift
**Timeline**: Days 1-7
**Priority**: CRITICAL - Foundation for all other improvements

---

## Overview

This plan implements the automation infrastructure required for Night Shift to run autonomously every night at 7pm, with proper monitoring, logging, and health checks.

---

## Implementation Tasks

### Task 1: Systemd Service & Timer
**Effort**: 2 hours | **Priority**: P0 (Critical)

**Deliverables**:
1. `/etc/systemd/system/j5a-nightshift.service` - Service definition
2. `/etc/systemd/system/j5a-nightshift.timer` - Timer for 7pm execution
3. Systemd integration testing

**Implementation**:
```bash
# Service file: /etc/systemd/system/j5a-nightshift.service
[Unit]
Description=J5A Nightshift Queue Processor
After=network.target ollama.service

[Service]
Type=oneshot
User=johnny5
WorkingDirectory=/home/johnny5/Johny5Alive/j5a-nightshift
ExecStartPre=/home/johnny5/Johny5Alive/j5a-nightshift/ops/pre_flight_check.sh
ExecStart=/usr/bin/python3 /home/johnny5/Johny5Alive/j5a-nightshift/process_nightshift_queue.py
ExecStartPost=/home/johnny5/Johny5Alive/j5a-nightshift/ops/nightshift_summary.py
StandardOutput=append:/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/systemd.log
StandardError=append:/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/systemd_error.log

[Install]
WantedBy=multi-user.target

# Timer file: /etc/systemd/system/j5a-nightshift.timer
[Unit]
Description=J5A Nightshift Daily Timer
Requires=j5a-nightshift.service

[Timer]
OnCalendar=*-*-* 19:00:00
Persistent=true
AccuracySec=1m

[Install]
WantedBy=timers.target
```

**Testing**:
```bash
# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable j5a-nightshift.timer
sudo systemctl start j5a-nightshift.timer

# Test service manually (don't wait for 7pm)
sudo systemctl start j5a-nightshift.service

# Check status
systemctl status j5a-nightshift.timer
systemctl list-timers --all | grep nightshift
```

---

### Task 2: Pre-Flight Check Script
**Effort**: 1 hour | **Priority**: P0 (Critical)

**Deliverable**: `ops/pre_flight_check.sh`

**Purpose**: Validate system readiness before processing

**Checks**:
1. Ollama server running
2. CPU temperature <80°C
3. Free RAM >6GB (model + processing buffer)
4. Queue database accessible
5. No business hours conflict (Mon-Fri 6am-7pm)

**Implementation**: See execution package

---

### Task 3: Nightshift Summary Script
**Effort**: 2 hours | **Priority**: P0 (Critical)

**Deliverable**: `ops/nightshift_summary.py`

**Purpose**: Generate completion report after processing

**Output**:
- Jobs processed (success/failure/parked counts)
- Processing time per job
- Thermal stats (max temp, avg temp)
- Validation results
- Errors encountered
- Next run schedule

**Format**: Markdown summary saved to `ops/logs/summaries/YYYY-MM-DD.md`

**Implementation**: See execution package

---

### Task 4: Log Rotation Configuration
**Effort**: 30 minutes | **Priority**: P1 (High)

**Deliverable**: `/etc/logrotate.d/j5a-nightshift`

**Configuration**:
```
/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 johnny5 johnny5
    sharedscripts
    postrotate
        systemctl reload j5a-nightshift.service 2>/dev/null || true
    endscript
}
```

**Testing**:
```bash
# Test rotation
sudo logrotate -d /etc/logrotate.d/j5a-nightshift
sudo logrotate -f /etc/logrotate.d/j5a-nightshift
```

---

### Task 5: Health Monitoring Dashboard
**Effort**: 3 hours | **Priority**: P1 (High)

**Deliverable**: `ops/monitor_nightshift.sh`

**Purpose**: Quick health check script for manual inspection

**Output**:
```
J5A NIGHTSHIFT HEALTH STATUS
=============================
System Status:
  ✅ Ollama: Running (qwen2.5:7b-instruct-q4_K_M loaded)
  ✅ CPU Temp: 53°C (Safe - limit 87°C)
  ✅ Free RAM: 9.2GB (Safe - need 6GB minimum)
  ✅ Timer: Active (next run: 2025-10-09 19:00:00)

Queue Status:
  📊 Total Jobs: 42
  ✅ Completed: 1
  📦 Parked (Phase 2): 4
  ⏸️  Deferred: 33
  ❌ Failed: 4

Last Run:
  📅 Date: 2025-10-08 00:55:33
  ⏱️  Duration: 8m 18s
  ✅ Success: 1/1 standard jobs (100%)
  📦 Parked: 4/4 demanding jobs

Recent Errors:
  (none)

Recommendations:
  ⚠️  33 deferred jobs need investigation
  ⚠️  4 failed jobs need root cause analysis
  ℹ️  Next run in 11h 23m
```

**Implementation**: See execution package

---

### Task 6: Thermal Alert System
**Effort**: 1.5 hours | **Priority**: P1 (High)

**Deliverable**: `ops/thermal_monitor.py`

**Purpose**: Monitor thermal state during processing

**Features**:
- Check temp every 60 seconds during processing
- Log thermal events
- Auto-defer jobs if temp >80°C
- Emergency stop if temp >90°C
- Integration with existing `thermal_check.py`

**Integration**: Update `j5a_worker.py` to call thermal monitor

---

### Task 7: Queue Status Dashboard
**Effort**: 2 hours | **Priority**: P2 (Medium)

**Deliverable**: `ops/queue_status.py`

**Purpose**: Detailed queue analysis

**Output**:
- Job distribution by type/class
- Processing time trends
- Success rate over time
- Failure pattern analysis
- Resource utilization stats

**Format**: Both CLI output and JSON export for graphing

---

## Execution Order

**Day 1-2**: Core Automation
1. Create systemd service + timer
2. Build pre-flight check script
3. Test manual execution

**Day 3-4**: Monitoring & Reporting
4. Build nightshift summary script
5. Configure log rotation
6. Test automated execution

**Day 5-6**: Health & Alerts
7. Build health monitoring dashboard
8. Implement thermal alert system
9. Integration testing

**Day 7**: Validation & Documentation
10. Build queue status dashboard
11. Full end-to-end testing
12. Update operator manual

---

## Testing Plan

### Unit Tests
- Pre-flight checks (all pass, individual failures)
- Summary generation (success, partial failure, complete failure)
- Health dashboard (all green, warning states, critical states)

### Integration Tests
- Systemd timer triggers service
- Pre-flight check blocks unhealthy execution
- Summary generated after completion
- Logs rotate properly
- Health dashboard accurate

### End-to-End Test
```bash
# Full overnight simulation
1. Set timer for +5 minutes (test trigger)
2. Add 3 test jobs to queue
3. Wait for automatic execution
4. Verify completion summary
5. Check health dashboard
6. Inspect logs
```

---

## Success Criteria

✅ **Automation**:
- Systemd timer executes Night Shift at 7pm daily
- No manual intervention required
- Pre-flight checks prevent unsafe execution

✅ **Monitoring**:
- Completion summary generated after each run
- Health dashboard shows accurate system state
- Thermal monitoring prevents overheating

✅ **Logging**:
- All logs properly rotated (30-day retention)
- Errors captured and surfaced
- Historical data preserved

✅ **Reliability**:
- 3 consecutive successful automated runs
- Pre-flight checks catch >90% of failure conditions
- Thermal safety validated under load

---

## Files Created

**Configuration**:
- `/etc/systemd/system/j5a-nightshift.service`
- `/etc/systemd/system/j5a-nightshift.timer`
- `/etc/logrotate.d/j5a-nightshift`

**Scripts**:
- `ops/pre_flight_check.sh`
- `ops/nightshift_summary.py`
- `ops/monitor_nightshift.sh`
- `ops/thermal_monitor.py`
- `ops/queue_status.py`

**Documentation**:
- Updated `README.md` with automation instructions
- Updated `INTEGRATION_GUIDE.md` with monitoring commands

---

## Next Steps (Week 2)

After Week 1 automation is complete:
1. Run production validation with 20-30 jobs
2. Analyze deferred/failed jobs
3. Measure actual success rate vs 85% target
4. Document failure patterns

---

**Plan Version**: 1.0
**Created**: 2025-10-09
**Status**: Ready for execution
