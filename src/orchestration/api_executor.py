"""
API Executor Implementation

Executes tasks using Anthropic API with MultiRoundExecutor.
Supports structured data extraction for dependency injection (Day 5).

Features:
- Uses MultiRoundExecutor for agent-tool interaction
- Extracts structured data from tool results
- Supports multiple agents (Claude, OpenAI, Gemini)
- Full visibility into tool calls and intermediate states
"""

import time
import json
import re
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from agents import BaseAgent
    from adapters import ToolRegistry

# Use absolute import for compatibility
try:
    from .executor import ToolExecutor, TaskResult, ExecutorInitializationError
except ImportError:
    from executor import ToolExecutor, TaskResult, ExecutorInitializationError


class APIExecutor(ToolExecutor):
    """
    API-based task executor using Anthropic API + MultiRoundExecutor

    Uses the full MultiRoundExecutor for rich agent-tool interaction.
    Provides structured data extraction for dependency injection.

    Example:
        >>> from agents import ClaudeAgent
        >>> from adapters import ToolRegistry
        >>>
        >>> registry = ToolRegistry()
        >>> await registry.initialize(docker_image="ubuntu:22.04")
        >>>
        >>> agents = {"claude": ClaudeAgent(api_key="...")}
        >>> executor = APIExecutor(agents, registry)
        >>> await executor.initialize()
        >>>
        >>> result = await executor.execute(
        ...     task_prompt="List all users in the database",
        ...     agent_name="claude",
        ...     task_id="task1"
        ... )
    """

    def __init__(
        self,
        agents: Optional[Dict[str, 'BaseAgent']] = None,
        tool_registry: Optional['ToolRegistry'] = None
    ):
        """
        Initialize API executor

        Args:
            agents: Dictionary of agent instances (e.g., {"claude": ClaudeAgent()})
            tool_registry: ToolRegistry for tool execution
        """
        self.agents = agents or {}
        self.tool_registry = tool_registry
        self.multi_round = None
        self.initialized = False

    async def initialize(self, **kwargs) -> None:
        """
        Initialize API executor

        Args:
            **kwargs: Optional parameters
                - agents: Dict of agents (overrides constructor)
                - tool_registry: ToolRegistry (overrides constructor)
                - docker_image: Docker image for OS tasks
                - db_type: Database type ("mysql" or "sqlite")
                - database: Database name or path

        Raises:
            ExecutorInitializationError: If initialization fails
        """
        if self.initialized:
            return

        # Override with kwargs if provided
        if "agents" in kwargs:
            self.agents = kwargs["agents"]
        if "tool_registry" in kwargs:
            self.tool_registry = kwargs["tool_registry"]

        # Validate
        if not self.agents:
            raise ExecutorInitializationError("No agents provided")
        if not self.tool_registry:
            raise ExecutorInitializationError("No tool_registry provided")

        # Initialize tool registry if needed
        if not self.tool_registry.initialized:
            docker_image = kwargs.get("docker_image", "ubuntu:22.04")
            db_type = kwargs.get("db_type", "sqlite")
            database = kwargs.get("database", "test_agentbench.db")

            await self.tool_registry.initialize(
                docker_image=docker_image,
                db_type=db_type,
                database=database
            )

        # Create MultiRoundExecutor
        # Note: We'll set the agent dynamically in execute()
        from .multi_round_executor import MultiRoundExecutor
        self.multi_round = MultiRoundExecutor(
            agent=None,  # Will be set per task
            tool_registry=self.tool_registry
        )

        self.initialized = True

    async def execute(
        self,
        task_prompt: str,
        agent_name: str,
        task_id: str,
        **kwargs
    ) -> TaskResult:
        """
        Execute task using API + MultiRoundExecutor

        Args:
            task_prompt: Task description/prompt
            agent_name: Agent name (key in self.agents)
            task_id: Unique task identifier
            **kwargs: Optional parameters
                - max_rounds: Maximum rounds for multi-round execution (default: 10)
                - extract_data: Whether to extract structured data (default: False, Day 5 feature)

        Returns:
            TaskResult with execution details

        Raises:
            ExecutorInitializationError: If not initialized
            KeyError: If agent_name not in self.agents
        """
        if not self.initialized:
            raise ExecutorInitializationError("Executor not initialized. Call initialize() first.")

        if agent_name not in self.agents:
            available = ", ".join(self.agents.keys())
            return TaskResult(
                task_id=task_id,
                success=False,
                output="",
                agent=agent_name,
                error=f"Agent '{agent_name}' not found. Available: {available}"
            )

        start_time = time.time()
        agent = self.agents[agent_name]

        # Set agent for this task
        self.multi_round.agent = agent

        # Get parameters
        max_rounds = kwargs.get("max_rounds", 10)
        extract_data = kwargs.get("extract_data", False)

        try:
            # Execute via MultiRoundExecutor
            result = await self.multi_round.execute_task(
                task_prompt=task_prompt,
                max_rounds=max_rounds,
                verbose=False
            )

            latency = time.time() - start_time

            # Extract parsed data if requested (Day 5 feature)
            parsed_data = None
            if extract_data and result.get("success"):
                parsed_data = self._extract_structured_data(result)

            return TaskResult(
                task_id=task_id,
                success=result["success"],
                output=result["final_answer"],
                parsed_data=parsed_data,
                latency=latency,
                agent=agent.name,
                error=None if result["success"] else "Task incomplete",
                metadata={
                    "rounds": result["rounds"],
                    "tool_calls_count": result["tool_calls_count"],
                    "max_rounds_reached": result.get("max_rounds_reached", False)
                }
            )

        except Exception as e:
            latency = time.time() - start_time
            return TaskResult(
                task_id=task_id,
                success=False,
                output="",
                latency=latency,
                agent=agent_name,
                error=f"Execution error: {str(e)}",
                metadata={"exception": type(e).__name__}
            )

    def _extract_structured_data(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from task result (Day 5 feature)

        Attempts to parse JSON from final_answer or tool results.
        Used for dependency injection between tasks.

        Args:
            result: Result from MultiRoundExecutor

        Returns:
            Dictionary of extracted data, or None if no data found

        Example output:
            {
                "user_count": 5,
                "users": ["alice", "bob", "charlie"],
                "disk_usage": "45%"
            }
        """
        final_answer = result.get("final_answer", "")

        # Try to parse as JSON
        try:
            # Look for JSON in final answer
            json_match = re.search(r'\{[^}]+\}', final_answer)
            if json_match:
                return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

        # Try to extract key-value pairs
        # Pattern: "key: value" or "key = value"
        data = {}
        for match in re.finditer(r'(\w+)[:=]\s*([^\n,]+)', final_answer):
            key = match.group(1)
            value = match.group(2).strip()

            # Try to parse value as number
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string

            data[key] = value

        return data if data else None

    async def shutdown(self) -> None:
        """Clean up resources"""
        if self.tool_registry:
            await self.tool_registry.close()
        self.initialized = False


# TODO: Day 5 - Complete _extract_structured_data() with more robust parsing
# TODO: Day 5 - Add support for output schema validation
# TODO: Day 5 - Implement data transformation for input mapping
