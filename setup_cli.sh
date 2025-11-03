#!/bin/bash
# CLI Setup and Testing Script

echo "========================================"
echo "  🔧 CLI Setup Helper"
echo "========================================"
echo ""

# Check if claude is installed
echo "1️⃣ Checking Claude CLI installation..."
if command -v claude &> /dev/null; then
    echo "   ✅ Claude CLI installed: $(which claude)"
    claude --version 2>&1 | head -1
else
    echo "   ❌ Claude CLI not found"
    echo "   Install: npm install -g @anthropic-ai/claude-code"
    exit 1
fi
echo ""

# Test authentication
echo "2️⃣ Testing Claude CLI authentication..."
echo "   (This will timeout after 5 seconds if not authenticated)"
echo ""

timeout 5 claude -p "Respond with: OK" > /tmp/claude_test.txt 2>&1
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "   ✅ Claude CLI is authenticated and working!"
    echo "   Response: $(cat /tmp/claude_test.txt | head -2)"
    rm /tmp/claude_test.txt
    echo ""
    echo "🎉 You can now run:"
    echo "   python demo_cli_full.py"
    echo "   python smart_demo.py --preset  # Select option 2 (CLI mode)"
    exit 0
else
    echo "   ⚠️  Claude CLI needs authentication"
    echo ""
    echo "========================================"
    echo "  📝 Authentication Steps:"
    echo "========================================"
    echo ""
    echo "Run this command:"
    echo ""
    echo "   claude auth login"
    echo ""
    echo "This will:"
    echo "  1. Open your browser"
    echo "  2. Ask you to login to Claude"
    echo "  3. Authorize Claude CLI"
    echo "  4. Return to terminal"
    echo ""
    echo "Then run this script again to verify."
    echo ""
    echo "========================================"
    echo "  💡 Alternative: Use Mock Mode"
    echo "========================================"
    echo ""
    echo "If you don't want to authenticate now,"
    echo "you can use Mock mode for demonstration:"
    echo ""
    echo "   python smart_demo.py --test"
    echo ""
    echo "Mock mode demonstrates all scheduling"
    echo "features without requiring authentication."
    echo ""
fi
