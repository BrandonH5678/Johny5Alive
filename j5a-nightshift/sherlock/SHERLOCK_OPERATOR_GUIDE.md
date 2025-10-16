# Sherlock Operator Guide

**Version:** 1.0
**Date:** 2025-10-15
**Constitutional Authority:** J5A_CONSTITUTION.md
**Strategic Framework:** J5A_STRATEGIC_AI_PRINCIPLES.md

---

## Overview

Sherlock is the intelligence analysis and research processing system within the J5A ecosystem. It specializes in long-form audio processing, document analysis, and evidence correlation.

## Core Capabilities

### Audio Processing
- Long-form podcast transcription (faster-whisper)
- Multi-speaker diarization (resemblyzer)
- Chunked processing for memory efficiency
- Incremental checkpoint saving

### Document Analysis
- PDF processing and text extraction
- Entity extraction and timeline construction
- Evidence correlation across sources
- Structured research output generation

### Integration Points
- **J5A Queue Manager:** Task coordination and scheduling
- **Squirt:** Shared voice processing infrastructure
- **Constitutional Framework:** All operations governed by J5A principles

## Operating Procedures

### 1. Audio Processing Operations

**For Long-Form Audio (>15 minutes):**

```bash
# Automatic chunking and processing
cd /home/johnny5/Sherlock
./process_audio.sh <audio_file>
```

**Constitutional Compliance:**
- Principle 3: Incremental saves prevent data loss
- Principle 4: Resource gates enforce memory/thermal limits
- Principle 7: Autonomous workflows support overnight processing

### 2. Evidence Processing

**For Research Documents:**

```bash
# Process and analyze documents
python3 process_document.py <document_path> --extract-entities
```

**Strategic Principle Integration:**
- Principle 1: Executes analysis, not just planning
- Principle 4: Persistent knowledge storage
- Principle 8: Full audit trail and governance logging

### 3. Night Shift Operations

Sherlock integrates with J5A's overnight queue system:

```bash
# Queue research task for overnight processing
python3 queue_research_task.py --task <task_definition.json>
```

**Key Features:**
- Unattended operation with safety gates
- Automatic model selection (faster-whisper vs large-v3)
- Checkpoint-based recovery
- Morning summary reports

## Principle Integration

### Constitutional Principles

**Human Agency (Principle 1)**
- All significant operations require approval or pre-approval
- Easy pause/resume controls
- Human validation of outputs

**Transparency (Principle 2)**
- Complete logging of all processing steps
- Audit trails for decision points
- Source attribution for all extracted information

**System Viability (Principle 3)**
- Graceful handling of errors
- Incremental saves for long processes
- Priority: Completion over speed

**Resource Stewardship (Principle 4)**
- Memory-aware model selection
- Thermal monitoring and protection
- Efficient use of local vs API resources

### Strategic Principles

**Tool-Augmented Reasoning (Principle 1)**
- Sherlock executes analysis, not just describes it
- Automated entity extraction and correlation
- Direct interaction with evidence sources

**Agent Orchestration (Principle 2)**
- Specialized agents for retrieval, processing, analysis
- Clear role boundaries and output contracts
- Coordinated workflows across subsystems

**Active Memory (Principle 4)**
- Persistent evidence database
- Cross-session knowledge retention
- Entity and timeline tracking

**Autonomous Workflows (Principle 7)**
- Night Shift processing for research tasks
- Queue-based task management
- Checkpoint recovery for interrupted work

## Common Operations

### Processing a Podcast Episode

```bash
# 1. Download audio
youtube-dl <url> -o episode.mp3

# 2. Process with Sherlock
./process_audio.sh episode.mp3 --model faster-whisper-small --diarization

# 3. Review output
cat episode_summary.md
```

### Research Document Analysis

```bash
# Extract entities and timeline
python3 analyze_document.py <document.pdf> --output analysis.json

# Generate research summary
python3 generate_summary.py analysis.json --output summary.md
```

### Overnight Queue Management

```bash
# Add research task to queue
python3 queue_task.py --type audio --source <url> --priority high

# Check queue status
python3 queue_status.py

# Review morning results
cat ~/Sherlock/artifacts/nightshift/$(date +%Y-%m-%d)/summary.md
```

## Troubleshooting

### Audio Processing Issues

**Symptom:** System freeze during transcription
**Cause:** Memory exhaustion with large-v3 model
**Solution:** Use faster-whisper-small (proven 1.63 min/min speed)

**Symptom:** Incomplete transcripts after crash
**Cause:** Missing incremental saves
**Solution:** Verify chunking enabled (automatic for audio >15 min)

### Resource Constraints

**Memory Limit:** 14GB safe threshold
- Use faster-whisper-small for long audio
- Enable chunking for files >15 minutes
- Monitor with resource safety gates

**Thermal Limit:** 80°C maximum
- Operations pause if exceeded
- Allow cooldown before resuming

## Integration with J5A

Sherlock operates as a specialized subsystem within J5A:

```
J5A (Coordinator)
  ↓
Night Shift Queue
  ↓
Sherlock Worker
  ↓
[Audio Processing] → [Analysis] → [Output]
  ↓
Results to artifacts/
```

All Sherlock operations:
- Respect J5A resource limits
- Log to J5A audit trails
- Follow constitutional principles
- Integrate with cross-system coordination

## Best Practices

1. **Always use incremental saves** for processes >1 hour
2. **Validate inputs** before queueing overnight tasks
3. **Check resource availability** before heavy processing
4. **Review morning summaries** for overnight work
5. **Maintain audit trails** for research provenance

## Reference

- **Constitution:** `J5A_CONSTITUTION.md`
- **Strategic Principles:** `J5A_STRATEGIC_AI_PRINCIPLES.md`
- **Operator Manual:** `JOHNY5_AI_OPERATOR_MANUAL.md`
- **Operating Protocols:** `OPERATING_PROTOCOLS_HEAVY_PROCESSES.md`

---

**Document Status:** Autonomous Implementation - Phase 3
**Last Updated:** 2025-10-15
