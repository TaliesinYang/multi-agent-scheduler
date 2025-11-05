"""
Unit tests for CLI Output Adapters

Tests the CLIOutputAdapter class to ensure correct detection
and unwrapping of different CLI output formats.

Run with: pytest tests/test_cli_adapters.py -v
"""

import pytest
import json
from src.cli_adapters import CLIOutputAdapter, unwrap_cli_output, get_cli_metadata


class TestFormatDetection:
    """Test CLI format detection"""

    def test_detect_claude_format(self):
        """Should detect Claude CLI format"""
        output = json.dumps({
            "type": "result",
            "result": "Hello world",
            "total_cost_usd": 0.01
        })
        assert CLIOutputAdapter.detect_format(output) == 'claude'

    def test_detect_gemini_format(self):
        """Should detect Gemini CLI format"""
        output = json.dumps({
            "response": "Hello world",
            "stats": {"models": {}}
        })
        assert CLIOutputAdapter.detect_format(output) == 'gemini'

    def test_detect_raw_format(self):
        """Should detect raw text format"""
        output = "Just plain text"
        assert CLIOutputAdapter.detect_format(output) == 'raw'

    def test_detect_invalid_json(self):
        """Should handle invalid JSON as raw"""
        output = '{"incomplete": '
        assert CLIOutputAdapter.detect_format(output) == 'raw'


class TestClaudeUnwrapping:
    """Test Claude CLI output unwrapping"""

    def test_unwrap_basic_claude(self):
        """Should unwrap basic Claude output"""
        output = json.dumps({
            "type": "result",
            "result": "Task completed successfully",
            "total_cost_usd": 0.015,
            "duration_ms": 5000
        })

        result = CLIOutputAdapter.unwrap(output)

        assert result['content'] == "Task completed successfully"
        assert result['format'] == 'claude'
        assert result['metadata']['cost_usd'] == 0.015
        assert result['metadata']['duration_ms'] == 5000

    def test_unwrap_claude_with_markdown(self):
        """Should strip markdown from Claude output"""
        output = json.dumps({
            "type": "result",
            "result": "```json\n{\"key\": \"value\"}\n```"
        })

        result = CLIOutputAdapter.unwrap(output)

        assert result['content'] == '{"key": "value"}'
        assert '```' not in result['content']

    def test_unwrap_claude_with_full_metadata(self):
        """Should preserve all Claude metadata"""
        output = json.dumps({
            "type": "result",
            "result": "Content",
            "total_cost_usd": 0.025,
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "modelUsage": {"sonnet": {"tokens": 150}},
            "duration_ms": 3000,
            "duration_api_ms": 2500,
            "num_turns": 3,
            "session_id": "sess_123"
        })

        result = CLIOutputAdapter.unwrap(output)

        assert result['metadata']['cost_usd'] == 0.025
        assert result['metadata']['usage']['input_tokens'] == 100
        assert result['metadata']['num_turns'] == 3
        assert result['metadata']['session_id'] == "sess_123"


class TestGeminiUnwrapping:
    """Test Gemini CLI output unwrapping"""

    def test_unwrap_basic_gemini(self):
        """Should unwrap basic Gemini output"""
        output = json.dumps({
            "response": "Analysis complete",
            "stats": {
                "models": {"gemini-2.5-pro": {"tokens": 100}}
            }
        })

        result = CLIOutputAdapter.unwrap(output)

        assert result['content'] == "Analysis complete"
        assert result['format'] == 'gemini'
        assert 'models' in result['metadata']

    def test_unwrap_gemini_with_markdown_json(self):
        """Should strip markdown code blocks from Gemini JSON output"""
        output = json.dumps({
            "response": "```json\n[\n  {\"task_id\": \"task1\", \"prompt\": \"Do something\"}\n]\n```",
            "stats": {}
        })

        result = CLIOutputAdapter.unwrap(output)

        # Should remove markdown wrapper
        assert '```' not in result['content']
        assert result['content'].startswith('[')
        assert '"task_id"' in result['content']

    def test_unwrap_gemini_with_stats(self):
        """Should extract all Gemini stats metadata"""
        output = json.dumps({
            "response": "Done",
            "stats": {
                "models": {
                    "gemini-2.5-flash-lite": {"tokens": 50}
                },
                "tools": {"totalCalls": 5},
                "files": {"totalLinesAdded": 100}
            }
        })

        result = CLIOutputAdapter.unwrap(output)

        assert result['metadata']['models']['gemini-2.5-flash-lite']['tokens'] == 50
        assert result['metadata']['tools']['totalCalls'] == 5
        assert result['metadata']['files']['totalLinesAdded'] == 100


class TestMarkdownStripping:
    """Test markdown code block stripping"""

    def test_strip_json_block(self):
        """Should strip ```json blocks"""
        text = "```json\n{\"key\": \"value\"}\n```"
        result = CLIOutputAdapter._strip_markdown_blocks(text)
        assert result == '{"key": "value"}'

    def test_strip_generic_block(self):
        """Should strip generic ``` blocks"""
        text = "```\nsome code\n```"
        result = CLIOutputAdapter._strip_markdown_blocks(text)
        assert result == 'some code'

    def test_strip_python_block(self):
        """Should strip ```python blocks"""
        text = "```python\nprint('hello')\n```"
        result = CLIOutputAdapter._strip_markdown_blocks(text)
        assert result == "print('hello')"

    def test_no_strip_without_markdown(self):
        """Should not modify text without markdown"""
        text = "Plain text without markdown"
        result = CLIOutputAdapter._strip_markdown_blocks(text)
        assert result == text

    def test_strip_multiline_json(self):
        """Should strip markdown from multiline JSON"""
        text = """```json
[
  {
    "id": "task1",
    "prompt": "Test"
  }
]
```"""
        result = CLIOutputAdapter._strip_markdown_blocks(text)
        assert '```' not in result
        assert '"id": "task1"' in result


class TestRawOutput:
    """Test raw text output handling"""

    def test_unwrap_raw_text(self):
        """Should handle raw text output"""
        output = "Simple text response"
        result = CLIOutputAdapter.unwrap(output)

        assert result['content'] == output
        assert result['format'] == 'raw'
        assert result['metadata'] == {}

    def test_unwrap_raw_with_markdown(self):
        """Should strip markdown from raw text"""
        output = "```\nCode snippet\n```"
        result = CLIOutputAdapter.unwrap(output)

        assert result['content'] == "Code snippet"


class TestConvenienceFunctions:
    """Test convenience helper functions"""

    def test_unwrap_cli_output_gemini(self):
        """Should extract only content from Gemini output"""
        output = json.dumps({
            "response": "Hello",
            "stats": {}
        })
        content = unwrap_cli_output(output)
        assert content == "Hello"

    def test_get_cli_metadata_claude(self):
        """Should extract only metadata from Claude output"""
        output = json.dumps({
            "type": "result",
            "result": "Content",
            "total_cost_usd": 0.02
        })
        metadata = get_cli_metadata(output)
        assert metadata['cost_usd'] == 0.02


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_string(self):
        """Should handle empty string input"""
        result = CLIOutputAdapter.unwrap("")
        assert result['content'] == ""
        assert result['format'] == 'raw'

    def test_null_values(self):
        """Should handle null/None values in JSON"""
        output = json.dumps({
            "type": "result",
            "result": None
        })
        result = CLIOutputAdapter.unwrap(output)
        assert result['content'] == ""  # None should become empty string

    def test_malformed_claude_json(self):
        """Should handle malformed Claude JSON gracefully"""
        output = '{"type": "result", "result":'  # Incomplete JSON
        result = CLIOutputAdapter.unwrap(output)
        assert result['format'] == 'raw'  # Falls back to raw
        assert result['content'] == output

    def test_unicode_content(self):
        """Should handle Unicode characters"""
        output = json.dumps({
            "response": "你好世界 🌍",
            "stats": {}
        })
        result = CLIOutputAdapter.unwrap(output)
        assert "你好世界" in result['content']
        assert "🌍" in result['content']

    def test_nested_json_in_response(self):
        """Should handle JSON nested in response field"""
        output = json.dumps({
            "response": '{"nested": "json"}',
            "stats": {}
        })
        result = CLIOutputAdapter.unwrap(output)
        # Should return the nested JSON as string
        assert result['content'] == '{"nested": "json"}'


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
