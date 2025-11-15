"""
Tool Registry and Router

Defines AgentBench tools and routes tool calls to appropriate executors.
"""

from typing import Dict, Any, Callable, Awaitable
from .docker_executor import DockerExecutor, get_default_executor as get_docker_executor
from .database_executor import DatabaseExecutor, get_mysql_executor


# AgentBench Tool Definitions (Anthropic format)
AGENTBENCH_TOOLS = [
    {
        "name": "execute_shell",
        "description": "Execute a shell command in a Docker container. Use this to perform OS operations like listing files, searching text, managing users, checking permissions, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute (e.g., 'ls -la /root', 'grep pattern file.txt')"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "execute_sql",
        "description": "Execute a SQL query on the database. Use this to query tables, filter data, join tables, aggregate results, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute (e.g., 'SELECT * FROM users WHERE age > 18')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "commit_final_answer",
        "description": "Submit your final answer when you have completed the task. This should be called after you have gathered all necessary information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Your final answer to the task"
                }
            },
            "required": ["answer"]
        }
    }
]


class ToolRegistry:
    """
    Tool registry and router for AgentBench tasks

    Routes tool calls to appropriate executors and manages executor lifecycle.

    Example:
        registry = ToolRegistry()
        await registry.initialize()

        result = await registry.execute_tool("execute_shell", {"command": "ls /root"})
        print(result)

        await registry.shutdown()
    """

    def __init__(
        self,
        docker_executor: DockerExecutor = None,
        database_executor: DatabaseExecutor = None
    ):
        """
        Initialize tool registry

        Args:
            docker_executor: Docker executor instance (optional, will create default)
            database_executor: Database executor instance (optional, will create default)
        """
        self.docker_executor = docker_executor
        self.database_executor = database_executor
        self.initialized = False

        # Tool routing map
        self.tool_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[str]]] = {
            "execute_shell": self._handle_execute_shell,
            "execute_sql": self._handle_execute_sql,
            "commit_final_answer": self._handle_commit_answer
        }

    async def initialize(
        self,
        docker_image: str = "ubuntu:22.04",
        db_type: str = "mysql",
        **db_kwargs
    ):
        """
        Initialize executors

        Args:
            docker_image: Docker image for OS tasks (default: ubuntu:22.04)
            db_type: Database type ("mysql" or "sqlite")
            **db_kwargs: Database connection parameters (host, user, password, database)
        """
        if self.initialized:
            return

        # Initialize Docker executor
        if not self.docker_executor:
            self.docker_executor = get_docker_executor()

        await self.docker_executor.start_container(image=docker_image)

        # Initialize Database executor
        if not self.database_executor:
            if db_type == "mysql":
                self.database_executor = get_mysql_executor(**db_kwargs)
            else:
                self.database_executor = DatabaseExecutor(db_type="sqlite", **db_kwargs)

        await self.database_executor.connect()

        self.initialized = True

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result as string

        Raises:
            ValueError: If tool not found
            RuntimeError: If not initialized or execution fails
        """
        if not self.initialized:
            raise RuntimeError("ToolRegistry not initialized. Call initialize() first.")

        if tool_name not in self.tool_handlers:
            raise ValueError(f"Unknown tool: {tool_name}")

        handler = self.tool_handlers[tool_name]
        return await handler(arguments)

    async def _handle_execute_shell(self, arguments: Dict[str, Any]) -> str:
        """Handle execute_shell tool call"""
        command = arguments.get("command")
        if not command:
            return "Error: Missing 'command' argument"

        try:
            result = await self.docker_executor.execute_shell(command, timeout=30.0)
            return result
        except Exception as e:
            return f"Error executing shell command: {str(e)}"

    async def _handle_execute_sql(self, arguments: Dict[str, Any]) -> str:
        """Handle execute_sql tool call"""
        query = arguments.get("query")
        if not query:
            return "Error: Missing 'query' argument"

        try:
            result = await self.database_executor.execute_sql(query, timeout=30.0)
            return result
        except Exception as e:
            return f"Error executing SQL query: {str(e)}"

    async def _handle_commit_answer(self, arguments: Dict[str, Any]) -> str:
        """Handle commit_final_answer tool call"""
        answer = arguments.get("answer")
        if not answer:
            return "Error: Missing 'answer' argument"

        # This is a special tool that signals task completion
        # The multi-round executor will use this to stop the loop
        return f"FINAL_ANSWER: {answer}"

    async def shutdown(self):
        """Shutdown all executors"""
        if self.docker_executor:
            await self.docker_executor.stop_container()

        if self.database_executor:
            await self.database_executor.close()

        self.initialized = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()


# Global registry instance
_global_registry: ToolRegistry = None


def get_global_registry() -> ToolRegistry:
    """
    Get or create global tool registry

    Returns:
        Shared ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
