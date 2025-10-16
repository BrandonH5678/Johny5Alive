#!/usr/bin/env bash
#
# Safe Backup Utility - Create timestamped backups with verification
#
# Usage: safe_backup.sh [source_path] [dest_base]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H%M%SZ)

# Default source: current working directory or J5A root
SOURCE="${1:-$ROOT}"

# Default destination: artifacts/nightshift/backups
DEST_BASE="${2:-$ROOT/artifacts/nightshift/$(date +%Y-%m-%d)/backups}"
DEST="$DEST_BASE/backup_$TIMESTAMP"

# Verify source exists
if [ ! -e "$SOURCE" ]; then
    echo "❌ Source does not exist: $SOURCE" >&2
    exit 1
fi

# Create destination directory
mkdir -p "$DEST"

echo "🔄 Creating backup..."
echo "   Source: $SOURCE"
echo "   Destination: $DEST"
echo ""

# Exclude patterns for backup
EXCLUDE_PATTERNS=(
    "--exclude=.git"
    "--exclude=__pycache__"
    "--exclude=*.pyc"
    "--exclude=*.pyo"
    "--exclude=.pytest_cache"
    "--exclude=node_modules"
    "--exclude=venv"
    "--exclude=.venv"
    "--exclude=*.log"
    "--exclude=.DS_Store"
)

# Perform backup with rsync
if rsync -av --progress "${EXCLUDE_PATTERNS[@]}" "$SOURCE/" "$DEST/"; then
    echo ""
    echo "✅ Backup complete: $DEST"

    # Calculate size
    BACKUP_SIZE=$(du -sh "$DEST" | cut -f1)
    echo "   Size: $BACKUP_SIZE"

    # Count files
    FILE_COUNT=$(find "$DEST" -type f | wc -l)
    echo "   Files: $FILE_COUNT"

    # Create metadata file
    cat > "$DEST/backup_metadata.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "source": "$SOURCE",
  "destination": "$DEST",
  "size": "$BACKUP_SIZE",
  "file_count": $FILE_COUNT,
  "completed": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

    echo ""
    echo "📄 Metadata saved: $DEST/backup_metadata.json"
else
    echo ""
    echo "❌ Backup failed" >&2
    exit 1
fi
