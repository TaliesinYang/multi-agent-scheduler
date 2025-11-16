"""
Tool Executor Abstraction Layer

Provides a unified interface for executing tasks across different backends:
- CLI mode (Claude CLI with local Bash tools)
- API mode (Anthropic API with Tool Calling)
- Hybrid mode (mix of CLI and API)

Design Pattern: Strategy Pattern + Dependency Inversion Principle
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskResult:
    """
    Unified task execution result

    Attributes:
        task_id: Unique task identifier
        success: Whether task completed successfully
        output: Raw output text from agent
        parsed_data: Structured data extracted from output (for dependency injection)
        latency: Task execution time in seconds
        agent: Agent name used for execution
        error: Error message if failed
        metadata: Additional execution metadata
    """
    task_id: str
    success: bool
    output: str
    parsed_data: Optional[Dict[str, Any]] = None
    latency: float = 0.0
    agent: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Add timestamp to metadata"""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now().isoformat()


class ToolExecutor(ABC):
    """
    Abstract base class for tool executors

    Different implementations:
    - CLIExecutor: Uses Claude CLI with local Bash tools
    - APIExecutor: Uses Anthropic API with MultiRoundExecutor
    - MockExecutor: For testing purposes

    Example:
        >>> executor = CLIExecutor()
        >>> await executor.initialize()
        >>> result = await executor.execute(
        ...     task_prompt="List files in /root",
        ...     agent_name="claude",
        ...     task_id="task1"
        ... )
        >>> print(result.output)
    """

    @abstractmethod
    async def execute(
        self,
        task_prompt: str,
        agent_name: str,
        task_id: str,
        **kwargs
    ) -> TaskResult:
        """
        Execute a single task

        Args:
            task_prompt: Task description/prompt for the agent
            agent_name: Name of agent to use (e.g., "claude", "gemini")
            task_id: Unique identifier for this task
            **kwargs: Additional executor-specific parameters

        Returns:
            TaskResult with execution details

        Raises:
            Exception: If task execution fails critically
        """
        pass

    @abstractmethod
    async def initialize(self, **kwargs) -> None:
        """
        Initialize executor resources

        Args:
            **kwargs: Executor-specific initialization parameters

        Example:
            >>> executor = CLIExecutor()
            >>> await executor.initialize(db_path="test.db")
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Clean up executor resources

        Should be called when executor is no longer needed.
        Releases connections, closes files, etc.
        """
        pass

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()


class ExecutorError(Exception):
    """Base exception for executor errors"""
    pass


class ExecutorInitializationError(ExecutorError):
    """Raised when executor initialization fails"""
    pass


class ExecutorExecutionError(ExecutorError):
    """Raised when task execution fails"""
    pass
