# J5A Nightshift - Autonomous Local Operations Framework

**Status:** Phase 1 Implementation
**Hardware:** 2012 Mac Mini, 16GB RAM, Intel i5-3210M (4 cores), CPU-only
**Goal:** ≥85% autonomous overnight task completion with local 7B LLM models

---

## Overview

J5A Nightshift is the autonomous, offline (or semi-offline) operations subsystem of the J5A ecosystem. It coordinates overnight and background workloads for Sherlock (retrieval), Squirt (rendering), and J5A core orchestration using **scripts-first automation** backed by a **local LLM** (7B model).

### Design Philosophy

- **Scripts-first**: Deterministic, testable behavior via Python modules
- **Local-first**: 80-90% computation on local 7B models
- **Completion over quality**: System viability priority (85% complete > 95% crash)
- **Governance-focused**: Strong validation, audit trails, blocking gates
- **Thermal-aware**: Conservative operation for aging 2012 Mac Mini hardware

---

## Hardware Constraints

| Resource | Specification | Safe Limit | Notes |
|----------|---------------|------------|-------|
| **RAM** | 16GB total | 12GB safe threshold | 4GB system/OS buffer |
| **CPU** | Intel i5-3210M @ 2.50GHz | 80°C thermal limit | 4 cores, no GPU |
| **LLM Model** | qwen2.5:7b-instruct-q4_K_M | ~6GB RAM @ inference | 4096 context, 600 output tokens |
| **Business Hours** | Mon-Fri 6am-7pm | LibreOffice priority | Squirt has absolute priority |

**Model Capabilities (7B Q4_K_M on CPU):**
- Inference speed: ~10-20 tokens/sec (CPU-only)
- Context window: 4096 tokens (~3000 words)
- Memory footprint: ~4.5GB model + ~2GB context = ~6GB peak
- Suitable for: Summarization, simple code, format conversion

---

## Directory Structure

```
/j5a-nightshift/
├── ops/
│   ├── inbox/          # New jobs, inputs (READ-ONLY after queuing)
│   ├── processed/      # Normalized text, chunks (WRITABLE)
│   ├── outputs/        # Rendered results (WRITABLE)
│   ├── logs/           # Execution logs (APPEND-ONLY)
│   ├── schemas/        # JSON/YAML schemas (READ-ONLY)
│   ├── templates/      # Jinja2 templates (READ-ONLY)
│   ├── validators/     # Validation scripts (READ-ONLY)
│   └── viz/            # Diagrams & specs (WRITABLE)
│
├── contracts/          # LLM prompt contracts
│   ├── summary_contract.txt
│   └── code_stub_contract.txt
│
├── models/             # Model storage (if local)
├── rules.yaml          # Phase 1 configuration
├── llm_gateway.py      # Unified LLM interface
├── sherlock_ingest.py  # Content normalization
├── sherlock_chunk.py   # Text splitting/scoring
├── summarize_local.py  # LLM-based summarization
├── j5a_worker.py       # Main orchestrator (TODO)
└── README.md           # This file
```

---

## Phase Progression

| Phase | LLM Strategy | API Usage | Target Success | Status |
|-------|--------------|-----------|----------------|--------|
| **Phase 1** | Local 7B models only | None (`api.enabled: false`) | ≥85% autonomous | ✅ In Progress |
| **Phase 2** | Local first → API fallback | Limited (5 jobs/day, 60K tokens/job) | ≥95% coverage | Future |
| **Phase 3** | Adaptive routing | On-demand with learning | Continuous improvement | Aspirational |

---

## Components Implemented

### Core Infrastructure ✅

- [x] **Directory structure**: ops/{inbox,processed,outputs,logs,schemas,templates,validators,viz}
- [x] **Configuration**: `rules.yaml` with Phase 1 settings (local-only, 16GB RAM constraints)
- [x] **LLM Gateway**: `llm_gateway.py` - Unified interface for local/remote/API modes
- [x] **Prompt Contracts**: `summary_contract.txt`, `code_stub_contract.txt`

### Sherlock Components ✅

- [x] **Content Ingestion**: `sherlock_ingest.py` - Normalize files/URLs to UTF-8 text
- [x] **Text Chunking**: `sherlock_chunk.py` - Split text with scoring, generate `excerpts.json`
- [x] **Summarization**: `summarize_local.py` - Evidence-based synthesis with citation validation

### Squirt Components ⏳

- [ ] **Template Rendering**: `squirt_render.py` - Jinja2 + pandoc conversion (TODO)

### Validation Framework ⏳

- [ ] **Code Validator**: ruff + mypy + pytest (100% pass requirement) (TODO)
- [ ] **Summaries Validator**: ≥3 excerpt citations or INSUFFICIENT_EVIDENCE (TODO)
- [ ] **Docs Validator**: pandoc build check (TODO)
- [ ] **Viz Validator**: graphviz SVG hash comparison (TODO)

### Orchestration ⏳

- [ ] **Worker**: `j5a_worker.py` - Main processing loop, queue integration (TODO)
- [ ] **Queue Integration**: Connect to existing `j5a_queue_manager.db` (TODO)
- [ ] **Job Routing**: Standard vs demanding classification (TODO)

---

## Installation & Setup

### 1. Install Ollama + Model

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull 7B model (4.7GB download, ~2-3 minutes)
ollama pull qwen2.5:7b-instruct-q4_K_M

# Start Ollama server
ollama serve &

# Verify
ollama list
# Should show: qwen2.5:7b-instruct-q4_K_M
```

### 2. Python Dependencies

```bash
# Already installed:
pip3 install jinja2 pyyaml pytest ruff mypy --break-system-packages

# For web scraping (optional):
pip3 install beautifulsoup4 requests --break-system-packages

# For PDF processing (optional):
pip3 install pdfplumber --break-system-packages
```

### 3. Test LLM Gateway

```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift

# Test local Ollama connection
python3 llm_gateway.py
```

**Expected output:**
```
INFO:LLM Gateway initialized in local mode
INFO:LLM completion: 450 in, 120 out
============================================================
LLM RESPONSE:
============================================================
- Python is a "high-level programming language" (source: intro.txt)
- It emphasizes "code readability with significant whitespace" (source: intro.txt)
- ...
============================================================
```

### 4. Test End-to-End Pipeline

```bash
# Test Sherlock ingestion
python3 sherlock_ingest.py

# Test chunking
python3 sherlock_chunk.py

# Test summarization
python3 summarize_local.py --test
```

---

## Configuration (`rules.yaml`)

### Key Settings (Phase 1)

```yaml
phase: 1
llm:
  default_mode: local
  local_endpoint: "http://localhost:11434"
  model: "qwen2.5:7b-instruct-q4_K_M"
  max_context: 4096
  max_output: 600

resources:
  max_ram_mb: 12288  # 12GB safe limit
  thermal_limit_celsius: 80
  max_processing_time_minutes: 30

api:
  enabled: false  # Phase 1: strict local-only
```

### Job Classification

**Standard Jobs (Local LLM):**
- Text summarization (<3000 words)
- Simple code stubs (<40 lines, stdlib only)
- Template rendering
- Format conversion

**Demanding Jobs (Park for Phase 2):**
- Complex code generation (>100 lines)
- Multi-document synthesis (>10K words)
- Advanced reasoning tasks

---

## Usage Examples

### Summarization Job

```python
from sherlock_ingest import ingest
from sherlock_chunk import chunk
from summarize_local import summarize, LLMMode

# 1. Ingest content
txt_path = ingest("input_document.pdf")

# 2. Chunk and score
chunks_path = chunk(txt_path)

# 3. Generate summary
summary_path = summarize(chunks_path, mode=LLMMode.LOCAL)

print(f"Summary: {summary_path}")
```

### Code Generation Job (Future)

```python
# TODO: Implement once validators and worker are complete
```

---

## Validation & Testing

### Validation Gates (Blocking)

| Validator | Success Criteria | Action on Failure |
|-----------|------------------|-------------------|
| **Code** | ruff + mypy + pytest 100% pass | Block output |
| **Docs** | pandoc successful build | Block output |
| **Viz** | SVG hash matches golden | Block output |
| **Summaries** | ≥3 excerpts cited OR "INSUFFICIENT_EVIDENCE" | Block output |

### Test Jobs

```bash
# Create test job in ops/inbox/
echo "Python is a programming language." > ops/inbox/test.txt

# Process manually
python3 sherlock_ingest.py ops/inbox/test.txt
python3 sherlock_chunk.py ops/processed/test.txt
python3 summarize_local.py ops/processed/test_chunks.json
```

---

## Monitoring

### Logs

```bash
# Worker logs
tail -f ops/logs/worker.log

# Ollama logs
journalctl -u ollama -f
```

### Queue Status

```bash
# Query J5A queue database
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/johnny5/Johny5Alive/j5a_queue_manager.db')
print(conn.execute('SELECT status, COUNT(*) FROM task_executions GROUP BY status').fetchall())
"
```

### System Resources

```bash
# RAM usage
free -h

# CPU temperature
sensors | grep "Package id 0"

# Ollama status
curl http://localhost:11434/api/version
```

---

## Thermal Safety Protocols

**CRITICAL for 2012 Mac Mini:**

```bash
# Check temperature before intensive operations
sensors | grep "Package id 0"

# Safe: <75°C - All operations allowed
# Warning: 75-80°C - Monitor closely
# Critical: >80°C - Defer jobs until cooled
```

**Automatic Throttling:**
- Worker checks thermal status every 60 seconds
- Operations pause if CPU >80°C
- Emergency shutdown if CPU >90°C

---

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not, start it
ollama serve &
```

### Model Not Found

```bash
# List installed models
ollama list

# Pull model if missing
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### Out of Memory

```bash
# Check RAM usage
free -h

# If >12GB used, wait or reduce chunk size:
# Edit sherlock_chunk.py: chunk_size = 1000 (instead of 1500)
```

### Thermal Throttling

```bash
# Check CPU temp
sensors

# If >80°C:
# - Stop Ollama: pkill ollama
# - Cool down system (5-10 minutes)
# - Improve ventilation
# - Restart: ollama serve &
```

---

## Next Steps (TODO)

### Short-term (1-2 days)

1. [x] Model download completion
2. [ ] Test llm_gateway with real Ollama
3. [ ] Implement validators (code, summaries)
4. [ ] Implement j5a_worker.py orchestrator
5. [ ] Integration with existing j5a_queue_manager.db

### Medium-term (1 week)

1. [ ] Squirt rendering module (squirt_render.py)
2. [ ] Job classification logic (standard vs demanding)
3. [ ] Systemd timer for 7pm daily execution
4. [ ] Production testing with 10+ jobs

### Long-term (Phase 2)

1. [ ] API escalation for demanding jobs
2. [ ] Adaptive routing based on success metrics
3. [ ] Continuous learning from failures

---

## Performance Targets (Phase 1)

| Metric | Target | Current |
|--------|--------|---------|
| **Success Rate** | ≥85% jobs complete without API | TBD |
| **Thermal Safety** | 0 emergencies (>80°C) | TBD |
| **OOM Crashes** | 0 crashes | TBD |
| **Validator Pass Rate** | ≥80% | TBD |
| **Avg Processing Time** | <30 min/job | TBD |

**Measurement Window:** 30 days continuous operation, ≥100 jobs

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    J5A NIGHTSHIFT PIPELINE                  │
└─────────────────────────────────────────────────────────────┘

INPUT (ops/inbox/)
   │
   ├─► sherlock_ingest.py ──► ops/processed/*.txt
   │                               │
   │                               ▼
   ├─► sherlock_chunk.py ───► ops/processed/*_chunks.json
   │                               │
   │                               ▼
   ├─► llm_gateway.py ────────┐   │
   │   (LOCAL MODE)            │   │
   │   ├─ Ollama              │   │
   │   │  qwen2.5:7b          │   │
   │   │  localhost:11434     │   │
   │   └─► summarize_local.py ├───┘
   │                          │
   │                          ▼
   └─► validators/ ──────► ops/outputs/*.md
       ├─ code (ruff/mypy/pytest)
       ├─ summaries (≥3 citations)
       ├─ docs (pandoc)
       └─ viz (graphviz)

MONITORING
   ├─► ops/logs/worker.log
   ├─► j5a_queue_manager.db (status tracking)
   └─► thermal_check.py (80°C limit enforcement)
```

---

## References

- **J5A Operator Manual**: `/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md`
- **Sherlock Documentation**: `/home/johnny5/Desktop/Sherlock/`
- **Squirt Documentation**: `/home/johnny5/Squirt/CLAUDE.md`
- **Hardware Specs**: 2012 Mac Mini, 16GB RAM, Intel i5-3210M

---

**Created:** 2025-10-07
**Version:** 1.0.0-alpha
**Phase:** 1 (Local-Only Operations)
