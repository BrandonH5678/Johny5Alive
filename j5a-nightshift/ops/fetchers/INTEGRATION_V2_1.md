# Retriever v2.1 — J5A Universe Integration

**Version:** 2.1
**Date:** 2025-10-14
**Status:** Integrated & Operational ✅

## Overview

Retriever v2.1 is now fully integrated across the J5A universe (Night Shift, Sherlock, Squirt, Jeeves), providing advanced multi-agent retrieval capabilities for:

- **Intelligence Discovery** - Multi-source intelligence gathering with OCR and structured extraction
- **Database Operations** - PostgreSQL, MySQL, MongoDB, SQLite queries
- **Web Scraping** - Selenium/Playwright browser automation
- **ML Inference** - sklearn/PyTorch/TensorFlow model execution
- **Multi-Agent Orchestration** - Complex multi-step retrieval workflows

---

## Architecture

### Integration Layers

```
┌─────────────────────────────────────────────────────────────┐
│              J5A Night Shift Orchestrator                    │
│                   (j5a_worker.py)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────┬──────────────┬──────────────┐
         │                      │              │              │
    ┌────▼─────┐         ┌─────▼──────┐  ┌───▼────┐   ┌─────▼────┐
    │ Sherlock │         │   Squirt   │  │ Jeeves │   │  Queue   │
    │ Intel    │         │  Document  │  │Personal│   │ Manager  │
    │ Analysis │         │ Automation │  │ Assist │   │          │
    └────┬─────┘         └─────┬──────┘  └───┬────┘   └─────┬────┘
         │                     │             │               │
         └────────────┬────────┴─────────────┴───────────────┘
                      │
            ┌─────────▼──────────┐
            │ J5A Retrieval      │
            │    Gateway         │
            │ (j5a_retrieval_    │
            │     gateway.py)    │
            └─────────┬──────────┘
                      │
      ┌───────────────┴───────────────┐
      │                               │
┌─────▼──────┐              ┌────────▼────────┐
│ v2 Core    │              │ v2.1 Extensions │
│ Agents     │              │                 │
│            │              │                 │
│ - API      │              │ - AgentChain    │
│ - Media    │              │ - PostgreSQL    │
│ - FS       │              │ - MySQL         │
│ - DB       │              │ - MongoDB       │
│ - OCR      │              │ - ML            │
│ - Index    │              │ - WebScraper    │
│ - NLP      │              │                 │
│ - Query    │              │                 │
│   Planner  │              │                 │
└────────────┘              └─────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `J5ARetrievalGateway` | `ops/fetchers/j5a_retrieval_gateway.py` | Unified retrieval interface for all systems |
| `SherlockRetrieval` | `sherlock_retrieval.py` | Enhanced Sherlock intelligence gathering |
| `J5AWorker` (enhanced) | `j5a_worker.py` | Night Shift orchestrator with v2.1 job types |
| Job Examples | `ops/queue/examples/v2_1_job_examples.json` | Template job definitions |

---

## Usage Patterns

### Pattern 1: Direct Gateway Access

```python
from j5a_retrieval_gateway import J5ARetrievalGateway

# Initialize gateway
gateway = J5ARetrievalGateway()

# Intelligent retrieval (auto-routes to appropriate agents)
result = gateway.retrieve("Find all PDF documents about UAP intelligence")

# Multi-step orchestration
result = gateway.retrieve_multi_step(
    "Discover intelligence sources, download documents, extract text with OCR"
)

# System-specific operations
podcast_result = gateway.nightshift_discover_podcast(
    home_url="https://podcast.example.com",
    prefer_epnum=91
)

db_result = gateway.sherlock_query_database(
    query="SELECT * FROM intelligence_reports WHERE topic = 'UAP'",
    database_type="sqlite"
)
```

### Pattern 2: Sherlock Intelligence Operations

```python
from sherlock_retrieval import SherlockRetrieval

# Initialize Sherlock retrieval
sherlock = SherlockRetrieval()

# Discover intelligence sources
discovery = sherlock.discover_intelligence_sources(
    topic="UAP government disclosure",
    source_types=["files", "databases", "web"],
    search_depth="comprehensive"
)

# Ingest with OCR and structured extraction
result = sherlock.ingest_with_intelligence(
    source="/path/to/scanned_document.pdf",
    extract_structured=True,
    use_ocr=True
)

# Query intelligence database
query_result = sherlock.query_intelligence_database(
    query="SELECT * FROM reports WHERE classification = 'UAP'",
    database_type="sqlite"
)

# Index and search intelligence
sherlock.index_intelligence(documents)
search_results = sherlock.search_intelligence("UAP sightings 2024")
```

### Pattern 3: Night Shift Job Processing

```python
from j5a_worker import J5AWorker

# Initialize worker
worker = J5AWorker()

# Process intelligence discovery job
job = {
    "job_id": "intel_001",
    "type": "intelligence_discovery",
    "class": "standard",
    "inputs": {
        "topic": "UAP intelligence reports",
        "source_types": ["files", "databases", "web"],
        "search_depth": "standard"
    }
}

result = worker.process_job(job)
# Returns: {'success': True, 'status': 'completed', 'outputs': [...]}

# Process ML inference job
ml_job = {
    "job_id": "ml_001",
    "type": "ml_inference",
    "class": "demanding",
    "inputs": {
        "model_path": "/models/sentiment_classifier.pkl",
        "input_data": [["Text to classify"]],
        "operation": "predict"
    }
}

result = worker.process_job(ml_job)
```

---

## New Job Types

### 1. Intelligence Discovery

Discover intelligence sources across multiple channels.

**Job Type:** `intelligence_discovery`

**Inputs:**
- `topic` (string): Intelligence topic to research
- `source_types` (array): Types to search `["files", "web", "databases", "apis"]`
- `search_depth` (string): `"quick"`, `"standard"`, or `"comprehensive"`

**Outputs:**
- JSON file with discovered sources and metadata

**Example:**
```json
{
  "job_id": "intel_001",
  "type": "intelligence_discovery",
  "inputs": {
    "topic": "UAP government disclosure 2024",
    "source_types": ["files", "databases", "web"],
    "search_depth": "comprehensive"
  }
}
```

### 2. Database Query

Query databases (SQLite, PostgreSQL, MySQL, MongoDB).

**Job Type:** `database_query`

**Inputs:**
- `query` (string): SQL/NoSQL query
- `database_type` (string): `"sqlite"`, `"postgresql"`, `"mysql"`, `"mongodb"`
- `database_path` (string): Path to database file (for SQLite)
- Additional database connection parameters

**Outputs:**
- JSON file with query results

**Example:**
```json
{
  "job_id": "db_001",
  "type": "database_query",
  "inputs": {
    "query": "SELECT * FROM intelligence_reports WHERE topic LIKE '%UAP%'",
    "database_type": "sqlite",
    "database_path": "/path/to/sherlock_intelligence.db"
  }
}
```

### 3. Web Scraping

Scrape dynamic web content with browser automation.

**Job Type:** `web_scraping`

**Inputs:**
- `url` (string): URL to scrape
- `backend` (string): `"selenium"` or `"playwright"`
- `headless` (boolean): Run in headless mode
- `selectors` (object): CSS selectors for data extraction
- `wait_for` (string): CSS selector to wait for
- `screenshot` (boolean): Capture screenshot

**Outputs:**
- JSON file with scraped data
- Optional screenshot PNG file

**Example:**
```json
{
  "job_id": "scrape_001",
  "type": "web_scraping",
  "inputs": {
    "url": "https://example.com/reports",
    "backend": "selenium",
    "headless": true,
    "selectors": {
      "title": "h1.page-title",
      "reports": ".report-item"
    },
    "screenshot": true
  }
}
```

### 4. ML Inference

Run machine learning model inference.

**Job Type:** `ml_inference`

**Inputs:**
- `model_path` (string): Path to ML model file
- `input_data` (array): Input data for inference
- `operation` (string): `"predict"`, `"predict_proba"`, or `"info"`
- `preprocess` (string): `"standardize"` or `"normalize"`
- `postprocess` (string): `"argmax"`, `"sigmoid"`, or `"softmax"`

**Outputs:**
- JSON file with predictions and model info

**Example:**
```json
{
  "job_id": "ml_001",
  "type": "ml_inference",
  "inputs": {
    "model_path": "/models/classifier.pkl",
    "input_data": [["Sample text for classification"]],
    "operation": "predict",
    "postprocess": "argmax"
  }
}
```

### 5. Multi-Source Retrieval

Intelligent multi-agent orchestration for complex retrieval tasks.

**Job Type:** `multi_source_retrieval`

**Inputs:**
- `query` (string): Natural language description of retrieval task
- Additional context parameters

**Outputs:**
- JSON file with aggregated results from multiple agents

**Example:**
```json
{
  "job_id": "multi_001",
  "type": "multi_source_retrieval",
  "inputs": {
    "query": "Find all UAP intelligence reports from government sources, extract key findings, and analyze sentiment",
    "sources": ["databases", "files", "web"],
    "depth": "comprehensive"
  }
}
```

---

## System-Specific Integration

### Sherlock Intelligence Analysis

**Enhanced Capabilities:**
- Multi-source intelligence discovery (files, web, databases, APIs)
- OCR for scanned documents (PDF, images)
- Structured data extraction from unstructured sources
- Intelligence indexing and full-text search
- Cross-source pattern analysis

**Usage:**
```python
from sherlock_retrieval import SherlockRetrieval

sherlock = SherlockRetrieval()

# Discover and ingest intelligence
discovery = sherlock.discover_intelligence_sources("UAP disclosure")
for source in discovery['sources']:
    sherlock.ingest_with_intelligence(source['path'], use_ocr=True)

# Query and search
results = sherlock.query_intelligence_database(
    "SELECT * FROM reports WHERE date > '2024-01-01'"
)
search = sherlock.search_intelligence("recent UAP sightings")
```

### Squirt Document Automation

**Enhanced Capabilities:**
- Template fetching from multiple sources (local, API, web)
- Voice memo processing (placeholder for Whisper integration)
- Document data extraction
- Multi-format output generation

**Usage:**
```python
from j5a_retrieval_gateway import J5ARetrievalGateway

gateway = J5ARetrievalGateway()

# Fetch document template
template = gateway.squirt_fetch_template(
    template_name="invoice_template_2024",
    template_source="local"
)

# Extract from voice (requires Whisper integration)
voice_data = gateway.squirt_extract_from_voice(
    audio_path="/path/to/voice_memo.mp3"
)
```

### Jeeves Personal Assistant

**Enhanced Capabilities:**
- Schedule/calendar data retrieval
- Multi-source research for daily briefings
- Intelligent topic research with depth control

**Usage:**
```python
from j5a_retrieval_gateway import J5ARetrievalGateway

gateway = J5ARetrievalGateway()

# Fetch schedule
schedule = gateway.jeeves_fetch_schedule(
    calendar_source="local",
    date_range={"start": "2024-10-14", "end": "2024-10-15"}
)

# Research for briefing
research = gateway.jeeves_research_topic(
    topic="autonomous systems developments",
    depth="detailed"
)
```

### Night Shift Podcast Intelligence

**Enhanced Capabilities:**
- Podcast discovery (v1 production system - unchanged)
- Media download with v2.1 MediaAgent
- ML inference for content classification
- Database queries for podcast metadata

**Usage:**
```python
from j5a_retrieval_gateway import J5ARetrievalGateway

gateway = J5ARetrievalGateway()

# Discover podcast (v1)
podcast = gateway.nightshift_discover_podcast(
    home_url="https://podcast.example.com",
    prefer_epnum=91
)

# Download with v2.1
download = gateway.nightshift_download_media(
    media_url=podcast['media_url'],
    output_path="/downloads/episode_91.mp3"
)

# ML inference on transcript
inference = gateway.nightshift_ml_inference(
    model_path="/models/topic_classifier.pkl",
    input_data=[["Transcript text here"]]
)
```

---

## Configuration

Add Retriever v2.1 configuration to `rules.yaml`:

```yaml
retriever:
  # Database connections
  postgresql:
    host: localhost
    port: 5432
    user: postgres
    # password: set via environment variable

  mysql:
    host: localhost
    port: 3306
    # user/password: set via environment variables

  mongodb:
    host: localhost
    port: 27017

  # ML agent settings
  ml:
    device: cpu  # or 'cuda', 'mps'
    batch_size: 32

  # WebScraper settings
  webscraper:
    backend: selenium  # or 'playwright'
    browser: chrome
    headless: true
    timeout: 30
```

---

## Testing

### Test Gateway Initialization

```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers
python3 j5a_retrieval_gateway.py
```

### Test Sherlock Integration

```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift
python3 sherlock_retrieval.py
```

### Test Job Processing

```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift
python3 -c "
from j5a_worker import J5AWorker
import json

worker = J5AWorker()

# Load example job
with open('ops/queue/examples/v2_1_job_examples.json') as f:
    examples = json.load(f)
    job = examples['jobs'][0]  # intelligence_discovery example

result = worker.process_job(job)
print(f'Result: {result}')
"
```

### Run Full Integration Tests

```bash
# Core v2 agents
cd ops/fetchers/retriever
python3 test_retriever_v2.py

# v2.1 extensions
python3 test_retriever_v2_1.py
```

---

## Migration from v1

**Good News:** All v1 functionality remains intact! The podcast discovery system (`discover_audio_from_homepage`) continues to work exactly as before.

**New v2.1 Capabilities** are additive - you can adopt them incrementally:

1. **Start using the gateway for new operations:**
   ```python
   from j5a_retrieval_gateway import J5ARetrievalGateway
   gateway = J5ARetrievalGateway()
   ```

2. **Keep existing v1 code unchanged:**
   ```python
   from retriever.discovery import discover_audio_from_homepage
   # Works exactly as before
   ```

3. **Gradually adopt v2.1 for new features:**
   - Use `gateway.sherlock_query_database()` for database operations
   - Use `gateway._get_webscraper_agent()` for dynamic web content
   - Use `gateway.nightshift_ml_inference()` for ML models

---

## Troubleshooting

### Gateway Initialization Fails

**Symptom:** `Retriever v2.1 initialization failed: ...`

**Solution:** Check that retriever module is accessible:
```bash
export PYTHONPATH="/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers:$PYTHONPATH"
```

### Optional Dependencies Missing

**Symptom:** `ImportError: psycopg2 not installed`

**Solution:** Install required dependencies:
```bash
# PostgreSQL
pip install psycopg2-binary

# MySQL
pip install mysql-connector-python

# MongoDB
pip install pymongo

# ML frameworks
pip install scikit-learn torch tensorflow

# Web scraping
pip install selenium playwright
playwright install

# NLP transformers
pip install sentence-transformers
```

### Job Processing Fails

**Symptom:** Job status: `failed`, reason: `Retrieval gateway not available`

**Solution:** Check worker initialization logs for gateway errors. Ensure all paths are correct in job definitions.

---

## Performance Considerations

- **Database connections:** Reused within job execution, connection pooling recommended for high-volume
- **ML models:** Cached in memory after first load (configure `ml.batch_size` based on available RAM)
- **Web scraping:** Headless mode recommended for Night Shift (faster, lower resource usage)
- **Multi-step retrieval:** Can be resource-intensive, consider job class `demanding` for Phase 2

---

## Future Enhancements

Potential future additions (beyond v2.1 scope):

- **Distributed execution:** Multi-machine agent orchestration
- **Cloud storage integration:** S3, GCS, Azure Blob support
- **Real-time monitoring:** Dashboard for agent execution metrics
- **Advanced NLP:** Always-on transformer models for better query understanding
- **Agent marketplace:** Plugin system for community-contributed agents

---

**For additional documentation:**
- Core architecture: `retriever/ARCHITECTURE_V2.md`
- Agent details: `retriever/README.md`
- Original integration guide: `retriever/INTEGRATION.md`
