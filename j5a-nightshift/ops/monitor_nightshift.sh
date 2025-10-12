#!/bin/bash
# J5A Nightshift Health Monitoring Dashboard
# Quick health check for manual inspection

set -euo pipefail

# Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
QUEUE_DB="/home/johnny5/Johny5Alive/j5a_queue_manager.db"
OLLAMA_ENDPOINT="http://localhost:11434"
LOGS_DIR="/home/johnny5/Johny5Alive/j5a-nightshift/ops/logs"

echo ""
echo -e "${BOLD}=========================================="
echo "J5A NIGHTSHIFT HEALTH STATUS"
echo -e "==========================================${NC}"
echo ""

# System Status
echo -e "${BOLD}System Status:${NC}"

# Check Ollama
echo -n "  "
if curl -s -f "${OLLAMA_ENDPOINT}/api/version" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama:${NC} Running"

    # Check model loaded
    MODEL=$(ollama list | grep "qwen2.5:7b-instruct-q4_K_M" | awk '{print $1}')
    if [ -n "$MODEL" ]; then
        echo -e "     ${BLUE}ℹ${NC}  Model: qwen2.5:7b-instruct-q4_K_M loaded"
    fi
else
    echo -e "${RED}❌ Ollama:${NC} Not running"
    echo -e "     ${YELLOW}⚠${NC}  Run 'ollama serve &' to start"
fi

# Check CPU Temperature
echo -n "  "
if command -v sensors > /dev/null 2>&1; then
    TEMP=$(sensors | grep "Package id 0" | awk '{print $4}' | sed 's/+//;s/°C//' | cut -d'.' -f1)
    if [ -z "$TEMP" ]; then
        TEMP=$(sensors | grep "Core 0" | head -n1 | awk '{print $3}' | sed 's/+//;s/°C//' | cut -d'.' -f1)
    fi

    if [ -n "$TEMP" ]; then
        if [ "$TEMP" -lt 70 ]; then
            STATUS="${GREEN}EXCELLENT${NC}"
            ICON="✅"
        elif [ "$TEMP" -lt 75 ]; then
            STATUS="${GREEN}GOOD${NC}"
            ICON="✅"
        elif [ "$TEMP" -lt 80 ]; then
            STATUS="${YELLOW}WARM${NC}"
            ICON="⚠️"
        elif [ "$TEMP" -lt 87 ]; then
            STATUS="${YELLOW}HOT${NC}"
            ICON="🔥"
        else
            STATUS="${RED}CRITICAL${NC}"
            ICON="🔥"
        fi
        echo -e "${ICON} ${BOLD}CPU Temp:${NC} ${TEMP}°C (${STATUS} - limit 87°C)"
    else
        echo -e "${YELLOW}⚠${NC}  ${BOLD}CPU Temp:${NC} Unable to read"
    fi
else
    echo -e "${YELLOW}⚠${NC}  ${BOLD}CPU Temp:${NC} sensors not installed"
fi

# Check Free RAM
echo -n "  "
FREE_RAM_MB=$(free -m | awk '/^Mem:/ {print $7}')
FREE_RAM_GB=$(echo "scale=1; $FREE_RAM_MB / 1024" | bc)
TOTAL_RAM_GB=$(free -g | awk '/^Mem:/ {print $2}')

if [ "$FREE_RAM_MB" -ge 6144 ]; then
    echo -e "${GREEN}✅ Free RAM:${NC} ${FREE_RAM_GB}GB (Safe - need 6GB minimum)"
else
    echo -e "${YELLOW}⚠️  Free RAM:${NC} ${FREE_RAM_GB}GB (Low - need 6GB for LLM)"
fi

# Check Systemd Timer
echo -n "  "
if systemctl is-active --quiet j5a-nightshift.timer 2>/dev/null; then
    NEXT_RUN=$(systemctl status j5a-nightshift.timer 2>/dev/null | grep "Trigger:" | awk '{print $2, $3, $4}' || echo "Unknown")
    echo -e "${GREEN}✅ Timer:${NC} Active (next run: ${NEXT_RUN})"
else
    echo -e "${YELLOW}⚠️  Timer:${NC} Not active"
    echo -e "     ${BLUE}ℹ${NC}  Enable with: sudo systemctl enable j5a-nightshift.timer"
fi

echo ""

# Queue Status
echo -e "${BOLD}Queue Status:${NC}"

if [ -f "$QUEUE_DB" ]; then
    # Get status counts
    COMPLETED=$(python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); count = conn.execute('SELECT COUNT(*) FROM task_executions WHERE status=\"completed\"').fetchone()[0]; conn.close(); print(count)" 2>/dev/null || echo "0")
    PARKED=$(python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); count = conn.execute('SELECT COUNT(*) FROM task_executions WHERE status=\"parked\"').fetchone()[0]; conn.close(); print(count)" 2>/dev/null || echo "0")
    DEFERRED=$(python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); count = conn.execute('SELECT COUNT(*) FROM task_executions WHERE status=\"deferred\"').fetchone()[0]; conn.close(); print(count)" 2>/dev/null || echo "0")
    FAILED=$(python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); count = conn.execute('SELECT COUNT(*) FROM task_executions WHERE status=\"failed\"').fetchone()[0]; conn.close(); print(count)" 2>/dev/null || echo "0")
    QUEUED=$(python3 -c "import sqlite3; conn = sqlite3.connect('${QUEUE_DB}'); count = conn.execute('SELECT COUNT(*) FROM task_executions WHERE status=\"queued\"').fetchone()[0]; conn.close(); print(count)" 2>/dev/null || echo "0")

    TOTAL=$((COMPLETED + PARKED + DEFERRED + FAILED + QUEUED))

    echo "  📊 ${BOLD}Total Jobs:${NC} $TOTAL"
    echo "  ${GREEN}✅ Completed:${NC} $COMPLETED"
    echo "  📦 ${BOLD}Parked (Phase 2):${NC} $PARKED"
    echo "  ⏸️  ${BOLD}Deferred:${NC} $DEFERRED"
    echo "  ❌ ${BOLD}Failed:${NC} $FAILED"
    echo "  ⏳ ${BOLD}Queued:${NC} $QUEUED"
else
    echo -e "  ${RED}❌ Database not found:${NC} $QUEUE_DB"
fi

echo ""

# Last Run
echo -e "${BOLD}Last Run:${NC}"

# Find most recent log
LATEST_LOG=$(ls -t "${LOGS_DIR}"/nightshift_*.log 2>/dev/null | head -n1 || echo "")

if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    # Extract date from filename
    LOG_DATE=$(basename "$LATEST_LOG" | sed 's/nightshift_//;s/.log//')
    LOG_TIMESTAMP=$(echo "$LOG_DATE" | sed 's/_/ /' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\) \([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')

    echo "  📅 ${BOLD}Date:${NC} $LOG_TIMESTAMP"

    # Calculate duration from log
    START_LINE=$(grep "Nightshift processor initialized" "$LATEST_LOG" | head -n1)
    END_LINE=$(grep "Queue processing complete" "$LATEST_LOG" | head -n1)

    if [ -n "$START_LINE" ] && [ -n "$END_LINE" ]; then
        START_TIME=$(echo "$START_LINE" | awk '{print $1}')
        END_TIME=$(echo "$END_LINE" | awk '{print $1}')

        # Simple duration (just show times)
        echo "  ⏱️  ${BOLD}Duration:${NC} $START_TIME → $END_TIME"
    fi

    # Count successes from log
    SUCCESS_COUNT=$(grep -c "COMPLETED" "$LATEST_LOG" 2>/dev/null || echo "0")
    PARKED_COUNT=$(grep -c "PARKED" "$LATEST_LOG" 2>/dev/null || echo "0")

    if [ "$SUCCESS_COUNT" -gt 0 ] || [ "$PARKED_COUNT" -gt 0 ]; then
        echo "  ${GREEN}✅ Success:${NC} $SUCCESS_COUNT standard jobs completed"
        echo "  📦 ${BOLD}Parked:${NC} $PARKED_COUNT demanding jobs"
    fi
else
    echo "  ${YELLOW}⚠${NC}  No logs found in ${LOGS_DIR}"
fi

echo ""

# Recent Errors
echo -e "${BOLD}Recent Errors:${NC}"

if [ -f "${LOGS_DIR}/systemd_error.log" ]; then
    ERROR_COUNT=$(wc -l < "${LOGS_DIR}/systemd_error.log" 2>/dev/null || echo "0")

    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "  ${RED}❌ Errors:${NC} $ERROR_COUNT lines in systemd_error.log"
        echo "     Last 3 errors:"
        tail -n3 "${LOGS_DIR}/systemd_error.log" | while read -r line; do
            echo "     $line"
        done
    else
        echo -e "  ${GREEN}✅ No errors${NC}"
    fi
else
    echo -e "  ${GREEN}✅ No errors${NC}"
fi

echo ""

# Recommendations
echo -e "${BOLD}Recommendations:${NC}"

RECS=0

if [ "$DEFERRED" -gt 10 ]; then
    echo -e "  ${YELLOW}⚠${NC}  $DEFERRED deferred jobs need investigation"
    ((RECS++))
fi

if [ "$FAILED" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠${NC}  $FAILED failed jobs need root cause analysis"
    ((RECS++))
fi

if [ "$QUEUED" -eq 0 ] && [ "$PARKED" -eq 0 ]; then
    echo -e "  ${BLUE}ℹ${NC}  No jobs queued - add jobs for overnight processing"
    ((RECS++))
fi

if ! systemctl is-active --quiet j5a-nightshift.timer 2>/dev/null; then
    echo -e "  ${YELLOW}⚠${NC}  Timer not active - enable for automatic overnight runs"
    ((RECS++))
fi

if [ "$RECS" -eq 0 ]; then
    echo -e "  ${GREEN}✅ All systems nominal${NC}"
fi

# Next Run
if systemctl is-active --quiet j5a-nightshift.timer 2>/dev/null; then
    NEXT_RUN_FULL=$(systemctl status j5a-nightshift.timer 2>/dev/null | grep "Trigger:" | awk '{$1=""; print $0}' | xargs || echo "Unknown")
    if [ -n "$NEXT_RUN_FULL" ] && [ "$NEXT_RUN_FULL" != "Unknown" ]; then
        echo -e "  ${BLUE}ℹ${NC}  Next run: $NEXT_RUN_FULL"
    fi
fi

echo ""
echo -e "${BOLD}==========================================${NC}"
echo ""
