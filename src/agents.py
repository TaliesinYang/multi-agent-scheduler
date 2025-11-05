"""
Multi-Agent System - AI Agent Wrappers
Unified interface supporting Claude, OpenAI, and Gemini
"""

import asyncio
import subprocess
import time
import shlex
from typing import Dict, Optional
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from src.cli_adapters import CLIOutputAdapter


class BaseAgent:
    """Base AI Agent Class"""

    def __init__(self, name: str, max_concurrent: int = 10, workspace: str = None):
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.call_count = 0
        self.total_latency = 0.0
        self.total_tokens = 0
        self.workspace = workspace  # Working directory for file operations

    async def call(self, prompt: str) -> Dict:
        """
        Call AI model and return result

        Args:
            prompt: Input prompt

        Returns:
            Dict containing: agent name, result text, latency, token count
        """
        raise NotImplementedError("Subclass must implement call() method")

    def get_stats(self) -> Dict:
        """Get statistics"""
        avg_latency = self.total_latency / self.call_count if self.call_count > 0 else 0
        return {
            "agent": self.name,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "avg_latency": avg_latency
        }


class RobustCLIAgent(BaseAgent):
    """
    Robust CLI Agent base class with timeout and error handling

    Features:
    - Timeout handling (default 30s)
    - Automatic process cleanup on timeout
    - JSON and text output support
    - Structured error handling

    Example:
        class CustomCLIAgent(RobustCLIAgent):
            def __init__(self):
                super().__init__(
                    name="CustomAI",
                    cli_command="custom-cli"
                )
    """

    def __init__(self, name: str, cli_command: str, max_concurrent: int = 10, workspace: str = None):
        """
        Initialize robust CLI agent

        Args:
            name: Agent name
            cli_command: CLI command to execute (e.g., "claude", "gemini")
            max_concurrent: Maximum concurrent calls
            workspace: Working directory for file operations
        """
        super().__init__(name, max_concurrent, workspace)
        self.cli_command = cli_command
        self.default_timeout = 600.0  # 10 minutes timeout for complex tasks

    async def call(
        self,
        prompt: str,
        timeout: Optional[float] = None,
        output_format: str = "json"
    ) -> Dict:
        """
        Call CLI with robust error handling and timeout

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds (default: 30s)
            output_format: Output format ("json" or "text")

        Returns:
            Dict containing: agent name, result text, latency, token count, success status
        """
        async with self.semaphore:
            start_time = time.time()
            timeout_val = timeout or self.default_timeout

            try:
                # Build command arguments
                args = [self.cli_command, "-p", prompt]

                # Add output format if specified
                if output_format:
                    args.extend(["--output-format", output_format])

                # Create subprocess with workspace as working directory
                process = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.workspace  # Use workspace for file operations
                )

                # Wait with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout_val
                    )
                except asyncio.TimeoutError:
                    # Kill process on timeout
                    process.kill()
                    await process.communicate()  # Clean up zombie process

                    end_time = time.time()
                    return {
                        "agent": self.name,
                        "result": f"Timeout after {timeout_val}s",
                        "latency": end_time - start_time,
                        "tokens": 0,
                        "success": False,
                        "error": "Timeout"
                    }

                end_time = time.time()
                latency = end_time - start_time

                # Process successful response
                if process.returncode == 0:
                    result_text = stdout.decode('utf-8').strip()

                    # NEW: Unwrap CLI-specific format using adapter
                    unwrapped = CLIOutputAdapter.unwrap(result_text)
                    clean_content = unwrapped['content']
                    cli_metadata = unwrapped['metadata']
                    cli_format = unwrapped['format']

                    # Estimate tokens (rough approximation for CLI agents)
                    estimated_tokens = len(prompt.split()) + len(clean_content.split())

                    # Update statistics
                    self.call_count += 1
                    self.total_latency += latency
                    self.total_tokens += estimated_tokens

                    return {
                        "agent": self.name,
                        "result": clean_content,  # Standardized content
                        "metadata": cli_metadata,  # CLI-specific metadata
                        "cli_format": cli_format,  # Format identifier (claude/gemini/raw)
                        "latency": latency,
                        "tokens": estimated_tokens,
                        "success": True
                    }
                else:
                    # Process error
                    error_msg = stderr.decode('utf-8').strip()
                    return {
                        "agent": self.name,
                        "result": f"CLI Error: {error_msg}",
                        "latency": latency,
                        "tokens": 0,
                        "success": False,
                        "error": error_msg
                    }

            except Exception as e:
                end_time = time.time()
                return {
                    "agent": self.name,
                    "result": f"Error: {str(e)}",
                    "latency": end_time - start_time,
                    "tokens": 0,
                    "success": False,
                    "error": str(e)
                }


class ClaudeAgent(BaseAgent):
    """Claude API Agent"""

    def __init__(self, api_key: str, max_concurrent: int = 20, model: str = "claude-sonnet-4-5-20250929", workspace: str = None):
        super().__init__("Claude", max_concurrent, workspace)
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def call(self, prompt: str, max_tokens: int = 1024) -> Dict:
        """Call Claude API"""
        async with self.semaphore:
            start_time = time.time()

            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )

                end_time = time.time()
                latency = end_time - start_time

                # Update statistics
                self.call_count += 1
                self.total_latency += latency
                self.total_tokens += response.usage.total_tokens

                return {
                    "agent": self.name,
                    "result": response.content[0].text,
                    "latency": latency,
                    "tokens": response.usage.total_tokens,
                    "success": True
                }

            except Exception as e:
                end_time = time.time()
                return {
                    "agent": self.name,
                    "result": f"Error: {str(e)}",
                    "latency": end_time - start_time,
                    "tokens": 0,
                    "success": False,
                    "error": str(e)
                }


class ClaudeCLIAgent(RobustCLIAgent):
    """
    Claude CLI Agent

    Uses Claude Code CLI instead of API for cost optimization.
    Requires: npm install -g @anthropic-ai/claude-code

    Example:
        agent = ClaudeCLIAgent(workspace="/path/to/project")
        result = await agent.call("Explain quantum computing")
    """

    def __init__(self, max_concurrent: int = 10, workspace: str = None):
        """
        Initialize Claude CLI agent

        Args:
            max_concurrent: Maximum concurrent calls
            workspace: Working directory for file operations
        """
        super().__init__(
            name="Claude-CLI",
            cli_command="claude",
            max_concurrent=max_concurrent,
            workspace=workspace
        )


class CodexCLIAgent(RobustCLIAgent):
    """
    OpenAI Codex CLI Agent (DEPRECATED - use CodexExecAgent instead)

    Uses codex command for task execution instead of API.
    Requires: GitHub Copilot subscription or codex CLI access

    Example:
        agent = CodexCLIAgent()
        result = await agent.call("Write a Python function to sort a list")
    """

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize Codex CLI agent

        Args:
            max_concurrent: Maximum concurrent calls (default: 10)
        """
        super().__init__(
            name="Codex-CLI",
            cli_command="codex",
            max_concurrent=max_concurrent
        )


class CodexExecAgent(BaseAgent):
    """
    Codex Exec Agent - Uses correct 'codex exec' command format

    The standard codex CLI doesn't support -p and --output-format parameters.
    This agent uses the correct command format: codex exec "prompt" --skip-git-repo-check

    Requires: GitHub Copilot subscription or codex CLI access

    Example:
        agent = CodexExecAgent(workspace="/path/to/project")
        result = await agent.call("Write a Python function to sort a list")
    """

    def __init__(self, max_concurrent: int = 10, workspace: str = None):
        """
        Initialize Codex Exec agent

        Args:
            max_concurrent: Maximum concurrent calls (default: 10)
            workspace: Working directory for file operations
        """
        super().__init__("Codex-CLI", max_concurrent, workspace)
        self.default_timeout = 600.0  # 10 minutes timeout

    async def call(
        self,
        prompt: str,
        timeout: Optional[float] = None
    ) -> Dict:
        """
        Call Codex CLI using 'codex exec' command

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds (default: 600s)

        Returns:
            Dict containing: agent name, result text, latency, token count, success status
        """
        async with self.semaphore:
            start_time = time.time()
            timeout_val = timeout or self.default_timeout

            try:
                # Use shell to cd into workspace first, then run codex exec
                # This works around Codex CLI's cwd parameter bug with long/special paths
                if self.workspace:
                    # Use shlex.quote to safely handle spaces and special characters
                    safe_workspace = shlex.quote(str(self.workspace))
                    safe_prompt = shlex.quote(prompt)
                    shell_cmd = f"cd {safe_workspace} && codex exec {safe_prompt} --full-auto --skip-git-repo-check"
                    args = ["bash", "-c", shell_cmd]

                    # Create subprocess using shell command
                    process = await asyncio.create_subprocess_exec(
                        *args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    # No workspace - use direct command
                    args = [
                        "codex", "exec", prompt,
                        "--full-auto",
                        "--skip-git-repo-check"
                    ]
                    process = await asyncio.create_subprocess_exec(
                        *args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                # Wait with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout_val
                    )
                except asyncio.TimeoutError:
                    # Kill process on timeout
                    process.kill()
                    await process.communicate()  # Clean up zombie process

                    end_time = time.time()
                    return {
                        "agent": self.name,
                        "result": f"Timeout after {timeout_val}s",
                        "latency": end_time - start_time,
                        "tokens": 0,
                        "success": False,
                        "error": "Timeout"
                    }

                end_time = time.time()
                latency = end_time - start_time

                # Decode output
                stdout_text = stdout.decode('utf-8').strip()
                stderr_text = stderr.decode('utf-8').strip()

                # Codex CLI returns exit code 1 even on success, so check output content
                # instead of relying solely on returncode
                is_success = False

                if process.returncode == 0:
                    # Standard success case
                    is_success = True
                elif "Success" in stdout_text or "Updated the following files" in stdout_text:
                    # Codex CLI success markers (even with returncode 1)
                    is_success = True
                elif stderr_text and "ERROR" not in stderr_text.upper() and "FATAL" not in stderr_text.upper():
                    # Only warnings in stderr, not fatal errors
                    # Common case: MCP timeout warnings don't prevent task completion
                    is_success = True

                if is_success:
                    # Process successful response
                    # Estimate tokens (rough approximation)
                    estimated_tokens = len(prompt.split()) + len(stdout_text.split())

                    # Update statistics
                    self.call_count += 1
                    self.total_latency += latency
                    self.total_tokens += estimated_tokens

                    return {
                        "agent": self.name,
                        "result": stdout_text,
                        "latency": latency,
                        "tokens": estimated_tokens,
                        "success": True
                    }
                else:
                    # Process error
                    error_msg = stderr_text if stderr_text else stdout_text
                    return {
                        "agent": self.name,
                        "result": f"CLI Error: {error_msg}",
                        "latency": latency,
                        "tokens": 0,
                        "success": False,
                        "error": error_msg
                    }

            except Exception as e:
                end_time = time.time()
                return {
                    "agent": self.name,
                    "result": f"Error: {str(e)}",
                    "latency": end_time - start_time,
                    "tokens": 0,
                    "success": False,
                    "error": str(e)
                }


class OpenAIAgent(BaseAgent):
    """OpenAI API Agent"""

    def __init__(self, api_key: str, max_concurrent: int = 20, model: str = "gpt-4-turbo", workspace: str = None):
        super().__init__("OpenAI", max_concurrent, workspace)
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def call(self, prompt: str, max_tokens: int = 1024) -> Dict:
        """Call OpenAI API"""
        async with self.semaphore:
            start_time = time.time()

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )

                end_time = time.time()
                latency = end_time - start_time

                # Update statistics
                self.call_count += 1
                self.total_latency += latency
                self.total_tokens += response.usage.total_tokens

                return {
                    "agent": self.name,
                    "result": response.choices[0].message.content,
                    "latency": latency,
                    "tokens": response.usage.total_tokens,
                    "success": True
                }

            except Exception as e:
                end_time = time.time()
                return {
                    "agent": self.name,
                    "result": f"Error: {str(e)}",
                    "latency": end_time - start_time,
                    "tokens": 0,
                    "success": False,
                    "error": str(e)
                }


class GeminiAgent(RobustCLIAgent):
    """
    Gemini CLI Agent

    Uses Gemini CLI (free tier) for cost optimization.
    Requires: npm install -g @google/gemini-cli

    Features (inherited from RobustCLIAgent):
    - 30-second timeout handling
    - JSON output support
    - Automatic process cleanup

    Example:
        agent = GeminiAgent(workspace="/path/to/project")
        result = await agent.call("Explain quantum computing")
    """

    def __init__(self, max_concurrent: int = 10, workspace: str = None):
        """
        Initialize Gemini CLI agent

        Args:
            max_concurrent: Maximum concurrent calls
            workspace: Working directory for file operations
        """
        super().__init__(
            name="Gemini",
            cli_command="gemini",
            max_concurrent=max_concurrent,
            workspace=workspace
        )


class MockAgent(BaseAgent):
    """Mock Agent (for testing, no real API required)"""

    def __init__(self, name: str = "Mock", delay: float = 1.0, max_concurrent: int = 10, workspace: str = None):
        super().__init__(name, max_concurrent, workspace)
        self.delay = delay

    async def call(self, prompt: str) -> Dict:
        """Simulate API call"""
        async with self.semaphore:
            start_time = time.time()

            # Simulate network latency
            await asyncio.sleep(self.delay)

            end_time = time.time()
            latency = end_time - start_time

            # Generate mock response
            result_text = f"Mock response for: {prompt[:50]}..."
            estimated_tokens = len(prompt.split()) * 2

            self.call_count += 1
            self.total_latency += latency
            self.total_tokens += estimated_tokens

            return {
                "agent": self.name,
                "result": result_text,
                "latency": latency,
                "tokens": estimated_tokens,
                "success": True
            }
