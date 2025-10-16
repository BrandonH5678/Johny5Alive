# Sherlock → J5A Dual-Queue Integration

## Overview

Complete integration between Sherlock's targeting system and J5A's dual-queue architecture for automated research package execution.

**Status**: ✅ OPERATIONAL (as of 2025-10-11)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SHERLOCK TARGETING SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Target Library (39 targets) → Targeting Officer (Daily Sweep)  │
│                                                                   │
│  Creates Research Packages:                                      │
│    • YOUTUBE: Video/podcast transcription & analysis            │
│    • DOCUMENT: Book/PDF processing & extraction                 │
│    • COMPOSITE: Multi-source intelligence synthesis              │
│                                                                   │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    │ submit_package_to_j5a()
                    │ (Routes by package type)
                    │
        ┌───────────┴──────────┐
        │                      │
        ▼                      ▼
┌──────────────┐    ┌───────────────────┐
│  NIGHTSHIFT  │    │      CLAUDE       │
│    QUEUE     │    │       QUEUE       │
├──────────────┤    ├───────────────────┤
│              │    │                   │
│  YOUTUBE &   │    │    COMPOSITE      │
│  DOCUMENT    │    │    (Reasoning)    │
│  packages    │    │                   │
│              │    │                   │
│  inbox.jsonl │    │  YYYY-MM-DD.jsonl │
│              │    │                   │
└──────┬───────┘    └─────────┬─────────┘
       │                      │
       │ Dispatcher           │ Claude Code
       │                      │
       ▼                      ▼
┌──────────────┐    ┌───────────────────┐
│ qwen_task_   │    │  Claude processes │
│ router.py    │    │  research tasks   │
├──────────────┤    ├───────────────────┤
│              │    │                   │
│ sherlock_    │    │ • Read artifacts  │
│ content_     │    │ • Extract claims  │
│ collection   │    │ • Find entities   │
│              │    │ • Synthesize      │
│ (curl, wget) │    │   research        │
│              │    │                   │
└──────┬───────┘    └─────────┬─────────┘
       │                      │
       │ Saves artifacts      │ Saves reports
       │                      │
       ▼                      ▼
┌──────────────────────────────────────┐
│   artifacts/nightshift/YYYY-MM-DD/   │
│   artifacts/claude/YYYY-MM-DD/       │
├──────────────────────────────────────┤
│                                      │
│  Content, claims, entities, reports  │
│                                      │
└──────────────┬───────────────────────┘
               │
               │ sherlock_status_updater.py
               │
               ▼
┌──────────────────────────────────────┐
│      PACKAGE STATUS UPDATES          │
├──────────────────────────────────────┤
│                                      │
│  queued → running → completed →      │
│  validated (V1 → V2) → closed        │
│                                      │
└──────────────────────────────────────┘
```

## End-to-End Workflow

### 1. Target Library & Targeting Officer

**Location**: `/home/johnny5/Sherlock/`

**Components**:
- `sherlock.db`: 39 research targets (people, orgs, operations, programs)
- `src/sherlock_targeting_officer.py`: Automated package generation
- `seed_targets.py`: Initial target library seeding

**Daily Sweep** (runs @ 1am via cron):
```bash
cd /home/johnny5/Sherlock
python3 src/sherlock_targeting_officer.py
```

**Manual trigger**:
```bash
cd /home/johnny5/Sherlock
python3 sherlock_targeting_cli.py officer run
```

### 2. Package Creation & Queue Routing

**Targeting Officer automatically**:
1. Scans all targets in library
2. Identifies targets without active packages
3. Creates research packages with:
   - Collection URLs (sources to scrape/download)
   - Expected outputs (deliverable files)
   - Package type (YOUTUBE, DOCUMENT, COMPOSITE)
4. Performs V0 validation (schema check)
5. Routes to appropriate queue:

**Routing Logic**:
```python
if package_type in [YOUTUBE, DOCUMENT]:
    # Deterministic content collection → NightShift
    queue: queue/nightshift/inbox.jsonl
    task: sherlock_content_collection

else:  # COMPOSITE
    # Reasoning-heavy research → Claude
    queue: queue/claude/YYYY-MM-DD.jsonl
    task: analysis (sherlock research)
```

### 3. NightShift Execution (YOUTUBE/DOCUMENT)

**Dispatcher**: `scripts/nightshift_dispatcher.sh`

**Task Handler**: `src/qwen_task_router.py::handle_sherlock_content_collection()`

**Process**:
1. Read task from `queue/nightshift/inbox.jsonl`
2. Download/scrape content from collection URLs
3. Save raw content to `artifacts/nightshift/YYYY-MM-DD/sherlock/content/`
4. Create manifest with collection metadata
5. Update package status: `queued` → `running` → `completed`

**Manual Execution**:
```bash
bash scripts/nightshift_dispatcher.sh
```

### 4. Claude Execution (COMPOSITE)

**Queue Reader**: `scripts/claude_queue_processor.py`

**Task Handler**: Manual (Claude Code reads and processes)

**Process**:
1. Claude reads task from `queue/claude/YYYY-MM-DD.jsonl`
2. Loads artifacts from NightShift (if applicable)
3. Performs research analysis:
   - Extract claims
   - Identify entities
   - Analyze relationships
   - Synthesize findings
4. Writes reports to `artifacts/claude/YYYY-MM-DD/reports/`
5. Updates SUMMARY.md
6. Updates package status via `sherlock_status_updater.py`

**Manual Execution**:
```bash
python3 scripts/claude_queue_processor.py
# Claude processes tasks interactively
```

### 5. Full Research Execution (Alternative)

**For packages requiring complete Claude API-driven analysis**:

**Task Handler**: `src/qwen_task_router.py::handle_sherlock_research_execution()`

**Executor**: `src/sherlock_research_executor.py`

**Process**:
1. Content collection (web scraping)
2. Text processing & chunking
3. Claim extraction via Claude API
4. Entity recognition via Claude API
5. Relationship analysis
6. Evidence card generation
7. Database storage in Sherlock's `evidence.db`

### 6. Package Status Updates

**Module**: `integrations/sherlock_status_updater.py`

**Package Lifecycle**:
```
draft → ready → queued → running → completed → validated → closed
                    ↓
                  failed
```

**Update Mechanisms**:
- Automatic: Task handlers call `update_package_status()`
- Manual: `python3 integrations/sherlock_status_updater.py --package-id <ID> --status <status>`

**Status Tracking**:
- Each status change logged in `metadata.status_history`
- Timestamps for audit trail
- Integration with validation system

### 7. Validation Pipeline

**Module**: `integrations/sherlock_validator.py`

**Validation Levels**:

**V0 (Schema Validation)** - Performed by Targeting Officer:
- Package has required fields
- Collection URLs present
- Expected outputs defined

**V1 (Execution Validation)** - After task completion:
```bash
python3 integrations/sherlock_validator.py --package-id <ID> --level v1
```
- Checks:
  - Package status is 'completed'
  - No execution errors
  - Outputs were generated
  - Normal status progression

**V2 (Output Conformance Validation)** - Quality check:
```bash
python3 integrations/sherlock_validator.py --package-id <ID> --level v2
```
- Checks:
  - Expected output files exist
  - Files are non-empty
  - JSON files are valid
  - Claims meet threshold (≥5)
  - Entities meet threshold (≥3)

**Full Validation**:
```bash
python3 integrations/sherlock_validator.py --package-id <ID> --level full
```
Runs V1, then V2 (if V1 passes), updates package to 'validated' status.

## Package Migration

**Migrate 35 existing packages from old queue format**:

**Dry Run** (preview changes):
```bash
python3 scripts/migrate_sherlock_packages.py --dry-run
```

**Execute Migration**:
```bash
python3 scripts/migrate_sherlock_packages.py --execute
```

**What it does**:
1. Finds all packages with status 'submitted' (old format)
2. Routes based on package type:
   - YOUTUBE/DOCUMENT → `queue/nightshift/inbox.jsonl`
   - COMPOSITE → `queue/claude/YYYY-MM-DD.jsonl`
3. Updates package status: `submitted` → `queued`
4. Archives old queue files to `queue/archive_old_format/`

## Testing & Verification

**Integration Test**:
```bash
bash scripts/test_sherlock_integration.sh
```

**Test Coverage**:
1. ✅ Sherlock database operational
2. ✅ Targeting Officer creates packages
3. ✅ Packages route to correct queue
4. ✅ NightShift processes content collection
5. ✅ Claude processes research tasks
6. ✅ Status updates work
7. ✅ Validation system operational

**Manual Testing**:

**Create test package**:
```bash
cd /home/johnny5/Sherlock
python3 sherlock_targeting_cli.py pkg create --target <target_id>
```

**Check queue status**:
```bash
# NightShift queue
cat queue/nightshift/inbox.jsonl | wc -l

# Claude queue
cat queue/claude/*.jsonl | wc -l
```

**Process packages**:
```bash
# NightShift
bash scripts/nightshift_dispatcher.sh

# Claude
python3 scripts/claude_queue_processor.py
```

**Validate results**:
```bash
python3 integrations/sherlock_validator.py --package-id <ID> --level full
```

## CLI Reference

### Targeting Officer Commands

```bash
# List all targets
python3 sherlock_targeting_cli.py target list

# Show target details
python3 sherlock_targeting_cli.py target show <id>

# List packages
python3 sherlock_targeting_cli.py pkg list

# Show package details
python3 sherlock_targeting_cli.py pkg show <id>

# Create package for target
python3 sherlock_targeting_cli.py pkg create --target <id>

# Run Targeting Officer sweep
python3 sherlock_targeting_cli.py officer run

# Show officer status
python3 sherlock_targeting_cli.py officer status
```

### Package Status Management

```bash
# Show package status
python3 integrations/sherlock_status_updater.py --package-id <ID> --show

# Update package status
python3 integrations/sherlock_status_updater.py --package-id <ID> --status <status>
```

### Validation

```bash
# V1 validation only
python3 integrations/sherlock_validator.py --package-id <ID> --level v1

# V2 validation only
python3 integrations/sherlock_validator.py --package-id <ID> --level v2

# Full validation (V1 + V2)
python3 integrations/sherlock_validator.py --package-id <ID> --level full

# Save validation report
python3 integrations/sherlock_validator.py --package-id <ID> --level full --save-report report.json
```

## File Locations

```
/home/johnny5/Sherlock/
├── sherlock.db                        # Target library & packages database
├── evidence.db                        # Research evidence storage
├── seed_targets.py                    # Initial target seeding
├── sherlock_targeting_cli.py          # CLI interface
├── src/
│   └── sherlock_targeting_officer.py  # Package generation engine
└── research_outputs/                  # Executor output directory

/home/johnny5/Johny5Alive/
├── queue/
│   ├── nightshift/
│   │   ├── inbox.jsonl                # NightShift task queue
│   │   └── archive/                   # Processed tasks
│   ├── claude/
│   │   ├── YYYY-MM-DD.jsonl           # Claude task queue
│   │   └── archive/                   # Completed tasks
│   └── archive_old_format/            # Migrated old queue files
├── artifacts/
│   ├── nightshift/YYYY-MM-DD/
│   │   └── sherlock/
│   │       └── content/               # Collected content
│   └── claude/YYYY-MM-DD/
│       └── reports/                   # Research reports
├── scripts/
│   ├── nightshift_dispatcher.sh       # NightShift queue processor
│   ├── claude_queue_processor.py      # Claude queue reader
│   ├── test_sherlock_integration.sh   # Integration test
│   └── migrate_sherlock_packages.py   # Package migration tool
├── src/
│   ├── qwen_task_router.py            # Task routing & execution
│   └── sherlock_research_executor.py  # Full research pipeline
└── integrations/
    ├── sherlock_status_updater.py     # Package status updates
    └── sherlock_validator.py          # V1/V2 validation
```

## Integration Points

### With J5A Dual-Queue System

**Package Type → Queue Mapping**:
- **YOUTUBE/DOCUMENT** → NightShift (deterministic collection)
- **COMPOSITE** → Claude (reasoning-heavy analysis)

**Status Feedback Loop**:
- Task completion triggers status update
- Validation results stored in package metadata
- History tracking for audit trail

### With Sherlock Evidence System

**Evidence Storage**:
- Claims → `evidence.db::evidence_claims` table
- Entities extracted and stored
- Relationships mapped
- Source tracking maintained

### With Claude API

**Research Executor** (`sherlock_research_executor.py`):
- Claim extraction: `claude-3-haiku-20240307`
- Entity recognition: `claude-3-haiku-20240307`
- Relationship analysis: `claude-3-haiku-20240307`
- Token usage tracking

## Troubleshooting

### Package stuck in 'submitted' status

**Cause**: Created with old queue format before migration

**Fix**:
```bash
python3 scripts/migrate_sherlock_packages.py --execute
```

### Package status not updating

**Cause**: Status updater import failing or database locked

**Check**:
```bash
python3 integrations/sherlock_status_updater.py --package-id <ID> --show
```

**Fix**:
```python
# Manually update in Sherlock database
cd /home/johnny5/Sherlock
sqlite3 sherlock.db "UPDATE targeting_packages SET status='<status>' WHERE package_id=<ID>;"
```

### Validation fails

**V1 Failure**: Task didn't complete successfully
- Check task execution logs
- Verify outputs were generated
- Review error messages in package metadata

**V2 Failure**: Outputs don't meet quality thresholds
- Check claims_extracted count (need ≥5)
- Check entities_found count (need ≥3)
- Verify output files exist and are non-empty

### NightShift queue not processing

**Check queue contents**:
```bash
cat queue/nightshift/inbox.jsonl
```

**Manually process**:
```bash
head -1 queue/nightshift/inbox.jsonl | python3 src/qwen_task_router.py
```

### Claude queue not visible

**Check queue files**:
```bash
ls -la queue/claude/
cat queue/claude/*.jsonl
```

**Read tasks**:
```bash
python3 scripts/claude_queue_processor.py
```

## Success Metrics

**Target Coverage**:
- 39 targets in library
- 35 packages migrated to new system
- Coverage: High-priority targets (priority 1-2) prioritized

**Queue Performance**:
- Package routing: 100% accurate (type-based routing working)
- Status updates: Automated feedback loop operational
- Validation: V0/V1/V2 pipeline complete

**Validation Thresholds**:
- V1 (Execution): Must pass 100% of checks
- V2 (Conformance): Must meet ≥80% quality threshold
- Claims: ≥5 per package
- Entities: ≥3 per package

## Future Enhancements

1. **Automated Scheduler**: Cron job for nightly Targeting Officer sweep
2. **Dependency Tracking**: Composite packages wait for constituent documents
3. **Thermal Awareness**: YOUTUBE packages deferred during high CPU periods
4. **Quality Scoring**: ML-based evidence quality assessment
5. **Cross-Package Analysis**: Identify connections across research targets

---

**Last Updated**: 2025-10-11
**Status**: Production Ready
**Version**: 1.0
