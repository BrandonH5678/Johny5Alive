# J5A Nightshift Automation Installation Guide

**Created**: 2025-10-09
**Status**: Ready for installation

---

## Overview

This guide installs the automation infrastructure for J5A Nightshift, enabling autonomous overnight queue processing at 7pm daily.

**Components**:
- ✅ Systemd service + timer (automatic execution)
- ✅ Pre-flight safety checks
- ✅ Post-processing summary generation
- ✅ Health monitoring dashboard
- ✅ Log rotation

---

## Prerequisites

1. **Night Shift Core** installed and tested
2. **Ollama** running with qwen2.5:7b-instruct-q4_K_M model
3. **Queue database** accessible at `/home/johnny5/Johny5Alive/j5a_queue_manager.db`
4. **sudo access** for systemd configuration

---

## Installation Steps

### Step 1: Test Scripts

First, verify all automation scripts work:

```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift

# Test pre-flight check
./ops/pre_flight_check.sh

# Test health monitoring
./ops/monitor_nightshift.sh

# Test summary generation
python3 ops/nightshift_summary.py
```

**Expected**: All scripts should run without errors.

---

### Step 2: Install Systemd Service

Copy service and timer files to systemd directory:

```bash
# Copy service file
sudo cp j5a-nightshift.service /etc/systemd/system/

# Copy timer file
sudo cp j5a-nightshift.timer /etc/systemd/system/

# Reload systemd to recognize new files
sudo systemctl daemon-reload
```

**Verify installation**:
```bash
systemctl status j5a-nightshift.service
systemctl status j5a-nightshift.timer
```

---

### Step 3: Install Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Copy logrotate configuration
sudo cp j5a-nightshift-logrotate.conf /etc/logrotate.d/j5a-nightshift

# Test configuration
sudo logrotate -d /etc/logrotate.d/j5a-nightshift

# Force rotation test (optional)
sudo logrotate -f /etc/logrotate.d/j5a-nightshift
```

**Verify**:
```bash
ls -lh ops/logs/*.log
# Should see log files with proper permissions
```

---

### Step 4: Enable and Start Timer

Enable the timer to run automatically:

```bash
# Enable timer (starts on boot)
sudo systemctl enable j5a-nightshift.timer

# Start timer immediately
sudo systemctl start j5a-nightshift.timer

# Verify timer is active
systemctl status j5a-nightshift.timer

# Check next scheduled run
systemctl list-timers --all | grep nightshift
```

**Expected output**:
```
NEXT                         LEFT          LAST PASSED UNIT                    ACTIVATES
Thu 2025-10-10 19:00:00 EDT  20h left      n/a  n/a    j5a-nightshift.timer    j5a-nightshift.service
```

---

### Step 5: Test Manual Execution

Before waiting for 7pm, test the service manually:

```bash
# Trigger service manually (doesn't wait for timer)
sudo systemctl start j5a-nightshift.service

# Watch logs in real-time
tail -f ops/logs/systemd.log

# Check service status
systemctl status j5a-nightshift.service
```

**Expected**:
- Pre-flight checks pass
- Queue processing executes
- Summary generated
- No errors in systemd_error.log

---

### Step 6: Verify Health Monitoring

After manual test, check health dashboard:

```bash
./ops/monitor_nightshift.sh
```

**Expected output**:
```
==========================================
J5A NIGHTSHIFT HEALTH STATUS
==========================================

System Status:
  ✅ Ollama: Running
  ✅ CPU Temp: 72°C (GOOD - limit 87°C)
  ✅ Free RAM: 11.3GB (Safe - need 6GB minimum)
  ✅ Timer: Active (next run: 2025-10-10 19:00:00)

Queue Status:
  📊 Total Jobs: 42
  ✅ Completed: 1
  📦 Parked (Phase 2): 4
  ...

Recommendations:
  ✅ All systems nominal
```

---

## Validation Checklist

After installation, verify:

- [ ] **Systemd service** installed and configured
- [ ] **Systemd timer** enabled and active
- [ ] **Log rotation** configured
- [ ] **Pre-flight checks** pass
- [ ] **Health monitoring** shows accurate status
- [ ] **Summary generation** works
- [ ] **Manual execution** completes successfully
- [ ] **Next run** scheduled for 7pm

---

## Daily Operations

### Check System Status

```bash
# Quick health check
/home/johnny5/Johny5Alive/j5a-nightshift/ops/monitor_nightshift.sh

# View latest summary
cat /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/summaries/$(date +%Y-%m-%d).md

# View recent logs
tail -f /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/systemd.log
```

### Manual Execution (Emergency)

```bash
# Run immediately (doesn't wait for 7pm)
sudo systemctl start j5a-nightshift.service

# Run with specific job limit
cd /home/johnny5/Johny5Alive/j5a-nightshift
python3 process_nightshift_queue.py 10
```

### Disable Automation (Temporarily)

```bash
# Stop timer (processing won't run tonight)
sudo systemctl stop j5a-nightshift.timer

# Re-enable later
sudo systemctl start j5a-nightshift.timer
```

### Disable Automation (Permanently)

```bash
# Disable timer
sudo systemctl disable j5a-nightshift.timer
sudo systemctl stop j5a-nightshift.timer
```

---

## Monitoring

### Check Timer Status

```bash
# Is timer active?
systemctl is-active j5a-nightshift.timer

# When is next run?
systemctl list-timers --all | grep nightshift

# Timer configuration
systemctl cat j5a-nightshift.timer
```

### Check Service Logs

```bash
# Systemd journal (last 50 lines)
journalctl -u j5a-nightshift.service -n 50

# Systemd journal (follow live)
journalctl -u j5a-nightshift.service -f

# Application logs
tail -f ops/logs/systemd.log

# Error logs
tail -f ops/logs/systemd_error.log
```

### Check Queue Database

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/johnny5/Johny5Alive/j5a_queue_manager.db')
print('Queue Status:')
status = conn.execute('SELECT status, COUNT(*) FROM task_executions GROUP BY status').fetchall()
for s, c in status: print(f'  {s}: {c}')
conn.close()
"
```

---

## Troubleshooting

### Timer Not Triggering

**Symptom**: Timer shows active but service never runs

**Check**:
```bash
# Verify timer trigger time
systemctl list-timers --all | grep nightshift

# Check systemd journal
journalctl -u j5a-nightshift.timer -n 20
```

**Fix**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart timer
sudo systemctl restart j5a-nightshift.timer
```

---

### Pre-Flight Checks Failing

**Symptom**: Service fails immediately

**Check**:
```bash
# Run pre-flight check manually
./ops/pre_flight_check.sh

# Check specific failures
sensors  # Temperature
free -h  # RAM
ollama list  # Model
```

**Fix**: Address specific failures reported by pre-flight check

---

### Service Crashing

**Symptom**: Service starts but exits with error

**Check**:
```bash
# Check service status
systemctl status j5a-nightshift.service

# Check error logs
cat ops/logs/systemd_error.log

# Check application logs
tail -n 100 ops/logs/systemd.log
```

**Fix**: Review error logs and fix underlying issue

---

### Logs Growing Too Large

**Symptom**: ops/logs/ using excessive disk space

**Check**:
```bash
du -sh ops/logs/
ls -lh ops/logs/*.log
```

**Fix**:
```bash
# Force log rotation
sudo logrotate -f /etc/logrotate.d/j5a-nightshift

# Adjust retention in /etc/logrotate.d/j5a-nightshift
# Change 'rotate 30' to lower value
```

---

## Uninstallation

To remove automation (keeps Night Shift core intact):

```bash
# Stop and disable timer
sudo systemctl stop j5a-nightshift.timer
sudo systemctl disable j5a-nightshift.timer

# Remove systemd files
sudo rm /etc/systemd/system/j5a-nightshift.service
sudo rm /etc/systemd/system/j5a-nightshift.timer

# Remove logrotate config
sudo rm /etc/logrotate.d/j5a-nightshift

# Reload systemd
sudo systemctl daemon-reload
```

Automation scripts in `ops/` remain intact for manual use.

---

## Files Installed

### Systemd
- `/etc/systemd/system/j5a-nightshift.service` - Service definition
- `/etc/systemd/system/j5a-nightshift.timer` - Timer configuration

### Logrotate
- `/etc/logrotate.d/j5a-nightshift` - Log rotation rules

### Application Scripts (already present)
- `ops/pre_flight_check.sh` - Safety checks before execution
- `ops/nightshift_summary.py` - Post-processing summary
- `ops/monitor_nightshift.sh` - Health monitoring dashboard

### Logs (created automatically)
- `ops/logs/systemd.log` - Service stdout
- `ops/logs/systemd_error.log` - Service stderr
- `ops/logs/summaries/YYYY-MM-DD.md` - Daily summaries

---

## Success Criteria

After installation, verify:

✅ **Automation**:
- Timer triggers service at 7pm daily
- No manual intervention required
- Pre-flight checks prevent unsafe execution

✅ **Monitoring**:
- Health dashboard shows accurate status
- Summary generated after each run
- Logs properly rotated

✅ **Reliability**:
- 3 consecutive successful automated runs
- No crashes or errors
- Thermal safety maintained

---

## Next Steps

After automation is installed and tested:

1. **Week 2**: Run production validation (20-30 jobs)
2. **Week 3**: Implement Squirt rendering integration
3. **Week 4**: Plan Sherlock research integration

---

**Installation Guide Version**: 1.0
**Created**: 2025-10-09
**Status**: Ready for installation
