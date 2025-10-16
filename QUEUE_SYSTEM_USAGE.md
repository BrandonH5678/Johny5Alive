# J5A Dual-Queue System - Usage Guide

## Overview

The J5A system uses a dual-queue architecture to separate deterministic automation (NightShift) from reasoning tasks (Claude):

- **NightShift Queue**: Whitelisted automation tasks (repo sync, batch processing, exports, lint, backup)
- **Claude Queue**: Reasoning tasks (analysis, planning, code authoring)

## Quick Start

### 1. Processing NightShift Queue

**View Current Queue:**
```bash
cat queue/nightshift/inbox.jsonl
```

**Run Dispatcher:**
```bash
bash scripts/nightshift_dispatcher.sh
```

This will:
- Process all tasks in `queue/nightshift/inbox.jsonl`
- Execute whitelisted operations
- Archive processed tasks to `queue/nightshift/archive/`
- Create outputs in `artifacts/nightshift/YYYY-MM-DD/`

### 2. Processing Claude Queue

**View Current Tasks:**
```bash
python3 scripts/claude_queue_processor.py
```

**View as JSON:**
```bash
python3 scripts/claude_queue_processor.py --json
```

**Limit to First N Tasks:**
```bash
python3 scripts/claude_queue_processor.py --limit 3
```

**Process Tasks (Manual - Claude Code does this):**
1. Read task inputs
2. Perform analysis/planning/code_authoring
3. Write outputs to `artifacts/claude/YYYY-MM-DD/`
4. Mark task complete (see below)

**Mark Task Complete:**
```bash
python3 scripts/claude_task_complete.py \
  --task-id "2025-10-11T18:00:00Z-my-task" \
  --task-type "analysis" \
  --status "completed" \
  --deliverables "artifacts/claude/2025-10-11/reports/my_report.md" \
  --notes "Task completed successfully with key findings..."
```

**Mark Task Complete with NightShift Handoff:**
```bash
# Create handoff task specification
cat > /tmp/handoff.json <<'EOF'
{
  "id": "2025-10-11T22:00:00Z-execute-changes",
  "task": "repo_sync",
  "args": {"manifest": "configs/repos.json"},
  "priority": "normal"
}
EOF

# Complete task with handoff
python3 scripts/claude_task_complete.py \
  --task-id "2025-10-11T18:00:00Z-my-task" \
  --task-type "code_authoring" \
  --status "completed" \
  --deliverables "artifacts/claude/2025-10-11/patches/my_patch.diff" \
  --notes "Patch created, queued for NightShift to apply" \
  --handoff /tmp/handoff.json
```

## Task Schemas

### NightShift Task Schema

```json
{
  "id": "2025-10-11T20:00:00Z-task-name",
  "task": "repo_sync|squirt_batch|sherlock_export|lint|backup|llm_job",
  "args": {
    // Task-specific arguments
  },
  "priority": "low|normal|high"
}
```

**Allowed Task Types:**

1. **repo_sync** - Sync Git repositories
   ```json
   {
     "id": "2025-10-11T20:00:00Z-sync-repos",
     "task": "repo_sync",
     "args": {
       "manifest": "configs/repos.json"
     },
     "priority": "normal"
   }
   ```

2. **squirt_batch** - Batch document generation
   ```json
   {
     "id": "2025-10-11T20:00:00Z-generate-docs",
     "task": "squirt_batch",
     "args": {
       "batch_file": "batch_manifest.csv",
       "output": "artifacts/nightshift/2025-10-11/squirt"
     },
     "priority": "normal"
   }
   ```

3. **sherlock_export** - Export topic-based evidence packet
   ```json
   {
     "id": "2025-10-11T20:00:00Z-export-uap",
     "task": "sherlock_export",
     "args": {
       "topic": "anti-gravity",
       "out": "artifacts/nightshift/2025-10-11/sherlock/anti_gravity.jsonl"
     },
     "priority": "normal"
   }
   ```

4. **lint** - Code formatting and linting
   ```json
   {
     "id": "2025-10-11T20:00:00Z-lint-code",
     "task": "lint",
     "args": {
       "target": "src/",
       "fix": true
     },
     "priority": "low"
   }
   ```

5. **backup** - Safe backup operations
   ```json
   {
     "id": "2025-10-11T20:00:00Z-backup-data",
     "task": "backup",
     "args": {
       "source": "/home/johnny5/important_data",
       "dest": "artifacts/nightshift/2025-10-11/backups"
     },
     "priority": "high"
   }
   ```

6. **llm_job** - Queue LLM-based job for J5AWorker
   ```json
   {
     "id": "2025-10-11T20:00:00Z-llm-task",
     "task": "llm_job",
     "args": {
       "job_spec": {
         "job_id": "my_job_20251011",
         "type": "summary",
         "class": "standard",
         "priority": 1,
         "description": "Summarize document",
         "inputs": [{"path": "path/to/input.txt"}],
         "outputs": [{"kind": "markdown", "path": "path/to/output.md"}],
         "metadata": {}
       }
     },
     "priority": "normal"
   }
   ```

### Claude Task Schema

```json
{
  "id": "2025-10-11T18:00:00Z-task-name",
  "type": "analysis|planning|code_authoring",
  "priority": "high|normal|low",
  "inputs": ["file1.md", "file2.py"],
  "deliverables": ["artifacts/claude/2025-10-11/reports/output.md"],
  "constraints": {
    "max_tokens": 60000,
    "style": "concise|technical|production",
    "citations": true
  },
  "notes": "Additional context and instructions"
}
```

**Example Tasks:**

1. **Analysis Task**
   ```json
   {
     "id": "2025-10-11T18:00:00Z-analyze-packet",
     "type": "analysis",
     "priority": "high",
     "inputs": ["artifacts/nightshift/2025-10-11/sherlock/uap_packet.jsonl"],
     "deliverables": ["artifacts/claude/2025-10-11/reports/uap_analysis.md"],
     "constraints": {
       "max_tokens": 60000,
       "style": "concise",
       "citations": true
     },
     "notes": "Cross-reference with recent publications, identify key researchers"
   }
   ```

2. **Planning Task**
   ```json
   {
     "id": "2025-10-11T19:00:00Z-plan-feature",
     "type": "planning",
     "priority": "normal",
     "inputs": ["ARCHITECTURE_ORCHESTRATION.md"],
     "deliverables": ["artifacts/claude/2025-10-11/reports/feature_plan.md"],
     "constraints": {
       "max_tokens": 40000,
       "style": "technical"
     },
     "notes": "Design multi-day workflow dependency tracking system"
   }
   ```

3. **Code Authoring Task**
   ```json
   {
     "id": "2025-10-11T20:00:00Z-refactor-module",
     "type": "code_authoring",
     "priority": "normal",
     "inputs": ["src/module.py"],
     "deliverables": ["artifacts/claude/2025-10-11/patches/module_refactor.diff"],
     "constraints": {
       "max_tokens": 30000,
       "style": "production"
     },
     "notes": "Improve test coverage, reduce complexity"
   }
   ```

## Workflows

### Workflow 1: NightShift Generates → Claude Analyzes

1. **Queue NightShift export task:**
   ```bash
   cat >> queue/nightshift/inbox.jsonl <<'EOF'
   {"id":"2025-10-11T20:00:00Z-export-uap","task":"sherlock_export","args":{"topic":"UAP propulsion","out":"artifacts/nightshift/2025-10-11/sherlock/uap_packet.jsonl"},"priority":"normal"}
   EOF
   ```

2. **Run NightShift dispatcher:**
   ```bash
   bash scripts/nightshift_dispatcher.sh
   ```

3. **Queue Claude analysis task:**
   ```bash
   cat >> queue/claude/2025-10-11.jsonl <<'EOF'
   {"id":"2025-10-11T21:00:00Z-analyze-uap","type":"analysis","priority":"high","inputs":["artifacts/nightshift/2025-10-11/sherlock/uap_packet.jsonl"],"deliverables":["artifacts/claude/2025-10-11/reports/uap_analysis.md"],"constraints":{"max_tokens":60000,"style":"concise","citations":true},"notes":"Identify breakthrough technologies and key researchers"}
   EOF
   ```

4. **Claude processes task** (manual or automated via Claude Code)

5. **Mark task complete:**
   ```bash
   python3 scripts/claude_task_complete.py \
     --task-id "2025-10-11T21:00:00Z-analyze-uap" \
     --task-type "analysis" \
     --status "completed" \
     --deliverables "artifacts/claude/2025-10-11/reports/uap_analysis.md" \
     --notes "Analysis complete: identified 5 key technologies and 12 researchers"
   ```

### Workflow 2: Claude Creates → NightShift Executes

1. **Queue Claude code authoring task:**
   ```bash
   cat >> queue/claude/2025-10-11.jsonl <<'EOF'
   {"id":"2025-10-11T22:00:00Z-create-script","type":"code_authoring","priority":"normal","inputs":["requirements.md"],"deliverables":["artifacts/claude/2025-10-11/patches/new_script.py"],"constraints":{"max_tokens":30000,"style":"production"},"notes":"Create automation script with comprehensive error handling"}
   EOF
   ```

2. **Claude processes task and creates script**

3. **Mark task complete with handoff:**
   ```bash
   cat > /tmp/handoff.json <<'EOF'
   {
     "id": "2025-10-11T23:00:00Z-test-script",
     "task": "llm_job",
     "args": {
       "job_spec": {
         "job_id": "test_new_script_20251011",
         "type": "validation",
         "class": "standard",
         "priority": 1,
         "description": "Test and validate new automation script",
         "inputs": [{"path": "artifacts/claude/2025-10-11/patches/new_script.py"}],
         "outputs": [{"kind": "markdown", "path": "artifacts/nightshift/2025-10-12/validation_report.md"}],
         "metadata": {}
       }
     },
     "priority": "normal"
   }
   EOF

   python3 scripts/claude_task_complete.py \
     --task-id "2025-10-11T22:00:00Z-create-script" \
     --task-type "code_authoring" \
     --status "completed" \
     --deliverables "artifacts/claude/2025-10-11/patches/new_script.py" \
     --notes "Script created, queued for NightShift validation" \
     --handoff /tmp/handoff.json
   ```

4. **Run NightShift dispatcher to execute validation:**
   ```bash
   bash scripts/nightshift_dispatcher.sh
   ```

## Utility Scripts

### Git Sync
Sync all repositories from manifest:
```bash
bash scripts/git_sync.sh
# or with custom manifest:
bash scripts/git_sync.sh path/to/repos.json
```

### Safe Backup
Create timestamped backup:
```bash
bash scripts/safe_backup.sh
# or with custom source/dest:
bash scripts/safe_backup.sh /path/to/source /path/to/dest_base
```

## File Locations

```
Johny5Alive/
├── queue/
│   ├── nightshift/
│   │   ├── inbox.jsonl          # Active NightShift tasks
│   │   └── archive/             # Processed tasks
│   └── claude/
│       ├── YYYY-MM-DD.jsonl     # Claude tasks by date
│       └── archive/             # Completed tasks
├── artifacts/
│   ├── nightshift/
│   │   └── YYYY-MM-DD/
│   │       ├── squirt/          # Batch documents
│   │       ├── sherlock/        # Topic packets
│   │       └── backups/         # Backup artifacts
│   └── claude/
│       └── YYYY-MM-DD/
│           ├── reports/         # Analysis reports
│           ├── patches/         # Code patches
│           └── SUMMARY.md       # Daily summary
├── scripts/
│   ├── nightshift_dispatcher.sh           # NightShift queue processor
│   ├── claude_queue_processor.py          # Claude queue reader
│   ├── claude_task_complete.py            # Claude task completion helper
│   ├── git_sync.sh                        # Git repository sync
│   └── safe_backup.sh                     # Safe backup utility
└── src/
    └── qwen_task_router.py                # NightShift task router
```

## Safety Rules

### NightShift Safety
- **Whitelisted Operations Only**: Only approved task types are executed
- **No Destructive Commands**: No force operations, hard resets, or irreversible actions
- **Input Validation**: All paths and arguments are validated and quoted with `shlex.quote()`
- **Logging**: All operations are logged with full command output

### Claude Safety
- **No Direct Execution**: Claude never executes commands - only writes files/patches
- **Review Required**: All outputs written for human or NightShift review before application
- **Hand-off Pattern**: Execution tasks are queued for NightShift, not executed directly
- **Constraint Adherence**: Token limits and style requirements are strictly followed

## Troubleshooting

### NightShift Queue Not Processing
```bash
# Check inbox exists and has tasks
cat queue/nightshift/inbox.jsonl

# Verify dispatcher is executable
chmod +x scripts/nightshift_dispatcher.sh

# Run dispatcher with debug output
bash -x scripts/nightshift_dispatcher.sh
```

### Claude Queue Not Showing Tasks
```bash
# Check queue directory exists
ls -la queue/claude/

# Verify task files exist
ls -la queue/claude/*.jsonl

# Test queue reader
python3 scripts/claude_queue_processor.py --json
```

### Tasks Not Archiving
```bash
# Check archive directories exist
mkdir -p queue/nightshift/archive
mkdir -p queue/claude/archive

# Verify permissions
chmod 755 queue/nightshift/archive
chmod 755 queue/claude/archive
```

### Handoff Tasks Not Appearing in NightShift Queue
```bash
# Verify inbox exists
touch queue/nightshift/inbox.jsonl

# Check permissions
chmod 644 queue/nightshift/inbox.jsonl

# Verify handoff JSON is valid
cat /tmp/handoff.json | python3 -m json.tool
```

## Best Practices

1. **Task IDs**: Use ISO timestamps + descriptive slug: `2025-10-11T20:00:00Z-task-name`
2. **Priorities**: Reserve `high` for critical tasks, use `normal` for most work
3. **Deliverables**: Always specify exact file paths, create directories in advance
4. **Notes**: Include context for future reference and debugging
5. **Testing**: Test new task types in isolation before queuing multiple tasks
6. **Monitoring**: Check `SUMMARY.md` and archive directories regularly
7. **Cleanup**: Archive old task files periodically to prevent clutter

## Integration with Existing Systems

### J5A Night Shift (Ollama/Qwen)
The existing `j5a-nightshift/` system continues to work alongside the new queue:
- LLM-based jobs can be queued via `llm_job` task type
- Jobs are written to `j5a-nightshift/ops/queue/nightshift_jobs.json`
- Processed by existing `process_nightshift_queue.py`

### Squirt (Document Generation)
- Batch document generation via `squirt_batch` task type
- CSV manifests define job_type, input, style, output
- Outputs written to `artifacts/nightshift/YYYY-MM-DD/squirt/`

### Sherlock (Intelligence Analysis)
- **Topic Export**: Regex-based evidence extraction via `sherlock_export` task type
- **Content Collection**: Automated web scraping/downloading via `sherlock_content_collection`
- **Research Execution**: Full Claude API-driven analysis via `sherlock_research_execution`
- **Targeting Officer**: Automated package generation from target library (39 targets)
- **Validation**: V1 (execution) + V2 (output conformance) quality gates

**Package Types**:
- YOUTUBE: Video/podcast transcription & analysis → NightShift queue
- DOCUMENT: Book/PDF processing & extraction → NightShift queue
- COMPOSITE: Multi-source intelligence synthesis → Claude queue

**See Also**: `SHERLOCK_QUEUE_INTEGRATION.md` for complete integration guide

---

**Last Updated**: 2025-10-11
**Version**: 1.0 (Full Integration)
