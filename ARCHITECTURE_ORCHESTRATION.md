# J5A Orchestration Split

**NightShift (Ollama/Qwen)**
- Scope: deterministic, shell/python tasks; no new code authoring.
- Examples: repo sync, data exports, Squirt batch runs, Sherlock packet exports, lint/format, backups.
- Inputs: `queue/nightshift/*.jsonl`
- Runner: `scripts/nightshift_dispatcher.sh` → `src/qwen_task_router.py`

**J5A Queue Manager (Claude Code)**
- Scope: reasoning-heavy or creative tasks: research, plan synthesis, new script creation/refactor, long-form docs.
- Inputs: `queue/claude/*.jsonl`
- Runner: Claude session reading `CLAUDE_QUEUE_INSTRUCTIONS.md`.

**Hand-off Pattern**
1. NightShift generates artifacts → `artifacts/nightshift/YYYY-MM-DD/`.
2. Claude reads artifacts + requirements from `queue/claude/*.jsonl`, produces outputs → `artifacts/claude/YYYY-MM-DD/`.
3. Optional: NightShift commits / tag snapshots.

**Safety**
- NightShift executes only whitelisted commands (no destructive ops).
- Claude never executes commands; it only writes files/patches for review or NightShift to apply.

**Queue System**
- NightShift queue: `queue/nightshift/inbox.jsonl` (JSONL format, one task per line)
- Claude queue: `queue/claude/*.jsonl` (JSONL files, processed by date)
- Schemas: `queue/schemas/*.schema.json`

**Task Types**

*NightShift:*
- `repo_sync`: Git operations (pull, push, sync across repos)
- `squirt_batch`: Batch document generation (invoices, contracts)
- `sherlock_export`: Topic-based evidence packet export
- `lint`: Code formatting and linting
- `backup`: Safe backup operations

*Claude:*
- `analysis`: Deep analysis of data, code, or documents
- `planning`: Strategic planning, architecture design
- `code_authoring`: New code creation, refactoring

**Artifact Organization**
```
artifacts/
├── nightshift/
│   └── YYYY-MM-DD/
│       ├── squirt/          # Batch document outputs
│       ├── sherlock/        # Topic packets
│       └── backups/         # Backup artifacts
└── claude/
    └── YYYY-MM-DD/
        ├── patches/         # Code patches (*.diff)
        ├── reports/         # Analysis reports
        └── SUMMARY.md       # Task completion summary
```

**Integration Points**
- Squirt: `integrations/squirt_cli.py` (batch processing)
- Sherlock: `integrations/sherlock_export_topic.py` (topic extraction)
- Repos: `configs/repos.json` (repository definitions)

**Utility Scripts**
- `scripts/nightshift_dispatcher.sh`: Process NightShift queue
- `scripts/claude_queue_processor.py`: Read and display Claude tasks
- `scripts/claude_task_complete.py`: Mark Claude tasks complete and update SUMMARY.md
- `scripts/git_sync.sh`: Sync all repositories from manifest
- `scripts/safe_backup.sh`: Create timestamped backups with metadata

**Quick Start**

*Process NightShift Queue:*
```bash
bash scripts/nightshift_dispatcher.sh
```

*View Claude Queue:*
```bash
python3 scripts/claude_queue_processor.py
```

*Complete Claude Task:*
```bash
python3 scripts/claude_task_complete.py \
  --task-id "2025-10-11T18:00:00Z-task" \
  --task-type "analysis" \
  --status "completed" \
  --deliverables "artifacts/claude/2025-10-11/reports/output.md" \
  --notes "Task completed successfully"
```

**See Also**
- `QUEUE_SYSTEM_USAGE.md`: Comprehensive usage guide with examples
- `CLAUDE_QUEUE_INSTRUCTIONS.md`: Claude-specific task processing instructions
