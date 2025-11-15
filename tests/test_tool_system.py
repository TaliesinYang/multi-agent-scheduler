"""
Comprehensive tests for tool composition system
"""
import pytest
import asyncio
from typing import Dict, Any, List, Optional
from src.tool_system import (
    ToolParameter, Tool, ToolRegistry, ToolChain,
    ToolEnabledAgent, ToolType, ToolCall,
    create_calculator_tool, create_web_search_tool, create_file_tool
)


class TestToolParameter:
    """Test ToolParameter class"""

    def test_create_parameter(self):
        """Test creating a tool parameter"""
        param = ToolParameter(
            name="query",
            type="string",
            description="Search query",
            required=True
        )

        assert param.name == "query"
        assert param.type == "string"
        assert param.required is True

    def test_parameter_with_default(self):
        """Test parameter with default value"""
        param = ToolParameter(
            name="limit",
            type="number",
            description="Result limit",
            required=False,
            default=10
        )

        assert param.default == 10
        assert param.required is False


class TestTool:
    """Test Tool class"""

    def test_create_tool(self):
        """Test creating a tool"""
        async def handler(x: int, y: int) -> int:
            return x + y

        tool = Tool(
            name="add",
            description="Add two numbers",
            parameters=[
                ToolParameter("x", "number", "First number", True),
                ToolParameter("y", "number", "Second number", True)
            ],
            handler=handler
        )

        assert tool.name == "add"
        assert len(tool.parameters) == 2

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool"""
        async def multiply(x: int, y: int) -> int:
            return x * y

        tool = Tool(
            name="multiply",
            description="Multiply numbers",
            parameters=[
                ToolParameter("x", "number", "First", True),
                ToolParameter("y", "number", "Second", True)
            ],
            handler=multiply
        )

        result = await tool.execute(x=5, y=3)
        assert result == 15

    @pytest.mark.asyncio
    async def test_execute_missing_required_param(self):
        """Test execution with missing required parameter"""
        async def handler(x: int, y: int) -> int:
            return x + y

        tool = Tool(
            name="add",
            description="Add numbers",
            parameters=[
                ToolParameter("x", "number", "First", True),
                ToolParameter("y", "number", "Second", True)
            ],
            handler=handler
        )

        with pytest.raises(ValueError, match="Missing required parameter"):
            await tool.execute(x=5)

    @pytest.mark.asyncio
    async def test_execute_with_default_param(self):
        """Test execution with default parameter"""
        async def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        tool = Tool(
            name="greet",
            description="Greet someone",
            parameters=[
                ToolParameter("name", "string", "Name", True),
                ToolParameter("greeting", "string", "Greeting", False, default="Hello")
            ],
            handler=greet
        )

        result = await tool.execute(name="Alice")
        assert result == "Hello, Alice!"

    def test_to_openai_function(self):
        """Test OpenAI function calling format conversion"""
        tool = Tool(
            name="search",
            description="Search for information",
            parameters=[
                ToolParameter("query", "string", "Search query", True),
                ToolParameter("limit", "number", "Max results", False, default=10)
            ]
        )

        openai_format = tool.to_openai_function()

        assert openai_format["name"] == "search"
        assert openai_format["description"] == "Search for information"
        assert "parameters" in openai_format
        assert "query" in openai_format["parameters"]["properties"]
        assert "query" in openai_format["parameters"]["required"]
        assert "limit" not in openai_format["parameters"]["required"]


class TestToolRegistry:
    """Test ToolRegistry class"""

    def test_register_tool(self):
        """Test registering a tool"""
        registry = ToolRegistry()

        async def handler():
            pass

        tool = Tool("test", "Test tool", [], handler=handler)
        registry.register(tool)

        assert registry.get("test") is not None

    def test_get_tool(self):
        """Test getting a tool"""
        registry = ToolRegistry()

        async def handler():
            return "result"

        tool = Tool("getter", "Get tool", [], handler=handler)
        registry.register(tool)

        retrieved = registry.get("getter")
        assert retrieved is not None
        assert retrieved.name == "getter"

    def test_list_tools(self):
        """Test listing all tools"""
        registry = ToolRegistry()

        async def handler():
            pass

        registry.register(Tool("tool1", "Tool 1", [], handler=handler))
        registry.register(Tool("tool2", "Tool 2", [], handler=handler))

        tools = registry.list_tools()
        assert len(tools) == 2

    def test_to_openai_functions(self):
        """Test getting tools in OpenAI format"""
        registry = ToolRegistry()

        async def handler(x: int):
            return x

        tool = Tool(
            "calc",
            "Calculator",
            [ToolParameter("x", "number", "Number", True)],
            handler=handler
        )
        registry.register(tool)

        functions = registry.to_openai_functions()
        assert len(functions) == 1
        assert functions[0]["name"] == "calc"


class TestToolChain:
    """Test ToolChain class"""

    @pytest.mark.asyncio
    async def test_simple_chain(self):
        """Test simple tool chain"""
        registry = ToolRegistry()

        async def double(x: int) -> int:
            return x * 2

        async def add_ten(x: int) -> int:
            return x + 10

        registry.register(Tool(
            "double", "Double",
            [ToolParameter("x", "number", "X", True)],
            handler=double
        ))
        registry.register(Tool(
            "add_ten", "Add 10",
            [ToolParameter("x", "number", "X", True)],
            handler=add_ten
        ))

        chain = ToolChain(registry)
        chain.add_step("double", {"x": 5})
        chain.add_step("add_ten", {"x": "${double}"})

        results = await chain.execute()

        assert len(results) == 2
        assert results[0].result == 10  # 5 * 2
        assert results[1].result == 20  # 10 + 10

    @pytest.mark.asyncio
    async def test_chain_error_handling(self):
        """Test chain error handling"""
        registry = ToolRegistry()

        async def failing_tool(x: int) -> int:
            raise ValueError("Intentional error")

        registry.register(Tool(
            "fail", "Fail",
            [ToolParameter("x", "number", "X", True)],
            handler=failing_tool
        ))

        chain = ToolChain(registry)
        chain.add_step("fail", {"x": 1})

        results = await chain.execute()
        assert len(results) == 1
        assert results[0].success is False
        assert "Intentional error" in results[0].error


class TestBuiltInTools:
    """Test built-in tool factories"""

    @pytest.mark.asyncio
    async def test_calculator_tool(self):
        """Test calculator tool"""
        calc = create_calculator_tool()

        # Addition
        result = await calc.execute(expression="5 + 3")
        assert result == 8

        # Multiplication
        result = await calc.execute(expression="6 * 7")
        assert result == 42

        # Complex expression
        result = await calc.execute(expression="(10 + 5) * 2")
        assert result == 30

    @pytest.mark.asyncio
    async def test_web_search_tool(self):
        """Test web search tool"""
        search = create_web_search_tool()

        # Mock search
        result = await search.execute(query="Python programming", num_results=5)

        # Should return mock results
        assert isinstance(result, list)
        assert len(result) == 5
        assert "title" in result[0]
        assert "url" in result[0]

    @pytest.mark.asyncio
    async def test_file_tool(self):
        """Test file operations tool"""
        import tempfile
        import os

        file_tool = create_file_tool()

        # Create temp file
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)

        try:
            # Write file
            await file_tool.execute(
                operation="write",
                path=temp_path,
                content="Hello, World!"
            )

            # Read file
            content = await file_tool.execute(
                operation="read",
                path=temp_path
            )
            assert content == "Hello, World!"

            # Check exists
            exists = await file_tool.execute(
                operation="exists",
                path=temp_path
            )
            assert exists == "True"

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestToolEnabledAgent:
    """Test ToolEnabledAgent wrapper"""

    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """Test creating tool-enabled agent"""
        # Mock base agent
        class MockAgent:
            async def call(self, prompt: str) -> Dict[str, Any]:
                return {"result": "Processed"}

        registry = ToolRegistry()
        base_agent = MockAgent()
        tool_agent = ToolEnabledAgent(base_agent, registry)

        assert tool_agent.base_agent == base_agent
        assert tool_agent.tool_registry == registry


class TestIntegration:
    """Integration tests for tool system"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete tool workflow"""
        # Setup registry
        registry = ToolRegistry()

        # Add custom tools
        async def fetch_data(source: str) -> List[int]:
            return [1, 2, 3, 4, 5]

        async def calculate_sum(numbers: List[int]) -> int:
            return sum(numbers)

        registry.register(Tool(
            "fetch_data",
            "Fetch data",
            [ToolParameter("source", "string", "Data source", True)],
            handler=fetch_data
        ))

        registry.register(Tool(
            "calculate_sum",
            "Calculate sum",
            [ToolParameter("numbers", "array", "Numbers", True)],
            handler=calculate_sum
        ))

        # Create chain
        chain = ToolChain(registry)
        chain.add_step("fetch_data", {"source": "api"})
        chain.add_step("calculate_sum", {"numbers": "${fetch_data}"})

        # Execute
        results = await chain.execute()

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].result == 15  # sum([1,2,3,4,5])

    @pytest.mark.asyncio
    async def test_openai_compatible_workflow(self):
        """Test OpenAI-compatible function calling"""
        registry = ToolRegistry()
        registry.register(create_calculator_tool())
        registry.register(create_web_search_tool())

        # Get tools in OpenAI format
        functions = registry.to_openai_functions()

        # Verify format
        assert len(functions) == 2
        for func in functions:
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert func["parameters"]["type"] == "object"
            assert "properties" in func["parameters"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
