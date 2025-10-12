#!/bin/bash
# Quick installation script for J5A Nightshift automation
# Run this with: sudo ./install_automation.sh

set -euo pipefail

echo "Installing J5A Nightshift Automation..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run with sudo"
    echo "Usage: sudo ./install_automation.sh"
    exit 1
fi

cd /home/johnny5/Johny5Alive/j5a-nightshift

# Install systemd files
echo "1. Installing systemd service and timer..."
cp j5a-nightshift.service /etc/systemd/system/
cp j5a-nightshift.timer /etc/systemd/system/
systemctl daemon-reload
echo "   ✅ Systemd files installed"

# Install log rotation
echo "2. Installing log rotation..."
cp j5a-nightshift-logrotate.conf /etc/logrotate.d/j5a-nightshift
echo "   ✅ Log rotation configured"

# Enable and start timer
echo "3. Enabling timer..."
systemctl enable j5a-nightshift.timer
systemctl start j5a-nightshift.timer
echo "   ✅ Timer enabled and started"

# Show status
echo ""
echo "Installation complete!"
echo ""
echo "Status:"
systemctl status j5a-nightshift.timer --no-pager | head -n 10

echo ""
echo "Next run:"
systemctl list-timers --all | grep nightshift

echo ""
echo "To test manually: sudo systemctl start j5a-nightshift.service"
echo "To monitor: ./ops/monitor_nightshift.sh"
