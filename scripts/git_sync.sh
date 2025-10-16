#!/usr/bin/env bash
#
# Git Sync Utility - Sync repositories from manifest
#
# Usage: git_sync.sh [manifest_file]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="${1:-$ROOT/configs/repos.json}"

if [ ! -f "$MANIFEST" ]; then
    echo "❌ Manifest not found: $MANIFEST" >&2
    exit 1
fi

echo "🔄 Syncing repositories from: $MANIFEST"
echo ""

# Parse JSON and sync each repo
python3 -c "
import json
import subprocess
import sys
from pathlib import Path

with open('$MANIFEST') as f:
    repos = json.load(f)

results = {'synced': [], 'failed': [], 'missing': []}

for repo in repos:
    name = repo['name']
    path = repo['path']
    branch = repo.get('branch', 'main')

    print(f'=== {name} ===')

    if not Path(path).exists():
        print(f'⚠️  Path does not exist: {path}')
        results['missing'].append(name)
        print()
        continue

    # Pull latest changes
    try:
        result = subprocess.run(
            ['git', 'pull', 'origin', branch],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        results['synced'].append(name)
        print('✅ Synced')
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        results['failed'].append(name)
        print('❌ Failed')

    print()

# Summary
print('='*60)
print('SYNC SUMMARY')
print('='*60)
print(f'✅ Synced: {len(results[\"synced\"])}')
if results['synced']:
    for name in results['synced']:
        print(f'   - {name}')

if results['missing']:
    print(f'⚠️  Missing: {len(results[\"missing\"])}')
    for name in results['missing']:
        print(f'   - {name}')

if results['failed']:
    print(f'❌ Failed: {len(results[\"failed\"])}')
    for name in results['failed']:
        print(f'   - {name}')
    sys.exit(1)
"

echo ""
echo "✅ Repository sync complete"
