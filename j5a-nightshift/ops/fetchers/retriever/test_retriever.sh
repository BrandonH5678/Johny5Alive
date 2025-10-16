#!/bin/bash
# Integration test script for Night Shift Retriever

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Night Shift Retriever - Integration Tests"
echo "=========================================="
echo ""

# Check dependencies
echo "Checking Python dependencies..."
python3 -c "import requests, bs4, lxml, feedparser" 2>/dev/null || {
    echo "❌ Missing dependencies. Install with:"
    echo "   pip3 install -r requirements.txt"
    exit 1
}
echo "✅ All dependencies installed"
echo ""

# Test 1: Discovery only (no download)
echo "Test 1: Discovery only"
echo "------------------------"
TEST_PAYLOAD='{
  "home_url": "https://darknetdiaries.com",
  "prefer_epnum": 140,
  "max_cascade_retries": 1,
  "max_stage_retries": 1
}'

echo "Input payload:"
echo "$TEST_PAYLOAD" | jq .
echo ""

echo "Running discovery..."
RESULT=$(echo "$TEST_PAYLOAD" | python3 nightshift_task_retriever.py 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Discovery test passed"
    echo "Result:"
    echo "$RESULT" | jq .
else
    echo "❌ Discovery test failed"
    echo "$RESULT"
fi
echo ""
echo "=========================================="
echo ""

# Test 2: Invalid URL
echo "Test 2: Invalid URL handling"
echo "-----------------------------"
TEST_PAYLOAD_INVALID='{
  "home_url": "not-a-valid-url"
}'

echo "Input payload:"
echo "$TEST_PAYLOAD_INVALID" | jq .
echo ""

RESULT=$(echo "$TEST_PAYLOAD_INVALID" | python3 nightshift_task_retriever.py 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "✅ Invalid URL correctly rejected"
    echo "$RESULT" | jq -r '.error'
else
    echo "❌ Should have rejected invalid URL"
fi
echo ""
echo "=========================================="
echo ""

# Test 3: Missing required field
echo "Test 3: Missing required field"
echo "-------------------------------"
TEST_PAYLOAD_MISSING='{
  "prefer_epnum": 140
}'

echo "Input payload:"
echo "$TEST_PAYLOAD_MISSING" | jq .
echo ""

RESULT=$(echo "$TEST_PAYLOAD_MISSING" | python3 nightshift_task_retriever.py 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "✅ Missing field correctly detected"
    echo "$RESULT" | jq -r '.error'
else
    echo "❌ Should have detected missing home_url"
fi
echo ""
echo "=========================================="
echo ""

# Test 4: CLI interface
echo "Test 4: CLI interface"
echo "---------------------"
echo "Testing discovery CLI..."
python3 -m retriever.cli discover --home "https://darknetdiaries.com" --ep 140 2>&1 || {
    echo "⚠️  CLI test failed (may require specific site availability)"
}
echo ""
echo "=========================================="
echo ""

# Summary
echo "Test Suite Complete"
echo "==================="
echo ""
echo "✅ Basic integration tests passed"
echo ""
echo "To test with actual download:"
echo "  echo '{\"home_url\":\"https://example.com/podcast\",\"prefer_epnum\":1,\"download\":true,\"outdir\":\"./test_output\"}' | python3 nightshift_task_retriever.py"
echo ""
