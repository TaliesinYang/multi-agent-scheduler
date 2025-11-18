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
import json
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
        extract_data: bool = False,
        **kwargs
    ) -> TaskResult:
        """
        Execute task using specified CLI agent

        Args:
            task_prompt: Task description/prompt
            agent_name: Agent name (claude, codex, or gemini)
            task_id: Unique task identifier
            extract_data: Whether to extract structured data from output (default: False)
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

        # Use agent_name as CLI command (claude, codex, or gemini)
        # Falls back to self.cli_command if agent_name is not provided
        cli_cmd = agent_name if agent_name else self.cli_command

        # Build CLI command with agent-specific parameters
        # Different CLI tools use different APIs
        if cli_cmd == "gemini":
            # Gemini uses positional prompt (no -p flag) + output format
            # Note: -p is deprecated, use positional argument instead
            cmd = [cli_cmd, "-o", "json", "-y", task_prompt]
        else:
            # Claude and Codex use --tools Bash with -p flag
            cmd = [cli_cmd, "-p", "--tools", "Bash"]

            # Add agent-specific permission bypass parameters
            if cli_cmd == "claude":
                cmd.extend(["--permission-mode", "bypassPermissions"])
            elif cli_cmd == "codex":
                cmd.extend(["-a", "never"])  # never ask for approval

            # Add task prompt (for claude/codex only, gemini already has it)
            cmd.append(task_prompt)

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
                    agent=f"CLI-{cli_cmd}",
                    error=f"Timeout after {timeout}s",
                    metadata={"timeout": True}
                )

            # Decode output
            output = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            # Calculate latency
            latency = time.time() - start_time

            # Parse output based on agent type
            if cli_cmd == "gemini":
                # Gemini returns JSON: {"response": "...", "stats": {...}}
                try:
                    parsed = json.loads(output)
                    gemini_response = parsed.get('response', '')

                    # Check for FINAL_ANSWER in the response content
                    success = "FINAL_ANSWER:" in gemini_response
                    if success:
                        match = re.search(r'FINAL_ANSWER:\s*(.+?)(?:\n|$)', gemini_response, re.DOTALL)
                        if match:
                            final_answer = match.group(1).strip()
                        else:
                            final_answer = gemini_response.split("FINAL_ANSWER:", 1)[1].strip()
                    else:
                        final_answer = ""
                except json.JSONDecodeError:
                    # Fallback to plain text parsing
                    success = "FINAL_ANSWER:" in output
                    final_answer = ""
                    if success:
                        match = re.search(r'FINAL_ANSWER:\s*(.+?)(?:\n|$)', output, re.DOTALL)
                        if match:
                            final_answer = match.group(1).strip()
                        else:
                            final_answer = output.split("FINAL_ANSWER:", 1)[1].strip()
            else:
                # Claude and Codex return plain text
                success = "FINAL_ANSWER:" in output
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
                "has_stderr": bool(stderr_text.strip()),
                "detection_method": "final_answer" if success else "none"
            }

            # Multi-strategy success detection (fallback if FINAL_ANSWER not found)
            if not success:
                success, detection_method = self._detect_success_fallback(
                    task_prompt, output, process.returncode, stderr_text
                )
                if success:
                    metadata["detection_method"] = detection_method
                    # Use full output as final_answer for fallback methods
                    final_answer = output[:200] if output else ""

            if stderr_text.strip():
                metadata["stderr"] = stderr_text[:500]  # Truncate stderr

            # Determine error message
            error = None
            if not success:
                if process.returncode != 0:
                    error = f"CLI exited with code {process.returncode}"
                else:
                    error = "No FINAL_ANSWER found in output"

            # Extract structured data if requested (Day 7 feature)
            parsed_data = None
            if extract_data and success and final_answer:
                parsed_data = self._extract_structured_data(final_answer)

            return TaskResult(
                task_id=task_id,
                success=success,
                output=final_answer if success else output,
                parsed_data=parsed_data,
                latency=latency,
                agent=f"CLI-{cli_cmd}",
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
                agent=f"CLI-{cli_cmd}",
                error=f"Execution error: {str(e)}",
                metadata={"exception": type(e).__name__}
            )

    async def shutdown(self) -> None:
        """Clean up resources"""
        if self.cli_tool:
            await self.cli_tool.close()
        self.initialized = False

    def _detect_success_fallback(
        self,
        task_prompt: str,
        output: str,
        exit_code: int,
        stderr: str
    ) -> tuple[bool, str]:
        """
        Multi-strategy success detection (fallback when FINAL_ANSWER not found)

        Strategies (in order):
        1. File creation detection (for coding tasks)
        2. Clean exit detection (exit_code 0, no stderr, meaningful output)

        Args:
            task_prompt: The task prompt text
            output: Command output
            exit_code: Process exit code
            stderr: Standard error output

        Returns:
            (success: bool, detection_method: str)
        """
        from pathlib import Path

        # Strategy 1: File creation detection (for coding tasks)
        # Look for "create", "write", "generate" in prompt
        if any(keyword in task_prompt.lower() for keyword in ["create", "write", "generate", "add"]):
            # Extract potential filenames from prompt
            # Match patterns like "file.py", 'file.js', "script.sh", etc.
            import re
            filenames = re.findall(
                r'["\']([^"\']+\.(?:py|js|ts|html|css|json|csv|txt|md|sh|sql))["\']',
                task_prompt
            )

            if filenames:
                # Check if ALL mentioned files exist
                existing_files = [f for f in filenames if Path(f).exists()]
                if existing_files:
                    # At least some files were created
                    return (True, "file_created")

        # Strategy 2: Clean exit with meaningful output
        # Criteria:
        # - Exit code 0
        # - No stderr (or only minor warnings)
        # - Output length > 50 chars (not just empty/trivial)
        if exit_code == 0:
            has_stderr = bool(stderr.strip())
            has_meaningful_output = len(output.strip()) > 50

            if not has_stderr and has_meaningful_output:
                return (True, "clean_exit")

        # No fallback strategy matched
        return (False, "none")

    def _extract_structured_data(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from task output (Day 7 feature)

        Attempts to parse JSON from final_answer or use pattern matching.
        Used for dependency injection between tasks.

        Extraction strategies (in order):
        1. Parse complete JSON objects/arrays
        2. Extract key-value pairs ("key: value", "key = value")
        3. Extract numbered lists ("1. item", "2. item")
        4. Extract comma-separated values
        5. Extract counts/numbers

        Args:
            text: Text to extract data from (typically final_answer)

        Returns:
            Dictionary of extracted data, or None if no data found

        Example output:
            {
                "user_count": 5,
                "users": ["alice", "bob", "charlie"],
                "disk_usage": "45%"
            }
        """
        if not text or not text.strip():
            return None

        # Strategy 1: Try to parse as complete JSON
        try:
            # Look for JSON object or array
            # Match balanced braces/brackets
            json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])', text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
                elif isinstance(parsed, list):
                    return {"items": parsed}
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract key-value pairs
        # Patterns: "key: value", "key = value", "key is value"
        data = {}

        # Pattern 1: "key: value" or "key = value"
        for match in re.finditer(r'(\w+)\s*[:=]\s*([^\n,]+)', text):
            key = match.group(1)
            value = match.group(2).strip()
            data[key] = self._parse_value(value)

        # Pattern 2: "key is value"
        for match in re.finditer(r'(\w+)\s+is\s+([^\n,.]+)', text):
            key = match.group(1)
            value = match.group(2).strip()
            if key not in data:  # Don't override existing
                data[key] = self._parse_value(value)

        # Strategy 3: Extract numbered/bulleted lists
        # Pattern: "1. item", "2. item" or "- item", "* item"
        list_items = []

        # Numbered lists
        for match in re.finditer(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE):
            list_items.append(match.group(1).strip())

        # Bulleted lists
        if not list_items:
            for match in re.finditer(r'^\s*[-*]\s*(.+)$', text, re.MULTILINE):
                list_items.append(match.group(1).strip())

        if list_items:
            data["items"] = list_items

        # Strategy 4: Extract comma-separated values (if mentioned)
        # Look for patterns like "users: alice, bob, charlie"
        csv_match = re.search(r'(\w+):\s*([a-zA-Z0-9_]+(?:\s*,\s*[a-zA-Z0-9_]+)+)', text)
        if csv_match:
            key = csv_match.group(1)
            values_str = csv_match.group(2)
            values = [v.strip() for v in values_str.split(',')]
            data[key] = values

        # Strategy 5: Extract counts/numbers
        # Pattern: "found X items", "X users", "total: X"
        count_patterns = [
            r'found\s+(\d+)\s+(\w+)',
            r'(\d+)\s+(\w+)(?:\s+found)?',
            r'total\s*[:=]?\s*(\d+)',
            r'count\s*[:=]?\s*(\d+)'
        ]

        for pattern in count_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    count = int(match.group(1))
                    item_name = match.group(2)
                    data[f"{item_name}_count"] = count
                else:
                    data["count"] = int(match.group(1))
                break

        return data if data else None

    def _parse_value(self, value_str: str) -> Any:
        """
        Parse value string to appropriate type

        Args:
            value_str: String value to parse

        Returns:
            Parsed value (int, float, bool, list, or string)
        """
        value_str = value_str.strip()

        # Boolean
        if value_str.lower() in ('true', 'yes'):
            return True
        if value_str.lower() in ('false', 'no'):
            return False

        # Number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # List (comma-separated in brackets)
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                # Try manual parsing
                inner = value_str[1:-1]
                return [v.strip().strip('"\'') for v in inner.split(',')]

        # String
        return value_str.strip('"\'')  # Remove quotes if present


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
