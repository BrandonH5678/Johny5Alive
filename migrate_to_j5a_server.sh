#!/bin/bash
#
# Migrate Night Shift + Sherlock to J5A Server
# Run on Mac Mini to prepare migration
#
set -e

echo "======================================================================"
echo "J5A Migration to J5A Server - Preparation Script"
echo "======================================================================"
echo ""

# Configuration
J5A_SERVER="${1:-j5a-server}"  # Override with argument
MIGRATION_DIR="/tmp/j5a_migration"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Target server: $J5A_SERVER"
echo "Migration staging: $MIGRATION_DIR"
echo ""

# Create staging directory
mkdir -p "$MIGRATION_DIR"
cd "$MIGRATION_DIR"

echo "Step 1: Package Sherlock system..."
tar czf sherlock_${TIMESTAMP}.tar.gz -C /home/johnny5 Sherlock/
echo "  ✓ Sherlock packaged"

echo ""
echo "Step 2: Package Night Shift infrastructure..."
tar czf nightshift_${TIMESTAMP}.tar.gz \
    -C /home/johnny5/Johny5Alive \
    j5a-nightshift/ \
    queue/ \
    j5a_universe_memory.py \
    phoenix_validator.py \
    kaizen_optimizer.py \
    phoenix_validation.db \
    kaizen_improvements.db \
    2>/dev/null || echo "  ⚠️  Some files may not exist yet"
echo "  ✓ Night Shift packaged"

echo ""
echo "Step 3: Package configuration files..."
tar czf config_${TIMESTAMP}.tar.gz \
    -C /home/johnny5 \
    J5A_CONSTITUTION.md \
    J5A_STRATEGIC_AI_PRINCIPLES.md \
    J5A_INTEGRATION_MAP.md \
    J5A_CHANGE_LOG.md \
    J5A_UNIVERSE_ACTIVE_MEMORY_AND_ADAPTIVE_FEEDBACK_ARCHITECTURE.md \
    Johny5Alive/CLAUDE.md \
    2>/dev/null || echo "  ⚠️  Some config files may not exist"
echo "  ✓ Configuration packaged"

echo ""
echo "Step 4: Export systemd services..."
mkdir -p systemd_services
sudo cp /etc/systemd/system/j5a-nightshift.service systemd_services/ 2>/dev/null || echo "  ⚠️  Service file not found"
sudo cp /etc/systemd/system/j5a-nightshift.timer systemd_services/ 2>/dev/null || echo "  ⚠️  Timer file not found"
tar czf systemd_${TIMESTAMP}.tar.gz systemd_services/
echo "  ✓ Systemd services exported"

echo ""
echo "======================================================================"
echo "Migration packages ready in: $MIGRATION_DIR"
echo "======================================================================"
echo ""
ls -lh "$MIGRATION_DIR"/*.tar.gz

echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Transfer to J5A server:"
echo "   scp $MIGRATION_DIR/*.tar.gz $J5A_SERVER:/tmp/"
echo ""
echo "2. On J5A server, extract:"
echo "   cd /tmp"
echo "   tar xzf sherlock_${TIMESTAMP}.tar.gz -C /home/johnny5/"
echo "   tar xzf nightshift_${TIMESTAMP}.tar.gz -C /home/johnny5/Johny5Alive/"
echo "   tar xzf config_${TIMESTAMP}.tar.gz -C /home/johnny5/"
echo "   tar xzf systemd_${TIMESTAMP}.tar.gz"
echo "   sudo cp systemd_services/* /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable j5a-nightshift.timer"
echo ""
echo "3. Install dependencies on J5A server:"
echo "   # Python packages, Ollama, faster-whisper, etc."
echo ""
echo "4. Test on J5A server:"
echo "   systemctl status j5a-nightshift.timer"
echo "   python3 /home/johnny5/Sherlock/morning_review_generator.py"
echo ""
echo "5. Disable on Mac Mini:"
echo "   sudo systemctl disable j5a-nightshift.timer"
echo "   sudo systemctl stop j5a-nightshift.timer"
echo ""

echo "======================================================================"
echo "Migration preparation complete!"
echo "======================================================================"
