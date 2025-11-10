#!/bin/bash
# J5A Nightshift Pre-Flight Check
# Validates system readiness before processing queue
# Exit 0 = safe to proceed | Exit 1 = abort processing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Configuration
THERMAL_LIMIT=80
MIN_FREE_RAM_GB=6
QUEUE_DB="/home/johnny5/Johny5Alive/j5a_queue_manager.db"
OLLAMA_ENDPOINT="http://localhost:11434"

echo "=========================================="
echo "J5A NIGHTSHIFT PRE-FLIGHT CHECK"
echo "=========================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Check 1: Ollama Server Running (with retry logic)
echo -n "✓ Checking Ollama server... "
OLLAMA_CHECK_PASSED=false

for attempt in {1..3}; do
    if curl -s -f "${OLLAMA_ENDPOINT}/api/version" > /dev/null 2>&1; then
        VERSION=$(curl -s "${OLLAMA_ENDPOINT}/api/version" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}OK${NC} (version: $VERSION)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        OLLAMA_CHECK_PASSED=true
        break
    else
        if [ $attempt -lt 3 ]; then
            echo -e "${YELLOW}RETRY${NC} (attempt $attempt/3, waiting 5 seconds...)"
            sleep 5
            echo -n "✓ Checking Ollama server... "
        fi
    fi
done

if [ "$OLLAMA_CHECK_PASSED" = false ]; then
    echo -e "${RED}FAILED${NC}"
    echo "  ERROR: Ollama server not responding at ${OLLAMA_ENDPOINT} after 3 attempts"
    echo "  FIX: Run 'ollama serve &' to start the server"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check 2: Model Available
echo -n "✓ Checking LLM model... "
if ollama list | grep -q "qwen2.5:7b-instruct-q4_K_M"; then
    echo -e "${GREEN}OK${NC} (qwen2.5:7b-instruct-q4_K_M)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  ERROR: Required model not found"
    echo "  FIX: Run 'ollama pull qwen2.5:7b-instruct-q4_K_M'"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check 3: CPU Temperature
echo -n "✓ Checking CPU temperature... "
if command -v sensors > /dev/null 2>&1; then
    TEMP=$(sensors | grep "Package id 0" | awk '{print $4}' | sed 's/+//;s/°C//' | cut -d'.' -f1)
    if [ -z "$TEMP" ]; then
        # Fallback to Core 0 if Package id 0 not available
        TEMP=$(sensors | grep "Core 0" | head -n1 | awk '{print $3}' | sed 's/+//;s/°C//' | cut -d'.' -f1)
    fi

    if [ -n "$TEMP" ] && [ "$TEMP" -lt "$THERMAL_LIMIT" ]; then
        echo -e "${GREEN}OK${NC} (${TEMP}°C < ${THERMAL_LIMIT}°C limit)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ -n "$TEMP" ]; then
        echo -e "${RED}FAILED${NC} (${TEMP}°C >= ${THERMAL_LIMIT}°C limit)"
        echo "  ERROR: CPU temperature too high"
        echo "  FIX: Allow system to cool down, improve ventilation"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    else
        echo -e "${YELLOW}WARNING${NC} (unable to read temperature)"
        echo "  WARNING: Could not read CPU temperature"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))  # Don't fail if we can't read temp
    fi
else
    echo -e "${YELLOW}WARNING${NC} (sensors command not available)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))  # Don't fail if sensors not installed
fi

# Check 4: Available RAM (with Night Shift process detection)
echo -n "✓ Checking available RAM... "

# Detect Night Shift processes already running
NIGHTSHIFT_PROCS=$(ps aux | grep -E "(whisper.*artifacts/nightshift|podcast_intelligence_pipeline)" | grep -v grep | wc -l)

if [ "$NIGHTSHIFT_PROCS" -gt 0 ]; then
    # Night Shift job already running - skip RAM check
    echo -e "${YELLOW}OK${NC} (Night Shift job in progress - monitoring existing process)"
    echo "  INFO: Detected ${NIGHTSHIFT_PROCS} running Night Shift process(es)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    # Normal RAM check - no Night Shift processes running
    FREE_RAM_MB=$(free -m | awk '/^Mem:/ {print $7}')
    FREE_RAM_GB=$((FREE_RAM_MB / 1024))

    if [ "$FREE_RAM_GB" -ge "$MIN_FREE_RAM_GB" ]; then
        echo -e "${GREEN}OK${NC} (${FREE_RAM_GB}GB available >= ${MIN_FREE_RAM_GB}GB required)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}FAILED${NC} (${FREE_RAM_GB}GB available < ${MIN_FREE_RAM_GB}GB required)"
        echo "  ERROR: Insufficient free RAM for LLM inference"
        echo "  FIX: Close other applications or wait for memory to free up"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
fi

# Check 5: Queue Database Accessible
echo -n "✓ Checking queue database... "
if [ -f "$QUEUE_DB" ] && [ -r "$QUEUE_DB" ]; then
    # Try to query the database
    if python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); conn.execute('SELECT COUNT(*) FROM task_executions'); conn.close()" 2>/dev/null; then
        JOB_COUNT=$(python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); count = conn.execute('SELECT COUNT(*) FROM task_executions WHERE status=\"queued\"').fetchone()[0]; conn.close(); print(count)")
        echo -e "${GREEN}OK${NC} (${JOB_COUNT} queued jobs)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}FAILED${NC}"
        echo "  ERROR: Database query failed"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    echo -e "${RED}FAILED${NC}"
    echo "  ERROR: Queue database not found or not readable"
    echo "  PATH: $QUEUE_DB"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check 6: Business Hours Conflict
echo -n "✓ Checking business hours... "
CURRENT_HOUR=$(date +%H)
CURRENT_DAY=$(date +%u)  # 1=Monday, 7=Sunday

if [ "$CURRENT_DAY" -ge 1 ] && [ "$CURRENT_DAY" -le 5 ]; then
    # Monday-Friday
    if [ "$CURRENT_HOUR" -ge 6 ] && [ "$CURRENT_HOUR" -lt 19 ]; then
        echo -e "${YELLOW}WARNING${NC} (Business hours: Mon-Fri 6am-7pm)"
        echo "  WARNING: Running during business hours - Squirt has priority"
        echo "  INFO: Night Shift will defer demanding operations"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))  # Don't fail, but warn
    else
        echo -e "${GREEN}OK${NC} (After hours)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi
else
    # Weekend
    echo -e "${GREEN}OK${NC} (Weekend)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check 7: Python Dependencies
echo -n "✓ Checking Python dependencies... "
if python3 -c "import jinja2, yaml, requests" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo "  ERROR: Missing Python dependencies"
    echo "  FIX: pip3 install jinja2 pyyaml requests --break-system-packages"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Summary
echo ""
echo "=========================================="
echo "PRE-FLIGHT CHECK SUMMARY"
echo "=========================================="
echo -e "Checks Passed: ${GREEN}${CHECKS_PASSED}${NC}"
if [ "$CHECKS_FAILED" -gt 0 ]; then
    echo -e "Checks Failed: ${RED}${CHECKS_FAILED}${NC}"
fi
echo ""

if [ "$CHECKS_FAILED" -gt 0 ]; then
    echo -e "${RED}ABORT: Pre-flight checks failed${NC}"
    echo "Night Shift processing will not proceed."
    echo "Fix the issues above and try again."
    exit 1
else
    echo -e "${GREEN}CLEARED FOR TAKEOFF${NC}"
    echo "All pre-flight checks passed. Night Shift ready to process queue."
    exit 0
fi
