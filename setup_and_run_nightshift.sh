#!/bin/bash
# Complete Night Shift setup and execution script
# Designed to run when Claude Code session ends

set -e

echo "========================================================================"
echo "NIGHT SHIFT - SETUP AND RUN"
echo "Started: $(date)"
echo "========================================================================"
echo ""

# 1. Fix systemd service configuration
echo "Step 1: Fixing systemd service configuration..."
sudo cp /home/johnny5/Johny5Alive/j5a-nightshift/j5a-nightshift.service.fixed /etc/systemd/system/j5a-nightshift.service
sudo systemctl daemon-reload
echo "✅ Service configuration updated"
echo ""

# 2. Check Ollama is running
echo "Step 2: Checking Ollama server..."
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "⚠️  Ollama not running, starting it..."
    ollama serve &
    sleep 3
fi
echo "✅ Ollama server is running"
echo ""

# 3. Run Night Shift manually (not via systemd to capture all output)
echo "Step 3: Running Night Shift queue processor..."
echo "========================================================================"
cd /home/johnny5/Johny5Alive/j5a-nightshift

# Run with timeout protection (30 minutes)
if timeout 1800 python3 process_nightshift_queue.py; then
    echo ""
    echo "✅ Night Shift processing completed successfully"
    exit_code=0
else
    exit_code=$?
    echo ""
    if [ $exit_code -eq 124 ]; then
        echo "⚠️  Night Shift timed out after 30 minutes"
    else
        echo "❌ Night Shift failed with exit code: $exit_code"
    fi
fi

echo ""
echo "========================================================================"
echo "NIGHT SHIFT RUN COMPLETE"
echo "Ended: $(date)"
echo "========================================================================"

exit $exit_code
