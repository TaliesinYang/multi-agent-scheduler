#!/usr/bin/env python3
"""
Simple test script for CLI adapters (no pytest required)
"""

import json
from src.cli_adapters import CLIOutputAdapter

def test_gemini_format():
    """Test Gemini CLI format unwrapping"""
    print("Test 1: Gemini format...")

    output = json.dumps({
        "response": "```json\n[\n  {\"task_id\": \"task1\", \"prompt\": \"Test\"}\n]\n```",
        "stats": {"models": {}}
    })

    result = CLIOutputAdapter.unwrap(output)

    assert result['format'] == 'gemini', f"Expected format 'gemini', got '{result['format']}'"
    assert '```' not in result['content'], "Markdown blocks should be stripped"
    assert '"task_id"' in result['content'], "Content should contain task_id"

    print("  ✓ Gemini format detected correctly")
    print("  ✓ Markdown blocks stripped")
    print(f"  ✓ Content: {result['content'][:50]}...")

def test_claude_format():
    """Test Claude CLI format unwrapping"""
    print("\nTest 2: Claude format...")

    output = json.dumps({
        "type": "result",
        "result": "Task completed",
        "total_cost_usd": 0.01
    })

    result = CLIOutputAdapter.unwrap(output)

    assert result['format'] == 'claude', f"Expected format 'claude', got '{result['format']}'"
    assert result['content'] == "Task completed", f"Unexpected content: {result['content']}"
    assert result['metadata']['cost_usd'] == 0.01, "Metadata not preserved"

    print("  ✓ Claude format detected correctly")
    print("  ✓ Metadata preserved")
    print(f"  ✓ Content: {result['content']}")

def test_raw_format():
    """Test raw text handling"""
    print("\nTest 3: Raw format...")

    output = "Plain text response"
    result = CLIOutputAdapter.unwrap(output)

    assert result['format'] == 'raw', f"Expected format 'raw', got '{result['format']}'"
    assert result['content'] == output, "Content should match input"

    print("  ✓ Raw format detected correctly")
    print(f"  ✓ Content: {result['content']}")

def test_markdown_stripping():
    """Test markdown code block stripping"""
    print("\nTest 4: Markdown stripping...")

    cases = [
        ("```json\n{\"key\": \"value\"}\n```", '{"key": "value"}'),
        ("```\nsome code\n```", "some code"),
        ("No markdown here", "No markdown here"),
    ]

    for input_text, expected in cases:
        result = CLIOutputAdapter._strip_markdown_blocks(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"  ✓ Stripped: {input_text[:30]}... → {result[:30]}...")

def test_gemini_real_world():
    """Test real Gemini output from logs"""
    print("\nTest 5: Real Gemini output...")

    # Simulated real output from Gemini CLI
    output = json.dumps({
        "response": "```json\n[\n  {\"id\": \"task1\", \"prompt\": \"Set up FastAPI\", \"task_type\": \"coding\"}\n]\n```",
        "stats": {
            "models": {
                "gemini-2.5-flash-lite": {"tokens": 100}
            }
        }
    })

    result = CLIOutputAdapter.unwrap(output)

    assert result['format'] == 'gemini'
    assert '```' not in result['content']
    assert result['content'].startswith('[')
    assert result['content'].endswith(']')

    # Should be valid JSON after unwrapping
    tasks = json.loads(result['content'])
    assert len(tasks) == 1
    assert tasks[0]['id'] == 'task1'

    print("  ✓ Real-world Gemini output processed correctly")
    print(f"  ✓ Extracted {len(tasks)} task(s)")
    print(f"  ✓ Task: {tasks[0]['prompt']}")

if __name__ == '__main__':
    print("=" * 60)
    print("CLI Adapter Tests (Simple)")
    print("=" * 60)

    try:
        test_gemini_format()
        test_claude_format()
        test_raw_format()
        test_markdown_stripping()
        test_gemini_real_world()

        print("\n" + "=" * 60)
        print("✅ All tests PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
