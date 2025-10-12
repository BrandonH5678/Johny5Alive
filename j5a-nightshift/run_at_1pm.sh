#!/bin/bash
# One-time Night Shift run at 1:15pm today
# Run this script with: sudo ./run_at_1pm.sh

systemd-run --on-calendar="2025-10-11 13:15:00" --unit=j5a-nightshift-oneshot /bin/systemctl start j5a-nightshift.service

echo ""
echo "One-time run scheduled for 1:15pm today"
echo ""
echo "To verify:"
echo "  systemctl list-timers | grep nightshift"
