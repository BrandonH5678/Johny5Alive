# Night Shift — Retriever

**Retriever** is a local-first sub-agent for autonomous retrieval of target files (podcast audio, PDFs, webpages, etc.) across the **J5A universe** (Sherlock, Squirt, Jeeves, Night Shift, etc.).
It integrates a **Robust Web Fetcher (RWF)** layer with a **discovery cascade** for finding direct media URLs from high-level pages (e.g., a podcast homepage).

## Highlights
- **No API tokens required**; pure Python (+ optional proxies you control).
- **RSS-first** → **page-scan** → **sitemap** discovery cascade for podcasts.
- **RWF**: randomized headers, retries/backoff, conservative timeouts, simple proxy support.
- **CLI & Task**: run standalone or as a Night Shift task.

## Quickstart

```bash
# (optional) create venv
python3 -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt

# Try to discover a media URL from a podcast homepage
python -m retriever.cli discover --home https://example.com/podcast --ep 92

# Download the discovered media to ./output
python -m retriever.cli download --home https://example.com/podcast --ep 92 --out ./output

# Run as a Night Shift task (reads JSON args from stdin, writes JSON to stdout)
echo '{"home_url":"https://example.com/podcast","prefer_epnum":92,"outdir":"./output"}' | python nightshift_task_retriever.py
```

## Project Layout
- `retriever/rwf.py` — Robust Web Fetcher
- `retriever/discovery.py` — Podcast media discovery cascade on top of RWF
- `retriever/cli.py` — CLI for discovery and download workflows
- `nightshift_task_retriever.py` — Night Shift compatible task wrapper
- `site_templates.yaml` — (optional) per-site overrides for very stubborn sites
- `requirements.txt` — Python dependencies

## Integration Notes
- **Night Shift** can call `nightshift_task_retriever.py` with JSON over stdin.
- **Sherlock/Squirt/Jeeves** can import `retriever` directly or shell out to the CLI.
- Outputs include a `media_url` and a JSON `meta` block describing the method used.

## Retriever v2.1 — Extended Agent Architecture

Retriever v2.1 extends the original podcast discovery with a comprehensive agent-based architecture for multi-source data retrieval.

### New Capabilities

**v2.1 Advanced Extensions:**
- 🔗 **AgentChain** - Multi-agent workflow orchestration with automatic data flow
- 💾 **Database Agents** - PostgreSQL, MySQL, MongoDB support
- 🤖 **ML Agent** - scikit-learn, PyTorch, TensorFlow inference
- 🌐 **WebScraper Agent** - Selenium/Playwright browser automation
- 🧠 **Enhanced NLP** - Transformer-based semantic query understanding

**v2 Core Agents:**
- API, Media, Filesystem, SQLite, OCR, Index agents
- Query planning and task queue integration
- Natural language query routing

### Quick Example

```python
from retriever import AgentChain, FSAgent, MLAgent

# Orchestrate multi-agent workflows
chain = AgentChain({'fs': FSAgent(), 'ml': MLAgent()})

plan = [
    {'agent': 'fs', 'target': {'type': 'fs', 'path': './data', 'pattern': '*.csv'}},
    {'agent': 'ml', 'depends_on': 0, 'target': {'type': 'ml', 'model_path': './model.pkl'}}
]

result = chain.execute(plan)
```

For complete documentation, see **[ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)**

### Testing

```bash
# Test v1 podcast discovery + v2 core agents
python3 test_retriever_v2.py

# Test v2.1 advanced extensions
python3 test_retriever_v2_1.py
```
