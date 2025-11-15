#!/bin/bash

# Test Gemini CLI project configuration
# This script verifies that .gemini/GEMINI.md overrides global settings

cd "$(dirname "$0")"

echo "=== Testing Gemini CLI Project Configuration ==="
echo ""
echo "1. Testing basic response (should be in English, not Chinese):"
echo "---"
gemini -p "Respond with exactly one word: 'SUCCESS'"
echo ""
echo "---"
echo ""

echo "2. Testing JSON format (for task decomposition simulation):"
echo "---"
gemini -p "Return a JSON array with 3 simple tasks. Format: [{\"task_id\": \"task1\", \"prompt\": \"...\"}]. ONLY return the JSON, no explanatory text."
echo ""
echo "---"
echo ""

echo "3. Checking if three-stage workflow is disabled (should NOT see【分析问题】):"
echo "---"
gemini -p "How do I implement a REST API?"
echo ""
echo "---"
echo ""

echo "=== Test Complete ==="
echo ""
echo "Expected results:"
echo "  ✓ All responses in English"
echo "  ✓ No【分析问题】format"
echo "  ✓ JSON responses are valid JSON"
