# Night Shift Retriever - J5A Integration Guide

## Overview
The Night Shift Retriever is now integrated into the J5A NightShift system with enhanced retry logic at both the RWF (Robust Web Fetcher) level and the full multi-stage discovery cascade.

## Location
```
j5a-nightshift/ops/fetchers/retriever/
├── nightshift_task_retriever.py   # Main task interface
├── retriever/
│   ├── __init__.py
│   ├── rwf.py                     # Robust Web Fetcher (HTTP layer)
│   ├── discovery.py               # Multi-stage discovery cascade
│   └── cli.py                     # CLI interface
├── test_retriever.sh              # Integration test suite
├── requirements.txt               # Python dependencies
├── site_templates.yaml            # Site-specific overrides
├── README.md                      # Original documentation
└── INTEGRATION.md                 # This file
```

## Enhanced Features

### 1. Cascade-Level Retry Logic
The discovery cascade now includes retry logic at multiple levels:

- **Cascade-level retries**: Retry the entire discovery process (RSS → page-scan → sitemap)
- **Stage-level retries**: Retry individual stages independently
- **RWF-level retries**: HTTP request retries with exponential backoff (existing)

### 2. Configurable Retry Behavior
```python
DiscoveryRetryConfig(
    max_cascade_retries=2,      # Retry entire cascade up to 2 times
    max_stage_retries=2,        # Retry each stage up to 2 times
    retry_delay=2.0,            # Initial delay between retries (seconds)
    exponential_backoff=True    # Double delay after each retry
)
```

### 3. Enhanced Error Handling
- Structured error reporting with stage information
- Comprehensive logging at INFO/DEBUG levels
- Progress tracking for downloads
- Graceful failure handling

## Installation

### Install Python Dependencies
```bash
# Only feedparser is missing from the system
pip3 install feedparser

# Or install all dependencies from requirements.txt
pip3 install -r /home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/retriever/requirements.txt
```

### Verify Installation
```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/retriever
./test_retriever.sh
```

## Usage

### As a Night Shift Task (JSON stdin/stdout)
```bash
echo '{
  "home_url": "https://example.com/podcast",
  "prefer_epnum": 92,
  "max_cascade_retries": 2,
  "max_stage_retries": 2,
  "download": true,
  "outdir": "./output"
}' | python3 nightshift_task_retriever.py
```

### Discovery Only (No Download)
```bash
echo '{
  "home_url": "https://example.com/podcast",
  "prefer_title": "Episode Title"
}' | python3 nightshift_task_retriever.py
```

### Using CLI Interface
```bash
# Discovery only
python3 -m retriever.cli discover --home "https://example.com/podcast" --ep 92

# Discovery + Download
python3 -m retriever.cli download --home "https://example.com/podcast" --ep 92 --out ./output
```

### From Python Code
```python
from retriever.rwf import RobustWebFetcher
from retriever.discovery import discover_audio_from_homepage, DiscoveryRetryConfig

# Configure retry behavior
retry_config = DiscoveryRetryConfig(
    max_cascade_retries=3,
    max_stage_retries=2,
    retry_delay=2.0,
    exponential_backoff=True
)

# Initialize fetcher
fetcher = RobustWebFetcher(timeout=25, max_retries=3)

# Discover media
media_url, metadata = discover_audio_from_homepage(
    home_url="https://example.com/podcast",
    prefer_epnum=92,
    fetcher=fetcher,
    retry_config=retry_config
)

print(f"Found: {media_url}")
print(f"Method: {metadata['method']}")
```

## Input Parameters

### Required
- `home_url`: Homepage URL to start discovery (must be valid HTTP/HTTPS)

### Optional - Discovery
- `prefer_title`: Preferred episode title to match
- `prefer_epnum`: Preferred episode number to match
- `max_cascade_retries`: Number of full cascade retries (default: 2)
- `max_stage_retries`: Number of retries per stage (default: 2)
- `retry_delay`: Initial retry delay in seconds (default: 2.0)
- `exponential_backoff`: Use exponential backoff (default: true)
- `fetch_timeout`: HTTP request timeout in seconds (default: 25)
- `fetch_max_retries`: HTTP request retries (default: 3)

### Optional - Download
- `download`: Boolean, enable download (default: false)
- `outdir`: Output directory path (default: "./output")
- `filename`: Output filename (default: auto-generated with extension)
- `download_timeout`: Download timeout in seconds (default: 1800)

## Output Format

### Success Response
```json
{
  "success": true,
  "media_url": "https://cdn.example.com/episode.mp3",
  "meta": {
    "method": "rss",
    "title": "Episode 92 - Title",
    "pubDate": "2024-01-01",
    "rss": "https://example.com/feed"
  },
  "download": {
    "success": true,
    "path": "/path/to/output/episode.mp3",
    "size_bytes": 45678901,
    "size_mb": 43.56
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Discovery failed after 2 cascade attempts",
  "stage": "cascade",
  "errors": [
    "Cascade attempt 1 failed: Connection timeout",
    "Cascade attempt 2 failed: No valid RSS feeds found"
  ]
}
```

## Discovery Cascade Flow

```
1. Fetch Homepage
   ↓
2. Stage 1: RSS Discovery (with retries)
   - Find RSS feed links in HTML
   - Validate RSS feeds (HEAD request)
   - Parse RSS enclosures
   - Match preferred title/episode number
   ↓ (if no results)
3. Stage 2: Page-Scan Discovery (with retries)
   - Extract audio URLs from HTML
   - Check <audio> tags, links, JSON-LD
   - Scan iframes from known podcast hosts
   - Validate audio URLs (HEAD request)
   ↓ (if no results)
4. Stage 3: Sitemap Discovery (with retries)
   - Find sitemap.xml / sitemap_index.xml
   - Extract episode page URLs
   - Scan each episode page for audio
   - Validate discovered URLs
   ↓ (if no results)
5. Cascade Retry (if configured)
   - Wait with exponential backoff
   - Retry entire cascade from step 1
```

## Integration with J5A Night Shift

### Queue Task for Night Shift Processing
```bash
# Add retriever task to night shift queue
echo '{
  "task_type": "retriever",
  "home_url": "https://example.com/podcast",
  "prefer_epnum": 92,
  "download": true,
  "outdir": "/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs/podcast_downloads"
}' > /home/johnny5/Johny5Alive/j5a-nightshift/ops/queue/retriever_task_001.json
```

### From J5A Worker
```python
import subprocess
import json

def run_retriever_task(task_payload):
    """Run retriever as subprocess from J5A worker"""
    cmd = [
        "python3",
        "/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/retriever/nightshift_task_retriever.py"
    ]

    result = subprocess.run(
        cmd,
        input=json.dumps(task_payload),
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour timeout
    )

    return json.loads(result.stdout)
```

## Logging

### Log Levels
- **INFO**: Major stages, successes, progress
- **DEBUG**: Detailed discovery attempts, URL validation
- **WARNING**: Retry attempts, recoverable errors
- **ERROR**: Fatal errors, all retries exhausted

### Log Output
Logs are written to stderr. To capture:
```bash
python3 nightshift_task_retriever.py 2>retriever.log
```

## Troubleshooting

### "feedparser not found"
```bash
pip3 install feedparser
```

### Discovery fails on specific site
1. Check site accessibility manually
2. Add site-specific overrides to `site_templates.yaml`
3. Increase retry attempts: `max_cascade_retries: 3`
4. Enable DEBUG logging to see detailed attempts

### Timeout during download
1. Increase `download_timeout` parameter
2. Check network connectivity
3. Verify media URL is accessible

### All stages fail
1. Verify homepage URL is correct
2. Check if site requires authentication
3. Try with a known-working site first (e.g., Darknet Diaries)
4. Review logs for specific error patterns

## Known Compatible Sites
- Darknet Diaries (darknetdiaries.com)
- Most WordPress-based podcast sites
- Sites using standard RSS/Atom feeds
- Sites with JSON-LD structured data
- Common podcast hosting platforms:
  - Simplecast
  - Buzzsprout
  - Libsyn
  - Transistor
  - Captivate

## Performance Considerations

### Retry Configuration
- **Conservative** (slow but thorough):
  ```json
  {
    "max_cascade_retries": 3,
    "max_stage_retries": 3,
    "retry_delay": 3.0,
    "exponential_backoff": true
  }
  ```

- **Aggressive** (fast but may fail on flaky sites):
  ```json
  {
    "max_cascade_retries": 1,
    "max_stage_retries": 1,
    "retry_delay": 1.0,
    "exponential_backoff": false
  }
  ```

- **Balanced** (default):
  ```json
  {
    "max_cascade_retries": 2,
    "max_stage_retries": 2,
    "retry_delay": 2.0,
    "exponential_backoff": true
  }
  ```

## Testing

### Run Integration Tests
```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/retriever
./test_retriever.sh
```

### Manual Test Cases
```bash
# Test 1: Discovery only
echo '{"home_url":"https://darknetdiaries.com","prefer_epnum":140}' | python3 nightshift_task_retriever.py

# Test 2: Invalid URL handling
echo '{"home_url":"not-a-url"}' | python3 nightshift_task_retriever.py

# Test 3: Missing required field
echo '{"prefer_epnum":140}' | python3 nightshift_task_retriever.py
```

## Future Enhancements
- [ ] Support for video URLs (YouTube, Vimeo)
- [ ] PDF/document retrieval
- [ ] Authentication support for private feeds
- [ ] Caching layer for repeated requests
- [ ] Integration with J5A validation system
- [ ] Checkpoint/resume for interrupted downloads
