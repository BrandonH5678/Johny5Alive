#!/usr/bin/env bash
#
# Night Shift Weaponized Pipeline Monitor
# Real-time monitoring of timer, retrieval, Whisper, and Claude queue
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${BOLD}=========================================="
echo -e "🔫 Night Shift - Weaponized Pipeline Monitor"
echo -e "==========================================${NC}"
echo ""

# Function to check timer status
check_timer() {
    echo -e "${BLUE}${BOLD}[TIMER STATUS]${NC}"
    systemctl list-timers weaponized-ep91-pipeline.timer 2>/dev/null || echo "Timer not found"
    echo ""
}

# Function to check service status
check_service() {
    echo -e "${BLUE}${BOLD}[SERVICE STATUS]${NC}"
    systemctl status weaponized-ep91-pipeline.service --no-pager -l 2>/dev/null | head -15 || echo "Service not active yet"
    echo ""
}

# Function to check Whisper process
check_whisper() {
    echo -e "${BLUE}${BOLD}[WHISPER PROCESS]${NC}"

    # Check for PID file
    if [ -f "artifacts/nightshift/2025-10-13/weaponized/whisper.pid" ]; then
        WHISPER_PID=$(cat artifacts/nightshift/2025-10-13/weaponized/whisper.pid)
        if ps -p "$WHISPER_PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Whisper running (PID: $WHISPER_PID)${NC}"
            ps -p "$WHISPER_PID" -o pid,etime,%cpu,%mem,cmd --no-headers
        else
            echo -e "${RED}❌ Whisper process not found (PID: $WHISPER_PID)${NC}"
        fi
    else
        # Search for any whisper process
        if pgrep -f "whisper.*episode_91" > /dev/null; then
            echo -e "${GREEN}✅ Whisper process found:${NC}"
            ps aux | grep -v grep | grep "whisper.*episode_91" | head -1
        else
            echo -e "${YELLOW}⏳ No Whisper process running${NC}"
        fi
    fi
    echo ""
}

# Function to check outputs
check_outputs() {
    echo -e "${BLUE}${BOLD}[OUTPUT FILES]${NC}"
    OUTPUT_DIR="artifacts/nightshift/2025-10-13/weaponized"

    if [ -d "$OUTPUT_DIR" ]; then
        echo "Directory: $OUTPUT_DIR"
        ls -lh "$OUTPUT_DIR" 2>/dev/null || echo "No files yet"
    else
        echo -e "${YELLOW}Output directory not created yet${NC}"
    fi
    echo ""
}

# Function to show recent logs
show_logs() {
    echo -e "${BLUE}${BOLD}[RECENT LOGS]${NC}"

    # Pipeline log
    LATEST_PIPELINE_LOG=$(ls -t ops/logs/weaponized_ep91_pipeline_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_PIPELINE_LOG" ]; then
        echo -e "${GREEN}Pipeline log:${NC} $LATEST_PIPELINE_LOG"
        echo "Last 10 lines:"
        tail -10 "$LATEST_PIPELINE_LOG" | sed 's/^/  /'
    else
        echo -e "${YELLOW}No pipeline log found yet${NC}"
    fi

    echo ""

    # Whisper log
    LATEST_WHISPER_LOG=$(ls -t ops/logs/whisper_ep91_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_WHISPER_LOG" ]; then
        echo -e "${GREEN}Whisper log:${NC} $LATEST_WHISPER_LOG"
        echo "Last 5 lines:"
        tail -5 "$LATEST_WHISPER_LOG" | sed 's/^/  /'
    else
        echo -e "${YELLOW}No Whisper log found yet${NC}"
    fi

    echo ""
}

# Function to check Claude queue
check_claude_queue() {
    echo -e "${BLUE}${BOLD}[CLAUDE QUEUE]${NC}"
    CLAUDE_QUEUE="/home/johnny5/Johny5Alive/queue/claude/2025-10-13.jsonl"

    if [ -f "$CLAUDE_QUEUE" ]; then
        TASK_COUNT=$(wc -l < "$CLAUDE_QUEUE")
        echo -e "${GREEN}Queue file exists: $TASK_COUNT tasks${NC}"
        echo "Last task:"
        tail -1 "$CLAUDE_QUEUE" | jq -r '.id + " (" + .type + ")"' 2>/dev/null || tail -1 "$CLAUDE_QUEUE"
    else
        echo -e "${YELLOW}Queue file not created yet${NC}"
    fi
    echo ""
}

# Main monitoring loop
if [ "$1" == "--watch" ]; then
    # Continuous monitoring mode
    while true; do
        clear
        echo -e "${BOLD}=========================================="
        echo -e "🔫 Night Shift - Weaponized Pipeline (Auto-refresh)"
        echo -e "Press Ctrl+C to exit"
        echo -e "==========================================${NC}"
        echo ""

        check_timer
        check_service
        check_whisper
        check_outputs
        show_logs
        check_claude_queue

        echo -e "${YELLOW}Refreshing in 10 seconds...${NC}"
        sleep 10
    done
else
    # Single snapshot mode
    check_timer
    check_service
    check_whisper
    check_outputs
    show_logs
    check_claude_queue

    echo -e "${BOLD}=========================================="
    echo -e "Monitoring Commands:"
    echo -e "==========================================${NC}"
    echo ""
    echo "  Auto-refresh mode:"
    echo -e "    ${GREEN}./monitor_weaponized_pipeline.sh --watch${NC}"
    echo ""
    echo "  Follow pipeline log:"
    echo -e "    ${GREEN}tail -f ops/logs/weaponized_ep91_pipeline_*.log${NC}"
    echo ""
    echo "  Follow Whisper log:"
    echo -e "    ${GREEN}tail -f ops/logs/whisper_ep91_*.log${NC}"
    echo ""
    echo "  Check systemd journal:"
    echo -e "    ${GREEN}journalctl -u weaponized-ep91-pipeline.service -f${NC}"
    echo ""
fi
