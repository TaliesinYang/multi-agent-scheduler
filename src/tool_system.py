"""
Tool Composition System

Enables function calling, tool chaining, and composable operations for agents.
Inspired by LangChain tools and OpenAI function calling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import asyncio
import json


class ToolType(Enum):
    """Tool types"""
    FUNCTION = "function"
    API = "api"
    SHELL = "shell"
    DATABASE = "database"
    FILE = "file"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


@dataclass
class Tool:
    """
    Tool definition for agent use

    Compatible with OpenAI function calling format.
    """
    name: str
    description: str
    parameters: List[ToolParameter]
    tool_type: ToolType = ToolType.FUNCTION
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    async def execute(self, **kwargs) -> Any:
        """Execute tool with parameters"""
        if not self.handler:
            raise ValueError(f"Tool {self.name} has no handler")

        # Validate required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                if param.default is not None:
                    kwargs[param.name] = param.default
                else:
                    raise ValueError(f"Missing required parameter: {param.name}")

        # Execute handler
        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(**kwargs)
        else:
            return self.handler(**kwargs)


class ToolRegistry:
    """Registry of available tools"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self, tool_type: Optional[ToolType] = None) -> List[Tool]:
        """List all tools, optionally filtered by type"""
        if tool_type:
            return [t for t in self.tools.values() if t.tool_type == tool_type]
        return list(self.tools.values())

    def to_openai_functions(self) -> List[Dict[str, Any]]:
        """Convert all tools to OpenAI function format"""
        return [tool.to_openai_function() for tool in self.tools.values()]


# Built-in tools
def create_calculator_tool() -> Tool:
    """Create calculator tool"""
    async def calculate(expression: str) -> float:
        """Safely evaluate math expression"""
        try:
            # Simple safe evaluation (limited for security)
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")
            return eval(expression)
        except Exception as e:
            raise ValueError(f"Calculation error: {e}")

    return Tool(
        name="calculator",
        description="Performs mathematical calculations",
        parameters=[
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate",
                required=True
            )
        ],
        handler=calculate
    )


def create_web_search_tool() -> Tool:
    """Create web search tool (placeholder)"""
    async def search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Simulated web search"""
        return [
            {
                "title": f"Result {i+1} for: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"Summary of result {i+1}"
            }
            for i in range(num_results)
        ]

    return Tool(
        name="web_search",
        description="Search the web for information",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            ToolParameter(
                name="num_results",
                type="number",
                description="Number of results to return",
                required=False,
                default=5
            )
        ],
        handler=search
    )


def create_file_tool() -> Tool:
    """Create file operations tool"""
    async def file_operation(
        operation: str,
        path: str,
        content: Optional[str] = None
    ) -> str:
        """Perform file operations"""
        from pathlib import Path

        if operation == "read":
            return Path(path).read_text()
        elif operation == "write":
            Path(path).write_text(content or "")
            return f"Written to {path}"
        elif operation == "exists":
            return str(Path(path).exists())
        else:
            raise ValueError(f"Unknown operation: {operation}")

    return Tool(
        name="file_operations",
        description="Read, write, and check file existence",
        parameters=[
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=True,
                enum=["read", "write", "exists"]
            ),
            ToolParameter(
                name="path",
                type="string",
                description="File path",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write (for write operation)",
                required=False
            )
        ],
        handler=file_operation
    )


@dataclass
class ToolCall:
    """Record of a tool call"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None
    execution_time: float = 0.0


class ToolChain:
    """Chain of tools for sequential execution"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.steps: List[tuple[str, Dict[str, Any]]] = []

    def add_step(self, tool_name: str, parameters: Dict[str, Any]) -> 'ToolChain':
        """Add a step to the chain (fluent interface)"""
        self.steps.append((tool_name, parameters))
        return self

    async def execute(self) -> List[ToolCall]:
        """Execute chain sequentially"""
        results = []
        context = {}

        for tool_name, params in self.steps:
            tool = self.registry.get(tool_name)
            if not tool:
                results.append(ToolCall(
                    tool_name=tool_name,
                    parameters=params,
                    result=None,
                    success=False,
                    error=f"Tool not found: {tool_name}"
                ))
                break

            # Resolve parameter references to previous results
            resolved_params = self._resolve_parameters(params, context)

            # Execute tool
            import time
            start = time.time()
            try:
                result = await tool.execute(**resolved_params)
                execution_time = time.time() - start

                call = ToolCall(
                    tool_name=tool_name,
                    parameters=resolved_params,
                    result=result,
                    success=True,
                    execution_time=execution_time
                )
                results.append(call)

                # Update context with result
                context[tool_name] = result

            except Exception as e:
                execution_time = time.time() - start
                call = ToolCall(
                    tool_name=tool_name,
                    parameters=resolved_params,
                    result=None,
                    success=False,
                    error=str(e),
                    execution_time=execution_time
                )
                results.append(call)
                break

        return results

    def _resolve_parameters(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve parameter references like ${tool_name}"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Reference to previous tool result
                ref_tool = value[2:-1]
                resolved[key] = context.get(ref_tool)
            else:
                resolved[key] = value
        return resolved


class ToolEnabledAgent:
    """Wrapper to add tool capabilities to agents"""

    def __init__(self, base_agent, tool_registry: ToolRegistry):
        self.base_agent = base_agent
        self.tool_registry = tool_registry
        self.tool_calls: List[ToolCall] = []

    async def call_with_tools(
        self,
        prompt: str,
        available_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Call agent with tool access

        Args:
            prompt: Prompt with tool usage instructions
            available_tools: List of tool names to make available

        Returns:
            Result with tool calls
        """
        # Get available tools
        if available_tools:
            tools = [self.tool_registry.get(name) for name in available_tools]
            tools = [t for t in tools if t is not None]
        else:
            tools = self.tool_registry.list_tools()

        # Format tools in prompt
        tool_descriptions = "\n".join([
            f"- {t.name}: {t.description}"
            for t in tools
        ])

        enhanced_prompt = f"""{prompt}

Available Tools:
{tool_descriptions}

To use a tool, respond with JSON:
{{"tool": "tool_name", "parameters": {{"param": "value"}}}}
"""

        # Call base agent
        result = await self.base_agent.call(enhanced_prompt)

        # Check if agent wants to use a tool
        if result.get('result'):
            response = result['result']
            try:
                # Try to parse as JSON
                if response.strip().startswith('{'):
                    tool_request = json.loads(response)
                    if 'tool' in tool_request:
                        # Execute tool
                        tool_call = await self._execute_tool(
                            tool_request['tool'],
                            tool_request.get('parameters', {})
                        )
                        self.tool_calls.append(tool_call)
                        result['tool_call'] = tool_call
            except json.JSONDecodeError:
                pass

        return result

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> ToolCall:
        """Execute a tool and record the call"""
        tool = self.tool_registry.get(tool_name)

        import time
        start = time.time()

        if not tool:
            return ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                success=False,
                error=f"Tool not found: {tool_name}",
                execution_time=time.time() - start
            )

        try:
            result = await tool.execute(**parameters)
            return ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                success=True,
                execution_time=time.time() - start
            )
        except Exception as e:
            return ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                success=False,
                error=str(e),
                execution_time=time.time() - start
            )
