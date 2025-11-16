"""
CLI Executor Implementation

Executes tasks using Claude CLI with local Bash tools.
No API key required.

Features:
- Uses CLIToolExecutor for database/shell operations
- Parses FINAL_ANSWER from Claude CLI output
- Supports timeout and error handling
"""

import asyncio
import time
import re
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add adapters to path for CLIToolExecutor import
sys.path.insert(0, str(Path(__file__).parent.parent / "adapters"))
from cli_tool_executor import CLIToolExecutor

# Use absolute import for compatibility
try:
    from .executor import ToolExecutor, TaskResult, ExecutorExecutionError
except ImportError:
    from executor import ToolExecutor, TaskResult, ExecutorExecutionError


class CLIExecutor(ToolExecutor):
    """
    CLI-based task executor using Claude CLI

    Uses Claude CLI command-line tool for agent execution.
    Integrates with CLIToolExecutor for database/shell operations.

    Example:
        >>> executor = CLIExecutor()
        >>> await executor.initialize()
        >>> result = await executor.execute(
        ...     task_prompt="List users in database",
        ...     agent_name="claude",
        ...     task_id="task1"
        ... )
        >>> print(result.success)  # True
    """

    def __init__(
        self,
        cli_command: str = "claude",
        timeout: float = 60.0,
        cli_tool_executor: Optional[CLIToolExecutor] = None
    ):
        """
        Initialize CLI executor

        Args:
            cli_command: Claude CLI command name (default: "claude")
            timeout: Task execution timeout in seconds
            cli_tool_executor: Optional pre-configured CLIToolExecutor
        """
        self.cli_command = cli_command
        self.timeout = timeout
        self.cli_tool = cli_tool_executor
        self.initialized = False

    async def initialize(self, **kwargs) -> None:
        """
        Initialize CLI executor

        Args:
            **kwargs: Optional parameters
                - db_path: Database path for CLIToolExecutor
                - setup_db: Whether to create test database
        """
        if self.initialized:
            return

        # Initialize CLIToolExecutor if not provided
        if not self.cli_tool:
            db_path = kwargs.get("db_path", "agentbench_cli.db")
            self.cli_tool = CLIToolExecutor(db_path=db_path)

        # Initialize database
        setup_db = kwargs.get("setup_db", True)
        await self.cli_tool.initialize(setup_db=setup_db)

        self.initialized = True

    async def execute(
        self,
        task_prompt: str,
        agent_name: str,
        task_id: str,
        **kwargs
    ) -> TaskResult:
        """
        Execute task using Claude CLI

        Args:
            task_prompt: Task description/prompt
            agent_name: Agent name (not used in CLI mode, always "claude")
            task_id: Unique task identifier
            **kwargs: Optional parameters
                - timeout: Override default timeout

        Returns:
            TaskResult with execution details

        Raises:
            ExecutorExecutionError: If execution fails critically
        """
        if not self.initialized:
            raise ExecutorExecutionError("Executor not initialized. Call initialize() first.")

        start_time = time.time()
        timeout = kwargs.get("timeout", self.timeout)

        # Build CLI command
        cmd = [
            self.cli_command,
            "-p",  # Print mode
            "--tools", "Bash",  # Enable Bash tool
            "--dangerously-skip-permissions",  # Skip permission prompts
            task_prompt
        ]

        try:
            # Execute CLI command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                latency = time.time() - start_time

                return TaskResult(
                    task_id=task_id,
                    success=False,
                    output="",
                    latency=latency,
                    agent="CLI-Claude",
                    error=f"Timeout after {timeout}s",
                    metadata={"timeout": True}
                )

            # Decode output
            output = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            # Calculate latency
            latency = time.time() - start_time

            # Check for FINAL_ANSWER marker
            success = "FINAL_ANSWER:" in output

            # Extract final answer if present
            final_answer = ""
            if success:
                match = re.search(r'FINAL_ANSWER:\s*(.+?)(?:\n|$)', output, re.DOTALL)
                if match:
                    final_answer = match.group(1).strip()
                else:
                    # Fallback: everything after FINAL_ANSWER:
                    final_answer = output.split("FINAL_ANSWER:", 1)[1].strip()

            # Build metadata
            metadata = {
                "cli_command": " ".join(cmd[:3]),  # Don't include full prompt
                "exit_code": process.returncode,
                "has_stderr": bool(stderr_text.strip())
            }

            if stderr_text.strip():
                metadata["stderr"] = stderr_text[:500]  # Truncate stderr

            # Determine error message
            error = None
            if not success:
                if process.returncode != 0:
                    error = f"CLI exited with code {process.returncode}"
                else:
                    error = "No FINAL_ANSWER found in output"

            return TaskResult(
                task_id=task_id,
                success=success,
                output=final_answer if success else output,
                latency=latency,
                agent="CLI-Claude",
                error=error,
                metadata=metadata
            )

        except FileNotFoundError:
            raise ExecutorExecutionError(
                f"Claude CLI command '{self.cli_command}' not found. "
                f"Please install Claude CLI first."
            )

        except Exception as e:
            latency = time.time() - start_time
            return TaskResult(
                task_id=task_id,
                success=False,
                output="",
                latency=latency,
                agent="CLI-Claude",
                error=f"Execution error: {str(e)}",
                metadata={"exception": type(e).__name__}
            )

    async def shutdown(self) -> None:
        """Clean up resources"""
        if self.cli_tool:
            await self.cli_tool.close()
        self.initialized = False


# Convenience function
async def execute_cli_task(
    task_prompt: str,
    task_id: str = "task",
    timeout: float = 60.0
) -> TaskResult:
    """
    Quick CLI task execution (convenience function)

    Args:
        task_prompt: Task prompt
        task_id: Task identifier
        timeout: Timeout in seconds

    Returns:
        TaskResult

    Example:
        >>> result = await execute_cli_task("List files in /root", "task1")
        >>> print(result.success)
    """
    async with CLIExecutor(timeout=timeout) as executor:
        return await executor.execute(
            task_prompt=task_prompt,
            agent_name="claude",
            task_id=task_id
        )
