#!/usr/bin/env bash
#
# J5A Resource Safety Gate - Blocking Checkpoint System
# Prevents parallel heavy processes from causing system freeze/OOM
#
# Usage:
#   source ops/resource_safety_gate.sh
#   acquire_whisper_lock || exit 1
#   # ... run whisper process ...
#   release_whisper_lock
#
# Design Principles:
#   - MUTUAL EXCLUSION: Only 1 Whisper Large process at a time
#   - MEMORY SAFETY: Enforce 14GB safe threshold
#   - THERMAL SAFETY: Block if CPU >80°C
#   - CLAUDE AWARENESS: Detect Claude Code operations
#   - BLOCKING GATES: No bypass - hard failures on safety violations
#

set -euo pipefail

# ==========================================
# CONFIGURATION - CLAUDE.md Constraints
# ==========================================

readonly MEMORY_SAFE_THRESHOLD_GB=14.0
readonly THERMAL_LIMIT_CELSIUS=80
readonly WHISPER_MEMORY_REQUIREMENT_GB=10.0  # Conservative estimate for Large-v3
readonly LOCKFILE_DIR="/tmp/j5a_locks"
readonly WHISPER_LOCKFILE="$LOCKFILE_DIR/whisper_large.lock"
readonly CLAUDE_DETECTION_THRESHOLD_MB=500  # If Claude using >500MB, it's active

mkdir -p "$LOCKFILE_DIR"

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

get_available_memory_gb() {
    local available_kb
    available_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    echo "scale=2; $available_kb / 1024 / 1024" | bc
}

get_cpu_temperature() {
    # Get the highest core temperature
    if command -v sensors &> /dev/null; then
        sensors | grep -i "Package id 0" | awk '{print $4}' | tr -d '+°C' | head -1
    else
        # Fallback to thermal zone
        local max_temp=0
        for zone in /sys/class/thermal/thermal_zone*/temp; do
            if [ -f "$zone" ]; then
                local temp_millicelsius
                temp_millicelsius=$(cat "$zone")
                local temp_celsius=$((temp_millicelsius / 1000))
                if [ "$temp_celsius" -gt "$max_temp" ]; then
                    max_temp=$temp_celsius
                fi
            fi
        done
        echo "$max_temp"
    fi
}

check_claude_active() {
    # Check if Claude Code is running and using significant resources
    local claude_mem_mb=0
    if pgrep -f "claude" > /dev/null 2>&1; then
        claude_mem_mb=$(ps aux | grep -i claude | grep -v grep | awk '{sum+=$6} END {print sum/1024}' | cut -d. -f1)
        if [ -z "$claude_mem_mb" ]; then
            claude_mem_mb=0
        fi
    fi

    if [ "$claude_mem_mb" -gt "$CLAUDE_DETECTION_THRESHOLD_MB" ]; then
        return 0  # Claude is active
    else
        return 1  # Claude not active
    fi
}

check_existing_whisper_processes() {
    local count
    count=$(pgrep -f "whisper.*large" | wc -l)
    echo "$count"
}

# ==========================================
# SAFETY GATE CHECKS
# ==========================================

pre_flight_safety_check() {
    local check_name="$1"
    local error_msg="$2"
    local check_result="$3"

    if [ "$check_result" != "PASS" ]; then
        echo "❌ SAFETY GATE BLOCKED: $check_name" >&2
        echo "   Reason: $error_msg" >&2
        echo "   Status: $check_result" >&2
        return 1
    else
        echo "✅ Safety check passed: $check_name"
        return 0
    fi
}

run_all_safety_checks() {
    local checks_passed=0
    local checks_total=5

    echo "=========================================="
    echo "J5A Resource Safety Gate - Pre-Flight"
    echo "=========================================="
    echo ""

    # CHECK 1: Memory Availability
    local available_mem_gb
    available_mem_gb=$(get_available_memory_gb)
    local mem_after_whisper
    mem_after_whisper=$(echo "$available_mem_gb - $WHISPER_MEMORY_REQUIREMENT_GB" | bc)
    local mem_check_result="PASS"

    if (( $(echo "$mem_after_whisper < 1.5" | bc -l) )); then
        mem_check_result="FAIL: ${mem_after_whisper}GB remaining < 1.5GB safety margin"
    fi

    echo "CHECK 1: Memory Availability"
    echo "  Available:     ${available_mem_gb}GB"
    echo "  Required:      ${WHISPER_MEMORY_REQUIREMENT_GB}GB"
    echo "  After launch:  ${mem_after_whisper}GB"
    echo "  Safe minimum:  1.5GB"

    if pre_flight_safety_check "Memory Availability" \
        "Insufficient memory for Whisper Large v3" \
        "$mem_check_result"; then
        ((checks_passed++))
    fi
    echo ""

    # CHECK 2: Thermal Safety
    local cpu_temp
    cpu_temp=$(get_cpu_temperature)
    local thermal_check_result="PASS"

    if [ -n "$cpu_temp" ]; then
        # Convert to integer for comparison
        local cpu_temp_int=${cpu_temp%.*}
        if [ "$cpu_temp_int" -gt "$THERMAL_LIMIT_CELSIUS" ]; then
            thermal_check_result="FAIL: ${cpu_temp}°C > ${THERMAL_LIMIT_CELSIUS}°C limit"
        fi
    fi

    echo "CHECK 2: Thermal Safety"
    echo "  Current temp:  ${cpu_temp}°C"
    echo "  Safe limit:    ${THERMAL_LIMIT_CELSIUS}°C"

    if pre_flight_safety_check "Thermal Safety" \
        "CPU temperature exceeds safe operating limit" \
        "$thermal_check_result"; then
        ((checks_passed++))
    fi
    echo ""

    # CHECK 3: Existing Whisper Processes
    local whisper_count
    whisper_count=$(check_existing_whisper_processes)
    local whisper_check_result="PASS"

    if [ "$whisper_count" -gt 0 ]; then
        whisper_check_result="FAIL: $whisper_count Whisper process(es) already running"
    fi

    echo "CHECK 3: Whisper Process Mutex"
    echo "  Running:       $whisper_count processes"
    echo "  Allowed:       0 (mutual exclusion)"

    if pre_flight_safety_check "Whisper Process Mutex" \
        "Another Whisper Large process is already running" \
        "$whisper_check_result"; then
        ((checks_passed++))
    fi
    echo ""

    # CHECK 4: Claude Code Activity
    local claude_check_result="WARNING"
    if check_claude_active; then
        echo "CHECK 4: Claude Code Activity"
        echo "  Status:        ⚠️  ACTIVE (using >${CLAUDE_DETECTION_THRESHOLD_MB}MB)"
        echo "  Impact:        Reduced available resources"
        echo "  Recommendation: Wait for Claude to complete or reduce parallel load"
        echo ""
        # Don't fail on Claude activity, just warn
        ((checks_passed++))
    else
        echo "CHECK 4: Claude Code Activity"
        echo "  Status:        ✅ Inactive or low resource usage"
        echo ""
        ((checks_passed++))
    fi

    # CHECK 5: Lock File Status
    local lock_check_result="PASS"
    if [ -f "$WHISPER_LOCKFILE" ]; then
        local lock_pid
        lock_pid=$(cat "$WHISPER_LOCKFILE" 2>/dev/null || echo "unknown")
        if ps -p "$lock_pid" > /dev/null 2>&1; then
            lock_check_result="FAIL: Lock held by PID $lock_pid"
        else
            echo "  Stale lock detected (PID $lock_pid no longer exists) - will be cleared"
            rm -f "$WHISPER_LOCKFILE"
            lock_check_result="PASS"
        fi
    fi

    echo "CHECK 5: Process Lock Status"
    echo "  Lockfile:      $WHISPER_LOCKFILE"
    echo "  Status:        $([ -f "$WHISPER_LOCKFILE" ] && echo "LOCKED" || echo "AVAILABLE")"

    if pre_flight_safety_check "Process Lock Status" \
        "Whisper lock is held by another process" \
        "$lock_check_result"; then
        ((checks_passed++))
    fi
    echo ""

    # FINAL VERDICT
    echo "=========================================="
    echo "Safety Checks: $checks_passed/$checks_total passed"
    echo "=========================================="
    echo ""

    if [ "$checks_passed" -eq "$checks_total" ]; then
        echo "✅ ALL SAFETY CHECKS PASSED - Operation cleared for execution"
        echo ""
        return 0
    else
        echo "❌ SAFETY GATE BLOCKED - Cannot proceed with heavy process"
        echo ""
        echo "Required actions:"
        echo "  - Wait for existing processes to complete"
        echo "  - Allow system to cool down if thermal limit exceeded"
        echo "  - Free up memory if usage too high"
        echo "  - Check for Claude Code operations and wait if necessary"
        echo ""
        return 1
    fi
}

# ==========================================
# LOCK MANAGEMENT
# ==========================================

acquire_whisper_lock() {
    # Run safety checks first
    if ! run_all_safety_checks; then
        echo "❌ Cannot acquire Whisper lock - safety checks failed" >&2
        return 1
    fi

    # Acquire lock
    echo $$ > "$WHISPER_LOCKFILE"
    echo "🔒 Whisper lock acquired (PID: $$)"
    echo ""
    return 0
}

release_whisper_lock() {
    if [ -f "$WHISPER_LOCKFILE" ]; then
        local lock_pid
        lock_pid=$(cat "$WHISPER_LOCKFILE")
        if [ "$lock_pid" = "$$" ]; then
            rm -f "$WHISPER_LOCKFILE"
            echo ""
            echo "🔓 Whisper lock released (PID: $$)"
        else
            echo "⚠️  Warning: Lock was held by different PID ($lock_pid vs $$)" >&2
        fi
    fi
}

# Ensure lock is released on exit
trap release_whisper_lock EXIT INT TERM

# ==========================================
# HELPER FUNCTIONS FOR PARALLEL CONTROL
# ==========================================

calculate_safe_parallel_count() {
    # Always return 1 for Whisper Large v3 - too risky for parallel
    echo "1"
}

wait_for_safe_conditions() {
    local max_wait_seconds="${1:-300}"  # Default 5 minutes
    local wait_interval=10
    local elapsed=0

    echo "Waiting for safe operating conditions..."

    while [ $elapsed -lt $max_wait_seconds ]; do
        if run_all_safety_checks > /dev/null 2>&1; then
            echo "✅ Safe conditions achieved after ${elapsed}s"
            return 0
        fi

        echo "  Still waiting... (${elapsed}s/${max_wait_seconds}s)"
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done

    echo "❌ Timeout: Safe conditions not achieved after ${max_wait_seconds}s" >&2
    return 1
}

# ==========================================
# MAIN EXECUTION (if run directly)
# ==========================================

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being run directly, not sourced
    echo "J5A Resource Safety Gate - Standalone Check"
    echo ""

    if run_all_safety_checks; then
        echo "System is safe for heavy processing operations."
        exit 0
    else
        echo "System is NOT safe for heavy processing operations."
        exit 1
    fi
fi
