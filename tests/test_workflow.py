"""
Tests for Workflow Graph Engine

Tests the graph-based workflow functionality including conditional branching,
parallel execution, loops, and scheduler integration.
"""

import pytest
import asyncio
from src.workflow_graph import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    WorkflowState,
    NodeType,
    EdgeType,
    create_simple_workflow
)
from src.scheduler import MultiAgentScheduler, Task
from src.agents import BaseAgent


class MockWorkflowAgent(BaseAgent):
    """Mock agent for workflow testing"""

    def __init__(self):
        super().__init__(name="MockWorkflow", max_concurrent=5)
        self.call_history = []

    async def call(self, prompt: str):
        """Regular call"""
        self.call_history.append(prompt)
        await asyncio.sleep(0.01)  # Simulate work
        return {
            "agent": self.name,
            "result": f"Processed: {prompt}",
            "latency": 0.01,
            "tokens": 10,
            "success": True
        }


class TestWorkflowBasics:
    """Test basic workflow functionality"""

    @pytest.mark.asyncio
    async def test_simple_linear_workflow(self):
        """Test simple linear workflow"""
        graph = WorkflowGraph(graph_id="linear_test")

        # Track execution order
        execution_order = []

        async def task1(state: WorkflowState):
            execution_order.append("task1")
            return {"value": 1}

        async def task2(state: WorkflowState):
            execution_order.append("task2")
            return {"value": state.get("value") + 1}

        async def task3(state: WorkflowState):
            execution_order.append("task3")
            return {"value": state.get("value") + 1}

        # Build graph
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK, handler=task1))
        graph.add_node(WorkflowNode("task2", NodeType.TASK, handler=task2))
        graph.add_node(WorkflowNode("task3", NodeType.TASK, handler=task3))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "task2"))
        graph.add_edge(WorkflowEdge("task2", "task3"))
        graph.add_edge(WorkflowEdge("task3", "end"))

        # Execute
        result = await graph.execute()

        # Verify execution order
        assert execution_order == ["task1", "task2", "task3"]
        assert result.get("value") == 3
        assert result.history == ["start", "task1", "task2", "task3", "end"]

    @pytest.mark.asyncio
    async def test_workflow_state_management(self):
        """Test workflow state management"""
        graph = WorkflowGraph()

        async def set_data(state: WorkflowState):
            return {"name": "Alice", "age": 30}

        async def update_data(state: WorkflowState):
            age = state.get("age", 0)
            return {"age": age + 1}

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("set", NodeType.TASK, handler=set_data))
        graph.add_node(WorkflowNode("update", NodeType.TASK, handler=update_data))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "set"))
        graph.add_edge(WorkflowEdge("set", "update"))
        graph.add_edge(WorkflowEdge("update", "end"))

        result = await graph.execute()

        assert result.get("name") == "Alice"
        assert result.get("age") == 31


class TestConditionalBranching:
    """Test conditional branching"""

    @pytest.mark.asyncio
    async def test_conditional_edges(self):
        """Test conditional edge routing"""
        graph = WorkflowGraph(graph_id="conditional_test")

        async def analyze(state: WorkflowState):
            return {"score": 85}

        async def success_path(state: WorkflowState):
            return {"result": "success"}

        async def failure_path(state: WorkflowState):
            return {"result": "failure"}

        # Build graph
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("analyze", NodeType.TASK, handler=analyze))
        graph.add_node(WorkflowNode("success", NodeType.TASK, handler=success_path))
        graph.add_node(WorkflowNode("failure", NodeType.TASK, handler=failure_path))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "analyze"))

        # Add conditional edges
        graph.add_edge(WorkflowEdge(
            "analyze",
            "success",
            edge_type=EdgeType.CONDITIONAL,
            condition=lambda s: s.get("score", 0) >= 80,
            label="pass"
        ))
        graph.add_edge(WorkflowEdge(
            "analyze",
            "failure",
            edge_type=EdgeType.CONDITIONAL,
            condition=lambda s: s.get("score", 0) < 80,
            label="fail"
        ))

        graph.add_edge(WorkflowEdge("success", "end"))
        graph.add_edge(WorkflowEdge("failure", "end"))

        # Execute
        result = await graph.execute()

        # Should take success path (score >= 80)
        assert result.get("result") == "success"
        assert "success" in result.history

    @pytest.mark.asyncio
    async def test_add_conditional_edges_helper(self):
        """Test add_conditional_edges helper method"""
        graph = WorkflowGraph()

        async def router(state: WorkflowState):
            return {"route": "option_a"}

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("router", NodeType.TASK, handler=router))
        graph.add_node(WorkflowNode("option_a", NodeType.TASK))
        graph.add_node(WorkflowNode("option_b", NodeType.TASK))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "router"))

        # Use helper method
        graph.add_conditional_edges(
            "router",
            {
                "option_a": lambda s: s.get("route") == "option_a",
                "option_b": lambda s: s.get("route") == "option_b"
            }
        )

        graph.add_edge(WorkflowEdge("option_a", "end"))
        graph.add_edge(WorkflowEdge("option_b", "end"))

        result = await graph.execute()

        assert "option_a" in result.history
        assert "option_b" not in result.history


class TestParallelExecution:
    """Test parallel execution"""

    @pytest.mark.asyncio
    async def test_parallel_branches(self):
        """Test parallel branch execution"""
        graph = WorkflowGraph(graph_id="parallel_test")

        # Track execution
        execution_times = {}

        async def branch_a(state: WorkflowState):
            import time
            execution_times["branch_a"] = time.time()
            await asyncio.sleep(0.1)
            return {"result_a": "A"}

        async def branch_b(state: WorkflowState):
            import time
            execution_times["branch_b"] = time.time()
            await asyncio.sleep(0.1)
            return {"result_b": "B"}

        async def branch_c(state: WorkflowState):
            import time
            execution_times["branch_c"] = time.time()
            await asyncio.sleep(0.1)
            return {"result_c": "C"}

        # Build parallel workflow
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("branch_a", NodeType.TASK, handler=branch_a))
        graph.add_node(WorkflowNode("branch_b", NodeType.TASK, handler=branch_b))
        graph.add_node(WorkflowNode("branch_c", NodeType.TASK, handler=branch_c))
        graph.add_node(WorkflowNode("end", NodeType.END))

        # Add parallel branches using helper
        graph.add_parallel_branches(
            "start",
            ["branch_a", "branch_b", "branch_c"],
            "end"
        )

        # Execute
        import time
        start_time = time.time()
        result = await graph.execute()
        duration = time.time() - start_time

        # All branches should have executed
        assert result.get("result_a") == "A"
        assert result.get("result_b") == "B"
        assert result.get("result_c") == "C"

        # Should take ~0.1s (parallel), not ~0.3s (serial)
        assert duration < 0.25  # Allow some overhead for system variations

        # Verify branches started nearly simultaneously
        times = list(execution_times.values())
        time_spread = max(times) - min(times)
        assert time_spread < 0.15  # Started within 150ms (account for asyncio scheduling)


class TestLoops:
    """Test loop functionality"""

    @pytest.mark.asyncio
    async def test_loop_execution(self):
        """Test loop with condition"""
        graph = WorkflowGraph(graph_id="loop_test")

        async def increment(state: WorkflowState):
            count = state.get("count", 0)
            return {"count": count + 1}

        async def check_done(state: WorkflowState):
            # Continue looping if count < 5
            return {}

        # Build loop
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("increment", NodeType.TASK, handler=increment))
        graph.add_node(WorkflowNode("check", NodeType.TASK, handler=check_done))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "increment"))
        graph.add_edge(WorkflowEdge("increment", "check"))

        # Add loop back edge with condition
        graph.add_edge(WorkflowEdge(
            "check",
            "increment",
            edge_type=EdgeType.LOOP_BACK,
            condition=lambda s: s.get("count", 0) < 5,
            label="continue"
        ))

        # Exit loop edge
        graph.add_edge(WorkflowEdge(
            "check",
            "end",
            edge_type=EdgeType.CONDITIONAL,
            condition=lambda s: s.get("count", 0) >= 5,
            label="done"
        ))

        # Execute
        result = await graph.execute()

        # Should have looped 5 times
        assert result.get("count") == 5

        # Check loop count tracking
        loop_id = "check->increment"
        assert loop_id in result.loop_counts
        assert result.loop_counts[loop_id] == 5


class TestWorkflowValidation:
    """Test workflow validation"""

    def test_validate_missing_start_node(self):
        """Test validation catches missing start node"""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("task1", NodeType.TASK))
        graph.add_node(WorkflowNode("end", NodeType.END))

        issues = graph.validate()
        assert any("START" in issue for issue in issues)

    def test_validate_missing_end_node(self):
        """Test validation catches missing end node"""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK))

        issues = graph.validate()
        assert any("END" in issue for issue in issues)

    def test_validate_unreachable_nodes(self):
        """Test validation catches unreachable nodes"""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK))
        graph.add_node(WorkflowNode("task2", NodeType.TASK))  # Unreachable
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "end"))

        issues = graph.validate()
        assert any("Unreachable" in issue and "task2" in issue for issue in issues)

    def test_validate_dead_end(self):
        """Test validation catches dead end nodes"""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        # task1 has no outgoing edges (dead end)

        issues = graph.validate()
        assert any("Dead end" in issue and "task1" in issue for issue in issues)


class TestSchedulerIntegration:
    """Test scheduler integration with workflows"""

    @pytest.mark.asyncio
    async def test_execute_workflow_with_scheduler(self):
        """Test executing workflow through scheduler"""
        agent = MockWorkflowAgent()
        scheduler = MultiAgentScheduler(agents={'mock': agent})

        # Create simple workflow
        graph = WorkflowGraph()

        async def task_handler(state: WorkflowState):
            return {"processed": True}

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK, handler=task_handler))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "end"))

        # Execute through scheduler
        result = await scheduler.execute_workflow(graph)

        assert result.get("processed") is True
        assert "task1" in result.history

    @pytest.mark.asyncio
    async def test_create_task_workflow_sequential(self):
        """Test creating sequential workflow from tasks"""
        agent = MockWorkflowAgent()
        scheduler = MultiAgentScheduler(agents={'mock': agent})

        tasks = [
            Task(id="task1", prompt="Do task 1", task_type="general"),
            Task(id="task2", prompt="Do task 2", task_type="general"),
            Task(id="task3", prompt="Do task 3", task_type="general")
        ]

        # Create sequential workflow
        graph = scheduler.create_task_workflow(tasks, workflow_type="sequential")

        # Validate structure
        assert len(graph.nodes) == 5  # start + 3 tasks + end
        assert graph.start_node == "start"
        assert "end" in graph.end_nodes

        # Execute
        result = await scheduler.execute_workflow(graph)

        # Check tasks were executed
        assert "task1" in result.history
        assert "task2" in result.history
        assert "task3" in result.history

    @pytest.mark.asyncio
    async def test_create_task_workflow_parallel(self):
        """Test creating parallel workflow from tasks"""
        agent = MockWorkflowAgent()
        scheduler = MultiAgentScheduler(agents={'mock': agent})

        tasks = [
            Task(id="task1", prompt="Do task 1", task_type="general"),
            Task(id="task2", prompt="Do task 2", task_type="general"),
            Task(id="task3", prompt="Do task 3", task_type="general")
        ]

        # Create parallel workflow
        graph = scheduler.create_task_workflow(tasks, workflow_type="parallel")

        # Execute
        result = await scheduler.execute_workflow(graph)

        # All tasks should have executed
        assert "task1" in result.history or result.get("task_task1_result")
        assert "task2" in result.history or result.get("task_task2_result")
        assert "task3" in result.history or result.get("task_task3_result")

    @pytest.mark.asyncio
    async def test_create_task_workflow_dependency(self):
        """Test creating dependency-based workflow from tasks"""
        agent = MockWorkflowAgent()
        scheduler = MultiAgentScheduler(agents={'mock': agent})

        tasks = [
            Task(id="task1", prompt="Do task 1", task_type="general"),
            Task(id="task2", prompt="Do task 2", task_type="general", depends_on=["task1"]),
            Task(id="task3", prompt="Do task 3", task_type="general", depends_on=["task1"]),
            Task(id="task4", prompt="Do task 4", task_type="general", depends_on=["task2", "task3"])
        ]

        # Create dependency workflow
        graph = scheduler.create_task_workflow(tasks, workflow_type="dependency")

        # Validate structure
        assert len(graph.nodes) >= 6  # start + 4 tasks + end

        # Execute
        result = await scheduler.execute_workflow(graph)

        # Check execution order (task1 before task2/task3, task2/task3 before task4)
        task1_idx = result.history.index("task1")
        task2_idx = result.history.index("task2")
        task3_idx = result.history.index("task3")
        task4_idx = result.history.index("task4")

        assert task1_idx < task2_idx
        assert task1_idx < task3_idx
        assert task2_idx < task4_idx
        assert task3_idx < task4_idx


class TestWorkflowVisualization:
    """Test workflow visualization"""

    def test_visualize_generates_dot(self):
        """Test DOT format generation"""
        graph = WorkflowGraph(graph_id="viz_test")
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "end"))

        dot = graph.visualize()

        # Check basic DOT structure
        assert "digraph viz_test" in dot
        assert '"start"' in dot
        assert '"task1"' in dot
        assert '"end"' in dot
        assert '->' in dot


class TestUtilityFunctions:
    """Test utility functions"""

    @pytest.mark.asyncio
    async def test_create_simple_workflow(self):
        """Test create_simple_workflow utility"""

        async def task1(state: WorkflowState):
            return {"step": 1}

        async def task2(state: WorkflowState):
            return {"step": 2}

        async def task3(state: WorkflowState):
            return {"step": 3}

        graph = create_simple_workflow([task1, task2, task3])

        # Should create linear workflow
        assert graph.start_node is not None
        assert len(graph.end_nodes) > 0

        # Execute
        result = await graph.execute()
        assert result.get("step") == 3


class TestErrorHandling:
    """Test error handling in workflows"""

    @pytest.mark.asyncio
    async def test_node_error_handling(self):
        """Test error handling in node execution"""
        graph = WorkflowGraph()

        async def failing_task(state: WorkflowState):
            raise ValueError("Task failed!")

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("fail", NodeType.TASK, handler=failing_task))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "fail"))
        graph.add_edge(WorkflowEdge("fail", "end"))

        # Should capture error
        with pytest.raises(ValueError):
            await graph.execute()

    @pytest.mark.asyncio
    async def test_workflow_timeout(self):
        """Test workflow execution timeout"""
        graph = WorkflowGraph()

        async def slow_task(state: WorkflowState):
            await asyncio.sleep(2)  # 2 seconds
            return {}

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("slow", NodeType.TASK, handler=slow_task))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "slow"))
        graph.add_edge(WorkflowEdge("slow", "end"))

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await graph.execute(timeout=0.5)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
