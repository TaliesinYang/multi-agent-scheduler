"""
CLI Output Adapters for Multi-Agent Scheduler

This module provides unified adapters for different CLI output formats,
ensuring consistent parsing regardless of which CLI tool is used.

Supported CLI Formats:
- Claude CLI: {"type":"result", "result":"...", "usage":{...}}
- Gemini CLI: {"response":"...", "stats":{...}}
- Codex CLI: Raw text or structured format
- Raw text: Unstructured output

Author: Multi-Agent Scheduler Team
License: MIT
"""

from typing import Dict, Any, Optional
import json
import re


class CLIOutputAdapter:
    """
    Unified adapter for different CLI output formats.

    This adapter automatically detects and unwraps CLI-specific output
    formats into a standardized structure for consistent processing.

    Example:
        >>> raw_output = '{"response": "Hello", "stats": {...}}'
        >>> result = CLIOutputAdapter.unwrap(raw_output)
        >>> print(result['content'])  # "Hello"
        >>> print(result['format'])   # "gemini"
    """

    @staticmethod
    def detect_format(raw_output: str) -> str:
        """
        Automatically detect which CLI format this output is.

        Args:
            raw_output: Raw string output from CLI subprocess

        Returns:
            Format identifier: 'claude', 'gemini', or 'raw'
        """
        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, dict):
                # Claude CLI: {"type": "result", "result": "..."}
                if 'type' in parsed and 'result' in parsed:
                    return 'claude'
                # Gemini CLI: {"response": "...", "stats": {...}}
                elif 'response' in parsed and 'stats' in parsed:
                    return 'gemini'
        except (json.JSONDecodeError, ValueError):
            pass

        # Default: raw text (no structured wrapper)
        return 'raw'

    @staticmethod
    def unwrap(raw_output: str) -> Dict[str, Any]:
        """
        Unwrap CLI-specific format into standardized structure.

        Args:
            raw_output: Raw string output from CLI subprocess

        Returns:
            Standardized dictionary with:
            - content (str): Actual response text (cleaned)
            - metadata (dict): CLI-specific metadata
            - format (str): Original format type

        Example:
            >>> output = '{"response": "```json\\n[...]\\n```", "stats": {...}}'
            >>> result = CLIOutputAdapter.unwrap(output)
            >>> result['content']  # "[...]" (markdown removed)
            >>> result['format']   # "gemini"
        """
        format_type = CLIOutputAdapter.detect_format(raw_output)

        if format_type == 'claude':
            return CLIOutputAdapter._unwrap_claude(raw_output)
        elif format_type == 'gemini':
            return CLIOutputAdapter._unwrap_gemini(raw_output)
        else:
            return CLIOutputAdapter._unwrap_raw(raw_output)

    @staticmethod
    def _unwrap_claude(output: str) -> Dict[str, Any]:
        """
        Unwrap Claude CLI output format.

        Claude CLI returns:
        {
            "type": "result",
            "result": "actual content",
            "total_cost_usd": 0.123,
            "usage": {...},
            "duration_ms": 5000
        }
        """
        try:
            parsed = json.loads(output)
            content = parsed.get('result', '')

            # Clean markdown blocks if present
            content = CLIOutputAdapter._strip_markdown_blocks(content)

            return {
                "content": content,
                "metadata": {
                    "cost_usd": parsed.get('total_cost_usd'),
                    "usage": parsed.get('usage'),
                    "model_usage": parsed.get('modelUsage'),
                    "duration_ms": parsed.get('duration_ms'),
                    "duration_api_ms": parsed.get('duration_api_ms'),
                    "num_turns": parsed.get('num_turns'),
                    "session_id": parsed.get('session_id')
                },
                "format": "claude"
            }
        except Exception as e:
            # Fallback if parsing fails
            return {
                "content": output,
                "metadata": {"error": str(e)},
                "format": "claude_error"
            }

    @staticmethod
    def _unwrap_gemini(output: str) -> Dict[str, Any]:
        """
        Unwrap Gemini CLI output format.

        Gemini CLI returns:
        {
            "response": "actual content (may have markdown)",
            "stats": {
                "models": {...},
                "tools": {...},
                "files": {...}
            }
        }
        """
        try:
            parsed = json.loads(output)
            content = parsed.get('response', '')

            # IMPORTANT: Strip markdown code blocks (```json ... ```)
            # Gemini often wraps JSON in markdown blocks
            content = CLIOutputAdapter._strip_markdown_blocks(content)

            return {
                "content": content,
                "metadata": {
                    "stats": parsed.get('stats', {}),
                    "models": parsed.get('stats', {}).get('models', {}),
                    "tools": parsed.get('stats', {}).get('tools', {}),
                    "files": parsed.get('stats', {}).get('files', {})
                },
                "format": "gemini"
            }
        except Exception as e:
            # Fallback if parsing fails
            return {
                "content": output,
                "metadata": {"error": str(e)},
                "format": "gemini_error"
            }

    @staticmethod
    def _unwrap_raw(output: str) -> Dict[str, Any]:
        """
        Handle raw text output (no structured wrapper).

        This is used when CLI doesn't return JSON, or for
        legacy/fallback scenarios.
        """
        # Still try to clean markdown blocks
        content = CLIOutputAdapter._strip_markdown_blocks(output)

        return {
            "content": content,
            "metadata": {},
            "format": "raw"
        }

    @staticmethod
    def _strip_markdown_blocks(text: str) -> str:
        """
        Remove markdown code block wrappers from text.

        Handles formats like:
        - ```json ... ```
        - ``` ... ```
        - ```\n...\n```

        Args:
            text: Text potentially wrapped in markdown code blocks

        Returns:
            Clean text without markdown wrappers

        Example:
            >>> text = '```json\\n{"key": "value"}\\n```'
            >>> CLIOutputAdapter._strip_markdown_blocks(text)
            '{"key": "value"}'
        """
        if not text:
            return text

        text = text.strip()

        # Pattern: ```language\n content \n```
        # Match: ```json ... ``` or ``` ... ```
        pattern = r'^```(?:json|python|javascript|bash)?\s*\n?(.*?)\n?```$'
        match = re.match(pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        return text


# Convenience functions for direct usage
def unwrap_cli_output(raw_output: str) -> str:
    """
    Quick unwrap function that returns only the content.

    Args:
        raw_output: Raw CLI output string

    Returns:
        Clean content string

    Example:
        >>> output = '{"response": "Hello world", "stats": {}}'
        >>> unwrap_cli_output(output)
        'Hello world'
    """
    result = CLIOutputAdapter.unwrap(raw_output)
    return result['content']


def get_cli_metadata(raw_output: str) -> Dict[str, Any]:
    """
    Extract metadata from CLI output without content.

    Args:
        raw_output: Raw CLI output string

    Returns:
        Metadata dictionary
    """
    result = CLIOutputAdapter.unwrap(raw_output)
    return result['metadata']
