#!/usr/bin/env bash
set -euo pipefail
PAGE_URL="${1:?page URL}"
EP_TITLE="${2:?episode title}"
MODEL="${3:-qwen2.5:7b-instruct}"
ENDPOINT="${4:-http://localhost:11434}"
python3 ops/fetchers/podcast_fetch_with_rwf.py --url "$PAGE_URL" --title "$EP_TITLE" --model "$MODEL" --endpoint "$ENDPOINT" --outdir ops/outputs/podcast_download --log ops/logs/podcast_fetch.log
