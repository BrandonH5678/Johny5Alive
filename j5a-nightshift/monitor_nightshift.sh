#!/bin/bash
# Nightshift Monitoring Script - Real-time status display

LOG_DIR="/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs"
LATEST_LOG=$(ls -t ${LOG_DIR}/nightshift_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "No Nightshift logs found"
    exit 1
fi

echo "=========================================="
echo "🌙 J5A NIGHTSHIFT MONITOR"
echo "=========================================="
echo "Log: $(basename $LATEST_LOG)"
echo ""

# Check if process is running
if ps aux | grep "process_nightshift_queue.py" | grep -v grep > /dev/null; then
    echo "Status: ✅ RUNNING"
else
    echo "Status: ⏹️  STOPPED"
fi

echo ""
echo "=========================================="
echo "RECENT ACTIVITY:"
echo "=========================================="
tail -30 "$LATEST_LOG" | grep -E "(Processing job|Completed|Parked|Deferred|Failed|ERROR|WARNING|Summary saved|validation)"

echo ""
echo "=========================================="
echo "THERMAL STATUS:"
echo "=========================================="
sensors | grep "Package id 0"

echo ""
echo "=========================================="
echo "Full log: tail -f $LATEST_LOG"
echo "=========================================="
