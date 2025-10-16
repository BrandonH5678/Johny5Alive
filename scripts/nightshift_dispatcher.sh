#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INBOX="$ROOT/queue/nightshift/inbox.jsonl"
ROUTER="$ROOT/src/qwen_task_router.py"

[ -f "$INBOX" ] || { echo "No inbox found"; exit 0; }

while IFS= read -r line; do
  [ -z "$line" ] && continue
  echo "$line" | python3 "$ROUTER"
done < "$INBOX"

# rotate inbox
ts=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$ROOT/queue/nightshift/archive"
mv "$INBOX" "$ROOT/queue/nightshift/archive/inbox_$ts.jsonl" || true
touch "$INBOX"
