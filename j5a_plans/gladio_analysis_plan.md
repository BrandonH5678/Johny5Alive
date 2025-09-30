# Operation Gladio Intelligence Analysis - Implementation Plan

**Project:** Sherlock Operation Gladio Database Population
**Priority:** NORMAL (background processing)
**Risk Level:** LOW (read-only analysis of existing transcript)
**Created:** 2025-09-30

## Problem Statement

**Current State:**
Operation Gladio transcription complete (590,690 characters, 96,247 words) but evidence database is empty. The transcript contains rich intelligence data about historical events, people, organizations, and networks that needs to be extracted and structured for analysis.

**Challenge:**
Need to process large transcript (590KB) with minimal RAM/token usage to run in background while higher-priority Squirt and Sherlock print media work proceeds.

## Design Principle: Incremental Low-Memory Analysis

**Core Principle:**
> Process large intelligence documents incrementally in small batches, saving results after each batch to minimize memory usage and enable background processing without interfering with foreground tasks.

### Resource Constraints

**Memory Budget:**
- Maximum RAM per chunk: 150MB (leaves 2.25GB for other work)
- Process transcript in ~50 line batches (small enough for efficient processing)
- Incremental saves prevent memory accumulation

**Token Budget:**
- Maximum per session: 20,000 tokens (conservative for background work)
- Process ~10-15 entity batches per session
- Multi-session strategy spreads work across multiple overnight runs

**Processing Strategy:**
- Priority: BACKGROUND (yields to Squirt/Sherlock foreground work)
- Checkpoint-based (can pause/resume at any time)
- No blocking - errors don't halt pipeline

## Three-Phase Architecture

### Phase 2: Entity Extraction (Background Processing)

**Input:** `operation_gladio_transcript.txt` (590KB)
**Output:** Populated `people` and `organizations` tables
**Strategy:** Batch processing with checkpoints

**Approach:**
1. Split transcript into ~12 batches (~50 lines each)
2. Process each batch:
   - Extract people mentions (names, roles, dates)
   - Extract organization mentions (CIA, P2, Vatican Bank, etc.)
   - Create preliminary dossiers
3. Save after each batch (incremental checkpoint pattern)
4. Deduplicate and merge at end

**Memory Profile:**
- Per batch: ~100MB (text + model inference)
- Checkpoint files: ~50KB per batch
- Total storage: ~5MB for all entity data

**Time Estimate:** 3-4 hours spread across multiple sessions

---

### Phase 3: Relationship Mapping (Background Processing)

**Input:** Populated `people` and `organizations` tables + transcript
**Output:** Populated `relationships` and `resource_flows` tables
**Strategy:** Graph construction with incremental saves

**Approach:**
1. Re-read transcript in batches
2. For each batch:
   - Identify co-occurrences of entities
   - Extract relationship descriptors ("worked with", "paid", "founded")
   - Extract resource flows (money, weapons, drugs)
3. Save relationships after each batch
4. Build network graph from saved relationships

**Memory Profile:**
- Per batch: ~100MB
- Relationship storage: ~10MB total
- Graph data structures: <50MB

**Time Estimate:** 2-3 hours spread across sessions

---

### Phase 4: Intelligence Analysis (Background Processing)

**Input:** Populated database + transcript
**Output:** Populated `timeline` and `evidence` tables + analysis reports
**Strategy:** Multi-pass analytical processing

**Approach:**
1. **Timeline Construction:**
   - Extract all temporal references
   - Build chronological event sequence
   - Cross-reference with entity database

2. **Evidence Correlation:**
   - Tag claims in transcript with confidence levels
   - Link to supporting/contradicting evidence
   - Generate evidence chains

3. **Pattern Analysis:**
   - Network centrality (key figures/orgs)
   - Resource flow patterns (follow the money)
   - Temporal clusters (coordinated events)

4. **Intelligence Reports:**
   - Summary dossiers (top 20 people/orgs)
   - Network visualizations (GraphViz output)
   - Key findings report

**Memory Profile:**
- Per analysis: ~150MB
- Report generation: ~50MB
- Total outputs: ~15MB

**Time Estimate:** 2-3 hours

---

## Implementation Tasks

### Phase 2 Tasks (Entity Extraction)

**Task 2.1: Create BatchEntityExtractor**
- Input: Transcript, batch_size, checkpoint_dir
- Output: Incremental entity files
- Features: Resume capability, deduplication, merge

**Task 2.2: Create EntityDossierBuilder**
- Input: Raw entity mentions
- Output: Structured dossiers (JSON)
- Features: Consolidate multiple mentions, confidence scoring

**Task 2.3: Database Population Script**
- Input: Entity dossiers
- Output: Populated `people` and `organizations` tables
- Features: Atomic inserts, duplicate detection

**Task 2.4: Entity Extraction Validation**
- Input: Populated database
- Output: Quality report
- Features: Completeness check, accuracy sampling

---

### Phase 3 Tasks (Relationship Mapping)

**Task 3.1: Create RelationshipExtractor**
- Input: Transcript batches + entity database
- Output: Relationship records
- Features: Co-occurrence analysis, relationship typing

**Task 3.2: Create ResourceFlowTracker**
- Input: Transcript batches
- Output: Resource flow records (money, drugs, arms)
- Features: Flow path extraction, quantity tracking

**Task 3.3: Network Graph Builder**
- Input: Relationships database
- Output: GraphML/DOT files for visualization
- Features: Centrality metrics, community detection

**Task 3.4: Relationship Validation**
- Input: Relationship database
- Output: Network quality report
- Features: Connection density, orphan detection

---

### Phase 4 Tasks (Intelligence Analysis)

**Task 4.1: Timeline Constructor**
- Input: Transcript + entity database
- Output: Populated `timeline` table
- Features: Temporal extraction, event sequencing

**Task 4.2: Evidence Correlator**
- Input: Full database + transcript
- Output: Populated `evidence` table
- Features: Claim extraction, confidence assessment

**Task 4.3: Pattern Analyzer**
- Input: Complete database
- Output: Analysis reports
- Features: Network analysis, resource flow patterns

**Task 4.4: Intelligence Report Generator**
- Input: Complete database
- Output: Summary reports (MD/JSON)
- Features: Top entities, key findings, visualizations

---

## Resource Management Strategy

### Background Processing Protocol

**Priority Levels:**
1. **FOREGROUND**: Squirt voice processing, Sherlock print media (PRIORITY)
2. **BACKGROUND**: Gladio analysis (YIELDS to foreground)

**Yielding Strategy:**
- Check for foreground work every 5 minutes
- If foreground work detected: save checkpoint, exit gracefully
- Resume from checkpoint in next available slot

**J5A Integration:**
- Queue all tasks with `priority=BACKGROUND`
- Set `max_concurrent=1` (one Gladio task at a time)
- Set `yield_to=["squirt_voice", "sherlock_print"]`

### Checkpoint Pattern Implementation

**All tasks use TranscriptCheckpointManager pattern:**
```python
checkpoint_mgr = CheckpointManager("gladio_phase2_checkpoints")
completed = checkpoint_mgr.get_completed_chunks()

for batch_id in range(total_batches):
    if batch_id in completed:
        continue  # Skip already processed

    result = process_batch(batch_id)
    checkpoint_mgr.save_chunk(batch_id, result)
    checkpoint_mgr.update_manifest(batch_id)
```

**Benefits:**
- Crash recovery (resume from last checkpoint)
- Incremental progress (visible to user)
- Low memory (no accumulation)
- Interruptible (can pause for higher priority work)

---

## Estimated Resources

### Per Phase

| Phase | RAM (peak) | Tokens/session | Sessions | Total Time |
|-------|-----------|---------------|----------|------------|
| Phase 2 | 150MB | 15,000 | 3-4 | 3-4 hours |
| Phase 3 | 150MB | 12,000 | 2-3 | 2-3 hours |
| Phase 4 | 150MB | 18,000 | 2-3 | 2-3 hours |
| **Total** | **150MB** | **45,000** | **8-10** | **8-10 hours** |

### Disk Usage

- Checkpoints: ~10MB (temporary, cleaned after completion)
- Database: ~20MB (final populated state)
- Reports: ~5MB (visualizations, summaries)
- **Total:** ~35MB permanent, ~45MB peak

---

## Success Criteria

### Phase 2 Success
- ✅ At least 50 people extracted with dossiers
- ✅ At least 30 organizations extracted with profiles
- ✅ 80%+ named entities captured (sampling validation)
- ✅ All checkpoint saves successful

### Phase 3 Success
- ✅ At least 100 relationships mapped
- ✅ At least 20 resource flows documented
- ✅ Network graph generated with >50 nodes
- ✅ All relationship types represented

### Phase 4 Success
- ✅ Timeline with 50+ dated events
- ✅ Evidence table with confidence ratings
- ✅ Analysis reports generated (top entities, key findings)
- ✅ Network visualizations exported

---

## Rollback Plan

**Per-Phase Rollback:**
- Phase 2: Delete entity tables, keep transcript
- Phase 3: Delete relationship tables, keep entities
- Phase 4: Delete timeline/evidence, keep core database

**Full Rollback:**
```bash
# Restore empty database schema
rm gladio_intelligence.db
python3 evidence_schema_gladio.py --init-schema
```

**Checkpoint Recovery:**
- All checkpoints preserved in `gladio_checkpoints/`
- Can reconstruct any phase from checkpoint files
- Resume from last known good state

---

## Benefits

### Immediate
- ✅ Low-memory background processing (150MB max)
- ✅ Non-blocking for priority work
- ✅ Incremental progress (visible checkpoints)
- ✅ Crash-resistant (resume from checkpoints)

### Long-term
- ✅ Reusable pattern for other audiobooks
- ✅ Queryable intelligence database
- ✅ Network visualization capabilities
- ✅ Foundation for cross-document analysis

---

**Status:** Ready for J5A task generation
**Next Action:** Create J5A work assignments for all 12 tasks
**Dependencies:** Transcript complete ✅, Database schema exists ✅
