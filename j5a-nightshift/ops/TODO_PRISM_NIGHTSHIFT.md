# Prism + Night Shift Implementation TODO

**Created:** 2025-12-01
**Authority:** EXECUTION_PLAN_PRISM_NIGHTSHIFT.md
**Status Tracking:** Check boxes manually as completed

---

## CRITICAL: Post-Compaction Protocol

**IF YOU JUST EXPERIENCED AUTO-COMPACTION:**

1. Run `/context-refresh` immediately
2. Read this file: `/home/johnny5/Johny5Alive/j5a-nightshift/ops/TODO_PRISM_NIGHTSHIFT.md`
3. Read the execution plan: `/home/johnny5/Johny5Alive/j5a-nightshift/ops/EXECUTION_PLAN_PRISM_NIGHTSHIFT.md`
4. Find your current phase below and continue

---

## Phase 1: Feed the Queue

### 1.1 Run Targeting Officer Manually
- [ ] Check current package count: `python3 /home/johnny5/Sherlock/src/sherlock_targeting_officer.py --status`
- [ ] Generate packages: `python3 /home/johnny5/Sherlock/src/sherlock_targeting_officer.py --sweep --freshness-days 7`
- [ ] Verify packages in queue: `ls -la /home/johnny5/Johny5Alive/queue/nightshift/`
- [ ] Document package count: _____ packages created

### 1.2 Add Targeting Officer to Night Shift
- [ ] Choose integration method (ExecStartPre OR separate timer)
- [ ] Edit systemd service/create timer
- [ ] Run `sudo systemctl daemon-reload`
- [ ] Verify with `systemctl status j5a-nightshift.service`

### 1.3 Package Freshness Modification
- [ ] Read `sherlock_targeting_officer.py` to understand current logic
- [ ] Add freshness checking (7-day threshold)
- [ ] Add freshness statistics logging
- [ ] Test modified script

### 1.4 Verify Queue Integration
- [ ] Manually trigger: `sudo systemctl start j5a-nightshift.service`
- [ ] Watch logs: `journalctl -u j5a-nightshift.service -f`
- [ ] Confirm packages processed
- [ ] Check summary output

**Phase 1 Complete Checkpoint:**
- [ ] Targeting Officer runs automatically
- [ ] Packages populate queue
- [ ] Night Shift processes packages
- [ ] Summary generated

---

## Phase 2: Morning Review Enhancement

### 2.1 Create morning_review_generator.py
- [ ] Create file at `/home/johnny5/Sherlock/morning_review_generator.py`
- [ ] Include human-friendly format (see execution plan)
- [ ] Include "Awaiting Approval" section
- [ ] Include "Recommended Next Steps" section
- [ ] Test standalone execution

### 2.2 Add to ExecStopPost
- [ ] Edit `/etc/systemd/system/j5a-nightshift.service`
- [ ] Add: `ExecStopPost=-/usr/bin/python3 /home/johnny5/Sherlock/morning_review_generator.py`
- [ ] Run `sudo systemctl daemon-reload`
- [ ] Test by running Night Shift

### 2.3 Notification Hook (Optional)
- [ ] Choose method (email/desktop/cron)
- [ ] Implement notification
- [ ] Test notification

**Phase 2 Complete Checkpoint:**
- [ ] morning_review.md generates after Night Shift
- [ ] Review is human-friendly
- [ ] (Optional) Notification works

---

## Phase 3: Claude Queue Approval Workflow

### 3.1 Extend Queue Schema
- [ ] Create `/home/johnny5/Johny5Alive/queue/schemas/claude_max_task.schema.json`
- [ ] Add category, estimated_duration, approval fields
- [ ] Update queue processor to respect schema

### 3.2 Create Approval CLI
- [ ] Create `/home/johnny5/Johny5Alive/queue/approve_claude_queue.py`
- [ ] Implement `--approve`, `--approve-all`, `--reject` flags
- [ ] Test approval workflow

**Phase 3 Complete Checkpoint:**
- [ ] Queue tasks have category and approval fields
- [ ] Human can approve/reject via CLI
- [ ] Principle 1 (Human Agency) satisfied

---

## Phase 4: Feedback Loop - Hypothesis Bin

### 4.1 Create Hypothesis Table
- [ ] Add table to `/home/johnny5/Sherlock/sherlock.db`
- [ ] Create indexes
- [ ] Verify table created

### 4.2 Modify Claude Analysis Template
- [ ] Define hypothesis output format
- [ ] Update any existing templates
- [ ] Test hypothesis extraction

### 4.3 Targeting Officer Hypothesis Scan
- [ ] Add `scan_hypotheses_for_packages()` method
- [ ] Add to sweep logic
- [ ] Test hypothesis → package flow

**Phase 4 Complete Checkpoint:**
- [ ] Hypotheses stored in database
- [ ] Targeting Officer creates packages from hypotheses
- [ ] Feedback loop is closed

---

## Phase 5: RRARR Sustainability

### 5.1 Create PRISM_ESSENCE.md
- [ ] Create template at `/home/johnny5/Prism/PRISM_ESSENCE.md`
- [ ] Extract core identity from existing docs
- [ ] Verify <5K tokens

### 5.2 Create Tiered Loading
- [ ] Modify `/home/johnny5/Prism/.claude/commands/prism.md`
- [ ] Implement Tier 0/1/2 logic
- [ ] Test loading

### 5.3 Archive Existing Content
- [ ] Create archive directories
- [ ] Move October dialogues
- [ ] Move November dialogues
- [ ] Verify archive structure

### 5.4 Create Compression Script
- [ ] Create `/home/johnny5/Prism/scripts/compress_week.py`
- [ ] Implement weekly compression
- [ ] Test compression

**Phase 5 Complete Checkpoint:**
- [ ] PRISM_ESSENCE.md exists (<5K tokens)
- [ ] Tiered loading works
- [ ] Full refresh <30K tokens

---

## Session Tracking

**Session 1:** Date: _________ Phase: _____ Notes: _____________________
**Session 2:** Date: _________ Phase: _____ Notes: _____________________
**Session 3:** Date: _________ Phase: _____ Notes: _____________________
**Session 4:** Date: _________ Phase: _____ Notes: _____________________
**Session 5:** Date: _________ Phase: _____ Notes: _____________________

---

## Compaction Recovery Log

If you've just recovered from compaction, note it here:

| Timestamp | Compaction # | Phase at Compaction | Notes |
|-----------|--------------|---------------------|-------|
|           |              |                     |       |
|           |              |                     |       |

---

**Constitutional Reminder:**
- Principle 1: Human Agency - Claude Max needs approval
- Principle 3: System Viability - Completion > Speed
- Principle 4: Resource Stewardship - Check thermal before heavy ops

---

**END OF TODO**

*Update this file as tasks complete. This is the source of truth across compactions.*
