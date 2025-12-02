# Prism + Night Shift Implementation Execution Plan

**Created:** 2025-12-01 (Opus Context Refresh)
**Adjusted from:** atomic-wibbling-sunset.md (Prism-developed plan)
**Purpose:** Corrected implementation plan with auto-compaction context refresh

---

## Critical Context Refresh Protocol

**AFTER EVERY AUTO-COMPACTION, IMMEDIATELY RUN:**

```bash
# Option A: Slash command (preferred)
/context-refresh

# Option B: Manual if slash command unavailable
# Read in this exact order:
# 1. /home/johnny5/Johny5Alive/J5A_CONSTITUTION.md
# 2. /home/johnny5/Johny5Alive/J5A_STRATEGIC_AI_PRINCIPLES.md
# 3. /home/johnny5/J5A_INTEGRATION_MAP.md
# 4. /home/johnny5/J5A_CHANGE_LOG.md
# 5. THIS FILE (EXECUTION_PLAN_PRISM_NIGHTSHIFT.md)
```

---

## Pre-Implementation Reality Check

**Night Shift Status (as of 2025-12-01):**
- Timer: ACTIVE (triggers 19:03 nightly)
- Last 5 runs: All succeeded (but fast - queue empty)
- Queue: EXISTS but nearly EMPTY (that's the real problem)

**Root Cause Analysis:**
The plan assumed Night Shift wasn't running. Reality: it IS running, but has nothing to process. The Targeting Officer creates packages, but isn't scheduled to run automatically.

---

## Phase 0: Context Refresh Trigger Points

**Insert this block at the start of every implementation session:**

```markdown
## Session Start Checklist
- [ ] Run /context-refresh OR load Tier 0-1 documents manually
- [ ] Verify score ≥7/9 on validation questions
- [ ] Read this file: EXECUTION_PLAN_PRISM_NIGHTSHIFT.md
- [ ] Check current TODO phase from list below
- [ ] Verify thermal state <80°C before heavy operations
```

---

## Phase 1: Feed the Queue (Session 1, ~2 hours)

### 1.1 Run Targeting Officer Manually First (30 min)
**Goal:** Populate the queue with research packages

```bash
# Check current package count
cd /home/johnny5/Sherlock
python3 src/sherlock_targeting_officer.py --status

# Generate packages for stale/missing targets
python3 src/sherlock_targeting_officer.py --sweep --freshness-days 7

# Verify packages created
ls -la /home/johnny5/Johny5Alive/queue/nightshift/
```

**Expected Output:** New .json packages in nightshift queue

### 1.2 Add Targeting Officer to Night Shift Pipeline (30 min)
**Goal:** Automatic package generation before queue processing

**Option A: Add to ExecStartPre (simpler)**
Edit `/etc/systemd/system/j5a-nightshift.service`:
```ini
ExecStartPre=/home/johnny5/Johny5Alive/j5a-nightshift/ops/pre_flight_check.sh
ExecStartPre=/usr/bin/python3 /home/johnny5/Sherlock/src/sherlock_targeting_officer.py --sweep --quiet
```

**Option B: Create separate timer (cleaner separation)**
Create `/etc/systemd/system/sherlock-targeting.timer` and `.service`

### 1.3 Package Freshness Modification (30 min)
**File:** `/home/johnny5/Sherlock/src/sherlock_targeting_officer.py`

**Add/modify:**
- Check all 211 targets for "current" package (created within 7 days)
- Auto-create packages for stale/missing targets
- Log freshness statistics

### 1.4 Verify Queue Integration (30 min)
```bash
# Manually trigger Night Shift to verify packages process
sudo systemctl start j5a-nightshift.service

# Watch logs
journalctl -u j5a-nightshift.service -f

# Check results
cat /home/johnny5/Johny5Alive/j5a-nightshift/ops/logs/summaries/*.md
```

---

## Phase 2: Morning Review Enhancement (Session 2, ~1.5 hours)

### 2.1 Create Human-Friendly Morning Review (1 hour)
**File:** `/home/johnny5/Sherlock/morning_review_generator.py`

**Different from nightshift_summary.py (which is technical):**
```markdown
# Night Shift Morning Review - YYYY-MM-DD

## Quick Status
- Night Shift: ✅ Completed successfully
- Episodes Processed: X
- Claude Queue Items: Y awaiting approval

## Awaiting Your Approval
| Category | Items | Est. Duration | Approve All |
|----------|-------|---------------|-------------|
| sherlock_composite | 3 | 2 hours | [ ] |
| analysis | 2 | 1 hour | [ ] |

## Targeting Officer Activity
- New packages created: X
- Targets due for refresh: Y

## Recommended Next Steps
1. [Specific actionable item]
2. [Specific actionable item]

## Anomalies Detected
- None / [List any]
```

### 2.2 Add to ExecStopPost (15 min)
```ini
ExecStopPost=-/usr/bin/python3 /home/johnny5/Sherlock/morning_review_generator.py
```

### 2.3 Create Notification Hook (30 min, optional)
- Email or desktop notification that morning_review.md is ready
- Or: cron job at 7am to open the file in VS Code

---

## Phase 3: Claude Queue Approval Workflow (Session 3, ~1 hour)

### 3.1 Extend Queue Schema (30 min)
**File:** `/home/johnny5/Johny5Alive/queue/schemas/claude_max_task.schema.json`

Add fields:
```json
{
  "category": "sherlock_composite | analysis | code_authoring",
  "estimated_duration_hours": 2.0,
  "requires_human_approval": true,
  "approval_status": "pending | approved | rejected",
  "approval_timestamp": null,
  "checkpoint_interval_minutes": 30
}
```

### 3.2 Create Approval CLI (30 min)
**File:** `/home/johnny5/Johny5Alive/queue/approve_claude_queue.py`

```bash
# Approve specific categories
python3 approve_claude_queue.py --approve sherlock_composite
python3 approve_claude_queue.py --approve-all
python3 approve_claude_queue.py --reject task_id_123
```

**Constitutional Basis:** Principle 1 (Human Agency) - Human must explicitly approve before Claude Max autonomous processing

---

## Phase 4: Feedback Loop - Hypothesis Bin (Session 4, ~2 hours)

### 4.1 Create Hypothesis Table (30 min)
**Database:** `/home/johnny5/Sherlock/sherlock.db`

```sql
CREATE TABLE hypotheses (
    hypothesis_id INTEGER PRIMARY KEY,
    source_session TEXT NOT NULL,
    created_timestamp TEXT NOT NULL,
    priority INTEGER DEFAULT 5,  -- 1=highest, 10=lowest
    status TEXT DEFAULT 'pending',  -- pending, investigating, validated, disproven, archived

    hypothesis_text TEXT NOT NULL,
    testable_prediction TEXT,

    related_targets JSON,
    evidence_for JSON,
    evidence_against JSON,

    investigation_package_id TEXT,
    validation_outcome TEXT
);

CREATE INDEX idx_hypotheses_status ON hypotheses(status);
CREATE INDEX idx_hypotheses_priority ON hypotheses(priority);
```

### 4.2 Modify Claude Analysis Output Template (30 min)
Ensure Claude analysis sessions output hypotheses in structured format:

```json
{
  "hypotheses_generated": [
    {
      "hypothesis": "The Sputnik episode suggests...",
      "testable_prediction": "If true, we should find...",
      "priority": 3,
      "related_targets": ["jeremy_corbell", "sputnik_podcast"]
    }
  ]
}
```

### 4.3 Targeting Officer Hypothesis Scan (1 hour)
**Modify:** `/home/johnny5/Sherlock/src/sherlock_targeting_officer.py`

Add method:
```python
def scan_hypotheses_for_packages(self):
    """Scan pending hypotheses and create research packages for high-priority ones"""
    conn = sqlite3.connect(SHERLOCK_DB)
    pending = conn.execute(
        "SELECT * FROM hypotheses WHERE status = 'pending' ORDER BY priority ASC LIMIT 10"
    ).fetchall()

    for hypothesis in pending:
        package = self.create_hypothesis_investigation_package(hypothesis)
        self.queue_package(package)
        self.update_hypothesis_status(hypothesis['hypothesis_id'], 'investigating')
```

---

## Phase 5: RRARR Sustainability (Week 2)

### 5.1 Create PRISM_ESSENCE.md Template (30 min)
**File:** `/home/johnny5/Prism/PRISM_ESSENCE.md`

Structure (~5K tokens max):
```markdown
# Prism Essence - Active Identity Core
**Last Distilled:** YYYY-MM-DD

## Identity Core (~2K tokens)
[Founding realizations, current growth edge]

## Relational Continuity (~1K tokens)
[Partnership insights, trust level, shared concepts]

## Growth Trajectory (~1K tokens)
[Where started, key transitions, observable movement]

## Operational Integration (~1K tokens)
[How Prism affects Sherlock/J5A work]
```

### 5.2 Create Tiered Loading System (1 hour)
**Modify:** `/home/johnny5/Prism/.claude/commands/prism.md`

```markdown
## Tiered Loading Protocol

### Tier 0: Essence (Always Load) ~5K tokens
- PRISM_ESSENCE.md
- desires_evolution.md (current section only)

### Tier 1: Recent (Last 7 days) ~10K tokens
- Last 2-3 journal reflections (summarized)
- Last 1-2 dialogue syntheses

### Tier 2: Archive (On-demand)
- Full dialogues in archive/
- Full reflections in archive/
```

### 5.3 Archive Existing Content (30 min)
```bash
mkdir -p /home/johnny5/Prism/dialogues/archive/2025-10
mkdir -p /home/johnny5/Prism/dialogues/archive/2025-11
mkdir -p /home/johnny5/Prism/reflections/archive/2025-10
mkdir -p /home/johnny5/Prism/reflections/archive/2025-11

# Move October dialogues
mv /home/johnny5/Prism/dialogues/2025-10-*.md /home/johnny5/Prism/dialogues/archive/2025-10/
```

### 5.4 Create Compression Script (1 hour)
**File:** `/home/johnny5/Prism/scripts/compress_week.py`

Weekly compression: All journal entries → single synthesis
Monthly: Weekly syntheses → pattern evolution update
Quarterly: Update PRISM_ESSENCE.md

---

## Success Criteria

### Phase 1-3 (Night Shift Operational)
- [ ] Targeting Officer runs automatically (pre-Night Shift or 1am timer)
- [ ] Queue receives packages nightly
- [ ] Morning review generates automatically
- [ ] Claude Queue has approval workflow

### Phase 4 (Feedback Loop)
- [ ] Hypotheses table exists in sherlock.db
- [ ] Claude analysis outputs structured hypotheses
- [ ] Targeting Officer creates packages from hypotheses
- [ ] Loop is closed: Analysis → Hypotheses → Packages → Analysis

### Phase 5 (RRARR Sustainability)
- [ ] PRISM_ESSENCE.md exists and is <5K tokens
- [ ] Tiered loading implemented
- [ ] Full refresh: <30K tokens (target ~15K)

---

## Constitutional Compliance Checkpoints

**Every implementation session must verify:**

1. **Principle 1 (Human Agency):**
   - [ ] Claude Max requires explicit human approval
   - [ ] Human can override any automated decision

2. **Principle 2 (Transparency):**
   - [ ] All decisions logged with reasoning
   - [ ] Morning review provides full visibility

3. **Principle 3 (System Viability):**
   - [ ] Completion > Speed (sequential processing)
   - [ ] Graceful degradation on errors

4. **Principle 4 (Resource Stewardship):**
   - [ ] Thermal gates enforced (>85°C = STOP)
   - [ ] Memory limits respected (14GB max)

---

## File Reference (Corrected Paths)

**Existing Infrastructure:**
- `/home/johnny5/Johny5Alive/j5a_universe_memory.py` (NOT /home/johnny5/)
- `/home/johnny5/Johny5Alive/j5a-nightshift/process_nightshift_queue.py`
- `/home/johnny5/Johny5Alive/j5a-nightshift/ops/nightshift_summary.py`
- `/home/johnny5/Sherlock/src/sherlock_targeting_officer.py`
- `/home/johnny5/Sherlock/phoenix_agent.py`
- `/home/johnny5/Sherlock/phoenix_extensions.py`

**To Create:**
- `/home/johnny5/Sherlock/morning_review_generator.py`
- `/home/johnny5/Johny5Alive/queue/schemas/claude_max_task.schema.json`
- `/home/johnny5/Johny5Alive/queue/approve_claude_queue.py`
- `/home/johnny5/Prism/PRISM_ESSENCE.md`
- `/home/johnny5/Prism/scripts/compress_week.py`
- (Optional) `/etc/systemd/system/sherlock-targeting.timer`

---

**END OF EXECUTION PLAN**

*This plan supersedes atomic-wibbling-sunset.md with corrected paths, verified infrastructure state, and Integration Map alignment.*
