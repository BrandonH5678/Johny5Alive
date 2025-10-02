#!/bin/bash
# Setup Sherlock Research Execution

echo "🔬 Sherlock Research Execution Setup"
echo "===================================="
echo ""

# Check Python version
echo "1. Checking Python..."
python3 --version

# Install dependencies
echo ""
echo "2. Installing dependencies..."
echo "   (This will use --break-system-packages if needed)"
echo ""

pip3 install anthropic beautifulsoup4 requests lxml 2>/dev/null || \
pip3 install anthropic beautifulsoup4 requests lxml --break-system-packages 2>/dev/null || \
pip3 install anthropic beautifulsoup4 requests lxml --user 2>/dev/null || \
echo "   ⚠️  Could not install packages. Please install manually or use venv."

# Check API key
echo ""
echo "3. Checking ANTHROPIC_API_KEY..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "   ❌ ANTHROPIC_API_KEY not set"
    echo ""
    echo "   To set your API key:"
    echo "   export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    echo "   Get your key at: https://console.anthropic.com/settings/keys"
    echo ""
else
    echo "   ✅ API key is set (${#ANTHROPIC_API_KEY} characters)"
fi

# Test import
echo ""
echo "4. Testing imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    import anthropic
    print('   ✅ anthropic')
except ImportError:
    print('   ❌ anthropic (not installed)')

try:
    from bs4 import BeautifulSoup
    print('   ✅ beautifulsoup4')
except ImportError:
    print('   ❌ beautifulsoup4 (not installed)')

try:
    import requests
    print('   ✅ requests')
except ImportError:
    print('   ❌ requests (not installed)')

try:
    from sherlock_research_executor import SherlockResearchExecutor
    print('   ✅ SherlockResearchExecutor')
except Exception as e:
    print(f'   ❌ SherlockResearchExecutor ({e})')
"

# Run test
echo ""
echo "5. Running test execution..."
echo ""

python3 src/sherlock_research_executor.py 2>/dev/null

echo ""
echo "===================================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. If API key not set: export ANTHROPIC_API_KEY='your-key'"
echo "  2. Test single package: python3 src/sherlock_research_executor.py"
echo "  3. Run queue: python3 src/overnight_queue_manager.py --process-queue"
echo ""
echo "Documentation: SHERLOCK_EXECUTION_IMPLEMENTATION.md"
echo "===================================="
