#!/bin/bash
#
# Rsync Migration to J5A Server
# Much faster than tar - transfers compressed, can resume
#
set -e

# Configuration
J5A_SERVER="${1:-j5a-server}"
J5A_USER="${2:-johnny5}"

echo "======================================================================"
echo "J5A Rsync Migration to $J5A_USER@$J5A_SERVER"
echo "======================================================================"
echo ""

# Test SSH connection first
echo "Testing SSH connection to $J5A_SERVER..."
if ssh -o ConnectTimeout=5 "$J5A_USER@$J5A_SERVER" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✓ SSH connection working"
else
    echo "❌ Cannot connect to $J5A_SERVER"
    echo ""
    echo "Please ensure:"
    echo "  1. J5A server is running"
    echo "  2. SSH keys are set up (or you can enter password)"
    echo "  3. Hostname/IP is correct"
    echo ""
    echo "Usage: $0 <hostname-or-ip> [username]"
    echo "Example: $0 192.168.1.100 johnny5"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Step 1: Sync Sherlock system (37GB - will take ~10-15 minutes)"
echo "======================================================================"
echo ""

rsync -avz --progress \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.log' \
    /home/johnny5/Sherlock/ \
    "$J5A_USER@$J5A_SERVER:/home/johnny5/Sherlock/"

echo ""
echo "✓ Sherlock synced"
echo ""

echo "======================================================================"
echo "Step 2: Sync Night Shift infrastructure"
echo "======================================================================"
echo ""

# Create target directories
ssh "$J5A_USER@$J5A_SERVER" "mkdir -p /home/johnny5/Johny5Alive"

# Sync j5a-nightshift directory
rsync -avz --progress \
    /home/johnny5/Johny5Alive/j5a-nightshift/ \
    "$J5A_USER@$J5A_SERVER:/home/johnny5/Johny5Alive/j5a-nightshift/"

# Sync queue directory
rsync -avz --progress \
    /home/johnny5/Johny5Alive/queue/ \
    "$J5A_USER@$J5A_SERVER:/home/johnny5/Johny5Alive/queue/"

# Sync individual files
rsync -avz --progress \
    /home/johnny5/Johny5Alive/j5a_universe_memory.py \
    /home/johnny5/Johny5Alive/phoenix_validator.py \
    /home/johnny5/Johny5Alive/kaizen_optimizer.py \
    "$J5A_USER@$J5A_SERVER:/home/johnny5/Johny5Alive/"

# Sync databases
rsync -avz --progress \
    /home/johnny5/Johny5Alive/phoenix_validation.db \
    /home/johnny5/Johny5Alive/kaizen_improvements.db \
    "$J5A_USER@$J5A_SERVER:/home/johnny5/Johny5Alive/" 2>/dev/null || echo "  (Some DB files may not exist yet - OK)"

echo ""
echo "✓ Night Shift infrastructure synced"
echo ""

echo "======================================================================"
echo "Step 3: Sync configuration files"
echo "======================================================================"
echo ""

rsync -avz --progress \
    /home/johnny5/J5A_CONSTITUTION.md \
    /home/johnny5/J5A_STRATEGIC_AI_PRINCIPLES.md \
    /home/johnny5/J5A_INTEGRATION_MAP.md \
    /home/johnny5/J5A_CHANGE_LOG.md \
    /home/johnny5/J5A_UNIVERSE_ACTIVE_MEMORY_AND_ADAPTIVE_FEEDBACK_ARCHITECTURE.md \
    /home/johnny5/Johny5Alive/CLAUDE.md \
    "$J5A_USER@$J5A_SERVER:/home/johnny5/" 2>/dev/null || echo "  (Some config files may not exist - OK)"

echo ""
echo "✓ Configuration files synced"
echo ""

echo "======================================================================"
echo "Step 4: Transfer systemd services"
echo "======================================================================"
echo ""

# Create temp directory on remote server
ssh "$J5A_USER@$J5A_SERVER" "mkdir -p /tmp/j5a_systemd"

# Copy systemd files if they exist
if [ -f /etc/systemd/system/j5a-nightshift.service ]; then
    sudo cat /etc/systemd/system/j5a-nightshift.service | \
        ssh "$J5A_USER@$J5A_SERVER" "cat > /tmp/j5a_systemd/j5a-nightshift.service"
    echo "  ✓ Transferred j5a-nightshift.service"
fi

if [ -f /etc/systemd/system/j5a-nightshift.timer ]; then
    sudo cat /etc/systemd/system/j5a-nightshift.timer | \
        ssh "$J5A_USER@$J5A_SERVER" "cat > /tmp/j5a_systemd/j5a-nightshift.timer"
    echo "  ✓ Transferred j5a-nightshift.timer"
fi

# Also transfer the NEW service file we created
if [ -f /tmp/j5a-nightshift.service.new ]; then
    cat /tmp/j5a-nightshift.service.new | \
        ssh "$J5A_USER@$J5A_SERVER" "cat > /tmp/j5a_systemd/j5a-nightshift.service.new"
    echo "  ✓ Transferred updated service file"
fi

echo ""
echo "✓ Systemd services transferred to /tmp/j5a_systemd/ on J5A server"
echo ""

echo "======================================================================"
echo "Migration Complete!"
echo "======================================================================"
echo ""
echo "NEXT STEPS ON J5A SERVER:"
echo ""
echo "1. SSH to J5A server:"
echo "   ssh $J5A_USER@$J5A_SERVER"
echo ""
echo "2. Install systemd services:"
echo "   sudo cp /tmp/j5a_systemd/j5a-nightshift.service.new /etc/systemd/system/j5a-nightshift.service"
echo "   sudo cp /tmp/j5a_systemd/j5a-nightshift.timer /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable j5a-nightshift.timer"
echo "   sudo systemctl start j5a-nightshift.timer"
echo ""
echo "3. Install dependencies (if not already installed):"
echo "   pip3 install anthropic openai faster-whisper jsonschema"
echo "   # Install Ollama if needed: curl -fsSL https://ollama.com/install.sh | sh"
echo ""
echo "4. Set Anthropic API key:"
echo "   export ANTHROPIC_API_KEY='your-key-here'"
echo "   # Or add to ~/.bashrc for persistence"
echo ""
echo "5. Test Night Shift:"
echo "   systemctl status j5a-nightshift.timer"
echo "   python3 /home/johnny5/Sherlock/morning_review_generator.py"
echo ""
echo "6. DISABLE on Mac Mini (prevent dual runs):"
echo "   sudo systemctl stop j5a-nightshift.timer"
echo "   sudo systemctl disable j5a-nightshift.timer"
echo ""
echo "======================================================================"
