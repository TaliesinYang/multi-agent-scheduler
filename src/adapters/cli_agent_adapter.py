"""
CLI-based Agent Adapter for AgentBench Tasks

Provides a Claude CLI-based agent that supports Tool Calling without API keys.
Uses the 'claude' command-line tool for execution.
"""

import asyncio
import json
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CLIToolCall:
    """Tool call from CLI response"""
    id: str
    name: str
    arguments: Dict[str, Any]


class CLIClaudeAgent:
    """
    Claude CLI-based agent for AgentBench tasks

    Uses the local 'claude' CLI tool instead of API calls.
    Supports Tool Calling through --tools parameter.

    Features:
    - No API key required
    - Tool Calling support via CLI
    - Session management (--resume)
    - JSON output parsing

    Example:
        agent = CLIClaudeAgent()
        result = await agent.call(
            prompt="List files in /root",
            tools=[{"name": "execute_shell", "description": "..."}]
        )
    """

    def __init__(
        self,
        cli_command: str = "claude",
        model: str = "sonnet",
        max_concurrent: int = 3
    ):
        """
        Initialize CLI Claude agent

        Args:
            cli_command: CLI command name (default: "claude")
            model: Model to use (default: "sonnet")
            max_concurrent: Max concurrent calls (not used for CLI)
        """
        self.cli_command = cli_command
        self.model = model
        self.name = "CLI-Claude"
        self.session_id: Optional[str] = None

        # Check if CLI is available
        try:
            result = subprocess.run(
                [cli_command, "--help"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"CLI command '{cli_command}' not working")
        except FileNotFoundError:
            raise RuntimeError(
                f"CLI command '{cli_command}' not found. "
                f"Please install Claude CLI first."
            )

    async def call(
        self,
        prompt: str | List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_rounds: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Claude via CLI

        Args:
            prompt: Text prompt or messages list
            tools: Tool definitions (Anthropic format)
            max_rounds: Not used (CLI manages rounds internally)
            **kwargs: Additional arguments (ignored)

        Returns:
            Dict with response content and tool_calls
        """
        # Convert messages to text if needed
        if isinstance(prompt, list):
            # Extract last user message
            text_prompt = ""
            for msg in prompt:
                if msg["role"] == "user":
                    content = msg["content"]
                    if isinstance(content, str):
                        text_prompt = content
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_prompt += block.get("text", "")
            prompt = text_prompt

        # Build CLI command
        cmd = [
            self.cli_command,
            "-p",  # Print mode
            "--output-format", "json",
            "--model", self.model
        ]

        # Add tools if provided
        if tools:
            # Claude CLI uses built-in tools, we need to map AgentBench tools
            # For now, enable default tools (Bash for execute_shell)
            cmd.extend(["--tools", "Bash,Read,Write"])
            cmd.append("--dangerously-skip-permissions")

        # Add session management if continuing
        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        # Add prompt
        cmd.append(prompt)

        # Execute CLI command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120.0  # 2 minutes timeout
            )

            # Parse output
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                return {
                    "agent": self.name,
                    "result": f"CLI error: {error_msg}",
                    "content": "",
                    "tool_calls": [],
                    "success": False,
                    "error": error_msg
                }

            # Parse JSON output
            output_text = stdout.decode('utf-8', errors='replace')

            # Claude CLI output format may vary
            # Try to extract result
            try:
                # If output is JSON
                output_json = json.loads(output_text)
                content = output_json.get("text", output_text)
            except json.JSONDecodeError:
                # If output is plain text
                content = output_text.strip()

            # Return result
            return {
                "agent": self.name,
                "result": content,
                "content": content,
                "tool_calls": [],  # CLI manages tools internally
                "success": True,
                "latency": 0,  # Not tracked for CLI
                "tokens": 0    # Not tracked for CLI
            }

        except asyncio.TimeoutError:
            return {
                "agent": self.name,
                "result": "CLI timeout after 120s",
                "content": "",
                "tool_calls": [],
                "success": False,
                "error": "Timeout"
            }

        except Exception as e:
            return {
                "agent": self.name,
                "result": f"CLI error: {str(e)}",
                "content": "",
                "tool_calls": [],
                "success": False,
                "error": str(e)
            }

    async def shutdown(self):
        """Cleanup (nothing to do for CLI)"""
        pass
