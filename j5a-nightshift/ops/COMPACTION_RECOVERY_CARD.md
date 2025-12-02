# POST-COMPACTION RECOVERY CARD

**If you just experienced auto-compaction during Prism+NightShift implementation:**

## Step 1: Context Refresh (MANDATORY)
```
/context-refresh
```

## Step 2: Read These Files
1. `/home/johnny5/Johny5Alive/j5a-nightshift/ops/TODO_PRISM_NIGHTSHIFT.md` ← Your todo list
2. `/home/johnny5/Johny5Alive/j5a-nightshift/ops/EXECUTION_PLAN_PRISM_NIGHTSHIFT.md` ← Full plan

## Step 3: Find Your Phase
Check the TODO file for unchecked boxes. Continue from there.

## Step 4: Quick Verification
- Timer status: `systemctl status j5a-nightshift.timer`
- Thermal check: `sensors | grep "Package id"`
- Queue contents: `ls /home/johnny5/Johny5Alive/queue/nightshift/`

## Key File Paths (Corrected)
- Universe Memory: `/home/johnny5/Johny5Alive/j5a_universe_memory.py`
- Targeting Officer: `/home/johnny5/Sherlock/src/sherlock_targeting_officer.py`
- Phoenix Agent: `/home/johnny5/Sherlock/phoenix_agent.py`
- Night Shift Queue: `/home/johnny5/Johny5Alive/queue/nightshift/`
- Claude Queue: `/home/johnny5/Johny5Alive/queue/claude/`

## Constitutional Quick Reference
- Principle 1: Human Agency (approval required for Claude Max)
- Principle 3: System Viability (completion > speed)
- Principle 4: Resource Stewardship (85°C = STOP)

**Continue implementation from your current phase.**
