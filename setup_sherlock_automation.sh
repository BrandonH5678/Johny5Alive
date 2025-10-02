#!/bin/bash
"""
Setup Sherlock Targeting Officer Automation

Configures nightly 1am execution via cron for Targeting Officer.

Usage:
    chmod +x setup_sherlock_automation.sh
    ./setup_sherlock_automation.sh
"""

echo "========================================================================"
echo "Sherlock Targeting Officer Automation Setup"
echo "========================================================================"
echo ""

# Define paths
J5A_DIR="/home/johnny5/Johny5Alive"
INTEGRATION_SCRIPT="$J5A_DIR/src/j5a_sherlock_integration.py"
LOG_DIR="$J5A_DIR/logs"

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p "$LOG_DIR"

# Check if integration script exists
if [ ! -f "$INTEGRATION_SCRIPT" ]; then
    echo "❌ Error: Integration script not found at $INTEGRATION_SCRIPT"
    exit 1
fi

echo "✅ Integration script found: $INTEGRATION_SCRIPT"

# Make script executable
chmod +x "$INTEGRATION_SCRIPT"
echo "✅ Script made executable"

# Create cron job entry
CRON_JOB="0 1 * * * cd $J5A_DIR && /usr/bin/python3 $INTEGRATION_SCRIPT --run-targeting-officer --auto >> $LOG_DIR/sherlock_automation.log 2>&1"

echo ""
echo "========================================================================"
echo "Cron Job Configuration"
echo "========================================================================"
echo ""
echo "The following cron job will be added:"
echo ""
echo "$CRON_JOB"
echo ""
echo "This will:"
echo "  • Run daily at 1:00 AM"
echo "  • Execute Targeting Officer sweep"
echo "  • Import validated packages to J5A queue"
echo "  • Log all output to $LOG_DIR/sherlock_automation.log"
echo ""

# Ask for confirmation
read -p "Add this cron job? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added successfully"
    echo ""
    echo "Current crontab:"
    echo "----------------------------------------"
    crontab -l | grep "j5a_sherlock_integration"
    echo "----------------------------------------"
else
    echo "❌ Cron job not added"
    echo ""
    echo "To add manually, run:"
    echo "  crontab -e"
    echo ""
    echo "Then add this line:"
    echo "  $CRON_JOB"
fi

echo ""
echo "========================================================================"
echo "Setup Complete"
echo "========================================================================"
echo ""
echo "To test the integration manually, run:"
echo "  python3 $INTEGRATION_SCRIPT --run-targeting-officer"
echo ""
echo "To view automation logs:"
echo "  tail -f $LOG_DIR/sherlock_automation.log"
echo ""
echo "To remove the cron job later:"
echo "  crontab -e"
echo "  # Delete the line containing 'j5a_sherlock_integration'"
echo ""
